"""
ui/pages/upload_page.py — Upload Documents tab UI.
"""

import time
import streamlit as st
from ui import client

EXT_ICONS = {".pdf": "📕", ".docx": "📘", ".txt": "📄", ".md": "📝"}


def render():
    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1.5, 1])

    with left:
        _render_left()

    with right:
        _render_right()


def _render_left():
    # ── Active job ─────────────────────────────────────────────────────────────
    if st.session_state.job_id:
        try:
            job = client.get_job(st.session_state.job_id)
        except Exception:
            st.session_state.job_id = None
            st.rerun()
            return

        status      = job["status"]
        total       = max(job["files_found"], 1)
        done        = job["files_done"]
        status_icon = {"queued": "⏳", "running": "⚡", "done": "✅", "failed": "❌"}.get(status, "⏳")

        st.markdown(f"### {status_icon} Job `{job['id']}` — **{status.upper()}**")

        c1, c2, c3 = st.columns(3)
        c1.metric("Files processed", f"{done} / {job['files_found']}")
        c2.metric("Chunks stored",   f"{job['chunks_total']:,}")
        c3.metric("Started at",      job["started_at"][11:19] + " UTC")

        if job.get("current_file"):
            st.caption(f"↳ Currently processing: **{job['current_file']}**")

        st.progress(done / total)

        if job.get("log"):
            st.code("\n".join(job["log"][-25:]), language=None)

        if status in ("queued", "running"):
            time.sleep(1)
            st.rerun()
        elif status == "done":
            st.success(f"✅ Done — {job['chunks_total']:,} chunks stored. Switch to **Chat** tab.")
            if st.button("Upload more documents", use_container_width=True):
                st.session_state.job_id = None
                st.rerun()
        elif status == "failed":
            st.error(f"❌ Failed: {job.get('error')}")
            if st.button("Try again", use_container_width=True):
                st.session_state.job_id = None
                st.rerun()

    # ── Upload form ────────────────────────────────────────────────────────────
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
            if not client.is_online():
                st.error("API is offline. Run `make api` first.")
            elif st.button("① Upload files", use_container_width=True):
                with st.spinner("Uploading …"):
                    try:
                        result = client.upload_files(uploaded)
                        st.session_state.upload_id    = result["upload_id"]
                        st.session_state.staged_files = result["files"]
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Upload failed: {exc}")


def _render_right():
    if st.session_state.job_id:
        return

    if not st.session_state.upload_id:
        st.markdown("""
        <div style="color:#475569;font-size:13px;padding:16px 0;">
            <b style="color:#94a3b8">How it works</b><br><br>
            <b style="color:#e2e8f0">①</b> Select your files<br><br>
            <b style="color:#e2e8f0">②</b> Click <i>Upload files</i> — saved to server<br><br>
            <b style="color:#e2e8f0">③</b> Click <i>Store in Knowledge Base</i> — embedded + stored<br><br>
            <b style="color:#e2e8f0">④</b> Switch to Chat — ask questions
        </div>
        """, unsafe_allow_html=True)
        return

    # Files staged, ready to store
    st.success(f"✓ Uploaded  ·  ID: `{st.session_state.upload_id}`")
    st.markdown("**Files on server**")

    for fname in st.session_state.staged_files:
        ext  = "." + fname.rsplit(".", 1)[-1].lower()
        icon = EXT_ICONS.get(ext, "📄")
        st.markdown(f"""
        <div class="file-item">
            <div class="file-name"><span>{icon}</span>{fname}</div>
            <div class="file-size" style="color:#4ade80">✓ saved</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("② Store in Knowledge Base →", use_container_width=True, type="primary"):
        with st.spinner("Starting …"):
            try:
                result = client.trigger_store(st.session_state.upload_id)
                st.session_state.job_id       = result["job_id"]
                st.session_state.upload_id    = None
                st.session_state.staged_files = []
                st.rerun()
            except Exception as exc:
                st.error(f"Failed: {exc}")

    if st.button("✕ Cancel", use_container_width=True):
        st.session_state.upload_id    = None
        st.session_state.staged_files = []
        st.rerun()
