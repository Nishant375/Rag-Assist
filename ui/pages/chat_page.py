"""
ui/pages/chat_page.py — Chat tab UI.
"""

import streamlit as st
from ui import client


def render():
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

    # Clear button
    _, col_clear = st.columns([8, 1])
    with col_clear:
        if st.session_state.messages:
            if st.button("🗑", help="Clear chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

    # Input
    if prompt := st.chat_input("Ask anything …"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        answer = ""; meta_html = ""

        with messages_box:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner(""):
                    try:
                        data      = client.chat(prompt)
                        answer    = data["answer"]
                        rq        = data.get("rewritten_question")

                        st.markdown(answer)

                        t_rw      = '<span class="tag t-rw">✏️ rewritten</span>' if rq else ""
                        meta_html = f'<div class="msg-tags"><span class="tag t-api">🌐 API</span>{t_rw}</div>'
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
