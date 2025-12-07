import os
import functools
from dotenv import load_dotenv

from langchain.tools import tool
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware
from langchain.chat_models import init_chat_model
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# Load environment variables
load_dotenv()

# Initialize LLM
llm = init_chat_model(
    model="moonshotai/kimi-k2-instruct-0905",
    model_provider="groq",
    temperature=0.3
)

@functools.lru_cache(maxsize=1)
def _get_vectorstore():
    """
    Lazy-load the VectorStore. 
    This prevents the app from crashing on import if keys are missing/invalid.
    """
    try:
        print("Initializing Google Embeddings...")
        embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=os.getenv("API_4")
        )
        print("Initializing Pinecone VectorStore...")
        vectorstore = PineconeVectorStore(
            index_name="boundless-alder",
            embedding=embeddings,
            pinecone_api_key=os.getenv("PINECONE_API_KEY")
        )
        print("VectorStore initialized successfully.")
        return vectorstore
    except Exception as e:
        print(f"ERROR: Failed to initialize VectorStore: {e}")
        return None

@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    vectorstore = _get_vectorstore()
    
    if vectorstore is None:
         return "Error: Internal Knowledge Base is unavailable (Auth/Connection failed). check logs.", []
         
    try:
        retrieved_docs = vectorstore.similarity_search(query, k=4)
        if not retrieved_docs:
             return "No relevant internal documents found.", []
             
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\nContent: {doc.page_content}")
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs
    except Exception as e:
        return f"Error retrieval failed: {str(e)}", []


def get_knowledge_agent():
    """Create and return the internal knowledge agent."""
    # Define Tools and Prompt
    tools = [retrieve_context]
    system_prompt = (
        "You are a retriever agent. You are provided with context regarding "
        "internal documents of a company. Answer questions based on that and "
        "stick to that company's questions only."
    )

    # Create Agent with middleware
    agent = create_agent(
        llm, 
        tools=tools, 
        system_prompt=system_prompt,
        middleware=[
            ModelCallLimitMiddleware(run_limit=10, exit_behavior="end"),
            ToolCallLimitMiddleware(run_limit=3, exit_behavior="continue")
        ]
    )
    return agent


if __name__ == "__main__":
    # Smoke test the agent
    print("Testing Knowledge Agent...")
    agent = get_knowledge_agent()
    
    user_query = "What are our company products and their earning production"
    try:
        result = agent.invoke({
            "messages": [{"role": "user", "content": user_query}]
        })
        print(result["messages"][-1].content)
    except Exception as e:
        print(f"Agent execution failed: {e}")
