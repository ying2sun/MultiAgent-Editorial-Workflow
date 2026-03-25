import os
import requests
from typing import TypedDict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

openrouter_key = os.getenv("OPENROUTER_API_KEY")
if not openrouter_key:
    raise ValueError("CRITICAL ERROR: OPENROUTER_API_KEY is missing. Check your .env file!")

# --- 1. The Shared Clipboard (State) ---
# Added 'source_urls' to safely hold our links away from the LLM
class EditorialState(TypedDict):
    search_topic: str
    raw_data: str           
    draft_article: str      
    is_verified: bool       
    feedback: str           
    final_article: str      
    source_urls: str

# --- 2. Initialize the AI Brain ---
llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_key,
    model="google/gemini-2.5-flash",
    temperature=0.0
)

# --- 3. Structured Output Schema for Agent C ---
class FactCheckResult(BaseModel):
    is_verified: bool = Field(description="True if the draft matches the raw data exactly. False if there are hallucinations.")
    feedback: str = Field(description="If False, provide specific instructions on what to fix. If True, output 'Approved'.")

# --- 4. Agent A: The API Researcher ---
def researcher_agent(state: EditorialState):
    print("\n[Agent A] Searching the web and extracting facts and URLs...")
    topic = state.get("search_topic")
    news_api_key = os.getenv("NEWSDATA_API_KEY")
    
    if not news_api_key:
        return {"raw_data": "Error: NEWSDATA_API_KEY is missing.", "feedback": "", "source_urls": ""}

    url = "https://newsdata.io/api/1/news"
    params = {
        "apikey": news_api_key,
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
                
                # Feed the text to the LLM
                extracted_info.append(f"- Title: {title}\n  Summary: {description}")
                
                # Save the URL perfectly formatted for markdown
                if link != "#":
                    source_links.append(f"* [{title}]({link})")
                    
            raw_search_results = "\n\n".join(extracted_info)
            formatted_urls = "\n".join(source_links)
            
    except Exception as e:
        raw_search_results = f"API Request failed: {e}"
        formatted_urls = "Error fetching sources."

    system_instruction = SystemMessage(
        content="You are an expert Data Extraction Researcher. Review the provided news API data. Extract a clean, bulleted 'Fact Dossier' containing only names, dates, quotes, and statistics. Do not write an article."
    )
    user_prompt = HumanMessage(content=f"Raw API data:\n{raw_search_results}")
    
    response = llm.invoke([system_instruction, user_prompt])
    
    # We now return the source_urls to the clipboard
    return {"raw_data": response.content, "feedback": "", "source_urls": formatted_urls}

# --- 5. Agent B: The Journalist ---
def journalist_agent(state: EditorialState):
    print("[Agent B] Writing the journalistic draft...")
    raw_data = state.get("raw_data")
    feedback = state.get("feedback")
    
    system_instruction = SystemMessage(
        content="You are a professional News Reporter. Write a clear, objective news article in English based ONLY on the provided Fact Dossier. Do not add outside information."
    )
    
    prompt_content = f"Fact Dossier:\n{raw_data}"
    if feedback:
        print(f"   -> [Applying Editor Feedback: {feedback}]")
        prompt_content += f"\n\nCRITICAL EDITOR FEEDBACK to fix in this rewrite:\n{feedback}"
        
    user_prompt = HumanMessage(content=prompt_content)
    
    response = llm.invoke([system_instruction, user_prompt])
    return {"draft_article": response.content}

# --- 6. Agent C: The Fact-Checker ---
def fact_checker_agent(state: EditorialState):
    print("[Agent C] Fact-checking the draft against the dossier...")
    raw_data = state.get("raw_data")
    draft_article = state.get("draft_article")
    
    structured_llm = llm.with_structured_output(FactCheckResult)
    
    system_instruction = SystemMessage(
        content="You are a strict Managing Editor. Cross-reference the Reporter's Draft against the original Fact Dossier. If the draft contains names, dates, or numbers NOT found in the Dossier, you must fail it (False) and provide specific feedback on what to remove."
    )
    user_prompt = HumanMessage(
        content=f"Original Fact Dossier:\n{raw_data}\n\nReporter's Draft:\n{draft_article}"
    )
    
    evaluation = structured_llm.invoke([system_instruction, user_prompt])
    
    print(f"   -> [Pass/Fail Result: {evaluation.is_verified}]")
    return {
        "is_verified": evaluation.is_verified,
        "feedback": evaluation.feedback
    }

# --- 7. Agent D: The GEO Optimizer ---
def geo_optimizer_agent(state: EditorialState):
    print("[Agent D] Optimizing layout for AI Search Engines...")
    draft_article = state.get("draft_article")
    
    system_instruction = SystemMessage(
        content="""You are a Digital Publishing & GEO Specialist. 
Take the provided verified article and optimize it for AI Search Engines.
Rules:
1. Ensure the tone is objective and highly professional.
2. Use markdown formatting to create a compelling Headline.
3. Break the text into readable paragraphs.
4. Add 2 or 3 informative subheadings.
5. Append 5 SEO Keywords and a short Meta Description at the bottom.
"""
    )
    user_prompt = HumanMessage(content=f"Verified Draft to optimize:\n{draft_article}")
    
    response = llm.invoke([system_instruction, user_prompt])
    return {"final_article": response.content}

# --- 8. Build the Graph ---
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

workflow.add_conditional_edges(
    "fact_checker",
    verification_router
)

workflow.add_edge("geo_optimizer", END)

app = workflow.compile()

# --- 9. Execute the Test Run (Terminal) ---
def run_workflow():
    print("=========================================")
    print("  MULTI-AGENT NEWS VERIFICATION SYSTEM")
    print("=========================================")
    
    human_keywords = input("Enter keywords for the news search (e.g., Apple Tesla): ")
    
    # Ensure source_urls is initialized
    initial_state = {
        "search_topic": human_keywords,
        "raw_data": "",
        "draft_article": "",
        "is_verified": False,
        "feedback": "",
        "final_article": "",
        "source_urls": "" 
    }
    
    final_state = app.invoke(initial_state)

    print("\n=========================================")
    print("          FINAL GEO-OPTIMIZED ARTICLE      ")
    print("=========================================\n")
    print(final_state.get("final_article"))
    
    print("\n--- Sources ---")
    print(final_state.get("source_urls"))

if __name__ == "__main__":
    run_workflow()