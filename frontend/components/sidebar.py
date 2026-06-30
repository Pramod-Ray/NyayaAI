# ============================================
# NyayaAI — Sidebar Component
# ============================================

import streamlit as st
import requests
from ai.config import APP_NAME, APP_VERSION, CATEGORIES, TOPIC_GROUPS

BACKEND_URL = "http://127.0.0.1:8000"


def render_sidebar():
    with st.sidebar:
        # App name
        st.title(f"⚖️ {APP_NAME}")
        st.caption(f"Version {APP_VERSION}")
        st.divider()

        # New Chat button
        if st.button("➕ New Chat", use_container_width=True):
            res = requests.post(f"{BACKEND_URL}/session/new")
            st.session_state.session_id = res.json()["session_id"]
            st.session_state.messages = []
            st.rerun()

        st.divider()

        # ── Topic Lock ──────────────────────────────────
        # jab koi topic select ho, chat sirf usi topic ki
        # categories se jawab dega (session_state.topic_filter)
        st.subheader("🎯 Topic Lock")

        if "topic_filter" not in st.session_state:
            st.session_state.topic_filter = None
            st.session_state.topic_name = "All Topics"

        is_all = st.session_state.topic_filter is None
        if st.button(
            f"{'🟢 ' if is_all else ''}🌐 All Topics",
            use_container_width=True
        ):
            st.session_state.topic_filter = None
            st.session_state.topic_name = "All Topics"
            st.rerun()

        topic_icons = {
            "Cybercrime": "🔐",
            "Traffic & Motor Vehicle": "🚗",
            "Criminal Law (BNS & IT Act)": "⚖️",
        }

        for topic_name, categories in TOPIC_GROUPS.items():
            is_active = st.session_state.topic_name == topic_name
            icon = topic_icons.get(topic_name, "•")
            label = f"{'🟢 ' if is_active else ''}{icon} {topic_name}"
            if st.button(label, use_container_width=True, key=f"topic_{topic_name}"):
                st.session_state.topic_filter = categories
                st.session_state.topic_name = topic_name
                st.rerun()

        if st.session_state.topic_filter:
            st.caption(f"🔒 Locked to: **{st.session_state.topic_name}**")

        st.divider()

        # Purani Sessions
        st.subheader("🕘 Recent Chats")
        try:
            res = requests.get(f"{BACKEND_URL}/sessions")
            sessions = res.json()
            
            

            for session in sessions:
                col1, col2 = st.columns([4, 1])

                with col1:
                    # Current session highlight karo
                    is_active = session["session_id"] == st.session_state.get("session_id", "")
                    label = f"{'🟢 ' if is_active else ''}{session['title'][:30]}"

                    if st.button(label, key=session["session_id"], use_container_width=True):
                        # Session load karo
                        st.session_state.session_id = session["session_id"]

                        # History fetch karo
                        hist_res = requests.get(
                            f"{BACKEND_URL}/session/{session['session_id']}/history"
                        )
                        if hist_res.status_code == 200:
                            history = hist_res.json()
                            st.session_state.messages = [
                                {
                                    "role": h["role"],
                                    "content": h["message"],
                                    "attachment_name": h.get("attachment_name"),
                                }
                                for h in history
                            ]
                        st.rerun()

                with col2:
                    if st.button("🗑️", key=f"del_{session['session_id']}"):
                        requests.delete(
                            f"{BACKEND_URL}/session/{session['session_id']}"
                        )
                        # Agar current session delete ki to reset karo
                        if session["session_id"] == st.session_state.get("session_id", ""):
                            res = requests.post(f"{BACKEND_URL}/session/new")
                            st.session_state.session_id = res.json()["session_id"]
                            st.session_state.messages = []
                        st.rerun()

        except Exception as e:
            st.error(f"Sessions load nahi hui: {e}")

        st.divider()

        # About
        st.subheader("📌 About")
        # st.info(
        #     "NyayaAI is a cybercrime awareness "
        #     "chatbot powered by RAG technology."
        # )
        st.info(
            "NyayaAI is a legal awareness chatbot "
            "powered by RAG technology covering "
            "Cybercrime, Traffic Laws, and Criminal Law "
            "(BNS & IT Act)."
        )
        st.divider()

        # Emergency contacts
        st.subheader("🆘 Emergency Contacts")
        st.error("📞 Cybercrime Helpline: **1930**")
        st.warning("🚗 Traffic Helpline: **1073**")
        st.info("⚖️ Free Legal Aid (NALSA): **15100**")
        st.markdown(
            "🌐 [cybercrime.gov.in](https://www.cybercrime.gov.in)"
        )
        st.markdown("🌐 [parivahan.gov.in](https://parivahan.gov.in)")
        st.markdown("🌐 [nalsa.gov.in](https://nalsa.gov.in)")
        st.divider()

        # Topics
        st.subheader("🏷️ Topics Covered")
        for category in CATEGORIES:
            st.markdown(f"• {category}")