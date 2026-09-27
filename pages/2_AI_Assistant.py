# pages/2_AI_Assistant.py
"""WeatherIQ — Gemini-powered AI Weather Assistant page."""

import logging

import streamlit as st

import config
from ai_assistant import AIAssistantError, ask, gemini_available

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Assistant — WeatherIQ",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS (matches WeatherIQ light theme) ──────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap');

:root {
    --bg:           #F5F9FC;
    --surface:      #FFFFFF;
    --border:       #E2E8F0;
    --border-strong:#CBD5E1;
    --text:         #172033;
    --text-2:       #64748B;
    --text-3:       #94A3B8;
    --teal:         #0EA5A4;
    --teal-soft:    rgba(14,165,164,.10);
    --teal-mid:     rgba(14,165,164,.20);
    --blue:         #2563EB;
    --blue-soft:    rgba(37,99,235,.08);
    --violet:       #7C3AED;
    --violet-soft:  rgba(124,58,237,.09);
    --violet-mid:   rgba(124,58,237,.18);
    --amber:        #F59E0B;
    --green:        #10B981;
    --red:          #EF4444;
    --shadow-sm:    0 1px 3px rgba(23,32,51,.06), 0 1px 2px rgba(23,32,51,.04);
    --shadow-md:    0 4px 12px rgba(23,32,51,.08), 0 2px 4px rgba(23,32,51,.04);
    /* AI bubble colors */
    --ai-bubble:    #F8FAFF;
    --user-bubble:  rgba(14,165,164,.07);
}

html, body, [class*="css"] {
    font-family: 'DM Sans', system-ui, -apple-system, sans-serif;
}

.stApp {
    background: var(--bg);
    color: var(--text);
}

#MainMenu, footer, header, .stDeployButton { visibility: hidden; }

.block-container {
    max-width: 860px;
    padding-top: .75rem;
    padding-bottom: 3rem;
}

/* ── Hero ── */
.ai-hero {
    margin: 0 0 1rem;
    padding: 1.3rem 1.6rem;
    border: 1px solid var(--border);
    border-radius: 18px;
    background: var(--surface);
    box-shadow: var(--shadow-md);
}
.ai-hero-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
}
.ai-hero-brand {
    font-size: 1.85rem;
    font-weight: 700;
    letter-spacing: -.06em;
    line-height: 1;
    color: var(--text);
}
.ai-hero-brand span { color: var(--teal); }
.ai-hero-brand .ai-tag {
    display: inline-block;
    margin-left: .45rem;
    padding: .15rem .5rem;
    border-radius: 6px;
    background: var(--violet);
    color: #fff;
    font-size: .68rem;
    font-weight: 700;
    letter-spacing: .06em;
    vertical-align: middle;
}
.ai-hero-tagline {
    margin-top: .38rem;
    color: var(--text-2);
    font-size: .85rem;
}
.gemini-badge {
    display: flex;
    align-items: center;
    gap: .42rem;
    padding: .35rem .72rem;
    border: 1px solid var(--violet-mid);
    border-radius: 999px;
    background: var(--violet-soft);
    color: var(--violet);
    font-size: .68rem;
    font-weight: 700;
    letter-spacing: .05em;
    white-space: nowrap;
}
.gemini-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 0 3px rgba(16,185,129,.18);
    animation: pulse 2.2s ease-in-out infinite;
}
.gemini-dot.offline {
    background: var(--red);
    box-shadow: 0 0 0 3px rgba(239,68,68,.15);
    animation: none;
}

/* ── Section heading ── */
.section-heading {
    display: flex;
    align-items: center;
    gap: .55rem;
    margin: 1.3rem 0 .65rem;
    color: var(--text-2);
    font-size: .7rem;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
}
.section-heading::before {
    content: "";
    width: 3px;
    height: 14px;
    border-radius: 3px;
    background: var(--violet);
}

