import requests
from typing import TypedDict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

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
def researcher_agent(state: EditorialState):
    print("\n[Agent A] Searching the web and extracting facts and URLs...")
    topic = state.get("search_topic")
    newsdata_key = state.get("newsdata_key")
    openrouter_key = state.get("openrouter_key")
    
    # Initialize the AI Brain using the user's provided key
    llm = ChatOpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key, model="google/gemini-2.5-flash", temperature=0.0)

    url = "https://newsdata.io/api/1/news"
    params = {
        "apikey": newsdata_key,
        "q": topic,
        "language": "en"
    }
    
    try:
        api_response = requests.get(url, params=params)
        api_response.raise_for_status()
        json_data = api_response.json()
        
        articles = json_data.get("results", [])[:5]
        
        if not articles:
            raw_search_results = "No recent news articles found for this topic."
            formatted_urls = "No sources found."
        else:
            extracted_info = []
            source_links = []
            
            for article in articles:
                title = article.get("title", "No Title")
                description = article.get("description", "No Description")
                link = article.get("link", "#")
                
                extracted_info.append(f"- Title: {title}\n  Summary: {description}")
                if link != "#":
                    source_links.append(f"* [{title}]({link})")
                    
            raw_search_results = "\n\n".join(extracted_info)
            formatted_urls = "\n".join(source_links)
            
    except Exception as e:
        raw_search_results = f"API Request failed: {e}"
        formatted_urls = "Error fetching sources."

    system_instruction = SystemMessage(content="You are an expert Data Extraction Researcher. Extract a clean, bulleted 'Fact Dossier' containing only names, dates, quotes, and statistics. Do not write an article.")
    user_prompt = HumanMessage(content=f"Raw API data:\n{raw_search_results}")
    
    response = llm.invoke([system_instruction, user_prompt])
    
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
    final_state = app.invoke(initial_state)

    print("\n=========================================")
    print("          FINAL GEO-OPTIMIZED ARTICLE      ")
    print("=========================================\n")
    print(final_state.get("final_article"))
    
    print("\n--- Sources ---")
    print(final_state.get("source_urls"))

if __name__ == "__main__":
    run_workflow()