"""
ui/pages/auth_page.py — Login / signup screen.

Rendered before the main app when the user is not authenticated.
Sets st.session_state.token and st.session_state.user_email on success.
"""

import streamlit as st
from ui import client


def render():
    st.markdown("""
    <div style="max-width:400px;margin:60px auto 0;">
        <div style="text-align:center;margin-bottom:28px;">
            <div style="display:inline-flex;align-items:center;gap:10px;">
                <div style="width:40px;height:40px;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                     border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:20px;">⚡</div>
                <span style="font-size:22px;font-weight:700;color:#f1f5f9;">Rag-Assist</span>
            </div>
            <p style="color:#475569;font-size:13px;margin-top:8px;">
                Chat with your documents using AI
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        tab_login, tab_signup = st.tabs(["Login", "Sign up"])

        with tab_login:
            email    = st.text_input("Email", key="login_email",
                                     placeholder="you@example.com")
            password = st.text_input("Password", type="password",
                                     key="login_password")

            if st.button("Login →", use_container_width=True, type="primary"):
                if not email or not password:
                    st.error("Enter email and password.")
                elif not client.is_online():
                    st.error("API offline — run `make api`")
                else:
                    with st.spinner("Logging in …"):
                        try:
                            data = client.login(email, password)
                            st.session_state.token      = data["access_token"]
                            st.session_state.user_email = data["user"]["email"]
                            st.rerun()
                        except Exception:
                            st.error("Invalid email or password.")

        with tab_signup:
            s_email    = st.text_input("Email", key="signup_email",
                                       placeholder="you@example.com")
            s_password = st.text_input("Password (min 6 chars)", type="password",
                                       key="signup_password")

            if st.button("Create account", use_container_width=True, type="primary"):
                if not s_email or not s_password:
                    st.error("Enter email and password.")
                elif len(s_password) < 6:
                    st.error("Password must be at least 6 characters.")
                elif not client.is_online():
                    st.error("API offline — run `make api`")
                else:
                    with st.spinner("Creating account …"):
                        try:
                            client.signup(s_email, s_password)
                            st.success("Account created! Check your email to verify, then log in.")
                        except Exception as e:
                            st.error(f"Signup failed: {e}")
