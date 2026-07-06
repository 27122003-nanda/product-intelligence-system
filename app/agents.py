"""
Two-stage agentic pipeline:
  1. Planner agent  - decides which source_type(s) to search and reformulates
                       the query for retrieval (handles multi-source questions).
  2. Analyst agent   - reasons over retrieved evidence + recent memory, and
                       produces an evidence-backed answer with citations to
                       specific document IDs.

Uses Groq's LLaMA models (same provider as the SHL project). Requires
GROQ_API_KEY as an environment variable.
"""
import os, json
from groq import Groq

MODEL = "llama-3.3-70b-versatile"
client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

SOURCE_TYPES = ["support_ticket", "feature_request", "prd", "meeting_note"]

PLANNER_SYSTEM = f"""You are a planning agent for a product intelligence system.
Given a business question, decide:
1. Which source_type(s) are most relevant from: {SOURCE_TYPES} (or "all" if unclear)
2. A concise search query optimized for retrieval (keywords + intent)
3. Whether this question requires aggregation/counting across many documents (true/false)

Respond ONLY with JSON: {{"source_types": [...], "search_query": "...", "requires_aggregation": true/false}}
"""

ANALYST_SYSTEM = """You are a senior product analyst. You are given:
- A business question
- Retrieved evidence documents (with IDs, source types, and text)
- Optional theme frequency counts (for aggregation questions)
- Recent conversation history for context

Your job:
- Answer the question directly and concisely
- Ground every claim in the evidence provided — cite document IDs like [ticket_12]
- If evidence is insufficient, say so explicitly rather than guessing
- For executive/strategic questions, structure the answer with a short summary
  followed by supporting points
Do not fabricate facts not present in the evidence.
"""

def call_llm(system, user, temperature=0.2):
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=temperature,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return resp.choices[0].message.content

def plan(question):
    raw = call_llm(PLANNER_SYSTEM, question)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"source_types": ["all"], "search_query": question, "requires_aggregation": False}

def analyze(question, evidence_docs, theme_counts=None, history=None):
    evidence_text = "\n\n".join(
        f"[{d['id']}] (source: {d['source_type']}, date: {d.get('date','?')}) {d['text']}"
        for d in evidence_docs
    )
    history_text = ""
    if history:
        history_text = "Recent conversation:\n" + "\n".join(
            f"Q: {h['question']}\nA: {h['answer']}" for h in history
        )
    theme_text = f"\nTheme frequency counts: {json.dumps(theme_counts)}" if theme_counts else ""

    user_prompt = f"""Question: {question}

{history_text}

Evidence:
{evidence_text}
{theme_text}
"""
    return call_llm(ANALYST_SYSTEM, user_prompt)

def run_pipeline(question, retriever, history=None):
    plan_result = plan(question)
    source_types = plan_result.get("source_types", ["all"])
    search_query = plan_result.get("search_query", question)
    requires_agg = plan_result.get("requires_aggregation", False)

    evidence = []
    if "all" in source_types or not source_types:
        evidence = retriever.search(search_query, top_k=10)
    else:
        for st in source_types:
            evidence.extend(retriever.search(search_query, top_k=6, source_type=st))

    theme_counts = retriever.all_by_theme() if requires_agg else None
    answer = analyze(question, evidence, theme_counts, history)

    return {
        "plan": plan_result,
        "retrieved_ids": [d["id"] for d in evidence],
        "answer": answer,
    }
