# Multi-Agent Editorial & Fact-Verification Loop

**Live Demo:** [Launch the Streamlit App](https://multiagent-editorial-workflow-nx4legyb4hpt8x8ifpuy7s.streamlit.app) *(Bring your own OpenRouter and NewsData API keys.)*

A production-minded, stateful multi-agent pipeline that researches live news, drafts an article, autonomously catches and corrects LLM hallucinations, and publishes a GEO-optimised result — all without human intervention.

---

## The Problem This Solves

LLMs are fluent but unreliable. When tasked with writing news articles, they confabulate — inventing names, dates, and statistics with complete confidence. The naive fix (RAG) helps, but does not guarantee the final output stays grounded. This project solves that with a **closed correction loop**: a dedicated fact-checker that reads the draft against the original source data and routes it back for a rewrite if it detects any claim that cannot be verified. The loop only exits when the article passes.

---

## System Architecture

The workflow is built on **LangGraph** rather than a simple sequential chain. The key reason: LangGraph supports **conditional edges and stateful cycles**, which is what makes the hallucination-correction loop possible. A linear chain cannot route backwards — LangGraph can.

```
[Agent A: Researcher] → [Agent B: Journalist] → [Agent C: Fact-Checker]
                                ↑                        |
                                |      FAIL (hallucination detected)
                                └────────────────────────┘
                                         |
                                      PASS
                                         ↓
                              [Agent D: GEO Optimizer] → END
```

Each agent is isolated with a single responsibility. This is a deliberate design choice: isolation makes the pipeline debuggable. If the fact-checker fails, the problem is always in Agent B's output — not buried somewhere in a monolithic chain.

### Agent Breakdown

**Agent A — The Researcher**
Calls the NewsData.io REST API, pulls the top 5 live articles for the given keywords, and distils them into a structured "Fact Dossier" of names, dates, quotes, and figures. It separates source URLs at this stage so the GEO agent can attach citations at the end without touching the verification data.

**Agent B — The Journalist**
Writes a news article constrained *strictly* to the Fact Dossier. On a rewrite cycle, it receives the fact-checker's specific correction instructions embedded directly in the prompt — not a generic "try again" signal, but targeted feedback: exactly which claims to remove or fix.

**Agent C — The Fact-Checker**

This is the most deliberately engineered agent in the pipeline. Two key decisions:

- **Temperature set to `0.0`.** The fact-checker is not a creative agent — it is a logic gate. Determinism is a requirement here. Any temperature above zero introduces probabilistic variation into what should be a binary verdict.
- **Pydantic structured output.** Instead of parsing a free-text response, the LLM is forced to return a typed schema: `is_verified: bool` and `feedback: str`. This eliminates the entire class of bugs where a "yes, but..." response gets misread as a pass. The routing decision downstream is made on a boolean, not string matching.

**Agent D — The GEO Optimizer**

Formats the verified draft for **Generative Engine Optimization** — the emerging practice of structuring content so AI search engines (Perplexity, ChatGPT Search, Google AI Overviews) can cite it accurately. This goes beyond standard SEO: it includes explicit subheadings, a meta description written as a direct answer, and source citations attached inline.

---

## Engineering Decisions

| Decision | Rationale |
|---|---|
| LangGraph over LangChain LCEL | Needed stateful cycles and conditional routing. LCEL is linear. |
| Temperature 0.0 on fact-checker only | Verification is deterministic logic, not generation. Other agents benefit from slightly more flexible outputs. |
| Pydantic for structured output | Eliminates string parsing fragility on the pass/fail gate. Boolean in, boolean out. |
| Gemini 2.5 Flash via OpenRouter | Best latency-to-capability ratio for this use case. OpenRouter also decouples the app from any single model provider — swapping models requires changing one string. |
| API keys at runtime, never stored | Security-first. No `.env` hardcoding, no secrets in the repo. Keys are passed through LangGraph's shared state object and never logged. |
| Single Responsibility per agent | Each agent has one input, one output, one job. Debugging a failure in a 4-agent pipeline is straightforward; in a monolith, it is not. |

---

## What the Hallucination Loop Catches in Practice

In testing, Agent B consistently introduced hallucinations when source data was sparse — extrapolating company valuations, attributing quotes to unnamed sources, and filling gaps with plausible-but-fabricated context. Agent C catches these on the first or second cycle in most cases. The loop has never exceeded three iterations in testing, though there is no hard cap by design.

---

## Technology Stack

| Layer | Tool |
|---|---|
| Agent Orchestration | LangGraph, LangChain |
| LLM | Google Gemini 2.5 Flash (via OpenRouter) |
| Structured Output | Pydantic v2 |
| Live Data | NewsData.io REST API |
| Frontend | Streamlit |
| Language | Python 3.11+ |

---

## Running Locally

```bash
git clone https://github.com/ying2sun/MultiAgent-Editorial-Workflow.git
cd MultiAgent-Editorial-Workflow
pip install -r requirements.txt
streamlit run app.py
```

Enter your **OpenRouter API key** and **NewsData API key** in the sidebar. No keys are stored.

---

## What's Next

- [ ] Configurable max retry limit on the correction loop
- [ ] Support for multilingual fact-checking (Traditional Chinese headline generation)
- [ ] Integration with model distillation pipeline to fine-tune a smaller student model on verified editorial outputs
