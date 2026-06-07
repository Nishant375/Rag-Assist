"""
ui/main.py — Streamlit application entry point.

Run:  streamlit run ui/main.py
"""

import sys
from pathlib import Path

# Add project root to path so all modules resolve correctly
# when Streamlit runs this file as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from ui import client

st.set_page_config(
    page_title="Rag-Assist",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header   { visibility: hidden; }
.block-container { padding: 1.8rem 3rem 0 3rem; max-width: 1100px; }

/* Nav */
.topnav {
    display:flex; align-items:center; justify-content:space-between;
    padding-bottom:18px; border-bottom:1px solid #1e2130; margin-bottom:24px;
}
.topnav-logo { display:flex; align-items:center; gap:10px; }
.topnav-icon {
    width:34px; height:34px;
    background:linear-gradient(135deg,#6366f1,#8b5cf6);
    border-radius:9px; display:flex; align-items:center;
    justify-content:center; font-size:17px;
}
.topnav-name { font-size:16px; font-weight:700; color:#f1f5f9; letter-spacing:-.3px; }
.topnav-sub  { font-size:11px; color:#475569; }
.api-pill {
    display:inline-flex; align-items:center; gap:6px;
    padding:4px 12px; border-radius:20px; font-size:11px; font-weight:500;
}
.api-on  { background:#052e16; color:#4ade80; border:1px solid #166534; }
.api-off { background:#1c0a0a; color:#f87171; border:1px solid #991b1b; }
.dot { width:7px; height:7px; border-radius:50%; display:inline-block; }
.dot-on  { background:#22c55e; box-shadow:0 0 5px #22c55e; }
.dot-off { background:#f87171; }

/* File list */
.file-item {
    display:flex; align-items:center; justify-content:space-between;
    background:#0f1117; border:1px solid #1e2130; border-radius:10px;
    padding:10px 14px; margin-bottom:8px;
}
.file-name { font-size:13px; color:#e2e8f0; display:flex; align-items:center; gap:8px; }
.file-size { font-size:11px; color:#475569; }

/* Chat */
.chat-empty { text-align:center; padding:52px 20px; }
.chat-empty h2 { font-size:21px; font-weight:700; color:#e2e8f0; margin-bottom:8px; }
.chat-empty p  { color:#475569; font-size:14px; max-width:420px; margin:0 auto 22px; }
.chips { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; }
.chip {
    background:#0f1117; border:1px solid #2d3148; border-radius:20px;
    padding:7px 16px; font-size:12px; color:#94a3b8;
}
.msg-tags { display:flex; gap:6px; margin-top:6px; flex-wrap:wrap; }
.tag { padding:2px 9px; border-radius:10px; font-size:11px; font-weight:500;
       display:inline-flex; align-items:center; gap:3px; }
.t-api { background:#0f2027; color:#38bdf8; border:1px solid #0c4a6e; }
.t-rw  { background:#1a1040; color:#a78bfa; border:1px solid #4c1d95; }
.rw-box {
    background:#1a1040; border:1px solid #4c1d95; border-radius:8px;
    padding:8px 12px; font-size:12px; color:#a78bfa; margin-top:6px;
}
div[data-testid="stChatInput"] textarea {
    background:#0f1117 !important; border:1px solid #2d3148 !important;
    border-radius:12px !important; color:#e2e8f0 !important; font-size:14px !important;
}
div[data-testid="stChatInput"] textarea:focus {
    border-color:#6366f1 !important; box-shadow:0 0 0 2px #6366f130 !important;
}

/* Upload */
.upload-hint {
    border:2px dashed #2d3148; border-radius:14px;
    padding:36px 24px; text-align:center; background:#0a0d14; margin-bottom:16px;
}
.upload-hint .ico { font-size:36px; margin-bottom:10px; }
.upload-hint .ttl { font-size:16px; font-weight:600; color:#e2e8f0; margin-bottom:4px; }
.upload-hint .sub { font-size:12px; color:#475569; }

/* Buttons */
div[data-testid="stButton"] > button {
    border-radius:10px !important; font-weight:500 !important; transition:all .2s !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
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

# ── Auth gate — show login screen if not authenticated ────────────────────────
if not st.session_state.token:
    from ui.pages.auth_page import render as render_auth
    render_auth()
    st.stop()

# ── Top nav ───────────────────────────────────────────────────────────────────
online = client.is_online()
st.markdown(f"""
<div class="topnav">
    <div class="topnav-logo">
        <div class="topnav-icon">⚡</div>
        <div>
            <div class="topnav-name">Rag-Assist</div>
            <div class="topnav-sub">Chat with your documents using AI</div>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:12px;">
        <span class="api-pill {'api-on' if online else 'api-off'}">
            <span class="dot {'dot-on' if online else 'dot-off'}"></span>
            {'API connected' if online else 'API offline'}
        </span>
        <span style="font-size:12px;color:#475569;">👤 {st.session_state.user_email}</span>
    </div>
</div>
""", unsafe_allow_html=True)

_, logout_col = st.columns([9, 1])
with logout_col:
    if st.button("Logout", use_container_width=True):
        for k in ("token", "user_email", "messages", "upload_id", "staged_files", "job_id"):
            st.session_state[k] = None if k in ("token", "user_email", "upload_id", "job_id") else []
        st.rerun()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_chat, tab_upload, tab_docs = st.tabs(["💬  Chat", "📂  Upload Documents", "🗂️  Knowledge Base"])

with tab_chat:
    from ui.pages.chat_page import render as render_chat
    render_chat()

with tab_upload:
    from ui.pages.upload_page import render as render_upload
    render_upload()

with tab_docs:
    from ui.pages.kb_page import render as render_kb
    render_kb()
