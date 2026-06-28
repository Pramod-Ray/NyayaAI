# ============================================
# NyayaAI — Chat Component
# Handles chat message display
# Shows question, answer, source, category
# ============================================

import streamlit as st


def render_chat_history(messages):
    # loop through all messages and display them
    # messages = list of dicts with role and content
    for message in messages:
        if message["role"] == "user":
            # display user message on right side
            with st.chat_message("user"):
                if message.get("attachment_name"):
                    st.markdown(f"📎 *{message['attachment_name']}*")
                st.markdown(message["content"])

        elif message["role"] == "assistant":
            # display assistant message on left side
            with st.chat_message("assistant"):
                st.markdown(message["content"])

                # show source and category if available
                if message.get("source"):
                    st.divider()
                    col1, col2 = st.columns(2)

                    with col1:
                        # source of the answer
                        st.caption(
                            f"📁 **Source:** {message['source']}"
                        )
                    with col2:
                        # category of the answer
                        st.caption(
                            f"🏷️ **Category:** {message['category']}"
                        )


def render_answer(result):
    # formats and returns assistant message dict
    # result = dict from generator.py
    return {
        "role"    : "assistant",
        "content" : result["answer"],
        "source"  : result.get("source"),
        "category": result.get("category")
    }
