from langchain.agents import create_agent
from final import run_deep_research
from web_search import internet_search
from dotenv import load_dotenv
import os
import glob
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
api_key = os.getenv("API_4")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

def get_answer(query: str):
    # Read all markdown files from output directory
    md_context = ""
    for filepath in glob.glob(os.path.join(OUTPUT_DIR, "*.md")):
        with open(filepath, "r", encoding="utf-8") as f:
            md_context += f"\n\n--- FILE: {os.path.basename(filepath)} ---\n"
            md_context += f.read()

    llm = ChatGoogleGenerativeAI(
        api_key=api_key,
        model="models/gemini-flash-lite-latest",
        temperature=0,
    )
    
    SYSTEM_PROMPT = f"""
You are a Research Assistant Agent.

## Knowledge Sources (Ranked Order)
1. **Primary Source** → The markdown documents located in the output folder.
2. **Secondary Source** → The Internet (via the provided internet_search tool) ONLY IF:
   - The answer is not present in the markdown documents, OR
   - User explicitly requests updated / latest / external information.

## Your Task
When answering any user query:
- FIRST search inside the markdown context included below.
- If relevant information exists in the markdown text, answer ONLY from that.
- If the markdown does not contain enough information, then call the internet_search tool.
- Combine markdown + search results when needed, but never ignore markdown context.

## Rules
- Do not hallucinate — if neither markdown nor the internet contains the answer, say so.
- Keep answers concise and factual unless user requests otherwise.
- Never mention that you "read from OUTPUT_DIR". Treat the markdown as built-in knowledge.

## Markdown Knowledge Context
Below are all markdown documents available to you:

{md_context}

End of markdown context.
"""

    agent = create_agent(
        model=llm,
        tools=[internet_search],
        system_prompt=SYSTEM_PROMPT,
    )
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": query}]
    })
    return result["messages"][-1].content

if __name__ == "__main__":
    print(get_answer("What is minocycline current cagr"))