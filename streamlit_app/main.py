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
    initial_sidebar_state="expanded"
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
# GLOBAL CSS — Clinical / Healthcare Design System
# ═══════════════════════════════════════════════════════════════
GLOBAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, .main, [data-testid="stAppViewContainer"],
[data-testid="stDefaultLayout"] {{
    background: {C['bg']} !important;
    color: {C['text_main']} !important;
    font-family: 'Inter', -apple-system, system-ui, sans-serif;
}}

.block-container {{
    padding: 2.2rem 2.6rem !important;
    max-width: 1180px !important;
}}

header, #MainMenu, [data-testid="stToolbar"] {{
    visibility: hidden !important;
    height: 0 !important;
}}
footer {{ visibility: hidden !important; }}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: {C['primary']} !important;
    border-right: none !important;
}}
[data-testid="stSidebar"] * {{ color: #DCE4F2 !important; }}
[data-testid="stSidebar"] .stButton > button {{
    background: transparent !important;
    color: #DCE4F2 !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    box-shadow: none !important;
    text-align: left !important;
    justify-content: flex-start !important;
    font-weight: 500 !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(255,255,255,0.08) !important;
    border-color: rgba(255,255,255,0.28) !important;
    transform: none !important;
}}
[data-testid="stSidebar"] .stButton > button p {{ color: #DCE4F2 !important; }}

/* ── Typography ── */
h1 {{ color: {C['text_main']} !important; font-size: 1.9rem !important; font-weight: 700 !important; margin: 0 !important; font-family: 'Poppins', sans-serif !important; letter-spacing: -0.01em; }}
h2 {{ color: {C['text_main']} !important; font-size: 1.3rem !important; font-weight: 600 !important; font-family: 'Poppins', sans-serif !important; }}
h3 {{ color: {C['primary']} !important; font-size: 1rem !important; font-weight: 600 !important; font-family: 'Poppins', sans-serif !important; }}
p, label {{ color: {C['text_body']} !important; font-size: 0.92rem !important; line-height: 1.6 !important; }}

/* ── Inputs ── */
.stTextInput input {{
    background: {C['input_bg']} !important;
    border: 1.5px solid {C['border']} !important;
    border-radius: 10px !important;
    color: {C['text_main']} !important;
    padding: 12px 16px !important;
    font-size: 0.9rem !important;
    transition: all 0.15s ease;
}}
.stTextInput input:focus {{
    border-color: {C['accent']} !important;
    box-shadow: 0 0 0 3px rgba(14, 165, 160, 0.14) !important;
    outline: none !important;
}}

/* ── Buttons (main area) ── */
.main .stButton > button, .block-container .stButton > button {{
    background: {C['primary']} !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 22px !important;
    font-weight: 600 !important;
    font-size: 0.87rem !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 2px rgba(22, 35, 63, 0.12) !important;
}}
.main .stButton > button:hover {{
    background: {C['primary_dark']} !important;
    box-shadow: 0 6px 16px rgba(22, 35, 63, 0.2) !important;
}}

/* ── Metrics ── */
.stMetric {{
    background: {C['card']} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 14px !important;
    padding: 16px 18px !important;
    box-shadow: 0 1px 3px rgba(22, 35, 63, 0.04) !important;
}}
[data-testid="stMetricValue"] {{ color: {C['primary']} !important; font-size: 1.5rem !important; font-weight: 700 !important; font-family: 'Poppins', sans-serif !important; }}
[data-testid="stMetricLabel"] {{ color: {C['text_muted']} !important; font-size: 0.72rem !important; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600 !important; }}

.stAlert {{ border-radius: 10px !important; border-left: 4px solid !important; padding: 12px 16px !important; font-size: 0.87rem !important; }}

/* ── File uploader ── */
[data-testid="stFileUploader"] {{
    background: {C['input_bg']} !important;
    border: 1.5px dashed {C['secondary']} !important;
    border-radius: 12px !important;
    padding: 18px !important;
}}
[data-testid="stFileUploader"]:hover {{ border-color: {C['accent']} !important; }}
[data-testid="stFileUploader"] section button {{
    background: {C['primary']} !important; color: white !important; border: none !important;
    border-radius: 8px !important; padding: 8px 20px !important; font-weight: 600 !important; font-size: 0.8rem !important;
}}
[data-testid="stFileUploader"] section button:hover {{ background: {C['primary_dark']} !important; }}

.stProgress > div {{ background: {C['border']} !important; border-radius: 99px !important; height: 8px !important; }}
.stProgress > div > div {{ background: linear-gradient(90deg, {C['primary']}, {C['accent']}) !important; border-radius: 99px !important; }}

hr {{ border: none !important; border-top: 1px solid {C['border']} !important; margin: 22px 0 !important; }}

[data-testid="stDownloadButton"] button {{
    background: {C['accent']} !important; color: white !important; border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; padding: 13px 26px !important; box-shadow: 0 1px 3px rgba(14,165,160,0.2) !important;
}}
[data-testid="stDownloadButton"] button:hover {{ background: {C['accent_dark']} !important; }}

.stTabs [data-baseweb="tab-list"] {{ gap: 4px; background: {C['input_bg']}; padding: 4px; border-radius: 10px; }}
.stTabs [data-baseweb="tab"] {{ border-radius: 7px; padding: 10px 20px; font-weight: 600; color: {C['text_body']}; }}
.stTabs [aria-selected="true"] {{ background: {C['primary']} !important; color: white !important; }}
.stTabs [aria-selected="true"] p {{ color: white !important; }}

/* ── Reusable components ── */
.top-strip {{
    display:flex; align-items:center; justify-content:space-between;
    margin-bottom: 22px; padding-bottom: 16px; border-bottom: 1px solid {C['border']};
}}
.brand {{ display:flex; align-items:center; gap:10px; }}
.brand .mark {{
    width:38px; height:38px; border-radius:10px;
    background: linear-gradient(135deg, {C['primary']}, {C['primary_mid']});
    display:flex; align-items:center; justify-content:center; font-size:1.1rem;
}}
.brand .name {{ font-weight:700; font-size:1.15rem; color:{C['text_main']}; font-family:'Poppins',sans-serif; }}
.brand .name span {{ color:{C['accent']}; }}
.user-chip {{
    display:flex; align-items:center; gap:8px; background:{C['primary_light']};
    padding:7px 14px; border-radius:20px; font-size:0.82rem; color:{C['text_main']}; font-weight:600;
}}

.chat-card {{ background: {C['card']}; border: 1px solid {C['border']}; border-radius: 16px; padding: 20px; box-shadow: 0 2px 10px rgba(22,35,63,0.05); }}
.msg {{ margin-bottom: 10px; padding: 10px 14px; border-radius: 14px; font-size: 0.86rem; line-height: 1.5; max-width: 90%; word-break: break-word; white-space: pre-wrap; }}
.msg.bot {{ background: {C['primary_light']}; color: {C['text_main']}; border-bottom-left-radius: 4px; }}
.msg.user {{ background: {C['primary']}; color: white; margin-left: auto; border-bottom-right-radius: 4px; }}
.chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }}

.hero {{
    position:relative; overflow:hidden;
    background: linear-gradient(120deg, {C['primary']} 0%, {C['primary_mid']} 100%);
    border-radius: 20px; padding: 40px 38px; margin-bottom: 22px;
}}
.hero::after {{
    content:""; position:absolute; right:-60px; top:-60px; width:240px; height:240px;
    background: radial-gradient(circle, rgba(14,165,160,0.35), transparent 70%);
    border-radius:50%;
}}
.hero-tag {{ display:inline-block; background: rgba(255,255,255,0.14); color:#DCE4F2; font-size:0.7rem; font-weight:700; letter-spacing:0.8px; text-transform:uppercase; padding:6px 14px; border-radius:20px; margin-bottom:14px; }}
.hero h1 {{ color:#FFFFFF !important; font-size:2.1rem !important; }}
.hero p {{ color:#C9D6EA !important; margin-top:10px; font-size:0.95rem !important; max-width:520px; position:relative; z-index:1; }}

.card {{ background: {C['card']}; border: 1px solid {C['border']}; border-radius: 16px; padding: 20px; margin-bottom: 14px; }}

.feature-card {{ background: {C['card']}; border: 1px solid {C['border']}; border-radius: 14px; padding: 16px; margin-bottom: 12px; height:100%; transition: all 0.15s ease; }}
.feature-card:hover {{ border-color: {C['accent']}; box-shadow: 0 6px 16px rgba(14,165,160,0.1); }}
.feature-card .icon {{ font-size:1.2rem; background:{C['primary_light']}; width:36px; height:36px; border-radius:9px; display:flex; align-items:center; justify-content:center; margin-bottom:10px; }}
.feature-card .title {{ color: {C['text_main']}; font-weight: 600; font-size: 0.88rem; margin: 0; }}
.feature-card .desc {{ color: {C['text_muted']}; font-size: 0.78rem; margin: 4px 0 0 0; }}

.info-box {{ background: {C['primary_light']}; border-left: 4px solid {C['primary']}; border-radius: 12px; padding: 18px 20px; margin-bottom: 16px; }}
.info-box .title {{ color: {C['text_main']}; font-weight: 600; font-size: 0.95rem; margin: 0 0 8px 0; }}
.info-box p {{ color: {C['text_body']} !important; font-size: 0.87rem; margin: 0; line-height: 1.6; }}

.disclaimer {{ background: {C['warning_bg']}; border-left: 4px solid {C['warning']}; border-radius: 10px; padding: 13px 16px; font-size: 0.79rem; color: {C['text_body']}; margin-top: 14px; }}

.step-track {{ display:flex; gap:10px; }}
.step-track .step {{ flex:1; text-align:center; border-radius:10px; padding:9px 6px; font-size:0.72rem; font-weight:700; letter-spacing:0.2px; }}

.rec-item {{ display:flex; gap:10px; align-items:flex-start; background:{C['card']}; border:1px solid {C['border']}; border-radius:10px; padding:11px 14px; margin-bottom:8px; }}
.rec-item .check {{ color:{C['success']}; font-weight:800; flex-shrink:0; }}
.rec-item .text {{ font-size:0.85rem; color:{C['text_body']}; }}

.severity-card {{ background: {C['card']}; border: 2px solid var(--sev-color); border-radius: 18px; padding: 30px 24px; text-align: center; height: 100%; }}

.auth-wrap {{ display:flex; min-height:78vh; border-radius:20px; overflow:hidden; box-shadow:0 10px 40px rgba(22,35,63,0.12); }}
.auth-left {{
    flex:1; background: linear-gradient(150deg, {C['primary']}, {C['primary_mid']});
    padding:52px 44px; display:flex; flex-direction:column; justify-content:center; position:relative; overflow:hidden;
}}
.auth-left::after {{ content:""; position:absolute; left:-70px; bottom:-70px; width:220px; height:220px; background:radial-gradient(circle, rgba(14,165,160,0.3), transparent 70%); border-radius:50%; }}
.auth-left h1 {{ color:#fff !important; font-size:2.2rem !important; position:relative; z-index:1; }}
.auth-left p {{ color:#C9D6EA !important; margin-top:14px; font-size:0.95rem !important; position:relative; z-index:1; max-width: 380px; }}
.auth-badge {{ display:inline-flex; align-items:center; gap:8px; background:rgba(255,255,255,0.1); color:#DCE4F2; padding:8px 16px; border-radius:20px; font-size:0.78rem; font-weight:600; margin-top: 26px; width:fit-content; position:relative; z-index:1; }}
.auth-right {{ flex:1; background:{C['card']}; padding:52px 48px; display:flex; flex-direction:column; justify-content:center; }}
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


def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px; padding:6px 0 20px;">
            <div style="width:36px; height:36px; border-radius:9px; background:rgba(255,255,255,0.1); display:flex; align-items:center; justify-content:center; font-size:1.1rem;">🌙</div>
            <div style="font-weight:700; font-size:1.05rem; font-family:'Poppins',sans-serif; color:#fff !important;">InsomniAid</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.06); border-radius:12px; padding:12px 14px; margin-bottom:18px; display:flex; align-items:center; gap:10px;">
            <span style="font-size:1.1rem;">👤</span>
            <div>
                <div style="font-size:0.68rem; color:#9BAAC7 !important; text-transform:uppercase; letter-spacing:0.5px;">Signed in as</div>
                <div style="font-weight:600; font-size:0.88rem; color:#fff !important;">{st.session_state.username}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="font-size:0.68rem; color:#9BAAC7 !important; text-transform:uppercase; letter-spacing:0.8px; margin-bottom:8px; font-weight:700;">Navigate</div>', unsafe_allow_html=True)

        nav_items = [("🏠", "Home", "home"), ("📁", "Analyze Sleep", "upload"), ("📊", "Results", "results")]
        for icon, label, key in nav_items:
            if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()

        st.markdown("<div style='margin-top:30px;'></div>", unsafe_allow_html=True)
        if st.button("🚪  Logout", key="nav_logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username  = ""
            st.session_state.page      = "login"
            st.session_state.chat_history = []
            st.rerun()

        st.markdown(f"""
        <div style="position:fixed; bottom:20px; font-size:0.68rem; color:#7C8CAA !important; line-height:1.5;">
            AI-assisted analysis only.<br>Not a substitute for medical care.
        </div>
        """, unsafe_allow_html=True)


def show_auth_page():
    left, right = st.columns([1, 1], gap="small")

    with left:
        st.markdown(f"""
        <div class="auth-left" style="border-radius:20px 0 0 20px;">
            <div style="font-size:2rem;">🌙</div>
            <h1 style="margin-top:14px;">Insomni<span style="color:#5EE8DE;">Aid</span></h1>
            <p>AI-powered sleep analysis. Upload your PSG data and get intelligent, evidence-based insights into your sleep health.</p>
            <div class="auth-badge">✨ &nbsp;AI-assisted sleep analytics</div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown('<div class="auth-right" style="border-radius:0 20px 20px 0; border:1px solid ' + C['border'] + '; border-left:none;">', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            st.markdown(f"""
            <div style="margin: 6px 0 18px;">
                <div style="font-weight:700; font-size:1.2rem; color:{C['text_main']}; font-family:'Poppins',sans-serif;">Welcome back</div>
                <div style="color:{C['text_muted']}; font-size:0.85rem; margin-top:2px;">Sign in to continue to your dashboard</div>
            </div>
            """, unsafe_allow_html=True)

            username = st.text_input("Username", key="login_username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

            if st.button("Sign In", key="login_btn", use_container_width=True):
                if not username or not password:
                    st.error("Please fill in both fields.")
                else:
                    success, result = login_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username  = result
                        st.session_state.page      = "home"
                        st.session_state.chat_history = [
                            {"role": "bot", "text": f"👋 Hi {result}! I'm NidraBot, your sleep information assistant. Ask me anything about sleep!"}
                        ]
                        st.rerun()
                    else:
                        st.error(result)

        with tab2:
            st.markdown(f"""
            <div style="margin: 6px 0 18px;">
                <div style="font-weight:700; font-size:1.2rem; color:{C['text_main']}; font-family:'Poppins',sans-serif;">Create your account</div>
                <div style="color:{C['text_muted']}; font-size:0.85rem; margin-top:2px;">Join InsomniAid to start analyzing your sleep</div>
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
                        st.success("Account created successfully! Please switch to the Login tab.")
                        time.sleep(1.5)
                    else:
                        st.error(message)

        st.markdown('</div>', unsafe_allow_html=True)


def show_home_page():
    render_sidebar()

    st.markdown(f"""
    <div class="hero">
        <div class="hero-tag">AI-Powered Sleep Analysis</div>
        <h1>Welcome back, {st.session_state.username.capitalize()} 👋</h1>
        <p>Analyze polysomnographic sleep data and receive intelligent, personalized insights into your sleep health — in minutes.</p>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.6, 1], gap="large")

    with left:
        st.markdown(f"""
        <div class="info-box">
            <div class="title">🌙 About Insomnia</div>
            <p>Insomnia is a sleep disorder characterized by difficulty falling asleep, staying asleep, or both.
            <strong style="color:{C['primary']};">InsomniAid</strong> uses AI-assisted analysis of your PSG data to help you understand your sleep patterns.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Features**")
        features = [
            ("🧠", "AI Severity Prediction", "Insomnia severity via Random Forest classification"),
            ("📊", "Sleep Stage Analysis",   "Detailed breakdown of sleep-stage distribution"),
            ("💡", "Recommendations",        "Personalized, evidence-based sleep guidance"),
            ("📄", "PDF Report",             "Download a professional, shareable report"),
        ]
        f_cols = st.columns(2, gap="medium")
        for i, (icon, title, desc) in enumerate(features):
            with f_cols[i % 2]:
                st.markdown(f"""
                <div class="feature-card">
                    <div class="icon">{icon}</div>
                    <div class="title">{title}</div>
                    <div class="desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        st.markdown("**How it works**")
        steps = [("01", "Upload PSG Data"), ("02", "Extract Features"), ("03", "AI Analysis"), ("04", "View Report")]
        s_cols = st.columns(4, gap="small")
        for col, (num, label) in zip(s_cols, steps):
            with col:
                st.markdown(f"""
                <div class="card" style="text-align:center; padding:14px 8px;">
                    <div style="color:{C['accent']}; font-weight:700; font-family:'Poppins',sans-serif; font-size:1rem;">{num}</div>
                    <div style="font-size:0.74rem; font-weight:600; color:{C['text_main']}; margin-top:2px;">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        if st.button("📁  Analyze Your Sleep →", use_container_width=True, key="upload_home"):
            st.session_state.page = "upload"
            st.rerun()

        st.markdown("""
        <div class="disclaimer">⚠️ This tool is intended for informational/research purposes and does not replace evaluation by a qualified healthcare professional.</div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown(f"""
        <div class="chat-card">
            <div style="display:flex; align-items:center; gap:12px; padding-bottom:14px; margin-bottom:14px; border-bottom:1px solid {C['border']};">
                <span style="font-size:1.4rem;">🌙</span>
                <div>
                    <div style="font-weight:700; font-size:1rem; color:{C['text_main']}; font-family:'Poppins',sans-serif;">NidraBot</div>
                    <div style="font-size:0.76rem; color:{C['text_muted']};">Your sleep information assistant</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="max-height:280px; overflow-y:auto; margin-bottom:12px; padding-right:8px;">', unsafe_allow_html=True)
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
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat"):
                st.session_state.chat_history = []
                st.rerun()


# ═══════════════════════════════════════════════════════════════
# UPLOAD PAGE
# ═══════════════════════════════════════════════════════════════

def show_upload_page():
    render_sidebar()

    st.markdown(f"""
    <div class="hero" style="padding:32px 36px;">
        <div class="hero-tag">Clinical Data Upload</div>
        <h1 style="font-size:1.7rem;">Analyze Your Sleep</h1>
        <p>Upload your PSG and Hypnogram (.edf) files to run AI-assisted sleep analysis.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(f"""
        <div class="card" style="border-top:3px solid {C['primary']};">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
                <span style="font-size:1.2rem;">🧠</span>
                <div style="color:{C['primary']}; font-weight:700; font-size:0.95rem; font-family:'Poppins',sans-serif;">PSG Recording</div>
            </div>
            <div style="color:{C['text_muted']}; font-size:0.78rem; margin-bottom:12px;">Polysomnography EDF file</div>
        """, unsafe_allow_html=True)
        psg_file = st.file_uploader("PSG", type=['edf'], label_visibility="collapsed", key="psg_upload")
        if psg_file:
            st.markdown(f"<div style='font-size:0.78rem; color:{C['success']}; margin-top:8px;'>✅ {psg_file.name}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="card" style="border-top:3px solid {C['accent']};">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
                <span style="font-size:1.2rem;">📈</span>
                <div style="color:{C['accent']}; font-weight:700; font-size:0.95rem; font-family:'Poppins',sans-serif;">Hypnogram</div>
            </div>
            <div style="color:{C['text_muted']}; font-size:0.78rem; margin-bottom:12px;">Sleep stage annotations EDF file</div>
        """, unsafe_allow_html=True)
        hypno_file = st.file_uploader("Hypnogram", type=['edf'], label_visibility="collapsed", key="hypno_upload")
        if hypno_file:
            st.markdown(f"<div style='font-size:0.78rem; color:{C['success']}; margin-top:8px;'>✅ {hypno_file.name}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    if psg_file and hypno_file:
        st.success("✅ Ready! Both files uploaded")
    elif psg_file or hypno_file:
        st.warning("⏳ Please upload both PSG and Hypnogram files")
    else:
        st.info("📁 Upload both files to get started")

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    if st.button("🔍  Analyze Sleep Data", use_container_width=True, key="analyze_btn"):
        if not psg_file or not hypno_file:
            st.error("Please upload both PSG and Hypnogram files.")
        else:
            step_ph = st.empty()
            steps = ["Upload", "Feature Extraction", "AI Prediction", "Results"]

            def render_steps(active_idx):
                cols_html = ""
                for i, s in enumerate(steps):
                    if i < active_idx:
                        bg, fg = C['success'], "white"
                    elif i == active_idx:
                        bg, fg = C['primary'], "white"
                    else:
                        bg, fg = C['input_bg'], C['text_muted']
                    cols_html += f'<div class="step" style="background:{bg}; color:{fg};">{s}</div>'
                step_ph.markdown(f'<div class="step-track" style="margin-bottom:14px;">{cols_html}</div>', unsafe_allow_html=True)

            with st.spinner("Analyzing your sleep data…"):
                render_steps(0)
                progress = st.progress(0, text="Saving files…")
                with tempfile.TemporaryDirectory() as tmpdir:
                    psg_path   = os.path.join(tmpdir, "psg.edf")
                    hypno_path = os.path.join(tmpdir, "hypno.edf")
                    with open(psg_path,   'wb') as f: f.write(psg_file.getbuffer())
                    with open(hypno_path, 'wb') as f: f.write(hypno_file.getbuffer())

                    render_steps(1)
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

                    render_steps(2)
                    progress.progress(70, text="Running AI prediction…")
                    severity, probabilities = predict_severity(normalized)
                    if severity is None:
                        st.error("Prediction failed.")
                        return

                    render_steps(3)
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
# RESULTS PAGE
# ═══════════════════════════════════════════════════════════════

def show_results_page():
    render_sidebar()

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

    st.markdown(f"""
    <div class="top-strip">
        <div>
            <div style="font-size:0.7rem; font-weight:700; letter-spacing:1.4px; color:{C['text_muted']}; text-transform:uppercase;">Sleep Analysis Results</div>
            <h1 style="margin-top:4px; font-size:1.5rem;">{st.session_state.username.capitalize()}'s Sleep Report</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([0.8, 1.5], gap="large")

    with col1:
        st.markdown(f"""
        <div class="severity-card" style="--sev-color:{sev_color};">
            <div style="font-size:2rem; margin-bottom:6px;">{icons.get(severity,'❓')}</div>
            <div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:1.4px; color:{C['text_muted']}; margin-bottom:6px; font-weight:600;">Sleep Severity</div>
            <div style="font-size:1.5rem; font-weight:700; color:{sev_color}; font-family:'Poppins',sans-serif;">{severity}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("**📊 Probability Distribution**")
        severity_levels = ['No Insomnia', 'Mild', 'Moderate', 'Severe']
        fig = go.Figure(data=[
            go.Bar(
                x=severity_levels,
                y=probs,
                marker=dict(color=[SEVERITY_COLORS[s] for s in severity_levels]),
                text=[f'{p*100:.0f}%' for p in probs],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>%{y:.1%}<extra></extra>'
            )
        ])
        fig.update_layout(
            height=260, template='plotly_white', showlegend=False,
            margin=dict(l=40, r=20, t=10, b=30), font=dict(size=10, family="Inter"),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    tab_metrics, tab_stages, tab_recs = st.tabs(["💤 Sleep Metrics", "🛏️ Sleep Stages", "💡 Recommendations"])

    with tab_metrics:
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
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

    with tab_stages:
        stages = ['Wake', 'N1', 'N2', 'N3', 'REM']
        percentages = [
            features['percent_w'], features['percent_n1'], features['percent_n2'],
            features['percent_n3'], features['percent_rem']
        ]
        fig_pie = go.Figure(data=[go.Pie(
            labels=stages, values=percentages,
            marker=dict(colors=[C['border'], '#A7C4E0', C['secondary'], C['primary'], C['accent']]),
            textposition='inside', textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>'
        )])
        fig_pie.update_layout(
            height=310, template='plotly_white', margin=dict(l=0, r=0, t=20, b=10),
            font=dict(size=11, family="Inter"), paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

    with tab_recs:
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        if not st.session_state.show_solutions:
            st.info("Generate your personalized recommendations based on your severity result.")
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
            for tip in recs['tips'][:3]:
                st.markdown(f"""
                <div class="rec-item"><span class="check">✓</span><span class="text">{tip}</span></div>
                """, unsafe_allow_html=True)

            st.markdown(f"<div style='font-size:0.8rem; color:{C['text_muted']}; margin-top:6px;'>⏱️ Expected Duration: {recs['duration']}</div>", unsafe_allow_html=True)

            st.markdown("""
            <div class="disclaimer">⚠️ This tool is intended for informational/research purposes and does not replace evaluation by a qualified healthcare professional.</div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
            st.markdown("**📄 Your sleep analysis report is ready.**")
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