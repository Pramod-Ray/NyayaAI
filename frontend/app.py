# ============================================
# NyayaAI — Main Streamlit App (Backend Connected)
# Run with: streamlit run frontend/app.py
# ============================================

import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

import streamlit as st
import requests
# import uuid
import os
from ai.config import APP_NAME, validate_config, TOPIC_GROUPS
from frontend.components.sidebar import render_sidebar
from frontend.components.chat import render_chat_history
from dotenv import load_dotenv

load_dotenv()

# BACKEND_URL = "http://127.0.0.1:8000"
BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000"
)


# ── Page Config ───────────────────────────────────────
st.set_page_config(
    page_title=f"{APP_NAME} — Legal Awareness",
    page_icon="⚖️",
    layout="wide"
)

validate_config()

# ── Session State ─────────────────────────────────────
if "session_id" not in st.session_state:
    try:
        res = requests.post(
            f"{BACKEND_URL}/session/new",
            timeout=10
        )
        res.raise_for_status()

        st.session_state.session_id = res.json()["session_id"]

    except requests.exceptions.ConnectionError:
        st.error("❌ Backend is not running.\n\nPlease start FastAPI first.")
        st.stop()

    except requests.exceptions.Timeout:
        st.error("❌ Backend is taking too long to respond.")
        st.stop()

    except Exception as e:
        st.error(f"❌ Failed to connect to backend.\n\n{e}")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "language" not in st.session_state:
    st.session_state.language = "English"  # default

# ── Sidebar ───────────────────────────────────────────
render_sidebar()

# ── Main Header ───────────────────────────────────────
st.title("⚖️ NyayaAI")
st.caption("Your Legal Awareness Assistant")

# ── Language Toggle ───────────────────────────────────
lang_col1, lang_col2 = st.columns([3, 1])
with lang_col2:
    selected_language = st.radio(
        "Reply language",
        options=["English", "Hindi"],
        index=["English", "Hindi"].index(st.session_state.language),
        horizontal=True,
        label_visibility="collapsed",
        key="language_toggle"
    )
    st.session_state.language = selected_language

with lang_col1:
    if st.session_state.get("topic_filter"):
        st.markdown(f"🔒 **Topic Lock:** {st.session_state.get('topic_name', 'All Topics')}")
    else:
        st.markdown("🌐 **Topic Lock:** All Topics")

st.divider()

# ── Welcome Screen — Clickable Topic Cards ────────────
if not st.session_state.messages:
    is_hindi = st.session_state.language == "Hindi"

    st.markdown(
        "👋 **NyayaAI mein aapka swagat hai! Niche diye gaye topic pe click karein:**"
        if is_hindi else
        "👋 **Welcome to NyayaAI! Click a topic below to get started:**"
    )

    card_col1, card_col2, card_col3 = st.columns(3)

    topic_cards = [
        {
            "col": card_col1,
            "icon": "🔐",
            "title": "Cybercrime",
            "group_key": "Cybercrime",
            "points_hi": [
                "Digital arrest scams",
                "Banking fraud aur money mules",
                "Cybercrime kaise report karein",
                "Illegal loan apps",
            ],
            "points_en": [
                "Digital arrest scams",
                "Banking fraud and money mules",
                "How to report cybercrime",
                "Illegal loan apps",
            ],
        },
        {
            "col": card_col2,
            "icon": "🚗",
            "title": "Traffic & Motor Vehicle",
            "group_key": "Traffic & Motor Vehicle",
            "points_hi": [
                "Helmet, seat belt fines",
                "Drunk driving penalties",
                "Driving licence rules",
                "Hit and run compensation",
            ],
            "points_en": [
                "Helmet, seat belt fines",
                "Drunk driving penalties",
                "Driving licence rules",
                "Hit and run compensation",
            ],
        },
        {
            "col": card_col3,
            "icon": "⚖️",
            "title": "Criminal Law (BNS & IT Act)",
            "group_key": "Criminal Law (BNS & IT Act)",
            "points_hi": [
                "Murder, hurt aur assault",
                "Mahilaon ke khilaf apraadh",
                "Theft, robbery, cheating, forgery",
                "Cyber law aur IT Act",
            ],
            "points_en": [
                "Murder, hurt and assault",
                "Crimes against women",
                "Theft, robbery, cheating, forgery",
                "Cyber law and IT Act",
            ],
        },
    ]

    for card in topic_cards:
        with card["col"]:
            with st.container(border=True):
                st.markdown(f"### {card['icon']} {card['title']}")
                points = card["points_hi"] if is_hindi else card["points_en"]
                for p in points:
                    st.caption(f"• {p}")

                button_label = (
                    "Ye topic chuno 👉" if is_hindi else "Select this topic 👉"
                )
                if st.button(
                    button_label,
                    key=f"welcome_card_{card['group_key']}",
                    use_container_width=True,
                ):
                    st.session_state.topic_filter = TOPIC_GROUPS[card["group_key"]]
                    st.session_state.topic_name = card["group_key"]
                    st.rerun()

    st.caption(
        "💡 Ya seedha neeche kuch bhi pooch sakte hain — sabhi topics ke liye."
        if is_hindi else
        "💡 Or simply ask anything below — covering all topics."
    )



