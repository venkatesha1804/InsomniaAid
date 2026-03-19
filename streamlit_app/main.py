import streamlit as st
import os
import tempfile
import time
from config import (
    APP_NAME, APP_ICON, COLORS, SEVERITY_COLORS, SEVERITY_BG,
    UPLOADS_DIR, CHATBOT_KNOWLEDGE
)
from utils.ml_pipeline import extract_features_from_edf, normalize_features, predict_severity
from utils.database import register_user, login_user, validate_email, user_exists, username_exists, init_db
from utils.recommendations import get_recommendations
from utils.pdf_generator import generate_pdf_report
import plotly.graph_objects as go

st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

init_db()

defaults = {
    'logged_in': False,
    'username': "",
    'page': "home",
    'show_solutions': False,
    'analysis_data': None,
    'chat_history': [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

C = COLORS

# ═══════════════════════════════════════════════════════════════
# GLOBAL CSS
# ═══════════════════════════════════════════════════════════════
GLOBAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, .main, [data-testid="stAppViewContainer"],
[data-testid="stDefaultLayout"] {{
    background: {C['bg']} !important;
    color: {C['text_main']} !important;
    font-family: 'Inter', -apple-system, system-ui, sans-serif;
}}

.block-container {{
    padding: 2rem !important;
    max-width: 1150px !important;
    margin: 0 auto !important;
    border: 3px solid {C['primary']} !important;
    border-radius: 24px !important;
    background: {C['card']} !important;
    box-shadow: 0 20px 60px rgba(16, 185, 129, 0.15) !important;
    min-height: calc(100vh - 40px) !important;
    margin-top: 20px !important;
    margin-bottom: 20px !important;
}}

header, footer, #MainMenu, [data-testid="stToolbar"] {{
    visibility: hidden !important;
    height: 0 !important;
}}

h1 {{ 
    color: {C['text_main']} !important; 
    font-size: 2.2rem !important; 
    font-weight: 700 !important; 
    margin: 0 !important; 
    font-family: 'Poppins', sans-serif !important;
}}
h2 {{ 
    color: {C['text_main']} !important; 
    font-size: 1.6rem !important; 
    font-weight: 600 !important; 
    font-family: 'Poppins', sans-serif !important;
}}
h3 {{ 
    color: {C['primary']} !important; 
    font-size: 1.1rem !important; 
    font-weight: 600 !important; 
    font-family: 'Poppins', sans-serif !important;
}}
p, label {{ 
    color: {C['text_body']} !important; 
    font-size: 0.95rem !important; 
    line-height: 1.6 !important;
}}

.stTextInput input {{
    background: {C['input_bg']} !important;
    border: 2px solid {C['border']} !important;
    border-radius: 12px !important;
    color: {C['text_main']} !important;
    padding: 12px 16px !important;
    font-size: 0.9rem !important;
    transition: all 0.3s ease;
    font-family: 'Inter', sans-serif !important;
}}
.stTextInput input:focus {{
    border-color: {C['primary']} !important;
    box-shadow: 0 0 0 4px {C['primary_light']} !important;
    outline: none !important;
}}

.stButton > button {{
    background: {C['primary']} !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important;
}}
.stButton > button:hover {{
    background: {C['primary_dark']} !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3) !important;
}}

.stMetric {{
    background: {C['card']} !important;
    border: 2px solid {C['border']} !important;
    border-radius: 16px !important;
    padding: 20px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    transition: all 0.3s ease;
}}
.stMetric:hover {{
    border-color: {C['primary']} !important;
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.15) !important;
    transform: translateY(-3px);
}}
[data-testid="stMetricValue"] {{
    color: {C['primary']} !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    font-family: 'Poppins', sans-serif !important;
}}
[data-testid="stMetricLabel"] {{
    color: {C['text_muted']} !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600 !important;
}}

.stAlert {{
    border-radius: 12px !important;
    border-left: 4px solid !important;
    padding: 14px 18px !important;
    font-size: 0.9rem !important;
}}

[data-testid="stFileUploader"] {{
    background: linear-gradient(135deg, #c7f0d8, #f0fdf4) !important;
    border: 3px dashed {C['primary']} !important;
    border-radius: 16px !important;
    padding: 28px !important;
    transition: all 0.3s ease !important;
    margin: 0 !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1) !important;
}}

[data-testid="stFileUploader"]:hover {{ 
    border-color: {C['primary_dark']} !important;
    background: linear-gradient(135deg, rgba(26, 188, 156, 0.15), #f0fdf4) !important;
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.2) !important;
    transform: translateY(-2px);
}}

