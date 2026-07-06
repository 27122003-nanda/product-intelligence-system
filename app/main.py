import os, uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .retrieval import HybridRetriever
from .agents import run_pipeline
from . import memory

app = FastAPI(title="Autonomous Product Intelligence & Decision Support System")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

memory.init_db()
retriever = HybridRetriever()  # loaded once at startup


class AskRequest(BaseModel):
    question: str
    session_id: str | None = None


@app.post("/ask")
def ask(req: AskRequest):
    session_id = req.session_id or str(uuid.uuid4())
    history = memory.get_recent_history(session_id, limit=5)

    result = run_pipeline(req.question, retriever, history=history)

    memory.log_interaction(
        session_id, req.question, result["plan"], result["retrieved_ids"], result["answer"]
    )

    return {
        "session_id": session_id,
        "answer": result["answer"],
        "plan": result["plan"],
        "retrieved_ids": result["retrieved_ids"],
    }


@app.get("/logs")
def logs():
    rows = memory.get_all_logs()
    return [{"session_id": r[0], "question": r[1], "answer": r[2], "timestamp": r[3]} for r in rows]


@app.get("/health")
def health():
    return {"status": "ok", "docs_indexed": len(retriever.docs)}
