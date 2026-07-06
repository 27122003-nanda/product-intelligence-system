"""
Minimal Streamlit front-end for demoing the Product Intelligence system.
Run: streamlit run ui.py  (with the FastAPI backend running on localhost:8000)
"""
import streamlit as st
import requests
import uuid

st.set_page_config(page_title="Product Intelligence Analyst", layout="centered")
st.title("🧠 Autonomous Product Intelligence & Decision Support System")
st.caption("Ask a business question — the system retrieves evidence across tickets, "
           "feature requests, PRDs, and meeting notes, then reasons over it.")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat" not in st.session_state:
    st.session_state.chat = []
if "question_box" not in st.session_state:
    st.session_state.question_box = ""

API_URL = "http://localhost:8000/ask"

SAMPLE_QUESTIONS = [
    "What are the most common customer complaints during the last six months?",
    "Which feature requests appear most frequently across support tickets and feedback?",
    "Which issues reported by customers were eventually fixed?",
    "Generate an executive summary of major risks, opportunities, and recommendations.",
]

def set_question(q):
    st.session_state.question_box = q

st.sidebar.header("Try a sample question")
for q in SAMPLE_QUESTIONS:
    st.sidebar.button(q, on_click=set_question, args=(q,), key=q)

st.text_input("Your question", key="question_box")

def ask_question():
    question = st.session_state.question_box
    if not question:
        return
    resp = requests.post(API_URL, json={"question": question, "session_id": st.session_state.session_id})
    try:
        data = resp.json()
    except Exception:
        st.error(f"Backend error (status {resp.status_code}): {resp.text[:500]}")
        return
    st.session_state.chat.append((question, data))

st.button("Ask", on_click=ask_question)

for q, data in reversed(st.session_state.chat):
    st.markdown(f"**Q: {q}**")
    st.write(data.get("answer", "(no answer returned)"))
    with st.expander("Plan + retrieved evidence IDs"):
        st.json(data.get("plan", {}))
        st.write(data.get("retrieved_ids", []))
    st.divider()
