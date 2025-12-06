"""
Example client demonstrating usage of the Pharmaceutical Research Agent API.
Shows both streaming and non-streaming approaches.
"""

import requests
import json
import uuid
from typing import Optional


class ResearchAgentClient:
    """Client for interacting with the Pharmaceutical Research Agent API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id: Optional[str] = None
    
    def create_session(self) -> str:
        """Create a new session and return the session ID."""
        self.session_id = str(uuid.uuid4())
        print(f"📋 Created session: {self.session_id}")
        return self.session_id
    
    def query(
        self, 
        text: str, 
        agent_type: Optional[str] = None,
        use_session: bool = True
    ) -> dict:
        """
        Send a query and wait for complete result.
        
        Args:
            text: The research question
            agent_type: Optional override ('deep' or 'lite')
            use_session: Whether to use session-based routing
            
        Returns:
            Complete response with text, images, and metadata
        """
        payload = {"query": text}
        
        if use_session and self.session_id:
            payload["session_id"] = self.session_id
        
        if agent_type:
            payload["agent_type"] = agent_type
        
        print(f"🔍 Querying: {text[:60]}...")
        
        response = requests.post(
            f"{self.base_url}/api/query",
            json=payload,
            timeout=600  # Deep agent can take time
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response from {result['agent']} agent")
            print(f"   Text length: {len(result['text'])} chars")
            print(f"   Images: {len(result['images'])}")
            if result.get('file_path'):
                print(f"   File: {result['file_path']}")
            return result
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            response.raise_for_status()
    
    def query_stream(
        self, 
        text: str, 
        agent_type: Optional[str] = None,
        use_session: bool = True
    ):
        """
        Send a query with streaming response (Server-Sent Events).
        
        Yields events as they arrive from the agent.
        """
        payload = {"query": text}
        
        if use_session and self.session_id:
            payload["session_id"] = self.session_id
        
        if agent_type:
            payload["agent_type"] = agent_type
        
        print(f"🔍 Streaming query: {text[:60]}...")
        
        # Note: requests doesn't natively support SSE POST
        # For production, use httpx or a proper SSE client
        # This is a simplified demonstration
        
        response = requests.post(
            f"{self.base_url}/api/query/stream",
            json=payload,
            stream=True,
            timeout=600
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = json.loads(line_str[6:])
                        yield data
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            response.raise_for_status()
    
    def get_session_info(self) -> dict:
        """Get information about the current session."""
        if not self.session_id:
            raise ValueError("No active session")
        
        response = requests.get(f"{self.base_url}/api/sessions/{self.session_id}")
        return response.json()
    
    def reset_session(self):
        """Delete the current session to reset routing behavior."""
        if self.session_id:
            response = requests.delete(f"{self.base_url}/api/sessions/{self.session_id}")
            print(f"🗑️ Deleted session: {self.session_id}")
            self.session_id = None
            return response.json()
    
    def health_check(self) -> dict:
        """Check if the API is healthy."""
        response = requests.get(f"{self.base_url}/health")
        health = response.json()
        print(f"💚 Health: {health['status']} | Active sessions: {health['sessions_active']}")
        return health
    
    def save_images(self, result: dict, output_dir: str = "downloads"):
        """Save base64 images from result to files."""
        import os
        import base64
        
        os.makedirs(output_dir, exist_ok=True)
        
        for img in result.get('images', []):
            filepath = os.path.join(output_dir, img['filename'])
            
            # Decode and save
            img_data = base64.b64decode(img['base64'])
            with open(filepath, 'wb') as f:
                f.write(img_data)
            
            print(f"💾 Saved image: {filepath} ({img['size_bytes']} bytes)")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_basic_usage():
    """Example 1: Basic usage with session-based routing."""
    print("=" * 80)
    print("EXAMPLE 1: Basic Usage with Session-Based Routing")
    print("=" * 80)
    
    client = ResearchAgentClient()
    client.create_session()
    
    # First query - automatically uses deep agent
    print("\n--- First Query (Deep Agent) ---")
    result1 = client.query(
        "What are the repurposing opportunities for Minocycline in neurological disorders?"
    )
    print(f"\nResult preview: {result1['text'][:200]}...\n")
    
    # Second query - automatically uses lite agent
    print("\n--- Second Query (Lite Agent) ---")
    result2 = client.query(
        "What is the current market size for Minocycline?"
    )
    print(f"\nResult preview: {result2['text'][:200]}...\n")
    
    # Check session info
    session_info = client.get_session_info()
    print(f"\n📊 Session stats: {session_info['query_count']} queries")


def example_override_agent():
    """Example 2: Manually override agent selection."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Manual Agent Override")
    print("=" * 80)
    
    client = ResearchAgentClient()
    
    # Force lite agent for quick query
    print("\n--- Force Lite Agent ---")
    result = client.query(
        "Quick question: What is aspirin used for?",
        agent_type="lite"
    )
    print(f"Agent used: {result['agent']}")
    
    # Force deep agent for comprehensive research
    print("\n--- Force Deep Agent ---")
    result = client.query(
        "Comprehensive analysis of aspirin market dynamics",
        agent_type="deep"
    )
    print(f"Agent used: {result['agent']}")


