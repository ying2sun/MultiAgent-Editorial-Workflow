import os
import asyncio
import requests
from typing import TypedDict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langchain_mcp_adapters.client import MultiServerMCPClient

# --- 1. The Shared Clipboard (State) ---
# We added two new slots for the user's API keys
class EditorialState(TypedDict):
    search_topic: str
    raw_data: str           
    draft_article: str      
    is_verified: bool       
    feedback: str           
    final_article: str      
    source_urls: str
    openrouter_key: str     # NEW
    newsdata_key: str       # NEW

# --- 2. Structured Output Schema for Agent C ---
class FactCheckResult(BaseModel):
    is_verified: bool = Field(description="True if the draft matches the raw data exactly. False if there are hallucinations.")
    feedback: str = Field(description="If False, provide specific instructions on what to fix. If True, output 'Approved'.")

# --- 3. Agent A: The API Researcher ---
async def researcher_agent(state: EditorialState):
    print("\n[Agent A] Fetching live news via MCP server...")
    topic = state.get("search_topic")
    newsdata_key = state.get("newsdata_key")
    openrouter_key = state.get("openrouter_key")

    llm = ChatOpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key, model="google/gemini-2.5-flash", temperature=0.0)

    # Inject the NewsData key into the subprocess environment
    # os.environ["NEWSDATA_KEY"] = newsdata_key

    server_config = {
        "news": {
            "command": "python",
            "args": ["mcp_news_server.py", newsdata_key],
            "transport": "stdio",
        }
    }

    try:
        client = MultiServerMCPClient(server_config)
        tools = await client.get_tools()
        fetch_news_tool = next(t for t in tools if t.name == "fetch_news")
        raw_result = await fetch_news_tool.ainvoke({"query": topic, "language": "en"})
    except Exception as e:
        print(f"DEBUG MCP ERROR: {e}")
        raw_result = f"MCP fetch failed: {e}===SOURCES===Error fetching sources."

    # Split on the delimiter to separate article facts from source URLs
    if "===SOURCES===" in raw_result:
        raw_articles, formatted_urls = raw_result.split("===SOURCES===", 1)
    else:
        raw_articles = raw_result
        formatted_urls = "No sources found."

    system_instruction = SystemMessage(content="You are an expert Data Extraction Researcher. Extract a clean, bulleted 'Fact Dossier' containing only names, dates, quotes, and statistics. Do not write an article.")
    user_prompt = HumanMessage(content=f"Raw API data:\n{raw_articles}")

    response = await llm.ainvoke([system_instruction, user_prompt])

    return {"raw_data": response.content, "feedback": "", "source_urls": formatted_urls}

# --- 4. Agent B: The Journalist ---
def journalist_agent(state: EditorialState):
    print("[Agent B] Writing the journalistic draft...")
    raw_data = state.get("raw_data")
    feedback = state.get("feedback")
    openrouter_key = state.get("openrouter_key")
    
    llm = ChatOpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key, model="google/gemini-2.5-flash", temperature=0.0)
    
    system_instruction = SystemMessage(content="You are a professional News Reporter. Write a clear, objective news article in English based ONLY on the provided Fact Dossier. Do not add outside information.")
    
    prompt_content = f"Fact Dossier:\n{raw_data}"
    if feedback:
        prompt_content += f"\n\nCRITICAL EDITOR FEEDBACK to fix in this rewrite:\n{feedback}"
        
    user_prompt = HumanMessage(content=prompt_content)
    response = llm.invoke([system_instruction, user_prompt])
    return {"draft_article": response.content}

# --- 5. Agent C: The Fact-Checker ---
def fact_checker_agent(state: EditorialState):
    print("[Agent C] Fact-checking the draft against the dossier...")
    raw_data = state.get("raw_data")
    draft_article = state.get("draft_article")
    openrouter_key = state.get("openrouter_key")
    
    llm = ChatOpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key, model="google/gemini-2.5-flash", temperature=0.0)
    structured_llm = llm.with_structured_output(FactCheckResult)
    
    system_instruction = SystemMessage(content="You are a strict Managing Editor. Cross-reference the Reporter's Draft against the original Fact Dossier. If the draft contains names, dates, or numbers NOT found in the Dossier, you must fail it (False) and provide specific feedback on what to remove.")
    user_prompt = HumanMessage(content=f"Original Fact Dossier:\n{raw_data}\n\nReporter's Draft:\n{draft_article}")
    
    evaluation = structured_llm.invoke([system_instruction, user_prompt])
    print(f"   -> [Pass/Fail Result: {evaluation.is_verified}]")
    return {"is_verified": evaluation.is_verified, "feedback": evaluation.feedback}

# --- 6. Agent D: The GEO Optimizer ---
def geo_optimizer_agent(state: EditorialState):
    print("[Agent D] Optimizing layout for AI Search Engines...")
    draft_article = state.get("draft_article")
    openrouter_key = state.get("openrouter_key")
    
    llm = ChatOpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key, model="google/gemini-2.5-flash", temperature=0.0)
    
    system_instruction = SystemMessage(content="You are a Digital Publishing & GEO Specialist. Format the verified article with a Headline, paragraphs, 2-3 subheadings, 5 SEO Keywords, and a short Meta Description.")
    user_prompt = HumanMessage(content=f"Verified Draft to optimize:\n{draft_article}")
    
    response = llm.invoke([system_instruction, user_prompt])
    return {"final_article": response.content}

# --- 7. Build the Graph ---
workflow = StateGraph(EditorialState)
workflow.add_node("researcher", researcher_agent)
workflow.add_node("journalist", journalist_agent)
workflow.add_node("fact_checker", fact_checker_agent)
workflow.add_node("geo_optimizer", geo_optimizer_agent)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "journalist")
workflow.add_edge("journalist", "fact_checker")

def verification_router(state: EditorialState):
    if state.get("is_verified") == True:
        return "geo_optimizer"
    else:
        return "journalist"

workflow.add_conditional_edges("fact_checker", verification_router)
workflow.add_edge("geo_optimizer", END)

app = workflow.compile()

# --- 8. Execute the Test Run (Terminal) ---
def run_workflow():
    print("=========================================")
    print("  MULTI-AGENT NEWS VERIFICATION SYSTEM")
    print("=========================================")
    
    # Ask the user for inputs directly in the terminal
    user_openrouter = input("Enter your OpenRouter API Key: ")
    user_newsdata = input("Enter your NewsData API Key: ")
    human_keywords = input("Enter keywords for the news search (e.g., Apple Tesla): ")
    
    initial_state = {
        "search_topic": human_keywords,
        "raw_data": "",
        "draft_article": "",
        "is_verified": False,
        "feedback": "",
        "final_article": "",
        "source_urls": "",
        "openrouter_key": user_openrouter,
        "newsdata_key": user_newsdata
    }
    
    print("\nStarting the Workflow...")
    final_state = asyncio.run(app.ainvoke(initial_state))

    print("\n=========================================")
    print("          FINAL GEO-OPTIMIZED ARTICLE      ")
    print("=========================================\n")
    print(final_state.get("final_article"))
    
    print("\n--- Sources ---")
    print(final_state.get("source_urls"))

if __name__ == "__main__":
    run_workflow()