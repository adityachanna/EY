"""
Production-ready routing system for pharmaceutical research agents.
Handles session-based routing between deep research and lite agents with FastAPI integration.
"""

import os
import base64
import uuid
import asyncio
from typing import Optional, Dict, Any, Generator, List
from datetime import datetime
import logging
from pathlib import Path
import json

try:
    from agents.final import agent as deep_agent
    from agents.lite import get_answer as run_lite_agent
except ImportError:
    # Fallback for running directly from the agents directory
    from final import agent as deep_agent
    from lite import get_answer as run_lite_agent

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RouteLayer")


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for agent queries."""
    query: str = Field(..., description="The user's research question")
    agent_type: Optional[str] = Field(
        None, 
        description="Override agent selection: 'deep' or 'lite'. If not provided, uses session-based routing."
    )
    session_id: Optional[str] = Field(
        None,
        description="Session ID for maintaining conversation state. Auto-generated if not provided."
    )


class AgentResponse(BaseModel):
    """Response model for agent results."""
    agent: str = Field(..., description="Agent type that processed the query: 'deep' or 'lite'")
    text: str = Field(..., description="Response text in markdown format")
    images: List[Dict[str, str]] = Field(default=[], description="List of base64-encoded images")
    file_path: Optional[str] = Field(None, description="Path to saved report file (for deep agent)")
    report_base64: Optional[str] = Field(None, description="Base64 encoded content of the markdown report")
    report_filename: Optional[str] = Field(None, description="Filename of the saved report")
    session_id: str = Field(..., description="Session ID for tracking conversation state")
    timestamp: str = Field(..., description="ISO timestamp of the response")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: str


# ============================================================================
# ROUTE LAYER CLASS
# ============================================================================

class RouteLayer:
    """
    Main routing layer that manages agent selection and execution.
    
    Implements session-based routing:
    - First query in a session -> Deep Research Agent
    - Subsequent queries -> Lite Agent
    - Can be overridden via agent_type parameter
    """
    
    def __init__(self):
        """Initialize the RouteLayer with output directories and session tracking."""
        self.base_dir = Path(__file__).parent.parent
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Session tracking: session_id -> query_count
        self.sessions: Dict[str, int] = {}
        
        logger.info(f"RouteLayer initialized. Output directory: {self.output_dir}")

    def get_or_create_session(self, session_id: Optional[str] = None) -> tuple[str, bool]:
        """
        Get existing session or create a new one.
        
        Returns:
            tuple: (session_id, is_first_query)
        """
        if session_id and session_id in self.sessions:
            # Existing session
            self.sessions[session_id] += 1
            is_first = False
        else:
            # New session
            session_id = session_id or str(uuid.uuid4())
            self.sessions[session_id] = 1
            is_first = True
        
        return session_id, is_first

    def route(
        self, 
        query: str, 
        agent_type: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Route query to appropriate agent with streaming support.
        
        Args:
            query: The user's research question
            agent_type: Optional override ('deep' or 'lite')
            session_id: Session identifier for tracking conversation state
            
        Yields:
            Dict containing status updates, steps, or final results
        """
        # Session management
        session_id, is_first_query = self.get_or_create_session(session_id)
        
        # Determine target agent
        if agent_type:
            target_agent = agent_type.lower()
            if target_agent not in ['deep', 'lite']:
                yield {
                    "type": "error",
                    "content": f"Invalid agent_type '{agent_type}'. Must be 'deep' or 'lite'."
                }
                return
        else:
            # Default behavior: first query -> deep, subsequent -> lite
            target_agent = "deep" if is_first_query else "lite"

        logger.info(
            f"Session {session_id[:8]}... | Query #{self.sessions[session_id]} | "
            f"Agent: {target_agent} | Query: '{query[:50]}...'"
        )
        
        yield {
            "type": "session_info",
            "data": {
                "session_id": session_id,
                "query_count": self.sessions[session_id],
                "agent": target_agent,
                "is_first_query": is_first_query
            }
        }

        # Route to appropriate agent
        try:
            if target_agent == "deep":
                yield from self._run_deep_agent(query, session_id)
            else:
                yield from self._run_lite_agent(query, session_id)
        except Exception as e:
            logger.error(f"Routing error for session {session_id}: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"Routing failed: {str(e)}",
                "session_id": session_id
            }

    def _run_deep_agent(self, query: str, session_id: str) -> Generator[Dict[str, Any], None, None]:
        """
        Execute Deep Research Agent with full streaming support.
        
        Yields:
            - Status updates
            - Execution steps with tool calls
            - Final result with markdown report and base64 images
        """
        yield {
            "type": "status",
            "content": "🔬 Initiating Deep Research Agent...",
            "timestamp": datetime.now().isoformat()
        }

        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        # Setup steps logging file
        steps_file = self.base_dir / "steps.md"
        
        def log_step(message: str):
            """Log message to both terminal and steps.md file."""
            msg_str = str(message)
            print(msg_str)  # Terminal output
            try:
                with open(steps_file, "a", encoding='utf-8') as f:
                    f.write(msg_str + "\n")
            except Exception as e:
                logger.warning(f"Could not write to steps.md: {e}")
        
        # Initialize steps.md for this session
        log_step(f"\n--- Session Start: {thread_id[:16]} ---")
        log_step(f"Query: {query}")
        log_step(f"Timestamp: {datetime.now().isoformat()}")
        log_step("-" * 80)
        
        final_state = None
        step_count = 0
        
        try:
            # Stream execution steps
            for state in deep_agent.stream(
                {"messages": [{"role": "user", "content": query}]}, 
                config=config, 
                stream_mode="values"
            ):
                final_state = state
                step_count += 1
                
                if "messages" in state and state["messages"]:
                    last_msg = state["messages"][-1]
                    
                    # Get message details
                    sender = getattr(last_msg, "name", "DeepAgent")
                    msg_type = getattr(last_msg, "type", "assistant")
                    content = getattr(last_msg, "content", "")
                    
                    # Log to terminal and steps.md
                    log_step(f"\n[Step {step_count}] Role: {msg_type}")
                    if sender:
                        log_step(f"Sender: {sender}")
                    
                    if content:
                        content_preview = str(content)[:500] + "..." if len(str(content)) > 500 else str(content)
                        log_step(f"Content: {content_preview}")
                    
                    # Log tool calls
                    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                        log_step(f"Tool Calls ({len(last_msg.tool_calls)}):")
                        for tc in last_msg.tool_calls:
                            log_step(f"  - {tc.get('name', 'unknown')}: {tc.get('args', {})}")
                    
                    # Build step info for streaming
                    step_info = {
                        "step_number": step_count,
                        "role": msg_type,
                        "content": str(content) if content else "",
                        "sender": sender or "DeepAgent",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Include tool calls if present
                    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                        step_info["tool_calls"] = [
                            {
                                "name": tc.get("name", ""),
                                "args": tc.get("args", {})
                            }
                            for tc in last_msg.tool_calls
                        ]
                    
                    yield {"type": "step", "data": step_info}

        except Exception as e:
            error_msg = f"Deep Agent execution error: {e}"
            logger.error(error_msg, exc_info=True)
            log_step(f"\n❌ ERROR: {error_msg}")
            yield {
                "type": "error",
                "content": f"Deep Agent failed: {str(e)}",
                "session_id": session_id
            }
            return

        # Process final output
        if not final_state or "messages" not in final_state:
            log_step("\n❌ Deep Agent produced no output.")
            yield {
                "type": "error",
                "content": "Deep Agent produced no output.",
                "session_id": session_id
            }
            return
        
        result_msg = final_state["messages"][-1]
        report_content = str(result_msg.content)
        
        log_step(f"\n{'='*80}")
        log_step(f"✅ Execution Complete - {step_count} steps")
        log_step(f"{'='*80}")
        
        # Save markdown report
        report_filename = f"deep_report_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path = self.output_dir / report_filename
        
        try:
            report_path.write_text(report_content, encoding="utf-8")
            log_step(f"📄 Report saved to: {report_path}")
            yield {
                "type": "status",
                "content": f"📄 Report saved to {report_filename}",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            log_step(f"⚠️ Could not save report: {e}")
            yield {
                "type": "warning",
                "content": f"Could not save report file: {str(e)}"
            }
        
        # Collect and encode images
        yield {
            "type": "status",
            "content": "🖼️ Processing visualizations...",
            "timestamp": datetime.now().isoformat()
        }
        
        images = self._collect_images()
        
        if images:
            log_step(f"🖼️ Found {len(images)} visualization(s)")
            yield {
                "type": "status",
                "content": f"✅ Found {len(images)} visualization(s)",
                "timestamp": datetime.now().isoformat()
            }
        
        # Encode report content to base64
        report_base64 = None
        try:
            with open(report_path, "rb") as f:
                report_base64 = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encode report to base64: {e}")

        log_step(f"\n--- Session End: {thread_id[:16]} ---\n")
        
        # Final result
        yield {
            "type": "result",
            "data": {
                "agent": "deep",
                "text": report_content,
                "file_path": str(report_path),
                "report_base64": report_base64,
                "report_filename": report_filename,
                "images": images,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "total_steps": step_count
            }
        }

    def _run_lite_agent(self, query: str, session_id: str) -> Generator[Dict[str, Any], None, None]:
        """
        Execute Lite Agent for quick responses.
        
        Uses markdown knowledge base + internet search for fast answers.
        """
        yield {
            "type": "status",
            "content": "⚡ Consulting Lite Agent...",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Execute lite agent (synchronous)
            answer = run_lite_agent(query)
            
            yield {
                "type": "result",
                "data": {
                    "agent": "lite",
                    "text": answer,
                    "images": [],
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Lite Agent execution error: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"Lite Agent failed: {str(e)}",
                "session_id": session_id
            }

    def _collect_images(self) -> List[Dict[str, str]]:
        """
        Scan visualization directories and convert images to base64.
        
        Returns:
            List of dicts with filename, mime_type, and base64 data
        """
        images = []
        
        # Multiple possible paths for visualizations
        search_paths = [
            self.output_dir / "visualizations",
            self.output_dir / "output" / "visualizations"
        ]
        
        processed_files = set()
        supported_formats = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.svg']

        for viz_path in search_paths:
            if not viz_path.exists():
                continue
            
            for ext in supported_formats:
                for filepath in viz_path.glob(ext):
                    abs_path = filepath.resolve()
                    
                    # Skip duplicates
                    if abs_path in processed_files:
                        continue
                    
                    try:
                        # Read and encode image
                        with open(filepath, "rb") as image_file:
                            image_data = image_file.read()
                            encoded_string = base64.b64encode(image_data).decode('utf-8')
                        
                        # Determine MIME type
                        ext_lower = filepath.suffix[1:].lower()
                        mime_type = f"image/{ext_lower}"
                        if ext_lower == 'svg':
                            mime_type = "image/svg+xml"
                        
                        images.append({
                            "filename": filepath.name,
                            "mime_type": mime_type,
                            "base64": encoded_string,
                            "size_bytes": len(image_data)
                        })
                        
                        processed_files.add(abs_path)
                        logger.debug(f"Encoded image: {filepath.name}")
                        
                    except Exception as e:
                        logger.warning(f"Could not process image {filepath}: {e}")
        
        logger.info(f"Collected {len(images)} images")
        return images


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Initialize FastAPI app
app = FastAPI(
    title="Pharmaceutical Research Agent API",
    description="Production-ready API for deep research and lite query agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize router singleton
router = RouteLayer()


@app.get("/")
async def root():
    """API root - health check and info."""
    return {
        "service": "Pharmaceutical Research Agent API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "query": "/api/query",
            "query_stream": "/api/query/stream",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "sessions_active": len(router.sessions)
    }


@app.post("/api/query", response_model=AgentResponse)
async def query_agent(request: QueryRequest):
    """
    Process a research query and return the complete result.
    
    This endpoint waits for the full agent execution and returns the final result.
    For streaming responses, use /api/query/stream instead.
    """
    try:
        final_result = None
        
        # Collect all streaming results
        for event in router.route(
            query=request.query,
            agent_type=request.agent_type,
            session_id=request.session_id
        ):
            if event["type"] == "result":
                final_result = event["data"]
            elif event["type"] == "error":
                raise HTTPException(
                    status_code=500,
                    detail=event.get("content", "Unknown error occurred")
                )
        
        if not final_result:
            raise HTTPException(
                status_code=500,
                detail="Agent completed but produced no result"
            )
        
        return AgentResponse(**final_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query/stream")
async def query_agent_stream(request: QueryRequest):
    """
    Process a research query with Server-Sent Events (SSE) streaming.
    
    Returns a stream of events including:
    - session_info: Session initialization
    - status: Progress updates
    - step: Execution steps (for deep agent)
    - result: Final result
    - error: Error information
    """
    
    async def event_generator():
        """Generate SSE events from router stream."""
        try:
            for event in router.route(
                query=request.query,
                agent_type=request.agent_type,
                session_id=request.session_id
            ):
                # Format as SSE
                event_json = json.dumps(event, ensure_ascii=False)
                yield f"data: {event_json}\n\n"
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            error_event = {
                "type": "error",
                "content": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@app.get("/api/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a specific session."""
    if session_id not in router.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "query_count": router.sessions[session_id],
        "timestamp": datetime.now().isoformat()
    }


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and reset its state."""
    if session_id in router.sessions:
        del router.sessions[session_id]
        return {"message": "Session deleted", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


# ============================================================================
# MAIN & CLI
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Check if running as API server
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        import uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    else:
        # CLI testing mode
        print("=" * 80)
        print("PHARMACEUTICAL RESEARCH AGENT - Testing Mode")
        print("=" * 80)
        
        # Test 1: First query (should route to deep agent)
        print("\n🔬 TEST 1: First Query (Should use Deep Agent)")
        print("-" * 80)
        
        session_id = str(uuid.uuid4())
        for event in router.route(
            "What are the repurposing opportunities for Minocycline in neurological disorders?",
            session_id=session_id
        ):
            event_type = event.get("type")
            
            if event_type == "session_info":
                print(f"📋 Session: {event['data']['session_id'][:8]}... | Agent: {event['data']['agent']}")
            elif event_type == "status":
                print(f"⏳ {event['content']}")
            elif event_type == "step":
                data = event["data"]
                print(f"🔄 Step {data['step_number']}: {data['sender']}")
                if "tool_calls" in data:
                    for tc in data["tool_calls"]:
                        print(f"   🔧 Tool: {tc['name']}")
            elif event_type == "result":
                data = event["data"]
                print(f"\n✅ RESULT:")
                print(f"   Agent: {data['agent']}")
                print(f"   Text length: {len(data['text'])} chars")
                print(f"   Images: {len(data['images'])}")
                if "file_path" in data:
                    print(f"   Saved to: {data['file_path']}")
            elif event_type == "error":
                print(f"❌ ERROR: {event['content']}")
        
        # Test 2: Second query (should route to lite agent)
        print("\n" + "=" * 80)
        print("⚡ TEST 2: Second Query (Should use Lite Agent)")
        print("-" * 80)
        
        for event in router.route(
            "Summarize Minocycline's current market size",
            session_id=session_id
        ):
            event_type = event.get("type")
            
            if event_type == "session_info":
                print(f"📋 Session: {event['data']['session_id'][:8]}... | Agent: {event['data']['agent']}")
            elif event_type == "status":
                print(f"⏳ {event['content']}")
            elif event_type == "result":
                data = event["data"]
                print(f"\n✅ RESULT:")
                print(f"   Agent: {data['agent']}")
                print(f"   Text: {data['text'][:200]}...")
            elif event_type == "error":
                print(f"❌ ERROR: {event['content']}")
        
        print("\n" + "=" * 80)
        print("✅ Testing complete!")
        print(f"📊 Total sessions: {len(router.sessions)}")
        print("\nTo run as API server: python route.py serve")
        print("=" * 80)