def example_streaming():
    """Example 3: Streaming responses with real-time updates."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Streaming Response")
    print("=" * 80)
    
    client = ResearchAgentClient()
    client.create_session()
    
    print("\n--- Streaming Deep Research ---")
    
    for event in client.query_stream(
        "Research Minocycline repurposing opportunities",
        agent_type="deep"
    ):
        event_type = event.get('type')
        
        if event_type == 'session_info':
            data = event['data']
            print(f"📋 Session {data['session_id'][:8]}... | Agent: {data['agent']}")
        
        elif event_type == 'status':
            print(f"⏳ {event['content']}")
        
        elif event_type == 'step':
            data = event['data']
            print(f"🔄 Step {data['step_number']}: {data['sender']}")
            
            # Show tool calls if present
            if 'tool_calls' in data:
                for tc in data['tool_calls']:
                    print(f"   🔧 {tc['name']}")
        
        elif event_type == 'result':
            data = event['data']
            print(f"\n✅ FINAL RESULT:")
            print(f"   Agent: {data['agent']}")
            print(f"   Text length: {len(data['text'])} chars")
            print(f"   Images: {len(data['images'])}")
            print(f"   Steps: {data.get('total_steps', 'N/A')}")
            
            # Save images if any
            if data['images']:
                client.save_images(data)
                
            # Save report if provided as base64
            if data.get('report_base64') and data.get('report_filename'):
                import base64
                import os
                
                os.makedirs("downloads", exist_ok=True)
                report_path = os.path.join("downloads", data['report_filename'])
                
                try:
                    with open(report_path, "wb") as f:
                        f.write(base64.b64decode(data['report_base64']))
                    print(f"💾 Saved report: {report_path}")
                except Exception as e:
                    print(f"❌ Failed to save report: {e}")
        
        elif event_type == 'error':
            print(f"❌ ERROR: {event['content']}")


def example_session_management():
    """Example 4: Advanced session management."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Session Management")
    print("=" * 80)
    
    client = ResearchAgentClient()
    
    # Session 1
    client.create_session()
    client.query("First query - deep agent", use_session=True)
    client.query("Second query - lite agent", use_session=True)
    
    print(f"\nSession info: {client.get_session_info()}")
    
    # Reset session
    client.reset_session()
    
    # Session 2 - starts fresh
    client.create_session()
    client.query("New session - deep agent again", use_session=True)


def example_without_session():
    """Example 5: Queries without session tracking."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Queries Without Session")
    print("=" * 80)
    
    client = ResearchAgentClient()
    
    # Each query needs explicit agent type when not using sessions
    result1 = client.query("Query 1", agent_type="lite", use_session=False)
    result2 = client.query("Query 2", agent_type="deep", use_session=False)
    
    print(f"Query 1 used: {result1['agent']}")
    print(f"Query 2 used: {result2['agent']}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    try:
        # Check API health
        client = ResearchAgentClient()
        client.health_check()
        
        # Run examples
        print("\n")
        
        # Uncomment the examples you want to run:
        
        example_basic_usage()
        # example_override_agent()
        # example_streaming()
        # example_session_management()
        # example_without_session()
        
        print("\n" + "=" * 80)
        print("✅ Examples complete!")
        print("=" * 80)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API server")
        print("Make sure the server is running: python agents/route.py serve")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
