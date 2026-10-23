"""Text-only Streamlit frontend for Mini JARVIS."""

import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import dotenv_values

st.set_page_config(page_title="Mini JARVIS", page_icon="🤖", layout="centered")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
file_config = dotenv_values(ENV_FILE) if ENV_FILE.is_file() else {}
try:
    cloud_secrets = dict(st.secrets)
except Exception:
    cloud_secrets = {}

API_URL = (
    os.getenv("BACKEND_URL")
    or cloud_secrets.get("BACKEND_URL")
    or file_config.get("BACKEND_URL")
    or "http://127.0.0.1:8000"
).rstrip("/")
API_TOKEN = (
    os.getenv("BACKEND_API_TOKEN")
    or cloud_secrets.get("BACKEND_API_TOKEN")
    or file_config.get("BACKEND_API_TOKEN")
    or ""
).strip()
API_HEADERS = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}
REQUEST_TIMEOUT = 450

st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #101827 0%, #0b1220 100%); color: #edf2f7; }
.block-container { max-width: 850px; padding-top: 2.2rem; }
[data-testid="stChatMessage"] { border: 1px solid #26364b; border-radius: 14px; }
.status-pill { display:inline-block; color:#85efac; border:1px solid #276749; border-radius:20px; padding:4px 12px; font-size:14px; }
</style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

st.title("🤖 AI Assistant — Mini JARVIS")
st.markdown('<span class="status-pill">● Text assistant</span>', unsafe_allow_html=True)
st.caption("Text-only AI assistant. Type a question below; JARVIS replies in English or Urdu based on your message.")

try:
    health_response = requests.get(f"{API_URL}/health", timeout=8)
    health_response.raise_for_status()
    health = health_response.json()
    backend_state = "Online"
    ai_provider = health.get("ai_provider", "AI")
    ai_state = f"{ai_provider.title()} model listed" if health.get("ai_available") else f"{ai_provider.title()} unavailable"
    search_state = "Available" if health.get("search_available") else "Optional key missing"
except requests.RequestException:
    health = None
    backend_state = ai_state = search_state = "Unavailable"

with st.expander("System status and example questions", expanded=False):
    backend_col, ai_col, search_col = st.columns(3)
    backend_col.metric("Backend", backend_state)
    ai_col.metric("AI", ai_state)
    search_col.metric("Search", search_state)
    st.markdown("""
    - Hello JARVIS.
    - What is artificial intelligence?
    - Explain machine learning in simple words.
    - What time is it? / What is today's date?
    - Calculate 125 divided by 5.
    - Search the web for Python latest news.
    - Pakistan ke bare mein short information do.
    - Answer this in Urdu: What is machine learning?
    """)

if health and not health.get("ai_available"):
    if health.get("ai_provider") == "murakumo":
        st.warning("Online AI is not reachable right now. Check the connection and retry.")
    elif health.get("ai_provider") == "ollama":
        st.warning("Local AI is not ready. Start Ollama and check its configured model.")
    else:
        st.warning("AI is not configured. Check the backend's AI_PROVIDER and server configuration.")
if health and health.get("ai_provider") == "murakumo":
    st.info("Online mode: your questions and webpage text are sent to a third-party AI service. Do not submit passwords or private information.")
    st.caption("The free hosted model may take a few minutes to wake before its first answer.")
if not health:
    st.error("Cannot reach the backend. Start the FastAPI service and check BACKEND_URL.")

for item in st.session_state.history:
    with st.chat_message(item["role"], avatar="🧑" if item["role"] == "user" else "🤖"):
        st.markdown(item["content"])

message = st.chat_input("Ask JARVIS anything…")
if message:
    message = message.strip()
    if not message:
        st.warning("Please type a message first.")
    else:
        st.session_state.history.append({"role": "user", "content": message})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(message)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("JARVIS is thinking…"):
                try:
                    response = requests.post(
                        f"{API_URL}/chat",
                        json={"message": message},
                        headers=API_HEADERS,
                        timeout=REQUEST_TIMEOUT,
                    )
                    if response.status_code == 401:
                        st.error("The frontend and backend access tokens do not match. Check the deployment secrets.")
                    elif response.status_code == 503:
                        try:
                            detail = response.json().get("detail")
                        except (ValueError, TypeError):
                            detail = None
                        st.error(
                            detail
                            or "The backend is online, but its AI provider is temporarily unavailable. Please retry shortly."
                        )
                    elif response.status_code >= 400:
                        try:
                            detail = response.json().get("detail")
                        except (ValueError, TypeError):
                            detail = None
                        st.error(detail or "JARVIS could not complete that request. Please try again.")
                    else:
                        reply = response.json()["reply"]
                        st.markdown(reply)
                        st.session_state.history.append({"role": "assistant", "content": reply})
                except requests.Timeout:
                    st.error("JARVIS took too long to respond. Please try again.")
                except requests.RequestException:
                    st.error("JARVIS could not connect to the configured backend. Check that the backend URL is correct and the service is online.")

st.caption("Conversation history is kept in this browser session only.")
