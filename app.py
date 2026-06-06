"""
app.py — RAG Assistant UI.
Chat is always available. Upload tab is optional for adding documents.
Run:  uv run streamlit run app.py
"""

import os
import time
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="DocuMind",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header   { visibility: hidden; }
.block-container { padding: 1.8rem 3rem 0 3rem; max-width: 1100px; }

/* Nav */
.topnav {
    display: flex; align-items: center; justify-content: space-between;
    padding-bottom: 18px; border-bottom: 1px solid #1e2130; margin-bottom: 24px;
}
.topnav-logo { display: flex; align-items: center; gap: 10px; }
.topnav-icon {
    width: 34px; height: 34px;
    background: linear-gradient(135deg,#6366f1,#8b5cf6);
    border-radius: 9px; display:flex; align-items:center;
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

/* Progress card */
.prog-card {
    background:#0a0d14; border:1px solid #1e2130;
    border-radius:16px; padding:24px 28px; margin-bottom:16px;
}
.prog-header {
    display:flex; align-items:center; justify-content:space-between; margin-bottom:18px;
}
.prog-title { font-size:15px; font-weight:600; color:#e2e8f0; }
.sbadge { padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; }
.s-queued  { background:#1c1917; color:#fb923c; border:1px solid #92400e; }
.s-running { background:#0c1a2e; color:#38bdf8; border:1px solid #075985; }
.s-done    { background:#052e16; color:#4ade80; border:1px solid #166534; }
.s-failed  { background:#2d0a0a; color:#f87171; border:1px solid #991b1b; }

.stat-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-bottom:16px; }
.stat-box  {
    background:#0f1117; border:1px solid #1e2130;
    border-radius:10px; padding:12px 14px;
}
.stat-label { font-size:11px; color:#475569; margin-bottom:3px; }
.stat-value { font-size:20px; font-weight:700; color:#e2e8f0; }
.stat-sub   { font-size:11px; color:#64748b; margin-top:2px; }

.bar-wrap { background:#1e2130; border-radius:99px; height:7px; margin-bottom:16px; overflow:hidden; }
.bar-fill {
    height:100%; border-radius:99px;
    background:linear-gradient(90deg,#6366f1,#8b5cf6); transition:width .5s ease;
}

.log-box {
    background:#06080f; border:1px solid #1a1e2e; border-radius:10px;
    padding:12px 14px; font-family:'Courier New',monospace; font-size:11.5px;
    max-height:180px; overflow-y:auto; line-height:1.8;
}
.log-ok  { color:#4ade80; }
.log-err { color:#f87171; }
.log-cur { color:#38bdf8; }
.log-inf { color:#94a3b8; }

/* ── Chat input styling ── */
div[data-testid="stChatInput"] textarea {
    background: #0f1117 !important;
    border: 1px solid #2d3148 !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-size: 14px !important;
}
div[data-testid="stChatInput"] textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px #6366f130 !important;
}

/* Scrollable message container */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
    scrollbar-width: thin;
    scrollbar-color: #2d3148 transparent;
}

/* Empty state */
.chat-empty {
    text-align:center; padding:52px 20px;
}
.chat-empty h2 { font-size:21px; font-weight:700; color:#e2e8f0; margin-bottom:8px; }
.chat-empty p  { color:#475569; font-size:14px; max-width:420px; margin:0 auto 22px; }
.chips { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; }
.chip {
    background:#0f1117; border:1px solid #2d3148; border-radius:20px;
    padding:7px 16px; font-size:12px; color:#94a3b8;
}

.msg-tags { display:flex; gap:6px; margin-top:6px; flex-wrap:wrap; }
.tag { padding:2px 9px; border-radius:10px; font-size:11px; font-weight:500; display:inline-flex; align-items:center; gap:3px; }
.t-api    { background:#0f2027; color:#38bdf8; border:1px solid #0c4a6e; }
.t-direct { background:#1c1917; color:#fb923c; border:1px solid #78350f; }
.t-rw     { background:#1a1040; color:#a78bfa; border:1px solid #4c1d95; }
.rw-box {
    background:#1a1040; border:1px solid #4c1d95; border-radius:8px;
    padding:8px 12px; font-size:12px; color:#a78bfa; margin-top:6px;
}

div[data-testid="stButton"] > button {
    border-radius:10px !important; font-weight:500 !important; transition:all .2s !important;
}

/* Upload zone */
.upload-hint {
    border:2px dashed #2d3148; border-radius:14px;
    padding:36px 24px; text-align:center; background:#0a0d14; margin-bottom:16px;
}
.upload-hint .ico  { font-size:36px; margin-bottom:10px; }
.upload-hint .ttl  { font-size:16px; font-weight:600; color:#e2e8f0; margin-bottom:4px; }
.upload-hint .sub  { font-size:12px; color:#475569; }
</style>
""", unsafe_allow_html=True)


# ── API helpers ───────────────────────────────────────────────────────────────

def api_online() -> bool:
    try:
        return requests.get(f"{API_URL}/health", timeout=2).ok
    except Exception:
        return False


def upload_files(uploaded_files) -> dict:
    files = [("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
             for f in uploaded_files]
    resp = requests.post(f"{API_URL}/ingest/upload", files=files, timeout=30)
    resp.raise_for_status()
    return resp.json()


def trigger_store(upload_id: str) -> dict:
    resp = requests.post(f"{API_URL}/ingest/store/{upload_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_job(job_id: str) -> dict:
    return requests.get(f"{API_URL}/ingest/status/{job_id}", timeout=5).json()


def list_documents() -> list[dict]:
    try:
        resp = requests.get(f"{API_URL}/documents", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


def delete_document(source: str) -> bool:
    try:
        resp = requests.delete(f"{API_URL}/documents/{source}", timeout=10)
        return resp.ok
    except Exception:
        return False


def chat_query(message: str) -> dict:
    try:
        resp = requests.post(f"{API_URL}/chat", json={"message": message}, timeout=120)
        resp.raise_for_status()
        data = resp.json(); data["_mode"] = "api"; return data
    except Exception:
        from agent.graph import crag_graph
        result = crag_graph.invoke({
            "question": message, "original_question": message,
            "documents": [], "generation": "",
            "generation_attempts": 0, "retrieval_attempts": 0, "steps": [],
        })
        fq = result.get("question", "")
        return {
            "answer": result.get("generation") or "No relevant answer found.",
            "steps": result.get("steps", []),
            "rewritten_question": fq if fq != message else None,
            "_mode": "direct",
        }


# ── Session state ─────────────────────────────────────────────────────────────

for k, v in {
    "messages":     [],
    "upload_id":    None,
    "staged_files": [],
    "job_id":       None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Top nav ───────────────────────────────────────────────────────────────────

online = api_online()
st.markdown(f"""
<div class="topnav">
    <div class="topnav-logo">
        <div class="topnav-icon">⚡</div>
        <div>
            <div class="topnav-name">DocuMind</div>
            <div class="topnav-sub">Chat with your documents using AI</div>
        </div>
    </div>
    <span class="api-pill {'api-on' if online else 'api-off'}">
        <span class="dot {'dot-on' if online else 'dot-off'}"></span>
        {'API connected' if online else 'API offline — run: make api'}
    </span>
</div>
""", unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_chat, tab_upload, tab_docs = st.tabs(["💬  Chat", "📂  Upload Documents", "🗂️  Knowledge Base"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT  (always available)
# ══════════════════════════════════════════════════════════════════════════════

with tab_chat:

    # ── Scrollable messages box (fills screen, input sits below) ──────────────
    messages_box = st.container(height=570, border=False)

    with messages_box:
        if not st.session_state.messages:
            st.markdown("""
            <div class="chat-empty">
                <div style="font-size:44px;margin-bottom:16px;">⚡</div>
                <h2>Ask me anything</h2>
                <p>
                    Chat freely — or upload documents in the
                    <b>Upload Documents</b> tab and I'll answer from them.
                </p>
                <div class="chips">
                    <span class="chip">Hi!</span>
                    <span class="chip">What can you help me with?</span>
                    <span class="chip">Summarize my documents</span>
                    <span class="chip">What topics are covered?</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if msg.get("meta"):
                        st.markdown(msg["meta"], unsafe_allow_html=True)

    # ── Clear + Input row — always below the messages box ────────────────────
    col_input, col_clear = st.columns([8, 1])

    with col_clear:
        if st.session_state.messages:
            if st.button("🗑", help="Clear chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

    # Input — Streamlit renders chat_input pinned at bottom of page
    if prompt := st.chat_input("Ask anything …"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        answer = ""; meta_html = ""
        with messages_box:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner(""):
                    try:
                        data      = chat_query(prompt)
                        answer    = data["answer"]
                        mode      = data.get("_mode", "api")
                        rq        = data.get("rewritten_question")

                        st.markdown(answer)

                        t_mode    = '<span class="tag t-api">🌐 API</span>' if mode == "api" \
                                    else '<span class="tag t-direct">⚡ direct</span>'
                        t_rw      = '<span class="tag t-rw">✏️ rewritten</span>' if rq else ""
                        meta_html = f'<div class="msg-tags">{t_mode}{t_rw}</div>'
                        if rq:
                            meta_html += f'<div class="rw-box"><b>Rewritten to:</b> {rq}</div>'

                        st.markdown(meta_html, unsafe_allow_html=True)

                    except Exception as exc:
                        answer = f"Something went wrong: {exc}"
                        st.error(answer)

        st.session_state.messages.append(
            {"role": "assistant", "content": answer, "meta": meta_html}
        )
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MANAGE DOCUMENTS
# ══════════════════════════════════════════════════════════════════════════════

with tab_upload:

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1.5, 1])
    ext_icons = {".pdf": "📕", ".docx": "📘", ".txt": "📄", ".md": "📝"}

    with left:

        # ── Active job progress ───────────────────────────────────────────────
        if st.session_state.job_id:
            job    = get_job(st.session_state.job_id)
            status = job["status"]
            total  = max(job["files_found"], 1)
            done   = job["files_done"]
            pct    = done / total

            # Header
            status_icon = {"queued": "⏳", "running": "⚡", "done": "✅", "failed": "❌"}.get(status, "⏳")
            st.markdown(f"### {status_icon} Job `{job['id']}` — **{status.upper()}**")

            # Metrics row
            c1, c2, c3 = st.columns(3)
            c1.metric("Files processed", f"{done} / {job['files_found']}")
            c2.metric("Chunks stored",   f"{job['chunks_total']:,}")
            c3.metric("Started at",      job["started_at"][11:19] + " UTC")

            if job.get("current_file"):
                st.caption(f"↳ Currently processing: **{job['current_file']}**")

            # Progress bar
            st.progress(pct)

            # Live log
            if job.get("log"):
                log_text = "\n".join(job["log"][-25:])
                st.code(log_text, language=None)

            # Actions
            if status == "queued":
                st.info("Job is queued, starting soon …")
                time.sleep(1); st.rerun()
            elif status == "running":
                time.sleep(1); st.rerun()
            elif status == "done":
                st.success(f"✅ Done — {job['chunks_total']:,} chunks stored. Switch to **Chat** tab to ask questions.")
                if st.button("Upload more documents", use_container_width=True):
                    st.session_state.job_id = None
                    st.rerun()
            elif status == "failed":
                st.error(f"❌ Failed: {job.get('error')}")
                if st.button("Try again", use_container_width=True):
                    st.session_state.job_id = None
                    st.rerun()

        # ── Upload stage ──────────────────────────────────────────────────────
        else:
            st.markdown("""
            <div class="upload-hint">
                <div class="ico">📄</div>
                <div class="ttl">Upload your documents</div>
                <div class="sub">PDF, DOCX, TXT, MD — multiple files at once</div>
            </div>
            """, unsafe_allow_html=True)

            uploaded = st.file_uploader(
                "Choose files",
                type=["pdf", "docx", "txt", "md"],
                accept_multiple_files=True,
                label_visibility="collapsed",
            )

            if uploaded and not st.session_state.upload_id:
                if not online:
                    st.error("API is offline. Run `make api` first.")
                elif st.button("① Upload files", use_container_width=True):
                    with st.spinner("Uploading …"):
                        try:
                            result = upload_files(uploaded)
                            st.session_state.upload_id    = result["upload_id"]
                            st.session_state.staged_files = result["files"]
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Upload failed: {exc}")

    with right:
        if not st.session_state.job_id:

            # Awaiting upload
            if not st.session_state.upload_id:
                st.markdown("""
                <div style="color:#475569;font-size:13px;padding:16px 0;">
                    <b style="color:#94a3b8">How it works</b><br><br>
                    <b style="color:#e2e8f0">①</b> Select your files<br><br>
                    <b style="color:#e2e8f0">②</b> Click <i>Upload files</i> — they're saved to the server<br><br>
                    <b style="color:#e2e8f0">③</b> Click <i>Store in Knowledge Base</i> — files get embedded and stored in Pinecone<br><br>
                    <b style="color:#e2e8f0">④</b> Switch to Chat — ask questions immediately
                </div>
                """, unsafe_allow_html=True)

            # Files uploaded, ready to store
            elif st.session_state.upload_id:
                st.success(f"✓ Uploaded  ·  ID: `{st.session_state.upload_id}`")
                st.markdown("**Files on server**")

                for fname in st.session_state.staged_files:
                    ext  = "." + fname.rsplit(".", 1)[-1].lower()
                    icon = ext_icons.get(ext, "📄")
                    st.markdown(f"""
                    <div class="file-item">
                        <div class="file-name"><span>{icon}</span>{fname}</div>
                        <div class="file-size" style="color:#4ade80">✓ saved</div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                if st.button("② Store in Knowledge Base →", use_container_width=True, type="primary"):
                    with st.spinner("Starting …"):
                        try:
                            result = trigger_store(st.session_state.upload_id)
                            st.session_state.job_id    = result["job_id"]
                            st.session_state.upload_id    = None
                            st.session_state.staged_files = []
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Failed: {exc}")

                if st.button("✕ Cancel", use_container_width=True):
                    st.session_state.upload_id    = None
                    st.session_state.staged_files = []
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — KNOWLEDGE BASE (all stored documents)
# ══════════════════════════════════════════════════════════════════════════════

with tab_docs:
    st.markdown("<br>", unsafe_allow_html=True)

    col_hdr, col_btn = st.columns([5, 1])
    with col_hdr:
        st.markdown("### 🗂️ Stored Documents")
        st.caption("All files currently indexed in your vector database.")
    with col_btn:
        if st.button("↻ Refresh", use_container_width=True):
            st.rerun()

    st.divider()

    if not online:
        st.warning("API is offline. Run `make api` to see documents.")
    else:
        docs = list_documents()

        if not docs:
            st.markdown("""
            <div style="text-align:center; padding:48px 0; color:#475569;">
                <div style="font-size:40px; margin-bottom:12px;">📭</div>
                <div style="font-size:16px; font-weight:600; color:#94a3b8;">No documents yet</div>
                <div style="font-size:13px; margin-top:6px;">
                    Go to <b>Upload Documents</b> tab to add files to the knowledge base.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            total_chunks = sum(d["chunks"] for d in docs)
            store_name   = docs[0]["store"] if docs else "—"
            m1, m2, m3   = st.columns(3)
            m1.metric("Total files",  len(docs))
            m2.metric("Total chunks", f"{total_chunks:,}")
            m3.metric("Vector store", store_name)

            st.markdown("<br>", unsafe_allow_html=True)

            ext_icons = {".pdf": "📕", ".docx": "📘", ".txt": "📄", ".md": "📝"}

            h1, h2, h3, h4 = st.columns([3, 1, 1, 1])
            h1.markdown("**File**")
            h2.markdown("**Chunks**")
            h3.markdown("**Store**")
            h4.markdown("**Action**")
            st.divider()

            for doc in docs:
                source = doc["source"]
                ext    = "." + source.rsplit(".", 1)[-1].lower() if "." in source else ""
                icon   = ext_icons.get(ext, "📄")

                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                c1.markdown(f"{icon} **{source}**")
                c2.markdown(f"`{doc['chunks']:,}`")
                c3.markdown(f"`{doc['store']}`")

                with c4:
                    if st.button("🗑 Delete", key=f"del_{source}", use_container_width=True):
                        with st.spinner(f"Deleting {source} …"):
                            ok = delete_document(source)
                            if ok:
                                st.success(f"Deleted {source}")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Delete failed")
                st.divider()

        with st.expander("📡 API reference"):
            st.code(f"""# List all stored documents
GET {API_URL}/documents

# Delete a document
DELETE {API_URL}/documents/{{filename}}""", language="bash")