/* ── Streamlit inputs ── */
.stTextInput > div > div > input {
    min-height: 48px !important;
    border: 2px solid var(--border-strong) !important;
    border-radius: 10px !important;
    background: var(--surface) !important;
    color: var(--text) !important;
    font-size: .92rem !important;
    box-shadow: var(--shadow-sm) !important;
    caret-color: var(--violet) !important;
    transition: border-color .15s ease, box-shadow .15s ease !important;
}
.stTextInput > div > div > input::placeholder {
    color: var(--text-3) !important;
    font-style: italic;
}
.stTextInput > div > div > input:focus {
    border-color: var(--violet) !important;
    box-shadow: 0 0 0 4px rgba(124,58,237,.13) !important;
    outline: none !important;
}
.stTextInput > div > div > input:hover:not(:focus) {
    border-color: var(--violet-mid) !important;
}
/* Chat ask-input wrapper — extra visual weight */
div[data-testid="stForm"] .stTextInput > div > div > input {
    min-height: 52px !important;
    font-size: .95rem !important;
    border: 2px solid #A78BFA !important;
    background: #FDFAFF !important;
}
.stFormSubmitButton > button, .stButton > button {
    min-height: 46px !important;
    border-radius: 10px !important;
    border: none !important;
    background: var(--violet) !important;
    color: #fff !important;
    font-weight: 600 !important;
    font-size: .875rem !important;
    transition: background .15s ease, box-shadow .15s ease, transform .15s ease !important;
    box-shadow: 0 2px 8px rgba(124,58,237,.28) !important;
}
.stFormSubmitButton > button:hover, .stButton > button:hover {
    background: #6D28D9 !important;
    box-shadow: 0 4px 14px rgba(124,58,237,.36) !important;
    transform: translateY(-1px) !important;
}
label, .stMarkdown, .stCaption, .stTextInput label { color: var(--text-2) !important; }

div[data-testid="stForm"] {
    padding: .8rem .9rem !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    background: var(--surface) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ── Chat bubbles ── */
.chat-bubble {
    display: flex;
    gap: .65rem;
    align-items: flex-start;
    animation: rise .28s ease both;
}
.chat-bubble.user { flex-direction: row-reverse; }

.bubble-avatar {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: .72rem;
    font-weight: 700;
}
.bubble-avatar.ai {
    background: var(--violet);
    color: #fff;
}
.bubble-avatar.user {
    background: var(--teal-soft);
    color: var(--teal);
    border: 1px solid var(--teal-mid);
}

.bubble-body {
    max-width: 82%;
    padding: .75rem 1rem;
    border-radius: 14px;
    font-size: .87rem;
    line-height: 1.65;
}
.bubble-body.ai {
    border: 1px solid var(--border);
    border-top-left-radius: 4px;
    background: var(--ai-bubble);
    color: var(--text);
}
.bubble-body.user {
    border: 1px solid var(--teal-mid);
    border-top-right-radius: 4px;
    background: var(--user-bubble);
    color: var(--text);
    text-align: right;
}
.bubble-meta {
    margin-top: .28rem;
    color: var(--text-3);
    font-size: .62rem;
    letter-spacing: .04em;
}
.bubble-meta.user { text-align: right; }

/* ── Suggestions ── */
.stButton > button[kind="secondary"] {
    background: var(--surface) !important;
    color: var(--text-2) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
    font-weight: 500 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--violet) !important;
    color: var(--violet) !important;
    background: var(--violet-soft) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ── Divider ── */
.chat-divider {
    height: 1px;
    background: var(--border);
    margin: .25rem 0;
}

/* ── Scrollable chat ── */
.chat-scroll {
    max-height: 540px;
    overflow-y: auto;
    padding-right: .25rem;
    scroll-behavior: smooth;
}
.chat-scroll::-webkit-scrollbar { width: 4px; }
.chat-scroll::-webkit-scrollbar-track { background: transparent; }
.chat-scroll::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 4px; }

