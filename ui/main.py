"""
ui/main.py — Streamlit application entry point.
Run:  streamlit run ui/main.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from ui import client

st.set_page_config(
    page_title="Rag-Assist",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #111827;
    color: #f3f4f6;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 1.5rem 2rem 0 2rem;
    max-width: 1000px;
}

/* ── Top nav ── */
.topnav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 16px;
    border-bottom: 1px solid #1f2937;
    margin-bottom: 20px;
}
.topnav-logo { display: flex; align-items: center; gap: 10px; }
.topnav-icon {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
}
.topnav-name { font-size: 15px; font-weight: 700; color: #f9fafb; }
.topnav-sub  { font-size: 11px; color: #6b7280; margin-top: 1px; }
.status-dot {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 11px; color: #6b7280;
}
.dot-on  { width: 6px; height: 6px; border-radius: 50%; background: #22c55e; display:inline-block; }
.dot-off { width: 6px; height: 6px; border-radius: 50%; background: #ef4444; display:inline-block; }

/* ── Tabs ── */
div[data-testid="stTabs"] button {
    font-size: 13px !important;
    color: #9ca3af !important;
    padding: 8px 16px !important;
    border-radius: 8px 8px 0 0 !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #f9fafb !important;
    border-bottom: 2px solid #6366f1 !important;
    background: transparent !important;
}

/* ── Chat messages ── */
div[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 4px 0 !important;
}

/* User message bubble */
div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stMarkdown {
    background: #312e81 !important;
    border-radius: 18px 18px 4px 18px !important;
    padding: 10px 15px !important;
    color: #e0e7ff !important;
    display: inline-block;
    max-width: 75%;
    float: right;
    clear: both;
}

/* Assistant message bubble */
div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) .stMarkdown {
    background: #1f2937 !important;
    border-radius: 18px 18px 18px 4px !important;
    padding: 10px 15px !important;
    color: #e5e7eb !important;
    display: inline-block;
    max-width: 80%;
}

/* Avatar icons */
div[data-testid="chatAvatarIcon-user"] {
    background: #4f46e5 !important;
    color: white !important;
}
div[data-testid="chatAvatarIcon-assistant"] {
    background: #374151 !important;
    color: #a5b4fc !important;
}

/* ── Widget labels (force visible in any theme) ── */
div[data-testid="stWidgetLabel"] label,
div[data-testid="stWidgetLabel"] p,
label[data-testid="stWidgetLabel"],
.stTextInput label, .stTextInput label p {
    color: #d1d5db !important;
    -webkit-text-fill-color: #d1d5db !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    opacity: 1 !important;
}

/* ── Text inputs (email, password, etc.) ── */
div[data-testid="stTextInput"] label {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #d1d5db !important;
    margin-bottom: 4px !important;
    padding: 0 !important;
}
div[data-testid="stTextInput"] > div {
    margin-bottom: 0 !important;
}
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
    background: #1f2937 !important;
    border: 1px solid #374151 !important;
    border-radius: 10px !important;
}
div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}
div[data-testid="stTextInput"] input {
    background: transparent !important;
    color: #f3f4f6 !important;
    font-size: 14px !important;
    font-family: 'Inter', sans-serif !important;
    -webkit-text-fill-color: #f3f4f6 !important;
    caret-color: #6366f1 !important;
    padding: 10px 12px !important;
}
div[data-testid="stTextInput"] input::placeholder {
    color: #6b7280 !important;
    -webkit-text-fill-color: #6b7280 !important;
}
/* Autofill — kill the browser's white background + black text */
div[data-testid="stTextInput"] input:-webkit-autofill,
div[data-testid="stTextInput"] input:-webkit-autofill:hover,
div[data-testid="stTextInput"] input:-webkit-autofill:focus {
    -webkit-text-fill-color: #f3f4f6 !important;
    -webkit-box-shadow: 0 0 0 1000px #1f2937 inset !important;
    caret-color: #f3f4f6 !important;
}
/* Password reveal icon */
div[data-testid="stTextInput"] button {
    color: #9ca3af !important;
}

/* ── Chat input bar ── */
div[data-testid="stChatInput"] {
    border-top: 1px solid #1f2937 !important;
    padding: 12px 0 !important;
    background: #111827 !important;
}
div[data-testid="stChatInput"] > div {
    background: #1f2937 !important;
    border: 1px solid #374151 !important;
    border-radius: 14px !important;
    padding: 4px 8px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
}
div[data-testid="stChatInput"] > div:focus-within {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}
div[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #f3f4f6 !important;
    font-size: 14px !important;
    font-family: 'Inter', sans-serif !important;
    line-height: 1.5 !important;
    border: none !important;
    outline: none !important;
    resize: none !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
    color: #6b7280 !important;
}
/* Send button */
div[data-testid="stChatInput"] button {
    background: #6366f1 !important;
    border-radius: 10px !important;
    color: white !important;
    border: none !important;
    padding: 6px 10px !important;
}
div[data-testid="stChatInput"] button:hover {
    background: #4f46e5 !important;
}

/* ── Scrollable message area ── */
div[data-testid="stVerticalBlock"]:has(div[data-testid="stChatInput"]) {
    display: flex;
    flex-direction: column;
}

/* Page itself must NOT scroll — only the message list scrolls.
   The messages container (marked by #chat-scroll-anchor) is sized to fill
   the viewport, and the input is pinned to the bottom of the viewport
   (Streamlit loses native pinning when chat_input is inside a tab). */
.block-container { padding-bottom: 90px !important; }
div[data-testid="stMainBlockContainer"] { padding-bottom: 90px !important; }

div[data-testid="stVerticalBlockBorderWrapper"]:has(#chat-scroll-anchor) {
    height: calc(100vh - 230px) !important;
    min-height: 200px !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
}
#chat-scroll-anchor { display: block; height: 0; margin: 0; }

/* Pin the chat input to the bottom of the viewport, aligned with the
   centered content column. Hidden automatically on non-chat tabs because
   Streamlit sets [hidden] on inactive tab panels. */
div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 100% !important;
    max-width: 1000px !important;
    padding: 10px 2rem 14px 2rem !important;
    background: #111827 !important;
    z-index: 999 !important;
}

/* ── Empty state ── */
.chat-empty {
    text-align: center;
    padding: 60px 20px 40px;
    color: #6b7280;
}
.chat-empty .icon { font-size: 42px; margin-bottom: 16px; }
.chat-empty h3 {
    font-size: 20px; font-weight: 600;
    color: #f9fafb; margin-bottom: 8px;
}
.chat-empty p {
    font-size: 14px; color: #9ca3af;
    max-width: 380px; margin: 0 auto 24px; line-height: 1.6;
}
.chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.chip {
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 20px;
    padding: 7px 14px;
    font-size: 12px;
    color: #9ca3af;
    cursor: pointer;
    transition: all .15s;
}
.chip:hover { border-color: #6366f1; color: #a5b4fc; }

/* ── Message meta tags ── */
.msg-meta { margin-top: 4px; }
.tag {
    display: inline-flex; align-items: center; gap: 3px;
    padding: 2px 8px; border-radius: 8px;
    font-size: 10px; font-weight: 500; margin-right: 4px;
}
.t-api { background: #0c1a3a; color: #60a5fa; border: 1px solid #1d3a6e; }
.t-rw  { background: #1e1040; color: #a78bfa; border: 1px solid #3b1f7a; }
.rw-box {
    background: #1e1040; border: 1px solid #3b1f7a;
    border-radius: 8px; padding: 7px 11px;
    font-size: 12px; color: #a78bfa; margin-top: 5px;
}

/* ── Upload zone ── */
.upload-hint {
    border: 2px dashed #374151; border-radius: 14px;
    padding: 40px 24px; text-align: center;
    background: #1f2937; margin-bottom: 16px;
}
.upload-hint .ico  { font-size: 36px; margin-bottom: 10px; }
.upload-hint .ttl  { font-size: 16px; font-weight: 600; color: #f9fafb; margin-bottom: 4px; }
.upload-hint .sub  { font-size: 12px; color: #6b7280; }

/* ── File item ── */
.file-item {
    display: flex; align-items: center; justify-content: space-between;
    background: #1f2937; border: 1px solid #374151; border-radius: 10px;
    padding: 10px 14px; margin-bottom: 8px;
}
.file-name { font-size: 13px; color: #e5e7eb; display: flex; align-items: center; gap: 8px; }
.file-size { font-size: 11px; color: #6b7280; }

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    transition: all .15s !important;
    border: 1px solid #374151 !important;
    background: #1f2937 !important;
    color: #d1d5db !important;
}
div[data-testid="stButton"] > button:hover {
    border-color: #6366f1 !important;
    color: #a5b4fc !important;
    background: #1e1b4b !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: #6366f1 !important;
    border-color: #6366f1 !important;
    color: white !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: #4f46e5 !important;
    border-color: #4f46e5 !important;
    color: white !important;
}

/* ── Divider ── */
hr { border-color: #1f2937 !important; }

/* ── Metrics ── */
div[data-testid="metric-container"] {
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 10px;
    padding: 12px 16px;
}
div[data-testid="metric-container"] label { color: #9ca3af !important; font-size: 11px !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #f9fafb !important; font-size: 20px !important; font-weight: 700 !important;
}

/* ── Code blocks ── */
.stCode { border-radius: 10px !important; font-size: 12px !important; }

/* ── Progress ── */
div[data-testid="stProgress"] > div { background: #1f2937 !important; border-radius: 99px; }
div[data-testid="stProgress"] > div > div { background: #6366f1 !important; border-radius: 99px; }

/* ── Spinner ── */
div[data-testid="stSpinner"] { color: #6366f1 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {
    "token":        None,
    "user_email":   None,
    "messages":     [],
    "upload_id":    None,
    "staged_files": [],
    "job_id":       None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not st.session_state.token:
    from ui.pages.auth_page import render as render_auth
    render_auth()
    st.stop()

# ── Top nav ───────────────────────────────────────────────────────────────────
online = client.is_online()
nav_l, nav_r = st.columns([6, 1])

with nav_l:
    st.markdown(f"""
    <div class="topnav">
        <div class="topnav-logo">
            <div class="topnav-icon">⚡</div>
            <div>
                <div class="topnav-name">Rag-Assist</div>
                <div class="topnav-sub">Chat with your documents using AI</div>
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:16px;">
            <span class="status-dot">
                <span class="{'dot-on' if online else 'dot-off'}"></span>
                {'Connected' if online else 'API offline'}
            </span>
            <span style="font-size:12px;color:#6b7280;">
                {st.session_state.user_email or ''}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with nav_r:
    if st.button("Sign out", use_container_width=True):
        for k in ("token", "user_email", "upload_id", "job_id"):
            st.session_state[k] = None
        for k in ("messages", "staged_files"):
            st.session_state[k] = []
        st.rerun()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_chat, tab_upload, tab_docs = st.tabs(["💬  Chat", "📂  Documents", "🗂️  Knowledge Base"])

with tab_chat:
    from ui.pages.chat_page import render as render_chat
    render_chat()

with tab_upload:
    from ui.pages.upload_page import render as render_upload
    render_upload()

with tab_docs:
    from ui.pages.kb_page import render as render_kb
    render_kb()