[data-testid="stFileUploader"] section button {{
    background: {C['primary']} !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important;
}}

[data-testid="stFileUploader"] section button:hover {{
    background: {C['primary_dark']} !important;
    box-shadow: 0 6px 18px rgba(16, 185, 129, 0.3) !important;
    transform: translateY(-1px) !important;
}}

.stProgress > div {{ 
    background: {C['border']} !important; 
    border-radius: 99px !important; 
    height: 12px !important;
    overflow: hidden !important;
}}
.stProgress > div > div {{ 
    background: linear-gradient(90deg, {C['primary']}, {C['accent']}) !important; 
    border-radius: 99px !important; 
}}

hr {{ 
    border: none !important; 
    border-top: 2px solid {C['border']} !important; 
    margin: 28px 0 !important; 
    opacity: 0.6;
}}

[data-testid="stDownloadButton"] button {{
    background: {C['success']} !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 14px 28px !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(72, 187, 120, 0.2) !important;
}}
[data-testid="stDownloadButton"] button:hover {{
    background: #38A169 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(72, 187, 120, 0.3) !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 8px;
    background: {C['input_bg']};
    padding: 6px;
    border-radius: 12px;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 8px;
    padding: 12px 24px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    color: {C['text_body']};
}}
.stTabs [aria-selected="true"] {{
    background: {C['primary']} !important;
    color: white !important;
}}

.chat-card {{
    background: {C['card']};
    border: 2px solid {C['border']};
    border-radius: 20px;
    padding: 24px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}}

.msg {{
    margin-bottom: 12px;
    padding: 12px 16px;
    border-radius: 16px;
    font-size: 0.9rem;
    line-height: 1.6;
    max-width: 90%;
    word-break: break-word;
    white-space: pre-wrap;
}}
.msg.bot {{
    background: {C['primary_light']};
    color: {C['text_main']};
    border: 2px solid {C['primary']};
    border-bottom-left-radius: 6px;
}}
.msg.user {{
    background: {C['primary']};
    color: white;
    margin-left: auto;
    border-bottom-right-radius: 6px;
}}

.chips {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 14px;
}}
.chip {{
    background: {C['input_bg']};
    border: 2px solid {C['border']};
    color: {C['text_main']};
    padding: 8px 16px;
    border-radius: 24px;
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}}
.chip:hover {{
    background: {C['primary']};
    color: white;
    border-color: {C['primary']};
    transform: translateY(-2px);
}}

.hero-section {{
    background: linear-gradient(135deg, #c7f0d8, #e0f7f4);
    border: 2px solid {C['border']};
    border-radius: 20px;
    padding: 28px 28px;
    margin-bottom: 20px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
}}

.feature-card {{
    background: linear-gradient(135deg, #f8fdfb, #f0fdf4);
    border: 2px solid {C['border']};
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 12px;
    display: flex;
    gap: 14px;
    align-items: flex-start;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.04);
    transition: all 0.3s ease;
}}
.feature-card:hover {{
    border-color: {C['primary']} !important;
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.15) !important;
    transform: translateY(-3px);
}}
.feature-card .icon {{
    font-size: 1.5rem;
    line-height: 1;
    flex-shrink: 0;
}}
.feature-card .title {{
    color: {C['text_main']};
    font-weight: 600;
    font-size: 0.9rem;
    margin: 0;
}}
.feature-card .desc {{
    color: {C['text_muted']};
    font-size: 0.78rem;
    margin: 3px 0 0 0;
}}