/* ── Status messages ── */
.status-error {
    border-radius: 10px;
    padding: .82rem 1rem;
    font-size: .82rem;
    margin: .3rem 0;
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-left: 3px solid var(--red);
    color: #B91C1C;
}
.status-warning {
    border-radius: 10px;
    padding: .82rem 1rem;
    font-size: .82rem;
    margin: .3rem 0;
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-left: 3px solid var(--amber);
    color: #92400E;
}
.status-info {
    border-radius: 10px;
    padding: .82rem 1rem;
    font-size: .82rem;
    margin: .3rem 0;
    background: var(--teal-soft);
    border: 1px solid var(--teal-mid);
    color: #0F6B6A;
}

.stAlert { display: none !important; }

/* ── Back button ── */
.back-btn {
    display: inline-flex;
    align-items: center;
    gap: .45rem;
    margin-bottom: .9rem;
    padding: .45rem .9rem;
    border: 1px solid var(--border-strong);
    border-radius: 8px;
    background: var(--surface);
    color: var(--text-2);
    font-size: .8rem;
    font-weight: 600;
    letter-spacing: .01em;
    text-decoration: none;
    cursor: pointer;
    box-shadow: var(--shadow-sm);
    transition: border-color .14s ease, color .14s ease, box-shadow .14s ease, background .14s ease;
}
.back-btn:hover {
    border-color: var(--teal);
    color: var(--teal);
    background: var(--teal-soft);
    box-shadow: 0 2px 8px rgba(14,165,164,.14);
}
.back-btn .arrow { font-size: .95rem; line-height: 1; }