# ── Chat History Display ──────────────────────────────
render_chat_history(st.session_state.messages)

# ── Chat Input (with attach / + button) ───────────────
placeholder_text = (
    "Cybercrime, traffic laws, ya criminal law ke baare mein poochiye... (📎 document/photo bhi attach kar sakte hain)"
    if st.session_state.language == "Hindi"
    else "Ask me about cybercrime, traffic laws, or criminal law... (📎 you can also attach a document/photo)"
)

chat_value = st.chat_input(
    placeholder_text,
    accept_file=True,
    file_type=["png", "jpg", "jpeg", "webp", "pdf"],
)

user_question = None
uploaded_file = None

if chat_value:
    user_question = chat_value.text
    if chat_value.files:
        uploaded_file = chat_value.files[0]  # ek baar mein ek file

if uploaded_file is not None:
    # ── User ne document/photo attach kiya hai ────────
    file_bytes = uploaded_file.getvalue()
    is_image_file = uploaded_file.type.startswith("image/")

    # User message display (attachment preview ke saath)
    with st.chat_message("user"):
        if is_image_file:
            st.image(file_bytes, caption=uploaded_file.name, width=250)
        else:
            st.markdown(f"📎 **{uploaded_file.name}**")
        if user_question:
            st.markdown(user_question)

    st.session_state.messages.append({
        "role": "user",
        "content": user_question if user_question else f"[Uploaded: {uploaded_file.name}]",
        "attachment_name": uploaded_file.name,
        "file_bytes": file_bytes,
        "is_image": is_image_file,
    })

    # Backend ko file bhejo
    with st.chat_message("assistant"):
        spinner_text = (
            "दस्तावेज़ का विश्लेषण किया जा रहा है..."
            if st.session_state.language == "Hindi"
            else "Analyzing your document..."
        )
        
        with st.spinner(spinner_text):
            try:
                files = {
                    "file": (uploaded_file.name, file_bytes, uploaded_file.type)
                }
                data = {
                    "session_id": st.session_state.session_id,
                    "message": user_question or "",
                    "language": st.session_state.language,
                }
                res = requests.post(
                    f"{BACKEND_URL}/chat/upload",
                    files=files,
                    data=data,
                    timeout=180,
                )
                res.raise_for_status()
                ai_response = res.json()["response"]

            except requests.exceptions.Timeout:
                ai_response = "❌ Request timed out — document analysis mein zyada time lag raha hai."

            except requests.exceptions.ConnectionError:
                ai_response = "❌ Backend se connect nahi ho paya."

            except requests.exceptions.HTTPError as e:
                try:
                    detail = e.response.json().get("detail", e.response.text)
                except Exception:
                    detail = e.response.text
                ai_response = f"❌ {detail}"

            except Exception as e:
                ai_response = f"❌ Error: {e}"

        st.markdown(ai_response)

    st.session_state.messages.append({"role": "assistant", "content": ai_response})

elif user_question:
    # User message display
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    # Backend se response lo
    with st.chat_message("assistant"):
        spinner_text = (
            "आपका प्रश्न विश्लेषित किया जा रहा है..."
            if st.session_state.language == "Hindi"
            else "Analyzing your query..."
        )
        
        with st.spinner(spinner_text):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/chat",
                    json={
                        "session_id": st.session_state.session_id,
                        "message": user_question,
                        "language": st.session_state.language,
                        "topic_filter": st.session_state.get("topic_filter"),
                        "topic_name": st.session_state.get("topic_name")
                    },
                    timeout=120
                )
                
                res.raise_for_status()
                ai_response = res.json()["response"]

            except requests.exceptions.Timeout:
                ai_response = "❌ Request timed out."

            except requests.exceptions.ConnectionError:
                ai_response = "❌ Backend se connect nahi ho paya."

            except requests.exceptions.HTTPError as e:
                try:
                    detail = e.response.json().get("detail", "Server Error")
                except Exception:
                    detail = "Server Error"

                ai_response = f"❌ {detail}"

            except Exception as e:
                ai_response = f"❌ Error: {e}"

        st.markdown(ai_response)

    # Session state update
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
    
    
    
    
    


# streamlit run frontend/app.py