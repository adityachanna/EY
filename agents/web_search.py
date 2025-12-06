import os
import json
from typing import Literal
from tavily import TavilyClient
from langchain_core.tools import tool
from langchain.agents import create_agent

# Initialize Tavily Client
# Ensure TAVILY_API_KEY is set in your environment variables
tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

@tool
def internet_search(
    query: str,
    max_results: int = 5,
    search_depth: Literal["basic", "advanced"] = "basic",   
    topic: Literal["general", "finance","news"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search using Tavily API.
    
    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to return.
        search_depth (str): 'basic' or 'advanced'.
        topic (str): 'general', 'pharma', or 'finance','news'.
        include_raw_content (bool): Whether to include raw content.
    """
    results = tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
    return json.dumps(results)
    