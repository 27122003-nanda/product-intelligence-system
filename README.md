# Autonomous Product Intelligence & Decision Support System

An AI-powered product analyst that ingests support tickets, feature requests,
PRDs, and meeting notes, then answers business questions with evidence-backed,
citable answers — using a two-stage agentic pipeline, hybrid retrieval, and
persistent memory.

## Architecture

```
                     ┌─────────────────────┐
 User question ───▶  │   Planner Agent      │  decides source_types + search query
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │  Hybrid Retriever    │  BM25 (keyword) + MiniLM embeddings (semantic)
                     │  (+ theme frequency  │  weighted score, filtered by source_type
                     │   aggregation)       │
                     └──────────┬───────────┘
                                │  evidence chunks
                                ▼
                     ┌─────────────────────┐
   Memory (SQLite) ─▶│   Analyst Agent      │  reasons over evidence + recent
   recent Q&A history│                     │  conversation history, cites doc IDs
                     └──────────┬───────────┘
                                │
                                ▼
                     Evidence-backed answer + logged interaction
```

**Why this design:**
- **Hybrid retrieval** (not pure vector search) because exact terms — customer
  names, ticket IDs, feature keywords — matter as much as semantic similarity.
- **Two-agent split** (planner / analyst) rather than one monolithic prompt,
  so source selection and reasoning are separated and independently debuggable.
- **SQLite memory** logs every interaction; doubles as both long-term memory
  (follow-up question context) and an observability log for evaluation.
- **Synthetic data with repeated themes** so aggregation questions ("most
  common complaint") have real, checkable signal rather than random text.

## Project structure
```
product_intel/
├── data_gen.py          # generates synthetic multi-source corpus
├── data/raw/corpus.jsonl
├── app/
│   ├── retrieval.py      # hybrid BM25 + embedding retriever
│   ├── agents.py         # planner + analyst agent pipeline (Groq LLaMA)
│   ├── memory.py         # SQLite conversation memory / eval log
│   └── main.py           # FastAPI app (/ask, /logs, /health)
├── ui.py                 # Streamlit demo UI
├── eval_set.py           # small evaluation harness
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
python data_gen.py               # generate synthetic corpus
export GROQ_API_KEY=your_key_here
uvicorn app.main:app --reload    # starts API on :8000
streamlit run ui.py              # starts UI on :8501 (separate terminal)
```

## Evaluation

```bash
python eval_set.py   # runs 5 fixed questions, checks retrieval hit correct source type
```

## Example questions the system answers
- What are the most common customer complaints during the last six months?
- Which feature requests appear most frequently across support tickets and feedback?
- Which issues reported by customers were eventually fixed?
- Generate an executive summary of major risks, opportunities, and recommendations.

## Known trade-offs / scope cuts (given timeline)
- **No dedicated multi-hop research agent** — the analyst agent handles
  single-pass reasoning over retrieved evidence rather than iterative
  research loops. Future work: add a research agent that can re-query with
  refined terms when initial evidence is insufficient.
- **No fine-tuned reranker** — hybrid BM25 + embedding score combination is
  used as-is rather than a trained cross-encoder reranker.
- **Local FAISS-free vector store** — embeddings held in memory via numpy,
  not a dedicated vector DB. Fine at this corpus size; would move to a
  proper vector DB (e.g. Chroma/Pinecone) for production scale.
- **Eval harness checks retrieval correctness, not answer quality** — an
  LLM-as-judge layer would be the next addition for full answer-level eval.

## Deployment
Deployed live on Hugging Face Spaces: https://huggingface.co/spaces/nandabr/product-intelligence-system