/* ── Motion ── */
@keyframes rise {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50%     { opacity:.5; transform:scale(.84); }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration:.01ms !important;
        animation-iteration-count:1 !important;
        transition-duration:.01ms !important;
    }
}
@media (max-width: 640px) {
    .ai-hero-row { flex-direction: column; align-items: flex-start; }
}
</style>
""", unsafe_allow_html=True)


# ── Session state ────────────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "ai_chat_history": [],      # list of {"role": "user"|"ai", "text": str}
        "ai_language": "en",
        "ai_city": "",
        "ai_pending_suggestion": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _err(msg: str):
    st.markdown(f'<div class="status-error">{msg}</div>', unsafe_allow_html=True)

def _warn(msg: str):
    st.markdown(f'<div class="status-warning">{msg}</div>', unsafe_allow_html=True)

def _info(msg: str):
    st.markdown(f'<div class="status-info">{msg}</div>', unsafe_allow_html=True)

def _section(title: str):
    st.markdown(f'<div class="section-heading">{title}</div>', unsafe_allow_html=True)

LANG_OPTIONS = {"en": "🇬🇧 English", "hi": "🇮🇳 Hindi"}

SUGGESTIONS_EN = [
    "How is today's weather?",
    "Will it rain today?",
    "Should I carry an umbrella?",
    "Is it good for running outside?",
    "What should I wear today?",
    "Is it good for cycling?",
    "Is it suitable for a cricket match?",
    "What's the weather like for travel?",
]

SUGGESTIONS_HI = [
    "आज का मौसम कैसा है?",
    "क्या आज बारिश होगी?",
    "क्या मुझे छाता लेना चाहिए?",
    "क्या बाहर दौड़ने के लिए अच्छा मौसम है?",
    "आज मुझे क्या पहनना चाहिए?",
    "क्या साइकिलिंग के लिए अच्छा है?",
    "क्या क्रिकेट मैच के लिए उपयुक्त है?",
    "यात्रा के लिए मौसम कैसा है?",
]


def _render_bubble(role: str, text: str, index: int):
    """Render a single chat message bubble."""
    if role == "user":
        avatar_html = '<div class="bubble-avatar user">You</div>'
        body_html = f'<div class="bubble-body user">{text}</div>'
        st.markdown(
            f'<div class="chat-bubble user">{avatar_html}<div>'
            f'{body_html}<div class="bubble-meta user">You</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
    else:
        avatar_html = '<div class="bubble-avatar ai">AI</div>'
        # Preserve newlines as <br> for rendered markdown-ish display
        formatted = text.replace("\n", "<br>")
        body_html = f'<div class="bubble-body ai">{formatted}</div>'
        st.markdown(
            f'<div class="chat-bubble ai">{avatar_html}<div>'
            f'{body_html}<div class="bubble-meta">WeatherIQ AI · Gemini</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )


def _detect_comparison_cities(query: str, city: str) -> list[str] | None:
    """Heuristic: if the query mentions 'compare' and multiple cities, extract them.
    Falls back to None so the caller uses the single-city path."""
    lowered = query.lower()
    if "compare" not in lowered and " vs " not in lowered and " versus " not in lowered:
        return None
    # Extract comma/vs-separated tokens that look like city names
    import re
    tokens = re.split(r",| vs | versus | and ", query, flags=re.IGNORECASE)
    candidates = []
    for t in tokens:
        cleaned = re.sub(r"(?i)compare|weather|between|the|in|of|'s", "", t).strip()
        if 2 <= len(cleaned) <= 60:
            candidates.append(cleaned)
    return candidates if len(candidates) >= 2 else None


def _do_ask(user_query: str):
    """Call the backend, append both messages to history, handle errors."""
    city = st.session_state.ai_city.strip()
    lang = st.session_state.ai_language

    # Append user message immediately
    st.session_state.ai_chat_history.append({"role": "user", "text": user_query})

    comparison_cities = _detect_comparison_cities(user_query, city)

    try:
        response = ask(
            user_query=user_query,
            city=city,
            language=lang,
            comparison_cities=comparison_cities,
        )
        st.session_state.ai_chat_history.append({"role": "ai", "text": response})
    except AIAssistantError as exc:
        st.session_state.ai_chat_history.append({"role": "ai", "text": f"⚠️ {exc}"})


# ── Back to WeatherIQ button ─────────────────────────────────────────────────

st.markdown(
    '<a class="back-btn" href="/" target="_self">'
    '<span class="arrow">←</span> Back to WeatherIQ'
    '</a>',
    unsafe_allow_html=True,
)

# ── Hero header ───────────────────────────────────────────────────────────────

is_ready = gemini_available()
dot_class = "gemini-dot" if is_ready else "gemini-dot offline"
status_label = "Gemini Connected" if is_ready else "Gemini Offline"

st.markdown(f"""
<div class="ai-hero">
    <div class="ai-hero-row">
        <div>
            <div class="ai-hero-brand">
                Weather<span>IQ</span>
                <span class="ai-tag">AI</span>
            </div>
            <div class="ai-hero-tagline">
                Gemini-powered weather assistant — ask anything about your weather
            </div>
        </div>
        <div class="gemini-badge">
            <div class="{dot_class}"></div>
            {status_label}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if not is_ready:
    _err(
        "Gemini API key is not configured. "
        "Add <code>GEMINI_API_KEY</code> to your <code>.env</code> file and restart the app."
    )

# ── Config panel: city + language ────────────────────────────────────────────

_section("Configuration")

cfg_col1, cfg_col2 = st.columns([2, 1])

with cfg_col1:
    city_input = st.text_input(
        "City for weather data",
        value=st.session_state.ai_city,
        placeholder="e.g. Mumbai, London, New York",
        max_chars=100,
        key="city_input_widget",
        label_visibility="visible",
    )
    st.session_state.ai_city = city_input

with cfg_col2:
    lang_labels = list(LANG_OPTIONS.values())
    lang_keys   = list(LANG_OPTIONS.keys())
    current_idx = lang_keys.index(st.session_state.ai_language)
    selected_label = st.selectbox(
        "Language",
        options=lang_labels,
        index=current_idx,
        key="lang_selectbox",
    )
    st.session_state.ai_language = lang_keys[lang_labels.index(selected_label)]

lang = st.session_state.ai_language

# ── Suggested questions ───────────────────────────────────────────────────────

_section("Suggested Questions")

suggestions = SUGGESTIONS_HI if lang == "hi" else SUGGESTIONS_EN

