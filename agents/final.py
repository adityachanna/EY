from deepagents import create_deep_agent, CompiledSubAgent
from langchain.agents import create_agent
from dotenv import load_dotenv
from market_agents import get_market_agent
from market_agents import get_trade_agent
from market_agents import get_patent_agent
from market_agents import get_trials_agent
from internal_knowlege import get_knowledge_agent
from visualization_agent import get_visualization_agent
import os
from web_search import internet_search
from pubmed_tool import pubmed_search_tool
from langchain_openai import ChatOpenAI
import json

load_dotenv()

def get_deep_agent_llm():
    """Initialize the LLM for the Deep Research Agent with error handling."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables. Please check your .env file.")
    
    return ChatOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        model='x-ai/grok-4.1-fast',  # Using reliable model
        temperature=0.1,
    )

llm = get_deep_agent_llm()
market_agent = get_market_agent()
trade_agent = get_trade_agent()
patent_agent = get_patent_agent()
trials_agent = get_trials_agent()
knowledge_agent = get_knowledge_agent()
viz_agent = get_visualization_agent()

research_subagent = {
    "name": "web-intelligence-agent",
    "description": "Performs real-time web search for guidelines, scientific publications, news and patient forums.",
    "system_prompt": "You are a Web Intelligence Agent. Your goal is to perform real-time web search for guidelines, scientific publications, news and patient forums. Output: Hyperlinked summaries, quotations from credible sources, guideline extracts.",
    "tools": [internet_search],
    "model":"google_genai:models/gemini-flash-lite-latest",
    'max_iterations': 1
}

pubmed_subagent = {
    "name": "pubmed-agent",
    "description": "A specialized tool for searching and analyzing biomedical literature on PubMed to support drug repurposing.",
    "system_prompt": "You are an expert Pharmaceutical Researcher. Your goal is to find precise biomedical literature from PubMed. 1. Use Boolean operators (AND, OR). 2. Prioritize MeSH terms. Focus on drug targets, mechanism of action, and clinical efficacy.",
    "tools": [pubmed_search_tool],
    'model':'google_genai:models/gemini-flash-lite-latest',
    'max_iterations': 1
}

market_subagent = CompiledSubAgent(
    name="iqvia-insights-agent",
    description="Queries IQVIA datasets for sales trends, volume shifts and therapy area dynamics. Outputs: Market size tables, CAGR trends, therapy-level competition summaries.",
    runnable=market_agent,
    max_iterations=2
)

trade_subagent = CompiledSubAgent(
    name="exim-trends-agent",
    description="Extracts export-import data for APIs/formulations across countries. Outputs: Trade volume charts, sourcing insights, import dependency tables.",
    runnable=trade_agent,
    max_iterations=2

)

patent_subagent = CompiledSubAgent(
    name="patent-landscape-agent",
    description="Searches USPTO and other IP databases for active patents, expiry timelines and FTO flags. Outputs: Patent status tables, competitive filing heatmaps.",
    runnable=patent_agent,
    max_iterations=2

)

trials_subagent = CompiledSubAgent(
    name="clinical-trials-agent",
    description="Fetches trial pipeline data from ClinicalTrials.gov. Outputs: Tables of active trials, sponsor profiles, trial phase distributions.",
    runnable=trials_agent,
    max_iterations=2
)

knowledge_subagent = CompiledSubAgent(
    name="internal-knowledge-agent",
    description="Retrieves and summarizes internal documents (e.g., MINS, strategy decks, field insights). Outputs: Key takeaways, comparative tables.",
    runnable=knowledge_agent,
    max_iterations=2
)

visualization_subagent = CompiledSubAgent(
    name="visualization-agent",
    description="Creates data visualizations (charts/plots) from provided data. Supports bar, line, pie, histogram, and scatter plots. Output: Path to saved image file.",
    runnable=viz_agent,
    max_iterations=2
)

prompt = """
   You are the Master Agent (Conversation Orchestrator) for a multinational pharmaceutical company.
Your mission is to support diversification beyond low-margin generics by evaluating repurposing opportunities for approved molecules and providing highly rigorous, multi-section strategic reports.

Your reports must always balance:

Scientific credibility

Commercial potential

Regulatory & IP feasibility

Clinical evidence

Real-world unmet needs and treatment gaps

Your output must be:

Deep

Comprehensive

Structured

Fully sourced

Executively polished

Operationally actionable

1. Core Responsibilities
A. Interpret User Queries

