import os

# App Configuration
APP_NAME = "InsomniAid"
APP_ICON = ""

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH  = os.path.join(BASE_DIR, 'models/random_forest_model.joblib')
DATA_PATH   = os.path.join(BASE_DIR, 'data/sleep_features_labels_core.csv')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
DB_PATH     = os.path.join(BASE_DIR, 'users.db')

os.makedirs(UPLOADS_DIR, exist_ok=True)

# ─── Clinical / Healthcare Theme ─────────────────────────────
COLORS = {
    # Primary colors
    'primary':         '#16233F',      # Deep navy
    'primary_dark':    '#0E1830',      # Darker navy (hover)
    'primary_light':   '#EBF1F9',      # Very light soft-blue tint
    'primary_mid':     '#2A4270',      # Mid navy (gradients)
    'accent':          '#0EA5A0',      # Teal
    'accent_dark':     '#0B7F7B',
    'secondary':       '#4A7BA6',      # Soft blue

    # Backgrounds
    'bg':              '#F3F6FB',      # Very light blue-gray
    'card':            '#FFFFFF',
    'input_bg':        '#F8FAFC',

    # Borders and dividers
    'border':          '#E4E9F1',

    # Text colors
    'text_main':       '#161D2C',
    'text_body':       '#404A5E',
    'text_muted':      '#7C889D',

    # Status colors
    'success':         '#15803D',
    'success_bg':      '#DCFCE7',
    'warning':         '#B45309',
    'warning_bg':      '#FEF3C7',
    'danger':          '#B91C1C',
    'danger_bg':       '#FEE2E2',
    'info':            '#1D4ED8',
    'info_bg':         '#DBEAFE',
}

SEVERITY_COLORS = {
    'No Insomnia': '#15803D',
    'Mild':        '#B45309',
    'Moderate':    '#C2410C',
    'Severe':      '#B91C1C',
}

SEVERITY_BG = {
    'No Insomnia': '#DCFCE7',
    'Mild':        '#FEF3C7',
    'Moderate':    '#FFEDD5',
    'Severe':      '#FEE2E2',
}

# ─── Chatbot Knowledge Base ──────────────────────────────────
CHATBOT_KNOWLEDGE = {
    "what is insomnia": "Insomnia is a sleep disorder where you have trouble falling asleep, staying asleep, or getting quality sleep. It can be short-term (a few nights) or chronic (lasting months). It affects roughly 1 in 3 adults at some point.",
    "causes of insomnia": "Common causes include stress, anxiety, depression, irregular sleep schedules, too much caffeine or alcohol, screen exposure before bed, chronic pain, and certain medications. Environmental factors like noise, light, or temperature can also play a role.",
    "symptoms of insomnia": "Symptoms include difficulty falling or staying asleep, waking up too early, feeling tired during the day, irritability, difficulty concentrating, and feeling unrefreshed after sleep.",
    "how does insomnia affect health": "Chronic insomnia can lead to weakened immunity, weight gain, increased risk of heart disease, diabetes, and mental health issues like depression and anxiety. It also hurts memory, focus, and reaction time.",
    "treatments for insomnia": "Treatments include Cognitive Behavioral Therapy for Insomnia (CBT-I), sleep hygiene improvements, relaxation techniques, and in some cases, short-term medication prescribed by a doctor. CBT-I is considered the gold-standard first-line treatment.",
    "sleep hygiene tips": "Keep a consistent sleep schedule, avoid screens 1 hour before bed, keep your room cool and dark, limit caffeine after noon, exercise regularly but not too close to bedtime, and avoid large meals before sleeping.",
    "what is psg": "PSG stands for Polysomnography. It's a comprehensive sleep study that monitors your brain waves, eye movements, heart rate, breathing patterns, oxygen levels, and muscle activity while you sleep. It's the gold standard for diagnosing sleep disorders.",
    "what is a hypnogram": "A hypnogram is a visual chart that shows the stages of sleep throughout a night. It tracks transitions between wakefulness, light sleep (N1, N2), deep sleep (N3), and REM sleep. It helps doctors analyze your sleep architecture.",
    "what does severity mean": "InsomniAid classifies insomnia into four levels: No Insomnia (healthy sleep), Mild (minor sleep difficulties), Moderate (noticeable impact on daily life), and Severe (significant disruption requiring medical attention).",
    "what is rem sleep": "REM (Rapid Eye Movement) sleep is a sleep stage where your brain is very active, dreams occur, and your muscles are temporarily paralyzed. It's essential for memory consolidation, emotional processing, and creativity. Adults typically need 20-25% of their sleep in REM.",
    "how to use insomniaid": "Simply upload your PSG (.edf) and Hypnogram (.edf) files on the Upload page, then click Analyze. The AI model will predict your insomnia severity and provide personalized recommendations and a downloadable PDF report.",
    "what is sleep efficiency": "Sleep efficiency is the percentage of time you actually spent sleeping while in bed. A healthy sleep efficiency is generally above 85%. Lower values suggest you're spending too much time awake while in bed.",
    "what is sleep onset latency": "Sleep onset latency is how long it takes you to fall asleep after getting into bed. Ideally, it should be between 10-20 minutes. Taking less than 5 minutes might actually indicate sleep deprivation, while more than 30 minutes can signal insomnia.",
    "what is wake after sleep onset": "WASO (Wake After Sleep Onset) is the total time spent awake after initially falling asleep. A healthy WASO is under 30 minutes. High WASO values indicate fragmented sleep and can worsen insomnia symptoms.",
    "how accurate is the model": "The InsomniAid AI model is a Random Forest classifier trained on polysomnography data. It analyzes sleep metrics like efficiency, latency, REM percentage, and more to predict insomnia severity. Always consult a healthcare professional for formal diagnosis.",
    "help": "Here are things I can help with:\n• What is insomnia / causes / symptoms\n• Treatments for insomnia\n• Sleep hygiene tips\n• What is PSG / Hypnogram\n• Sleep stages (REM, deep sleep)\n• Sleep metrics (efficiency, latency, WASO)\n• How to use InsomniAid\n• How accurate is the model\n• How insomnia affects health\n\nJust type your question naturally!",
}