# Render as clickable buttons in a 4-column grid
btn_cols = st.columns(4)
for i, suggestion in enumerate(suggestions):
    with btn_cols[i % 4]:
        if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
            st.session_state.ai_pending_suggestion = suggestion

# ── Chat history ──────────────────────────────────────────────────────────────

_section("Conversation")

history = st.session_state.ai_chat_history

if not history:
    city_hint = st.session_state.ai_city or "a city"
    if lang == "hi":
        placeholder_text = (
            f"ऊपर '{city_hint}' दर्ज करें और नीचे अपना प्रश्न पूछें।<br>"
            "उदाहरण: आज का मौसम कैसा है?"
        )
    else:
        placeholder_text = (
            f"Enter a city above and ask your first weather question below.<br>"
            f"Example: <em>How is today's weather in {city_hint}?</em>"
        )
    st.markdown(
        f'<div class="status-info" style="text-align:center;padding:1.6rem 1rem">'
        f'{placeholder_text}</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown('<div class="chat-scroll">', unsafe_allow_html=True)
    for i, msg in enumerate(history):
        _render_bubble(msg["role"], msg["text"], i)
        if i < len(history) - 1:
            st.markdown('<div class="chat-divider"></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Handle pending suggestion click ──────────────────────────────────────────

if st.session_state.ai_pending_suggestion:
    pending = st.session_state.ai_pending_suggestion
    st.session_state.ai_pending_suggestion = None

    if not st.session_state.ai_city.strip():
        _warn("Please enter a city name in the Configuration section above before asking a question.")
    elif not is_ready:
        _err("Gemini is not configured. Please add GEMINI_API_KEY to your .env file.")
    else:
        with st.spinner("Thinking..."):
            _do_ask(pending)
        st.rerun()

# ── Chat input form ───────────────────────────────────────────────────────────

_section("Ask a Question")

with st.form("chat_form", clear_on_submit=True):
    if lang == "hi":
        placeholder = "WeatherIQ AI से मौसम के बारे में कुछ भी पूछें..."
        btn_label   = "पूछें"
    else:
        placeholder = "Ask WeatherIQ AI anything about the weather..."
        btn_label   = "Ask"

    user_query_input = st.text_input(
        "Your question",
        placeholder=placeholder,
        max_chars=1000,
        label_visibility="collapsed",
    )
    ask_submitted = st.form_submit_button(btn_label, use_container_width=True)

if ask_submitted:
    query = user_query_input.strip() if user_query_input else ""
    if not query:
        _warn("Please type a question before submitting." if lang == "en" else "कृपया प्रश्न दर्ज करें।")
    elif not st.session_state.ai_city.strip():
        _warn(
            "Please enter a city name in the Configuration section above."
            if lang == "en" else
            "कृपया ऊपर 'Configuration' में शहर का नाम दर्ज करें।"
        )
    elif not is_ready:
        _err(
            "Gemini is not configured. Please add GEMINI_API_KEY to your .env file."
            if lang == "en" else
            "Gemini कॉन्फ़िगर नहीं है। कृपया .env फ़ाइल में GEMINI_API_KEY जोड़ें।"
        )
    else:
        with st.spinner("Thinking..." if lang == "en" else "सोच रहे हैं..."):
            _do_ask(query)
        st.rerun()

# ── Clear chat button ─────────────────────────────────────────────────────────

if st.session_state.ai_chat_history:
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    if st.button(
        "🗑  Clear conversation" if lang == "en" else "🗑  बातचीत साफ़ करें",
        use_container_width=False,
    ):
        st.session_state.ai_chat_history = []
        st.rerun()

# ── Footer note ───────────────────────────────────────────────────────────────

st.markdown(
    '<div style="margin-top:2rem;text-align:center;color:#94A3B8;font-size:.7rem;">'
    'Powered by Google Gemini · Live data from OpenWeatherMap · '
    'API keys are never exposed to the browser'
    '</div>',
    unsafe_allow_html=True,
)
