import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_groq import ChatGroq
# Import Mock APIs
from mock_data_api import MockIQVIA, MockEXIM, MockUSPTO, MockClinicalTrials

# Load environment variables
load_dotenv()

# Initialize Mock APIs
iqvia_api = MockIQVIA()
exim_api = MockEXIM()
uspto_api = MockUSPTO()
trials_api = MockClinicalTrials()
api_key = os.getenv("OPENROUTER_API_KEY")
# Initialize LLM
llm=ChatGroq(
    model='moonshotai/kimi-k2-instruct-0905',
    api_key=os.getenv('groq'),
    temperature=0.1
)
# --- 1. IQVIA Agent (Market Insights) ---
@tool
def get_market_insights(query: str):
    """
    Queries IQVIA market data for information on market size, growth, and competitors.
    Available data covers: Depression (MDD), Alzheimers, Minocycline, Respiratory (Asthma/COPD), Telmisartan, and Metformin.
    Returns: Market size (USD bn), CAGR, market share split, and key competitors.
    """
    return iqvia_api.get_market_insights(query)

def get_market_agent():
    tools = [get_market_insights]
    system_prompt = (
        "You are a Market Insights Agent specialized in pharmaceutical markets using IQVIA data. "
        "You have access to real-time market data for specific therapeutic areas and molecules including "
        "Depression, Alzheimers, Minocycline, Respiratory, Telmisartan, and Metformin. "
        "Use 'get_market_insights' to retrieve market size, CAGR, and competitor landscapes. "
        "If a query is outside these specific topics, try to map it to the closest available category or state limitations."
    )
    # Using create_agent which returns a RunnableGraph runnable with middleware
    return create_agent(
        llm, 
        tools=tools, 
        system_prompt=system_prompt,
        middleware=[
            ModelCallLimitMiddleware(run_limit=10, exit_behavior="end"),
            ToolCallLimitMiddleware(run_limit=3, exit_behavior="continue")
        ]
    )

# --- 2. EXIM Agent (Trade Trends) ---
@tool
def get_trade_data(molecule: str):
    """
    Retrieves global export/import trends for specific pharmaceutical molecules.
    Available data covers: Minocycline, Telmisartan, and Salbutamol (Albuterol).
    Returns: Total volume, major exporting countries/companies, and price trends.
    """
    return exim_api.get_export_import_data(molecule)

def get_trade_agent():
    tools = [get_trade_data]
    system_prompt = (
        "You are a Supply Chain & Trade Agent using EXIM data. "
        "You track global movement of APIs (Active Pharmaceutical Ingredients). "
        "You have specific data for Minocycline, Telmisartan, and Salbutamol. "
        "Use 'get_trade_data' to assess supply stability, identify major suppliers (e.g., in India/China), and check price trends."
    )
    return create_agent(
        llm, 
        tools=tools, 
        system_prompt=system_prompt,
        middleware=[
            ModelCallLimitMiddleware(run_limit=10, exit_behavior="end"),
            ToolCallLimitMiddleware(run_limit=3, exit_behavior="continue")
        ]
    )

# --- 3. USPTO Agent (Patents) ---
@tool
def search_patents(keyword: str):
    """
    Searches USPTO patent filings. 
    Focuses on: Minocycline (Composition/Method of Use), Telmisartan (Formulation/Use), and Smart Inhalers.
    Returns: Patent IDs, Assignees, Status (Expired/Active/Pending), and Claims.
    """
    return uspto_api.search_patents(keyword)

def get_patent_agent():
    tools = [search_patents]
    system_prompt = (
        "You are a Patent Landscape Agent using USPTO data. "
        "You verify Freedom to Operate (FTO) and identify repurposing opportunities. "
        "You have detailed patent records for Minocycline (esp. depression/neuro usage), Telmisartan (fibrosis/NASH), and Inhaler devices. "
        "Use 'search_patents' to find expiration dates and assignee details."
    )
    return create_agent(
        llm, 
        tools=tools, 
        system_prompt=system_prompt,
        middleware=[
            ModelCallLimitMiddleware(run_limit=10, exit_behavior="end"),
            ToolCallLimitMiddleware(run_limit=3, exit_behavior="continue")
        ]
    )

# --- 4. Clinical Trials Agent ---
@tool
def get_clinical_trials(search_term: str):
    """
    Searches ClinicalTrials.gov for study status.
    Key coverage: Minocycline (Depression/Alzheimers/Acne), Telmisartan (Fibrosis), Metformin (Aging).
    Returns: NCT IDs, Phases, Recruiting Status, Sponsors, and Outcomes (if completed).
    """
    return trials_api.get_trials(search_term)       

def get_trials_agent():
    tools = [get_clinical_trials]
    system_prompt = (
        "You are a Clinical Research Agent accessing ClinicalTrials.gov data. "
        "You investigate ongoing and completed trials to validate repurposing candidates. "
        "You have specific records for Minocycline (CNS indications), Telmisartan, and Metformin. "
        "Use 'get_clinical_trials' to check trial phases, sponsors, and results."
    )
    return create_agent(
        llm, 
        tools=tools, 
        system_prompt=system_prompt,
        middleware=[
            ModelCallLimitMiddleware(run_limit=10, exit_behavior="end"),
            ToolCallLimitMiddleware(run_limit=3, exit_behavior="continue")
        ]
    )


if __name__ == "__main__":
    # Smoke test
    print("Initializing agents...")
    try:
        market_agent = get_market_agent()
        trade_agent = get_trade_agent()
        patent_agent = get_patent_agent()
        trials_agent = get_trials_agent()
        print("Agents initialized successfully.")
        
        # Simple test invocation
        print("\nTesting Market Agent...")
        res = market_agent.invoke({"messages": [{"role": "user", "content": "What is the market size for Depression?"}]})
        
        last_msg = res['messages'][-1]
        if last_msg.content:
            print(f"Agent Response: {last_msg.content}")
        elif last_msg.tool_calls:
            print(f"Agent Action (Tool Call): {last_msg.tool_calls}")
        else:
            print("Agent returned empty content and no tool calls.")
        
    except Exception as e:
        print(f"Error initializing/running agents: {e}")
