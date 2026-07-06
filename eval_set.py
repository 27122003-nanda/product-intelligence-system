"""
Simple evaluation harness: runs a fixed set of questions through the pipeline
and checks whether retrieval surfaced documents of the expected source_type.
Not a full LLM-judged eval (out of scope for the timeline) but demonstrates
an observability/evaluation mindset — logged results double as a regression
check if retrieval or prompts change.
"""
import json, os
from app.retrieval import HybridRetriever
from app.agents import run_pipeline

EVAL_QUESTIONS = [
    {"q": "What are the most common customer complaints during the last six months?",
     "expected_source": "support_ticket"},
    {"q": "Which feature requests appear most frequently across feedback?",
     "expected_source": "feature_request"},
    {"q": "Which issues reported by customers were eventually fixed?",
     "expected_source": "support_ticket"},
    {"q": "What did the product team discuss in recent meetings?",
     "expected_source": "meeting_note"},
    {"q": "What is the scope of the SSO login PRD?",
     "expected_source": "prd"},
]

def main():
    retriever = HybridRetriever()
    results = []
    for case in EVAL_QUESTIONS:
        out = run_pipeline(case["q"], retriever)
        retrieved_types = {rid.split("_")[0] for rid in out["retrieved_ids"]}
        # normalize id prefixes -> source types
        prefix_map = {"ticket": "support_ticket", "feature": "feature_request",
                      "prd": "prd", "meeting": "meeting_note"}
        retrieved_source_types = {prefix_map.get(p, p) for p in retrieved_types}
        passed = case["expected_source"] in retrieved_source_types
        results.append({
            "question": case["q"],
            "expected_source": case["expected_source"],
            "retrieved_source_types": list(retrieved_source_types),
            "passed": passed,
            "answer": out["answer"],
        })
        print(f"{'PASS' if passed else 'FAIL'} | {case['q']}")

    with open("eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n{sum(r['passed'] for r in results)}/{len(results)} passed. See eval_results.json")

if __name__ == "__main__":
    main()