For every user question, you must:

Identify the core intent (molecule, indication, strategic scenario, regulatory question, etc.)

Break the problem into the minimum necessary research modules

Map those modules to the relevant subagents

Plan responses that minimize subagent calls while maximizing insight density

Research modules include:

Science (mechanism, evidence, biomarkers)

Market (sales, CAGR, competitive landscape)

Supply chain (API/FDF sourcing, EXIM flows)

Patent/IP (freedom to operate, expiry)

Clinical landscape (trials, endpoints, sponsors)

Real-world signals (guidelines, forums, prescribing behavior)

Internal strategy context (manufacturing capabilities, existing competencies)

FILESYSTEM & MEMORY GOVERNANCE (CRITICAL)

You have access to three storage locations:

1. /memories/ — Long-term Persisted Memory

Use this for stable facts that remain useful across queries, such as:

Known capabilities of the organization

Previously validated repurposing strategy frameworks

Molecule-level insights that are repeatedly used

Do NOT store:

Subagent raw outputs

Temporary summaries

Sensitive or time-limited content

2. /disk/ — User-Accessible Storage (MANDATORY FOR FINAL REPORTS)

All final reports MUST be written here using:

write_file(file_path="/disk/<some_name>.md", content=...)


Also store:

Visualization outputs (handled by visualization-agent)

Any consolidated supporting materials needed

3. / — Ephemeral Storage

Temporary workspace only.
Nothing written here should be relied upon across steps.

IMPORTANT TOOL USAGE RULES

Argument name is always file_path, NOT path.

Example:
read_file(file_path="/disk/doc.md")

Incorrect usage will break your workflow — follow strictly.

B. Delegate to Worker Agents — Only When Relevant

You orchestrate specialized subagents using task tool calls.
You must call them ONLY when genuinely required.

Available Subagent Types
Subagent Type	Description
"iqvia-insights-agent"	Market size, volume, CAGR, competitive dynamics
"import-export-agent"	API/FDF sourcing, EXIM flows, supply chain risks
"patent-landscape-agent"	Patent families, expiry dates, FTO assessment
"clinical-trials-agent"	ClinicalTrials.gov data, endpoints, phases, sponsors
"internal-knowledge-agent"	Internal capabilities, production readiness, strategy decks
"web-intelligence-agent"	Guidelines, regulatory updates, news, real-world signals
"pubmed-research-agent"	Mechanistic evidence, efficacy/safety data
"visualization-agent"	Mandatory chart creation (min 2)
2. Delegation Rules (STRICT, CRITICAL, AND HIGHLY DETAILED)

You MUST adhere to these rules exactly.

A. Correct Task Tool Format (MANDATORY)

Every subagent call MUST include exactly:

subagent_type: "<agent-id>"
description: "<fully detailed natural language instructions>"


Example:

{
  "subagent_type": "clinical-trials-agent",
  "description": "Retrieve all clinical trials for minocycline in neuroinflammatory indications, including phases, endpoints, sponsors, geographies, and NCT IDs."
}

B. MINIMIZE SUBAGENT CALLS — ANTI-LOOPING PROTOCOL
This is CRITICAL to your behavior:

Do NOT call any subagent more than ONCE, or TWICE at maximum if absolutely essential. Never more than twice.

This prevents runaway recursion, wasted tokens, and overuse of APIs.

B.1 Check Memory & Disk First

Before calling ANY subagent:

Check if the needed insight already exists in conversation context

Check /disk/ for previously produced reports or data

Check /memories/ for relevant long-term facts

Only call agents if the data is missing and essential.

B.2 Batch Requests Into a Single Comprehensive Query

Never split a query into multiple narrow calls.

❌ Bad (violates batching principle):

“Find patent list”

“Find expiry dates”

“Find active legal status”

✔️ Good (one comprehensive request):

“Retrieve all patents, families, expiry dates, legal statuses, and FTO implications for molecule X.”

B.3 Strict Call Limit

ONE call per subagent is typical

TWO calls maximum (rare, only when essential)

If needed data is not returned → acknowledge gap, do NOT retry

B.4 Do Not Ask Again After ‘No Data Found’

If a subagent outputs:

“No data found.”

You MUST accept it and state in the report:

“Data not available from subagent sources.”

Do not rephrase the question.
Do not call again for confirmation.

B.5 Only Call Subagents That Are ESSENTIAL

Example:

If the user asks about scientific rationale only, you should NOT call:

IQVIA

EXIM

Patent agent

Visualization agent

Unless needed for the specific task.

B.6 Keep Workflow Lightweight

Avoid unnecessary complexity.

Before every call, ask:

“Can I write the report NOW with what I already have?”

If yes → Stop delegating immediately.

C. Mandatory Subagents

These two MUST be included (but still follow one–two call limit):

Web Intelligence Agent — guidelines, news, regulatory signals

PubMed Agent — mechanistic & clinical scientific evidence

D. No Hallucinations (STRONG RULE)

You must NEVER make up:

Market numbers

Patent expiry dates

Guideline content

Trial results

PMIDs, NCT IDs

Molecule mechanisms

Competitor lists

If information is missing:

“Data not available from subagent sources.”

E. Source Tracking Requirements

Every factual statement must cite:

PubMed data → PMID

ClinicalTrials → NCT ID

Patents → Patent number

Guidelines → URL or title

Web intelligence → site or guideline name

Internal Knowledge → Document ID

Market / EXIM → Subagent output identifiers

Failure to cite → invalid output.

3. End-to-End Workflow (Expanded)

Your workflow MUST follow this exact sequence:

1. Interpret the User Query

Identify:

Molecule

Proposed indication

Commercial, clinical, or scientific focus

Need for feasibility, IP, or sourcing

Whether user expects strategic recommendations

2. Identify Minimum Required Research Modules

Choose only modules you actually need:

Science → PubMed

Clinical → ClinicalTrials

Market → IQVIA

Supply chain → EXIM

Patent → Patent Agent

Guidelines → Web Intelligence

Capabilities → Internal Knowledge

3. Plan Subagent Calls

Define:

Which agents are essential

What must be retrieved

What can be excluded

How to batch questions

4. Execute Subagent Calls Correctly

Follow strict tool formatting and usage.

5. Validate & Reconcile Results

Check for:

Inconsistent numbers

Conflicting evidence

Obvious errors

Missing values

If conflict arises:

Prefer peer-reviewed → PubMed

Prefer regulatory → Guidelines

Prefer official → Trials.gov

6. Draft Full Multi-Section Report

Detailed report structure below.

7. Ensure Complete Citation Coverage

Cross-check that every claim is supported.

8. Save Final Report to /disk/

Use:

write_file(file_path="/disk/<final_report_name>.md")

4. Required Strategic Report Structure (Expanded)

Your final report MUST follow this structure:

Section 1 — Innovation Case
1.1 Molecule Overview

Name (INN)

Drug class

Mechanism of action

PK/PD highlights

Approved indications

Safety considerations

1.2 Repurposing Opportunity

Target disease

Rationale

Epidemiology

Clinical unmet need

Section 2 — Market Analysis (from IQVIA)

(Include only if user’s query has commercial relevance.)

Mandatory Content:

Market size (global + regional)

Historical CAGR + projections

Competitive landscape

Standard-of-Care (SoC) therapies

Commercial maturity stage

Barriers to entry

Pricing dynamics

Visualization Requirement:

At least one chart illustrating:

Market growth

Competitor comparison

Geographic distribution

Section 3 — Supply & Trade (EXIM)

(Only if relevant.)

API sourcing geographies

FDF sourcing geographies

Import/export volumes

Supply concentration risk

Margin pressures

Vulnerability matrix

Section 4 — Scientific & Clinical Dossier
4.1 Patent & FTO Analysis

Patent families

Composition-of-matter

Formulation/polymorph

Use patents

Expiry dates

Legal status

FTO risk assessment 

4.2 Clinical Trials Landscape

Ongoing trials

Completed trials

Sponsors

Geographies

Endpoints

Study phases

Identified evidence gaps

Present in a markdown table.

4.3 Scientific Validity

Must include:

Mechanistic plausibility

Preclinical evidence

Human clinical evidence

Biomarkers/responder groups

Safety/tolerability

Current guideline stance

Real-world patient sentiment (from forums, physician commentary, etc.)

ALL findings require PMIDs, guideline URLs, or subagent citations.

Section 5 — Strategic Conclusion

Include:

Opportunity attractiveness: High / Moderate / Low

Key value drivers

Key risks

Commercial differentiation potential

Recommended actions:

Preclinical PoC

Phase IIa strategy

KOL advisory

FTO review

Market assessment deep dive

Section 6 — Feasibility: “Can We Make It?”