.info-box {{
    background: linear-gradient(135deg, #e6f8f5, #f0fdf4);
    border-left: 4px solid {C['primary']};
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}}
.info-box .title {{
    color: {C['text_main']};
    font-weight: 600;
    font-size: 1rem;
    margin: 0 0 10px 0;
}}
.info-box p {{
    color: {C['text_body']};
    font-size: 0.9rem;
    margin: 0;
    line-height: 1.7;
}}

</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def chatbot_response(user_input: str) -> str:
    query = user_input.strip().lower()
    if not query:
        return "Say something! Try 'help' to see what I know. 😊"

    for key, answer in CHATBOT_KNOWLEDGE.items():
        if key == "help":
            continue
        words = key.split()
        if all(w in query for w in words):
            return answer

    kw_map = {
        "insomnia":  "what is insomnia",
        "cause":     "causes of insomnia",
        "treatment": "treatments for insomnia",
        "hygiene":   "sleep hygiene tips",
        "psg":       "what is psg",
        "help":      "help",
    }
    for kw, mapped in kw_map.items():
        if kw in query:
            return CHATBOT_KNOWLEDGE.get(mapped, "")

    return "I'm not sure about that. Try asking about insomnia, PSG, or how to use InsomniAid! 😊"


def render_top_nav():
    st.markdown(f"""
    <div style="
        display:flex; align-items:center; justify-content:space-between;
        background: linear-gradient(135deg, {C['primary_light']}, {C['card']});
        border: 2px solid {C['border']};
        border-radius: 16px;
        padding: 14px 24px; 
        margin-bottom:24px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    ">
        <div style="font-weight:700; font-size:1.2rem; color:{C['text_main']}; font-family: 'Poppins', sans-serif;">
             <span style="background: linear-gradient(135deg, {C['primary']}, {C['accent']}); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">InsomniAid</span>
        </div>
        <div style="font-size:0.85rem; color:{C['text_body']};">
            👤 <strong style="color:{C['text_main']};">{st.session_state.username}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns([1, 1, 1, 0.7])
    with cols[0]:
        if st.button("🏠 Home", key="nav_home", use_container_width=True):
            st.session_state.page = "home"; st.rerun()
    with cols[1]:
        if st.button("📁 Upload", key="nav_upload", use_container_width=True):
            st.session_state.page = "upload"; st.rerun()
    with cols[2]:
        if st.button("📊 Results", key="nav_results", use_container_width=True):
            st.session_state.page = "results"; st.rerun()
    with cols[3]:
        if st.button("🚪 Logout", key="nav_logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username  = ""
            st.session_state.page      = "login"
            st.session_state.chat_history = []
            st.rerun()


def show_auth_page():
    _, col, _ = st.columns([1, 2.5, 1])
    with col:
        st.markdown(f"""
        <div style="text-align:center; padding:20px 0 16px;">
            <h1 style="font-size:2.8rem; color:{C['text_main']}; margin:0; font-family: 'Poppins', sans-serif;">
                <span style="background: linear-gradient(135deg, {C['primary']}, {C['accent']}); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Insomni</span>Aid
            </h1>
            <p style="color:{C['text_muted']}; font-size:0.92rem; margin-top:8px;">
                AI-Powered Sleep Analysis & Insomnia Detection
            </p>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

        with tab1:
            st.markdown(f"""
            <div style="margin: 12px 0 16px;">
                <div style="font-weight:600; font-size:1.1rem; color:{C['text_main']}; margin-bottom:6px; font-family: 'Poppins', sans-serif;">
                    Welcome Back
                </div>
                <div style="color:{C['text_muted']}; font-size:0.85rem;">
                    Sign in to continue to your account
                </div>
            </div>
            """, unsafe_allow_html=True)

            username = st.text_input("Username", key="login_username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

            if st.button("Login to InsomniAid", key="login_btn", use_container_width=True):
                if not username or not password:
                    st.error("Please fill in both fields.")
                else:
                    success, result = login_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username  = result
                        st.session_state.page      = "home"
                        st.session_state.chat_history = [
                            {"role": "bot", "text": f"👋 Hi {result}! I'm your InsomniAid Assistant. Ask me anything about sleep!"}
                        ]
                        st.rerun()
                    else:
                        st.error(result)

        with tab2:
            st.markdown(f"""
            <div style="margin: 12px 0 16px;">
                <div style="font-weight:600; font-size:1.1rem; color:{C['text_main']}; margin-bottom:6px; font-family: 'Poppins', sans-serif;">
                    Create Account
                </div>
                <div style="color:{C['text_muted']}; font-size:0.85rem;">
                    Join InsomniAid to start analyzing your sleep
                </div>
            </div>
            """, unsafe_allow_html=True)

            username = st.text_input("Username", key="reg_username", placeholder="Choose a username")
            email    = st.text_input("Email",    key="reg_email",    placeholder="you@email.com")
            password = st.text_input("Password", type="password", key="reg_password", placeholder="Min 6 characters")
            confirm  = st.text_input("Confirm Password", type="password", key="reg_confirm", placeholder="Re-enter password")

            if st.button("Create Account", key="register_btn", use_container_width=True):
                if not all([username, email, password, confirm]):
                    st.error("All fields are required.")
                elif username_exists(username):
                    st.error("Username is already taken.")
                elif not validate_email(email):
                    st.error("Invalid email format.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                elif user_exists(email):
                    st.error("Email is already registered.")
                else:
                    success, message = register_user(username, email, password)
                    if success:
                        st.success("Account created successfully! Please switch to Login tab.")
                        time.sleep(1.5)
                    else:
                        st.error(message)


def show_home_page():
    render_top_nav()

    left, right = st.columns([1.6, 1], gap="large")

    with left:
        st.markdown(f"""
        <div class="hero-section">
            <h1 style="color:{C['text_main']}; margin:0; font-size:1.8rem; font-family: 'Poppins', sans-serif;">
                Welcome, <span style="background: linear-gradient(135deg, {C['primary']}, {C['accent']}); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{st.session_state.username.capitalize()}</span> 👋
            </h1>
            <p style="color:{C['text_body']}; margin-top:10px; font-size:0.92rem;">
                Analyze your sleep data and receive personalized insights powered by AI.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="info-box">
            <div class="title">🌙 About Insomnia</div>
            <p>
                Insomnia is a sleep disorder characterized by difficulty falling asleep, staying asleep, or both.
                <strong style="color:{C['primary']};">InsomniAid</strong> uses AI to analyze your PSG data and deliver personalized treatment recommendations.
            </p>
        </div>
        """, unsafe_allow_html=True)

        features = [
            ("🤖", "AI Classification",   "Severity prediction via Random Forest ML"),
            ("📊", "Sleep Metrics",       "Detailed breakdown of sleep stages"),
            ("💡", "Recommendations",     "Personalized treatment & lifestyle tips"),
            ("📄", "PDF Reports",         "Download professional shareable reports"),
        ]
        f_cols = st.columns(2, gap="medium")
        for i, (icon, title, desc) in enumerate(features):
            with f_cols[i % 2]:
                st.markdown(f"""
                <div class="feature-card">
                    <span class="icon">{icon}</span>
                    <div>
                        <div class="title">{title}</div>
                        <div class="desc">{desc}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📁  Upload PSG Files →", use_container_width=True, key="upload_home"):
            st.session_state.page = "upload"
            st.rerun()

    with right:
        st.markdown(f"""
        <div class="chat-card">
            <div style="display:flex; align-items:center; gap:12px; padding-bottom:16px; margin-bottom:18px; border-bottom:2px solid {C['border']};">
                <span style="font-size:1.6rem;">🤖</span>
                <div>
                    <div style="font-weight:600; font-size:1.1rem; color:{C['text_main']}; margin:0; font-family: 'Poppins', sans-serif;">AI Assistant</div>
                    <div style="font-size:0.8rem; color:{C['text_muted']};">Ask me about sleep</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="max-height:280px; overflow-y:auto; margin-bottom:16px; padding-right:10px;">', unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            role = msg["role"]
            text = msg["text"].replace("\n", "<br>")
            st.markdown(f'<div class="msg {role}">{text}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if len(st.session_state.chat_history) == 0:
            chips = ["What is insomnia?", "Sleep tips", "What is PSG?", "How to use?"]
            st.markdown('<div class="chips">', unsafe_allow_html=True)
            chip_cols = st.columns(2)
            for i, chip in enumerate(chips):
                with chip_cols[i % 2]:
                    if st.button(chip, key=f"chip_{i}", use_container_width=True):
                        st.session_state.chat_history.append({"role": "user", "text": chip})
                        reply = chatbot_response(chip)
                        st.session_state.chat_history.append({"role": "bot",  "text": reply})
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        inp, btn = st.columns([5, 1])
        with inp:
            user_msg = st.text_input("Ask…", key="chat_inp", label_visibility="collapsed", placeholder="Type your question…")
        with btn:
            send = st.button("▶", key="chat_send", use_container_width=True)

        if send and user_msg.strip():
            st.session_state.chat_history.append({"role": "user", "text": user_msg.strip()})
            reply = chatbot_response(user_msg.strip())
            st.session_state.chat_history.append({"role": "bot",  "text": reply})
            st.rerun()

        if len(st.session_state.chat_history) > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat"):
                st.session_state.chat_history = []
                st.rerun()


# ═══════════════════════════════════════════════════════════════
# UPLOAD PAGE - COMPACT NO SCROLL
# ═══════════════════════════════════════════════════════════════

def show_upload_page():
    render_top_nav()

    st.markdown(f"""
    <div class="hero-section">
        <h2>📤 Upload PSG Data</h2>
        <p style="font-size:0.9rem; margin:8px 0 0 0;">Upload your Polysomnography files for AI-powered sleep analysis</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(f"""
        <div style="
            background:linear-gradient(135deg, {C['primary_light']}, {C['card']});
            border: 2px solid {C['primary']};
            border-radius:16px;
            padding:20px 24px;
            margin-bottom:12px;
        ">
            <div style="color:{C['primary']}; font-weight:600; font-size:1rem; font-family: 'Poppins', sans-serif; margin-bottom:8px;">🧠 PSG Recording</div>
            <div style="color:{C['text_muted']}; font-size:0.8rem; margin-bottom:12px; font-weight:500;">Polysomnography EDF file</div>
        """, unsafe_allow_html=True)
        psg_file = st.file_uploader("PSG", type=['edf'], label_visibility="collapsed", key="psg_upload")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="
            background:linear-gradient(135deg, #16a08515, {C['card']});
            border: 2px solid #16a085;
            border-radius:16px;
            padding:20px 24px;
            margin-bottom:12px;
        ">
            <div style="color:#16a085; font-weight:600; font-size:1rem; font-family: 'Poppins', sans-serif; margin-bottom:8px;">📈 Hypnogram</div>
            <div style="color:{C['text_muted']}; font-size:0.8rem; margin-bottom:12px; font-weight:500;">Sleep stage annotations EDF file</div>
        """, unsafe_allow_html=True)
        hypno_file = st.file_uploader("Hypnogram", type=['edf'], label_visibility="collapsed", key="hypno_upload")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if psg_file and hypno_file:
        st.success(f"✅ Ready! Both files uploaded")
    elif psg_file or hypno_file:
        st.warning("⏳ Please upload both PSG and Hypnogram files")
    else:
        st.info("📁 Upload both files to get started")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔍  Analyze Sleep Data", use_container_width=True, key="analyze_btn"):
        if not psg_file or not hypno_file:
            st.error("Please upload both PSG and Hypnogram files.")
        else:
            with st.spinner("Analyzing your sleep data…"):
                progress = st.progress(0, text="Saving files…")
                with tempfile.TemporaryDirectory() as tmpdir:
                    psg_path   = os.path.join(tmpdir, "psg.edf")
                    hypno_path = os.path.join(tmpdir, "hypno.edf")
                    with open(psg_path,   'wb') as f: f.write(psg_file.getbuffer())
                    with open(hypno_path, 'wb') as f: f.write(hypno_file.getbuffer())

                    progress.progress(20, text="Extracting features…")
                    features = extract_features_from_edf(psg_path, hypno_path)
                    if features is None:
                        st.error("Failed to extract features.")
                        return

                    progress.progress(45, text="Normalizing data…")
                    normalized = normalize_features(features)
                    if normalized is None:
                        st.error("Normalization failed.")
                        return

                    progress.progress(70, text="Running AI prediction…")
                    severity, probabilities = predict_severity(normalized)
                    if severity is None:
                        st.error("Prediction failed.")
                        return

                    progress.progress(100, text="✅ Done!")
                    time.sleep(0.5)

                    st.session_state.analysis_data = {
                        'severity':     severity,
                        'features':     features,
                        'probabilities': probabilities
                    }
                    st.session_state.show_solutions = False
                    st.session_state.page = "results"
                    st.rerun()


# ═══════════════════════════════════════════════════════════════
# RESULTS PAGE - COMPACT NO SCROLL
# ═══════════════════════════════════════════════════════════════

def show_results_page():
    render_top_nav()

    if not st.session_state.analysis_data:
        st.error("No analysis data available. Please upload files first.")
        if st.button("← Go to Upload", use_container_width=True):
            st.session_state.page = "upload"; st.rerun()
        return

    data     = st.session_state.analysis_data
    severity = data['severity']
    features = data['features']
    probs    = data['probabilities']
    
    sev_color = SEVERITY_COLORS.get(severity, C['danger'])
    icons = {"No Insomnia":"✅", "Mild":"⚠️", "Moderate":"🟠", "Severe":"🔴"}

    # TOP: Severity + Chart
    col1, col2 = st.columns([0.8, 1.5], gap="large")
    
    with col1:
        st.markdown(f"""
        <div style="
            background:linear-gradient(135deg, #c7f0d8, #e0f7f4);
            border: 3px solid {sev_color};
            border-radius:18px;
            padding:28px 24px;
            text-align:center;
        ">
            <div style="font-size:2.2rem; margin-bottom:8px;">{icons.get(severity,'❓')}</div>
            <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1.6px; color:{C['text_muted']}; margin-bottom:8px; font-weight:600;">Severity</div>
            <div style="font-size:1.6rem; font-weight:700; color:{sev_color}; font-family: 'Poppins', sans-serif;">{severity}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("**📊 Prediction Confidence**")
        severity_levels = ['No Insomnia', 'Mild', 'Moderate', 'Severe']
        fig = go.Figure(data=[
            go.Bar(
                x=severity_levels,
                y=probs,
                marker=dict(color=['#48bb78', '#f6ad55', '#ed8936', '#f56565']),
                text=[f'{p*100:.0f}%' for p in probs],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>%{y:.1%}<extra></extra>'
            )
        ])
        fig.update_layout(
            height=280,
            template='plotly_white',
            showlegend=False,
            margin=dict(l=40, r=20, t=20, b=30),
            font=dict(size=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # MIDDLE: Sleep Metrics (2x3)
    st.markdown("**💤 Sleep Metrics**")
    mc1, mc2, mc3 = st.columns(3, gap="small")
    with mc1:
        st.metric("Sleep Efficiency", f"{features['sleep_efficiency_percent']:.0f}%")
        st.metric("Sleep Onset Latency", f"{features['sleep_onset_latency_min']:.0f}m")
    with mc2:
        st.metric("Total Sleep Time", f"{features['total_sleep_time_min']:.0f}m")
        st.metric("Wake After Sleep Onset", f"{features['wake_after_sleep_onset_min']:.0f}m")
    with mc3:
        st.metric("REM Latency", f"{features['rem_latency_min']:.0f}m")
        st.metric("REM Sleep %", f"{features['percent_rem']:.0f}%")

    st.markdown("<hr>", unsafe_allow_html=True)

    # BOTTOM: Sleep Stages Pie
    st.markdown("**🛏️ Sleep Stage Distribution**")
    
    stages = ['Wake', 'N1', 'N2', 'N3', 'REM']
    percentages = [
        features['percent_w'],
        features['percent_n1'],
        features['percent_n2'],
        features['percent_n3'],
        features['percent_rem']
    ]
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=stages,
        values=percentages,
        marker=dict(colors=['#e2e8f0', '#cbd5e0', '#a0aec0', '#718096', '#4a5568']),
        textposition='inside',
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>'
    )])
    fig_pie.update_layout(
        height=300,
        template='plotly_white',
        margin=dict(l=0, r=0, t=20, b=20),
        font=dict(size=11)
    )
    st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)

    # Recommendations
    if not st.session_state.show_solutions:
        if st.button("💡  View Personalized Recommendations", use_container_width=True, key="solutions_btn"):
            st.session_state.show_solutions = True
            st.rerun()
    else:
        recs = get_recommendations(severity)

        st.markdown(f"""
        <div class="info-box">
            <div class="title">{recs['title']}</div>
            <p>{recs['message']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**📋 Recommended Actions**")
        for i, tip in enumerate(recs['tips'][:3], 1):
            st.markdown(f"<div style='font-size:0.85rem; margin-bottom:6px;'><strong>{i}.</strong> {tip}</div>", unsafe_allow_html=True)
        
        st.markdown(f"<div style='font-size:0.8rem; color:{C['text_muted']}; margin-top:10px;'>⏱️ Expected Duration: {recs['duration']}</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📄  Generate & Download PDF Report", use_container_width=True, key="download_btn"):
            with st.spinner("Generating report…"):
                pdf_path = os.path.join(UPLOADS_DIR, f"report_{st.session_state.username}.pdf")
                ok = generate_pdf_report(pdf_path, st.session_state.username, severity, features, recs)
                if ok:
                    with open(pdf_path, 'rb') as f:
                        st.download_button(
                            label="⬇️  Download PDF Report",
                            data=f.read(),
                            file_name=f"InsomniAid_Report_{st.session_state.username}.pdf",
                            mime="application/pdf",
                            key="dl_pdf"
                        )
                    st.success("Report generated successfully!")
                else:
                    st.error("Failed to generate PDF.")


# ═══════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════

if not st.session_state.logged_in:
    show_auth_page()
else:
    if st.session_state.page == "home":
        show_home_page()
    elif st.session_state.page == "upload":
        show_upload_page()
    elif st.session_state.page == "results":
        show_results_page()
    else:
        show_home_page()