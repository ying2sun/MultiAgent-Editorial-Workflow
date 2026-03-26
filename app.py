import streamlit as st
from workflow import app as agent_workflow

st.set_page_config(page_title="AI Editorial Desk", layout="centered")

# --- Security: User Provides Their Own Keys ---
st.sidebar.title("Configuration")
st.sidebar.markdown("To run this live demo, please provide your own API keys. They are not stored permanently.")

user_openrouter_key = st.sidebar.text_input("OpenRouter API Key", type="password", placeholder="sk-or-v1-...")
user_newsdata_key = st.sidebar.text_input("NewsData API Key", type="password", placeholder="pub_...")

st.title("Multi-Agent Editorial & Fact-Verification Loop")
st.markdown("This system utilizes four distinct AI agents to research, draft, rigorously fact-check, and format breaking news into a publication-ready GEO article.")

search_query = st.text_input("Enter news keywords to research:", placeholder="e.g., Tech layoffs San Francisco")

if st.button("Generate Verified Article"):
    # First, verify the user actually entered the keys
    if not user_openrouter_key or not user_newsdata_key:
        st.error("Access Denied: Please enter both your OpenRouter and NewsData API keys in the sidebar menu.")
    elif not search_query:
        st.warning("Please enter keywords to begin.")
    else:
        with st.status("Initializing AI Agents...", expanded=True) as status:
            
            # Pass the user's keys directly into the LangGraph state
            initial_state = {
                "search_topic": search_query,
                "raw_data": "",
                "draft_article": "",
                "is_verified": False,
                "feedback": "",
                "final_article": "",
                "source_urls": "",
                "openrouter_key": user_openrouter_key,
                "newsdata_key": user_newsdata_key
            }
            
            st.write("Agent A: Fetching live API data and compiling Fact Dossier...")
            
            try:
                final_state = agent_workflow.invoke(initial_state)
                
                st.write("Agent B: Drafting journalistic narrative...")
                st.write(f"Agent C: Fact-checking draft against dossier... Verified: {final_state.get('is_verified')}")
                st.write("Agent D: Applying GEO formatting constraints...")
                
                status.update(label="Workflow Complete!", state="complete", expanded=False)
                
                st.subheader("Final GEO-Optimized Article")
                st.markdown(final_state.get("final_article"))
                
                st.divider()
                st.subheader("Verified Sources")
                st.markdown(final_state.get("source_urls"))
                
                with st.expander("View Agent A's Raw Fact Dossier"):
                    st.text(final_state.get("raw_data"))
                    
            except Exception as e:
                status.update(label="System Error", state="error")
                st.error(f"An error occurred during execution: {e}")