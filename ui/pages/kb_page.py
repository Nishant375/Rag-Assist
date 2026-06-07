"""
ui/pages/kb_page.py — Knowledge Base tab UI.
Lists all stored documents with delete capability.
"""

import time
import streamlit as st
from ui import client
from core.config import settings

EXT_ICONS = {".pdf": "📕", ".docx": "📘", ".txt": "📄", ".md": "📝"}


def render():
    st.markdown("<br>", unsafe_allow_html=True)

    col_hdr, col_btn = st.columns([5, 1])
    with col_hdr:
        st.markdown("### 🗂️ Stored Documents")
        st.caption("All files currently indexed in your vector database.")
    with col_btn:
        if st.button("↻ Refresh", use_container_width=True):
            st.rerun()

    st.divider()

    if not client.is_online():
        st.warning("API is offline. Run `make api` to see documents.")
        return

    docs = client.list_documents()

    if not docs:
        st.markdown("""
        <div style="text-align:center;padding:48px 0;color:#475569;">
            <div style="font-size:40px;margin-bottom:12px;">📭</div>
            <div style="font-size:16px;font-weight:600;color:#94a3b8;">No documents yet</div>
            <div style="font-size:13px;margin-top:6px;">
                Go to <b>Upload Documents</b> tab to add files to the knowledge base.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        total_chunks = sum(d["chunks"] for d in docs)
        m1, m2, m3  = st.columns(3)
        m1.metric("Total files",  len(docs))
        m2.metric("Total chunks", f"{total_chunks:,}")
        m3.metric("Vector store", docs[0]["store"] if docs else "—")

        st.markdown("<br>", unsafe_allow_html=True)

        h1, h2, h3, h4 = st.columns([3, 1, 1, 1])
        h1.markdown("**File**")
        h2.markdown("**Chunks**")
        h3.markdown("**Store**")
        h4.markdown("**Action**")
        st.divider()

        for doc in docs:
            source = doc["source"]
            ext    = "." + source.rsplit(".", 1)[-1].lower() if "." in source else ""
            icon   = EXT_ICONS.get(ext, "📄")

            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            c1.markdown(f"{icon} **{source}**")
            c2.markdown(f"`{doc['chunks']:,}`")
            c3.markdown(f"`{doc['store']}`")

            with c4:
                if st.button("🗑", key=f"del_{source}", use_container_width=True,
                             help=f"Delete {source}"):
                    with st.spinner(f"Deleting {source} …"):
                        if client.delete_document(source):
                            st.success(f"Deleted {source}")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Delete failed")
            st.divider()

    with st.expander("📡 API reference"):
        st.code(f"""# List all stored documents
GET {settings.api_url}/documents

# Delete a document
DELETE {settings.api_url}/documents/{{filename}}""", language="bash")
