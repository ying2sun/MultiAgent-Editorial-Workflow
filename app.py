import streamlit as st
import os
from dotenv import load_dotenv
from workflow import app as agent_workflow

load_dotenv()

st.set_page_config(page_title="AI Editorial Desk", layout="centered")

st.title("Multi-Agent Editorial & Fact-Verification Loop")
st.markdown("This system utilizes four distinct AI agents to research, draft, rigorously fact-check, and format breaking news into a publication-ready GEO article.")

search_query = st.text_input("Enter news keywords to research:", placeholder="e.g., Tech layoffs San Francisco")

if st.button("Generate Verified Article"):
    if not search_query:
        st.warning("Please enter keywords to begin.")
    else:
        with st.status("Initializing AI Agents...", expanded=True) as status:
            
            # Initial state now includes the source_urls slot
            initial_state = {
                "search_topic": search_query,
                "raw_data": "",
                "draft_article": "",
                "is_verified": False,
                "feedback": "",
                "final_article": "",
                "source_urls": ""
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
                
                # Create a clear visual break for the citations
                st.divider()
                st.subheader("Verified Sources")
                st.markdown(final_state.get("source_urls"))
                
                with st.expander("View Agent A's Raw Fact Dossier"):
                    st.text(final_state.get("raw_data"))
                    
            except Exception as e:
                status.update(label="System Error", state="error")
                st.error(f"An error occurred during execution: {e}")