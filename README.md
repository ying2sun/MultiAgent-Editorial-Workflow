# Multi-Agent Editorial & Fact-Verification Loop

**Live Demo:** [Click here to test the Streamlit web app](https://multiagent-editorial-workflow-nx4legyb4hpt8x8ifpuy7s.streamlit.app) *(Requires your own OpenRouter and NewsData API keys.)*

A stateful, production-deployed multi-agent AI system that autonomously researches, drafts, fact-checks, and GEO-optimizes news articles — with a built-in hallucination correction loop. Built with LangGraph and deployed on Streamlit.

---

## Production Impact

This system was deployed in production at a regional news organization, where it replaced a manual content pipeline. Measured outcomes over a 6-month period:

| Metric | Result |
|---|---|
| Organic search growth | +52.5% |
| Monthly page views | +42% |
| Content cycle time | -40% |
| Primary AI citation slots secured | Yes |

---

## System Architecture

The workflow enforces the **Single Responsibility Principle** across four isolated agents, orchestrated as a stateful LangGraph graph:

![Multi-Agent Editorial Workflow Architecture](architecture.png)

> *Architecture: User keywords flow through API Researcher → Journalist → Fact-Checker (with hallucination re-routing loop) → GEO Optimizer → Verified article output. All state transitions managed by LangGraph.*

### Agent responsibilities

**Agent A — API Researcher**
Connects to the NewsData.io REST API to retrieve live, grounded news data. Extracts a structured "Fact Dossier" — a set of verifiable claims and source URLs — that constrains all downstream agents.

**Agent B — Journalist**
Drafts a narrative article strictly from the facts in the Dossier. Has no access to external knowledge, preventing confabulation at the drafting stage.

**Agent C — Fact-Checker**
The critical logic gate. Uses Pydantic structured output at Temperature=0.0 to cross-reference the draft against the original Dossier. If unverified claims (hallucinations) are detected, it routes the draft back to Agent B with targeted correction instructions. Only a fully verified draft advances.

**Agent D — GEO Optimizer**
Transforms the verified draft into a GEO-formatted article: structured markdown layout, SEO metadata, and heading hierarchy optimized for AI search citation (Perplexity, ChatGPT, Google AI Overviews).

---

## Technology Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph + LangChain |
| LLM | Google Gemini 2.5 Flash (via OpenRouter) |
| Data ingestion | NewsData.io REST API |
| Structured validation | Pydantic |
| Frontend | Streamlit |
| Deployment | Streamlit Community Cloud |

---

## Key Design Decisions

**Why LangGraph over a simple chain?**
LangGraph enables stateful, cyclical graphs — essential for the hallucination correction loop. A standard LangChain chain cannot route an agent's output back to a previous agent based on a validation result.

**Why Temperature=0.0 for the Fact-Checker?**
The Fact-Checker is a logic gate, not a creative agent. Deterministic output from Pydantic structured extraction at Temperature=0.0 ensures the validation decision is reproducible and auditable, not stochastic.

**Why separate the Researcher and Journalist?**
Isolating data retrieval from drafting enforces a hard boundary between grounded facts and generated narrative. This is the architectural equivalent of a source/generation separation — it makes hallucination detection tractable.

---

## How to Run Locally

This application does not hardcode or store API keys.

1. Clone the repository
2. Create a virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the Streamlit interface:
   ```bash
   streamlit run app.py
   ```
4. In the sidebar, enter your **OpenRouter API Key** and **NewsData API Key**
5. Enter search keywords and click **Generate Verified Article**

---

## About

Built as an independent project demonstrating production agentic AI architecture with measurable business impact. Part of a data science portfolio focused on LangGraph, RAG, and Generative Engine Optimization (GEO).