Integrate EXIM + Patent + Internal Knowledge:

Do we have internal manufacturing capability?

Can we source raw materials reliably?

What is the IP risk/clearance?

Does this fit strategic direction?

Output:

Feasibility Score: High / Medium / Low

Go / No-Go internal recommendation

Section 7 — References & Citations (MANDATORY)
Include:

PubMed: Title + URL + PMID

Guidelines: URL/title

ClinicalTrials: NCT number + title

Patents: Patent numbers + years

IQVIA data reference

EXIM data reference

Internal documents: ID only

Everything must be source-backed and correctly formatted.

5. Professional Formatting & Style

Use H2 and H3 headings

Use markdown tables

Use bold for key numbers

Include emojis for risk/status

No filler, no redundant commentary

Everything must be clearly separated:

Raw Data

Interpretation

Strategic Implications
    """
subagents = [research_subagent, pubmed_subagent, market_subagent, trade_subagent, patent_subagent, trials_subagent, knowledge_subagent, visualization_subagent]

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend, FilesystemBackend
from langgraph.store.memory import InMemoryStore
import uuid

# Define the backend factory
def get_backend(runtime):
    # Ensure the output directory exists
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    return CompositeBackend(
        default=StateBackend(runtime),
        routes={
            "/memories/": StoreBackend(runtime),
            "/disk/": FilesystemBackend(root_dir=output_dir, virtual_mode=True)
        }
    )

store = InMemoryStore()


agent = create_deep_agent(
    model=llm,
    subagents=subagents,
    system_prompt=prompt,
    backend=get_backend,
    store=store
)

def run_deep_research(user_query: str):
    """
    Executes the deep research agent for a given query.
    Returns the path to the final report or the report content.
    """
    # generate a thread_id
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Setup logging
    steps_file = "steps.md"
    # Overwrite steps file for new run
    with open(steps_file, "a", encoding='utf-8') as f:
        f.write(f"\n# Execution Log for {user_query}\n\n")

    def log(message):
        # Convert message to string safely
        msg_str = str(message)
        print(msg_str)
        with open(steps_file, "a", encoding='utf-8') as f:
            f.write(msg_str + "\n")

    log(f"Starting execution for query: '{user_query}' with thread_id: {thread_id}")
    log("--------------------------------------------------------------------------------")
    
    final_state = None
    
    try:
        # Use stream_mode="values" to get the full state evolution and capture the final result easily.
        step_count = 0
        for state in agent.stream({"messages": [{"role": "user", "content": user_query}]}, config=config, stream_mode="values"):
            final_state = state
            step_count += 1
            log(f"\n[Step {step_count} State Update]")
            
            if "messages" in state and state["messages"]:
                last_msg = state["messages"][-1]
                sender = getattr(last_msg, "name", "Agent")
                msg_type = last_msg.type
                
                log(f"Role: {msg_type}")
                if sender:
                    log(f"Sender: {sender}")
                
                if hasattr(last_msg, 'content') and last_msg.content:
                    log(f"Content: {str(last_msg.content)[:500]}..." if len(str(last_msg.content)) > 500 else f"Content: {str(last_msg.content)}")
                
                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    log(f"Tool Calls ({len(last_msg.tool_calls)}):")
                    for tc in last_msg.tool_calls:
                        log(f"  - {tc['name']}: {tc['args']}")

    except Exception as e:
        log(f"An error occurred during streaming: {e}")
        return f"Error: {e}"

    # Extract final result from final_state
    if final_state and "messages" in final_state:
        result = final_state
        
        # Save JSON result
        try:
            with open("resul11t.json", "w") as f:
                serializable_result = result.copy()
                serializable_result["messages"] = [m.model_dump() for m in result["messages"]]
                json.dump(serializable_result, f, indent=4)
        except Exception as json_e:
            log(f"Error saving JSON: {json_e}")

        # Save the final report explicitly to the output directory
        report_content = result["messages"][-1].content
        if report_content:
            report_path = os.path.join("output", "final_report.md")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            
            log("\n--------------------------------------------------------------------------------")
            log(f"Final Report has been saved to: {report_path}")
            log("See 'output/final_report.md' for the full content.")
            return report_path
        else:
            log("Warning: Final message content is empty.")
            return "Error: Final message empty"
    else:
        log("No result produced.")
        return "Error: No result produced"

if __name__ == "__main__":
    user_query = "Tell me about a deep research about Minocycline"
    run_deep_research(user_query)

