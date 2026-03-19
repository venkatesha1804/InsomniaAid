import streamlit as st
import os
import tempfile
import time
import sqlite3
import hashlib
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(
    page_title="InsomniaAid",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════════
# COLORS & CONFIG
# ═══════════════════════════════════════════════════════════════
COLORS = {
    'primary': '#1abc9c',
    'primary_dark': '#16a085',
    'primary_light': '#c7f0d8',
    'accent': '#16a085',
    'bg': '#f5f5f5',
    'card': '#ffffff',
    'text_main': '#2c3e50',
    'text_body': '#555555',
    'text_muted': '#999999',
    'border': '#e0e0e0',
    'input_bg': '#f9f9f9',
    'success': '#48bb78',
    'danger': '#f56565',
}

SEVERITY_COLORS = {
    "No Insomnia": "#48bb78",
    "Mild": "#f6ad55",
    "Moderate": "#ed8936",
    "Severe": "#f56565"
}

SEVERITY_BG = {
    "No Insomnia": "#f0fdf4",
    "Mild": "#fffaf0",
    "Moderate": "#fff5f0",
    "Severe": "#fff5f5"
}

CHATBOT_KNOWLEDGE = {
    "what is insomnia": "Insomnia is a sleep disorder characterized by difficulty falling asleep, staying asleep, or both. It can be acute (short-term) or chronic (long-term).",
    "causes of insomnia": "Common causes include stress, anxiety, depression, poor sleep habits, medical conditions, medications, and lifestyle factors.",
    "symptoms of insomnia": "Symptoms include difficulty falling asleep, waking up frequently, early morning awakening, feeling unrefreshed, daytime fatigue, and mood disturbances.",
    "treatments for insomnia": "Treatments include cognitive behavioral therapy, medications, lifestyle changes, sleep hygiene improvements, and medical consultation.",
    "sleep hygiene tips": "Maintain consistent sleep schedule, keep bedroom cool and dark, avoid screens before bed, limit caffeine, exercise regularly, and manage stress.",
    "what is psg": "PSG (Polysomnography) is a comprehensive sleep study that records brain activity, eye movements, muscle tension, heart rate, and breathing patterns.",
    "what is a hypnogram": "A hypnogram is a visual representation of sleep stages over time, showing transitions between wake, light sleep, deep sleep, and REM sleep.",
    "what does severity mean": "Severity refers to the level of insomnia impact on your life, ranging from no insomnia to severe chronic insomnia.",
    "what is rem sleep": "REM (Rapid Eye Movement) sleep is when vivid dreams occur. It's crucial for cognitive development and emotional regulation.",
    "how to use insomniaid": "Upload your PSG and hypnogram files, click analyze, and our AI will predict severity and provide personalized recommendations.",
    "what is sleep efficiency": "Sleep efficiency is the percentage of time in bed actually spent sleeping. Healthy sleep efficiency is typically 85% or higher.",
    "what is sleep onset latency": "Sleep onset latency is the time it takes to fall asleep after getting into bed.",
    "what is wake after sleep onset": "WASO is the total time spent awake after initially falling asleep.",
    "how accurate is the model": "Our Random Forest model achieves 94.94% accuracy on test data for insomnia severity prediction.",
    "how does insomnia affect health": "Insomnia increases risk of cardiovascular disease, depression, obesity, accidents, and impairs cognitive function.",
    "help": "I can answer questions about insomnia, PSG, sleep stages, severity levels, treatments, and how to use InsomniAid. Ask away!",
}

C = COLORS

# ═══════════════════════════════════════════════════════════════
# DATABASE FUNCTIONS
# ═══════════════════════════════════════════════════════════════
def init_db():
    """Initialize SQLite database"""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, email TEXT UNIQUE, password TEXT)''')
        conn.commit()
        conn.close()
    except:
        pass

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, email, password):
    """Register new user"""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        hashed_pw = hash_password(password)
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, email, hashed_pw))
        conn.commit()
        conn.close()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        return False, "Username or email already exists"
    except Exception as e:
        return False, str(e)

def login_user(username, password):
    """Authenticate user"""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        hashed_pw = hash_password(password)
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_pw))
        result = c.fetchone()
        conn.close()
        if result:
            return True, username
        return False, "Invalid credentials"
    except:
        return False, "Database error"

def user_exists(email):
    """Check if email exists"""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        result = c.fetchone()
        conn.close()
        return result is not None
    except:
        return False

def username_exists(username):
    """Check if username exists"""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        result = c.fetchone()
        conn.close()
        return result is not None
    except:
        return False

def validate_email(email):
    """Validate email format"""
    return "@" in email and "." in email

# ═══════════════════════════════════════════════════════════════
# MOCK ML FUNCTIONS
# ═══════════════════════════════════════════════════════════════
def predict_severity(features_dict):
    """Mock prediction function"""
    try:
        # Mock prediction based on sleep efficiency
        efficiency = features_dict.get('sleep_efficiency_percent', 70)
        
        if efficiency > 85:
            severity = "No Insomnia"
            probs = [0.85, 0.10, 0.04, 0.01]
        elif efficiency > 75:
            severity = "Mild"
            probs = [0.20, 0.70, 0.08, 0.02]
        elif efficiency > 60:
            severity = "Moderate"
            probs = [0.05, 0.15, 0.70, 0.10]
        else:
            severity = "Severe"
            probs = [0.02, 0.05, 0.20, 0.73]
        
        return severity, probs
    except:
        return None, None

def get_recommendations(severity):
    """Get recommendations based on severity"""
    recs = {
        "No Insomnia": {
            "title": "✅ Great Sleep Health!",
            "message": "Your sleep patterns are healthy. Maintain your current sleep habits!",
            "tips": [
                "Continue maintaining consistent sleep schedule",
                "Keep your sleep environment cool and dark",
                "Regular exercise 3-4 times per week",
            ],
            "duration": "Ongoing maintenance"
        },
        "Mild": {
            "title": "⚠️ Mild Insomnia Detected",
            "message": "You have mild insomnia. Simple lifestyle changes can help significantly.",
            "tips": [
                "Improve sleep hygiene - consistent bedtime routine",
                "Reduce caffeine and screen time before bed",
                "Try relaxation techniques like deep breathing",
            ],
            "duration": "2-4 weeks for improvement"
        },
        "Moderate": {
            "title": "🟠 Moderate Insomnia Detected",
            "message": "Moderate insomnia requires more structured intervention.",
            "tips": [
                "Consider cognitive behavioral therapy for insomnia (CBT-I)",
                "Consult sleep specialist for evaluation",
                "Establish strict sleep schedule - sleep only when sleepy",
            ],
            "duration": "4-8 weeks with treatment"
        },
        "Severe": {
            "title": "🔴 Severe Insomnia Detected",
            "message": "Severe insomnia requires professional medical intervention.",
            "tips": [
                "Schedule appointment with sleep medicine specialist",
                "Consider sleep medication under medical supervision",
                "May require comprehensive sleep study and treatment plan",
            ],
            "duration": "8-12 weeks with medical treatment"
        }
    }
    return recs.get(severity, recs["Mild"])

# ═══════════════════════════════════════════════════════════════
# CSS STYLING
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
    box-shadow: 0 20px 60px rgba(26, 188, 156, 0.15) !important;
    min-height: calc(100vh - 40px) !important;
    margin-top: 20px !important;
    margin-bottom: 20px !important;
}}

header, footer, #MainMenu, [data-testid="stToolbar"] {{
    visibility: hidden !important;
    height: 0 !important;
}}

h1 {{ color: {C['text_main']} !important; font-size: 2.2rem !important; font-weight: 700 !important; margin: 0 !important; font-family: 'Poppins', sans-serif !important; }}
h2 {{ color: {C['text_main']} !important; font-size: 1.6rem !important; font-weight: 600 !important; font-family: 'Poppins', sans-serif !important; }}
h3 {{ color: {C['primary']} !important; font-size: 1.1rem !important; font-weight: 600 !important; font-family: 'Poppins', sans-serif !important; }}
p, label {{ color: {C['text_body']} !important; font-size: 0.95rem !important; line-height: 1.6 !important; }}

.stTextInput input {{
    background: {C['input_bg']} !important;
    border: 2px solid {C['border']} !important;
    border-radius: 12px !important;
    color: {C['text_main']} !important;
    padding: 12px 16px !important;
    font-size: 0.9rem !important;
    transition: all 0.3s ease;
}}

.stTextInput input:focus {{
    border-color: {C['primary']} !important;
    box-shadow: 0 0 0 4px rgba(26, 188, 156, 0.1) !important;
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
    box-shadow: 0 4px 12px rgba(26, 188, 156, 0.2) !important;
}}

.stButton > button:hover {{
    background: {C['primary_dark']} !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(26, 188, 156, 0.3) !important;
}}

.stAlert {{ border-radius: 12px !important; border-left: 4px solid !important; padding: 14px 18px !important; font-size: 0.9rem !important; }}

.stMetric {{
    background: {C['card']} !important;
    border: 2px solid {C['border']} !important;
    border-radius: 16px !important;
    padding: 20px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
}}

.stMetric:hover {{
    border-color: {C['primary']} !important;
    box-shadow: 0 8px 24px rgba(26, 188, 156, 0.15) !important;
}}

[data-testid="stMetricValue"] {{ color: {C['primary']} !important; font-size: 1.8rem !important; font-weight: 700 !important; }}
[data-testid="stMetricLabel"] {{ color: {C['text_muted']} !important; font-size: 0.8rem !important; text-transform: uppercase; letter-spacing: 1px; }}

.hero-section {{
    background: linear-gradient(135deg, #c7f0d8, #e0f7f4);
    border: 2px solid {C['border']};
    border-radius: 20px;
    padding: 28px;
    margin-bottom: 20px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
}}

.info-box {{
    background: linear-gradient(135deg, #e6f8f5, #f0fdf4);
    border-left: 4px solid {C['primary']};
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
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
    transition: all 0.3s ease;
}}

.feature-card:hover {{
    border-color: {C['primary']} !important;
    box-shadow: 0 8px 24px rgba(26, 188, 156, 0.15) !important;
    transform: translateY(-3px);
}}

hr {{ border: none !important; border-top: 2px solid {C['border']} !important; margin: 28px 0 !important; }}

[data-testid="stFileUploader"] {{
    background: linear-gradient(135deg, #c7f0d8, #f0fdf4) !important;
    border: 3px dashed {C['primary']} !important;
    border-radius: 16px !important;
    padding: 28px !important;
}}

[data-testid="stFileUploader"] section button {{
    background: {C['primary']} !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
}}

.stTabs [aria-selected="true"] {{ background: {C['primary']} !important; color: white !important; }}

[data-testid="stDownloadButton"] button {{
    background: {C['success']} !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}}

</style>
"""

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════
init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# ═══════════════════════════════════════════════════════════════
# CHATBOT
# ═══════════════════════════════════════════════════════════════
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
        "insomnia": "what is insomnia",
        "cause": "causes of insomnia",
        "treatment": "treatments for insomnia",
        "hygiene": "sleep hygiene tips",
        "psg": "what is psg",
    }
    for kw, mapped in kw_map.items():
        if kw in query:
            return CHATBOT_KNOWLEDGE.get(mapped, "")

    return "I'm not sure about that. Try asking about insomnia, PSG, or how to use InsomniAid! 😊"

# ═══════════════════════════════════════════════════════════════
# NAV
# ═══════════════════════════════════════════════════════════════
def render_top_nav():
    cols = st.columns([2, 1, 1, 1, 0.8])
    with cols[0]:
        st.markdown(f"""<div style="font-weight:700; font-size:1.2rem; color:{C['text_main']}; font-family: 'Poppins';">
            <span style="background: linear-gradient(135deg, {C['primary']}, {C['accent']}); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">InsomniaAid</span>
        </div>""", unsafe_allow_html=True)
    with cols[1]:
        if st.button("🏠 Home", key="nav_home", use_container_width=True):
            st.session_state.page = "home"; st.rerun()
    with cols[2]:
        if st.button("📁 Upload", key="nav_upload", use_container_width=True):
            st.session_state.page = "upload"; st.rerun()
    with cols[3]:
        if st.button("📊 Results", key="nav_results", use_container_width=True):
            st.session_state.page = "results"; st.rerun()
    with cols[4]:
        if st.button("🚪 Logout", key="nav_logout", use_container_width=True):
            st.session_state.logged_in = False; st.session_state.username = ""; st.rerun()

# ═══════════════════════════════════════════════════════════════
# AUTH PAGE
# ═══════════════════════════════════════════════════════════════
def show_auth_page():
    _, col, _ = st.columns([1, 2.5, 1])
    with col:
        st.markdown(f"""<div style="text-align:center; padding:20px 0 16px;">
            <h1 style="font-size:2.8rem; color:{C['text_main']}; margin:0; font-family: 'Poppins';">
                <span style="background: linear-gradient(135deg, {C['primary']}, {C['accent']}); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Insomni</span>Aid
            </h1>
            <p style="color:{C['text_muted']}; font-size:0.92rem; margin-top:8px;">AI-Powered Sleep Analysis & Insomnia Detection</p>
        </div>""", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

        with tab1:
            st.subheader("Welcome Back")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", key="login_btn", use_container_width=True):
                if username and password:
                    success, result = login_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = result
                        st.session_state.page = "home"
                        st.success("✅ Login successful!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"❌ {result}")

        with tab2:
            st.subheader("Create Account")
            username = st.text_input("Username", key="reg_username")
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password", type="password", key="reg_password")
            confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
            if st.button("Register", key="register_btn", use_container_width=True):
                if not all([username, email, password, confirm]):
                    st.error("All fields required")
                elif not validate_email(email):
                    st.error("Invalid email")
                elif len(password) < 6:
                    st.error("Min 6 chars")
                elif password != confirm:
                    st.error("Passwords don't match")
                elif username_exists(username):
                    st.error("Username taken")
                elif user_exists(email):
                    st.error("Email exists")
                else:
                    success, msg = register_user(username, email, password)
                    if success:
                        st.success("✅ Registered! Switch to Login.")
                    else:
                        st.error(f"❌ {msg}")

# ═══════════════════════════════════════════════════════════════
# HOME PAGE
# ═══════════════════════════════════════════════════════════════
def show_home_page():
    render_top_nav()
    
    left, right = st.columns([1.6, 1], gap="large")
    
    with left:
        st.markdown(f"""<div class="hero-section">
            <h1 style="color:{C['text_main']}; margin:0; font-size:1.8rem; font-family: 'Poppins';">
                Welcome, <span style="background: linear-gradient(135deg, {C['primary']}, {C['accent']}); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{st.session_state.username.capitalize()}</span> 👋
            </h1>
            <p style="color:{C['text_body']}; margin-top:10px; font-size:0.92rem;">Analyze your sleep data with AI-powered insights.</p>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="info-box">
            <h3>🌙 About Insomnia</h3>
            <p>Insomnia is a sleep disorder. <strong style="color:{C['primary']};">InsomniAid</strong> uses AI to analyze PSG data and deliver personalized recommendations.</p>
        </div>""", unsafe_allow_html=True)

        features = [
            ("🤖", "AI Classification", "Severity prediction"),
            ("📊", "Sleep Metrics", "Sleep stage breakdown"),
            ("💡", "Recommendations", "Personalized tips"),
            ("📄", "PDF Reports", "Download reports"),
        ]
        
        f_cols = st.columns(2)
        for i, (icon, title, desc) in enumerate(features):
            with f_cols[i % 2]:
                st.markdown(f"""<div class="feature-card">
                    <span style="font-size:1.5rem;">{icon}</span>
                    <div><h4 style="margin:0; font-weight:700;">{title}</h4>
                    <p style="margin:4px 0 0 0; font-size:0.85rem; color:{C['text_muted']};">{desc}</p></div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📁 Upload PSG Files →", use_container_width=True):
            st.session_state.page = "upload"; st.rerun()

    with right:
        st.markdown(f"""<div style="background:{C['card']}; border:2px solid {C['border']}; border-radius:20px; padding:24px;">
            <div style="display:flex; align-items:center; gap:12px; padding-bottom:16px; margin-bottom:18px; border-bottom:2px solid {C['border']};">
                <span style="font-size:1.6rem;">🤖</span>
                <div><div style="font-weight:600; font-size:1.1rem; color:{C['text_main']}; margin:0;">AI Assistant</div>
                <div style="font-size:0.8rem; color:{C['text_muted']};">Ask about sleep</div></div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div style="max-height:280px; overflow-y:auto; margin-bottom:16px;">', unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            role = msg["role"]
            text = msg["text"]
            st.markdown(f'<div style="background:{C["primary"] if role == "bot" else C["primary"]}; color:white; padding:10px; border-radius:10px; margin-bottom:8px; font-size:0.85rem;">{text}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        inp, btn = st.columns([5, 1])
        with inp:
            user_msg = st.text_input("Ask…", key="chat_inp", label_visibility="collapsed")
        with btn:
            if st.button("▶", key="chat_send", use_container_width=True):
                if user_msg.strip():
                    st.session_state.chat_history.append({"role": "user", "text": user_msg.strip()})
                    reply = chatbot_response(user_msg.strip())
                    st.session_state.chat_history.append({"role": "bot", "text": reply})
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# UPLOAD PAGE
# ═══════════════════════════════════════════════════════════════
def show_upload_page():
    render_top_nav()

    st.markdown(f"""<div class="hero-section">
        <h2>📤 Upload PSG Data</h2>
        <p style="font-size:0.9rem; margin:8px 0 0 0;">Upload files for AI analysis</p>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown(f"""<div style="background:linear-gradient(135deg, {C['primary_light']}, {C['card']}); border:2px solid {C['primary']}; border-radius:16px; padding:20px; margin-bottom:12px;">
            <div style="color:{C['primary']}; font-weight:600; font-size:1rem; margin-bottom:8px;">🧠 PSG</div>
            <div style="color:{C['text_muted']}; font-size:0.8rem; margin-bottom:12px;">EDF file</div>
        """, unsafe_allow_html=True)
        psg_file = st.file_uploader("PSG", type=['edf'], label_visibility="collapsed", key="psg_upload")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""<div style="background:linear-gradient(135deg, #16a08515, {C['card']}); border:2px solid #16a085; border-radius:16px; padding:20px; margin-bottom:12px;">
            <div style="color:#16a085; font-weight:600; font-size:1rem; margin-bottom:8px;">📈 Hypnogram</div>
            <div style="color:{C['text_muted']}; font-size:0.8rem; margin-bottom:12px;">EDF file</div>
        """, unsafe_allow_html=True)
        hypno_file = st.file_uploader("Hypno", type=['edf'], label_visibility="collapsed", key="hypno_upload")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if psg_file and hypno_file:
        st.success("✅ Ready!")
    elif psg_file or hypno_file:
        st.warning("⏳ Upload both files")
    else:
        st.info("📁 Upload both files")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔍 Analyze Sleep Data", use_container_width=True):
        if psg_file and hypno_file:
            with st.spinner("Analyzing..."):
                # Mock analysis
                features = {
                    'sleep_efficiency_percent': 75,
                    'sleep_onset_latency_min': 15,
                    'total_sleep_time_min': 420,
                    'wake_after_sleep_onset_min': 60,
                    'rem_latency_min': 90,
                    'percent_rem': 20,
                    'percent_w': 15,
                    'percent_n1': 5,
                    'percent_n2': 40,
                    'percent_n3': 20,
                }
                severity, probs = predict_severity(features)
                st.session_state.analysis_data = {
                    'severity': severity,
                    'features': features,
                    'probabilities': probs
                }
                st.session_state.page = "results"
                st.rerun()

# ═══════════════════════════════════════════════════════════════
# RESULTS PAGE
# ═══════════════════════════════════════════════════════════════
def show_results_page():
    render_top_nav()

    if not st.session_state.analysis_data:
        st.error("No data. Upload files first.")
        return

    data = st.session_state.analysis_data
    severity = data['severity']
    features = data['features']
    probs = data['probabilities']
    
    sev_color = SEVERITY_COLORS.get(severity, C['danger'])
    icons = {"No Insomnia":"✅", "Mild":"⚠️", "Moderate":"🟠", "Severe":"🔴"}

    col1, col2 = st.columns([0.8, 1.5], gap="large")
    
    with col1:
        st.markdown(f"""<div style="background:linear-gradient(135deg, #c7f0d8, #e0f7f4); border:3px solid {sev_color}; border-radius:18px; padding:28px; text-align:center;">
            <div style="font-size:2.2rem;">{icons.get(severity,'❓')}</div>
            <div style="font-size:0.75rem; text-transform:uppercase; color:{C['text_muted']}; margin:8px 0; font-weight:600;">Severity</div>
            <div style="font-size:1.6rem; font-weight:700; color:{sev_color};">{severity}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("**📊 Prediction Confidence**")
        severity_levels = ['No Insomnia', 'Mild', 'Moderate', 'Severe']
        fig = go.Figure(data=[go.Bar(
            x=severity_levels, y=probs,
            marker=dict(color=['#48bb78', '#f6ad55', '#ed8936', '#f56565']),
            text=[f'{p*100:.0f}%' for p in probs],
            textposition='outside',
        )])
        fig.update_layout(height=280, template='plotly_white', showlegend=False, margin=dict(l=40, r=20, t=20, b=30))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("**💤 Sleep Metrics**")
    mc1, mc2, mc3 = st.columns(3, gap="small")
    with mc1:
        st.metric("Sleep Efficiency", f"{features['sleep_efficiency_percent']:.0f}%")
        st.metric("Sleep Onset", f"{features['sleep_onset_latency_min']:.0f}m")
    with mc2:
        st.metric("Total Sleep", f"{features['total_sleep_time_min']:.0f}m")
        st.metric("WASO", f"{features['wake_after_sleep_onset_min']:.0f}m")
    with mc3:
        st.metric("REM Latency", f"{features['rem_latency_min']:.0f}m")
        st.metric("REM %", f"{features['percent_rem']:.0f}%")

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("**🛏️ Sleep Stages**")
    stages = ['Wake', 'N1', 'N2', 'N3', 'REM']
    percentages = [features['percent_w'], features['percent_n1'], features['percent_n2'], features['percent_n3'], features['percent_rem']]
    
    fig_pie = go.Figure(data=[go.Pie(labels=stages, values=percentages, marker=dict(colors=['#e2e8f0', '#cbd5e0', '#a0aec0', '#718096', '#4a5568']), textinfo='label+percent')])
    fig_pie.update_layout(height=300, template='plotly_white', margin=dict(l=0, r=0, t=20, b=20))
    st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)

    recs = get_recommendations(severity)
    st.markdown(f"""<div class="info-box"><h3>{recs['title']}</h3><p>{recs['message']}</p></div>""", unsafe_allow_html=True)

    st.markdown("**📋 Recommended Actions**")
    for i, tip in enumerate(recs['tips'][:3], 1):
        st.markdown(f"<div style='font-size:0.85rem; margin-bottom:6px;'><strong>{i}.</strong> {tip}</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# MAIN ROUTER
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