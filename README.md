# Multi-Agent Editorial & Fact-Verification Loop

**Live Demo:** [Click here to test the Streamlit web app]([https://your-streamlit-app-url-here.share.streamlit.io](https://multiagent-editorial-workflow-nx4legyb4hpt8x8ifpuy7s.streamlit.app/)) *(Note: Requires your own OpenRouter and NewsData API keys to run).*

This repository contains a stateful, multi-agent AI architecture designed to automate the research, drafting, and rigorous fact-checking of global news. Built with LangGraph, it addresses the critical issue of Large Language Model (LLM) hallucinations in journalistic and content generation workflows.

## System Architecture

The workflow orchestrates four distinct agents with isolated responsibilities to enforce the Single Responsibility Principle:

1. Agent A (The API Researcher): Connects to the NewsData.io REST API to fetch live, grounded data based on search keywords. It extracts a clean "Fact Dossier" and verifiable source URLs.
2. Agent B (The Journalist): Drafts a narrative news article strictly constrained to the facts provided in the Dossier.
3. Agent C (The Fact-Checker): A strict logic gate utilizing Pydantic structured output (Temperature 0.0). It cross-references the Journalist's draft against the original Dossier. If unverified claims (hallucinations) are detected, it routes the draft back to Agent B with specific correction feedback.
4. Agent D (The GEO Optimizer): Formats the verified draft for Generative Engine Optimization (GEO), applying markdown layouts, SEO keywords, and meta descriptions.

## Technology Stack

* Orchestration: LangGraph & LangChain
* Models: Google Gemini 2.5 Flash (via OpenRouter)
* Data Ingestion: NewsData.io REST API
* Frontend Interface: Streamlit
* Verification: Pydantic Structured Outputs

## How to Run Locally

This application is designed to be secure. It does not hardcode or store API keys. To run this system, you must provide your own API keys at runtime.

1. Clone the repository.
2. Create a virtual environment and install the dependencies: `pip install -r requirements.txt`
3. Launch the interface: `streamlit run app.py`
4. In the Streamlit web interface, use the sidebar to input your OpenRouter API Key and NewsData API Key.
5. Enter your search keywords and click "Generate Verified Article".
