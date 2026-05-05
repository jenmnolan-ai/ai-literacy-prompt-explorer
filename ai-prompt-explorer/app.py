import streamlit as st
import json
import textstat
import re

# ── Helpers ──────────────────────────────────────────────────────
def tip(word, definition):
    return (
        f'<span class="vocab-tip" tabindex="0" role="button"'
        f' aria-label="{word}: {definition}">'
        f'{word}'
        f'<span class="tiptext" role="tooltip">{definition}</span>'
        f'</span>'
    )

TIPS = {
    "prompt":        "A question or instruction you give an AI to tell it what to do",
    "prompts":       "Questions or instructions you give an AI to tell it what to do",
    "identify":      "To find, spot, or name something",
    "bias":          "When something is unfair and treats some people better or worse than others",
    "biases":        "Ways something can be unfair to some people more than others",
    "assumption":    "Something you think is true without checking first",
    "assumptions":   "Things you think are true without checking first",
    "stereotype":    "A fixed idea about a group of people that is often unfair or not true",
    "access":        "Being able to get or use something",
    "equity":        "Making sure everyone gets what they need to be treated fairly",
    "responsible":   "Making good choices that think about how others are affected",
    "reflection":    "Stopping to think carefully about what you learned and could do better",
    "hallucination": "When an AI makes up facts that sound real but are actually wrong",
}

font_size_map = {
    "Standard":       "16px",
    "Larger Text":    "20px",
    "Very Large Text":"25px",
}
bg_color_map = {
    "Default":    "#ffffff",
    "Soft Green": "#e8f5e9",
    "Soft Cream": "#fff8e1",
}

# ── Session state defaults ────────────────────────────────────────
if "font_choice" not in st.session_state:
    st.session_state.font_choice = "Larger Text"
if "bg_choice" not in st.session_state:
    st.session_state.bg_choice = "Default"
if "explored_scenarios" not in st.session_state:
    st.session_state.explored_scenarios = set()
if "checked_scenarios" not in st.session_state:
    st.session_state.checked_scenarios = set()
if "quote_index" not in st.session_state:
    st.session_state.quote_index = 0

font_size = font_size_map[st.session_state.font_choice]
bg_color  = bg_color_map[st.session_state.bg_choice]

# ── Global CSS ────────────────────────────────────────────────────
st.markdown(f"""
<style>

/* ════════════════════════════════════════════
   BANNER TYPOGRAPHY — fixed sizes, independent of Display Supports
   ════════════════════════════════════════════ */
.banner-title {{
    font-size: 3.2rem !important;
}}
.banner-sub {{
    font-size: 1.55rem !important;
    font-weight: 400;
}}
@media (max-width: 900px) {{
    .banner-title {{ font-size: 2.6rem !important; }}
    .banner-sub   {{ font-size: 1.35rem !important; }}
}}
@media (max-width: 600px) {{
    .banner-title {{ font-size: 2rem !important; }}
    .banner-sub   {{ font-size: 1.15rem !important; }}
}}

/* ════════════════════════════════════════════
   PART 3 · OUTER FRAME — always gray, never changes
   ════════════════════════════════════════════ */
.stApp {{
    background-color: #f0f2f6 !important;
}}
section[data-testid="stMain"] {{
    background-color: #f0f2f6 !important;
    padding: 0 !important;
}}

/* ════════════════════════════════════════════
   CONTENT CARD — bg_color fills the whole card
   Default=white · Soft Green=#e8f5e9 · Soft Cream=#fff8e1
   ════════════════════════════════════════════ */
div[data-testid="stMainBlockContainer"] {{
    background: {bg_color} !important;
    border-radius: 16px;
    box-shadow: 0 2px 18px rgba(0,0,0,0.08);
    padding: 28px 36px 48px 36px !important;
    max-width: 1180px !important;
    margin: 16px auto 24px auto !important;
}}

/* Left column is transparent — card color shows through */
div[data-testid="column"]:nth-child(1) {{
    background-color: transparent;
    border-radius: 8px;
    padding: 0.5rem 1rem 1.5rem 1rem !important;
}}

/* ════════════════════════════════════════════
   BODY TEXT SCALING
   ════════════════════════════════════════════ */
section[data-testid="stMain"] p,
section[data-testid="stMain"] li,
section[data-testid="stMain"] .stMarkdown p,
section[data-testid="stMain"] .stMarkdown li {{
    font-size: {font_size} !important;
    line-height: 1.75 !important;
}}

section[data-testid="stMain"] h3 {{
    font-size: calc({font_size} * 1.25) !important;
    margin-top: 1.2rem !important;
    margin-bottom: 0.25rem !important;
    color: #2c3e50;
}}

section[data-testid="stMain"] h1 {{
    font-size: 1.9rem !important;
    margin-bottom: 0.25rem !important;
}}

section[data-testid="stMain"] h4 {{
    font-size: calc({font_size} * 1.05) !important;
    margin-top: 0.75rem !important;
    margin-bottom: 0.3rem !important;
}}

/* ════════════════════════════════════════════
   INPUTS & SELECTS SCALING
   ════════════════════════════════════════════ */
div[data-testid="stSelectbox"] label {{
    font-size: {font_size} !important;
    margin-top: 0.6rem !important;
}}
/* Selectbox outer container — height grows with font */
div[data-baseweb="select"] > div {{
    height: auto !important;
    min-height: calc({font_size} * 2.4) !important;
    padding-top: 0.35rem !important;
    padding-bottom: 0.35rem !important;
    align-items: center !important;
}}
/* Inner value + icon row */
div[data-baseweb="select"] > div > div {{
    height: auto !important;
    line-height: 1.5 !important;
}}
div[data-baseweb="select"] span,
div[data-baseweb="select"] div,
div[data-baseweb="select"] input {{
    font-size: {font_size} !important;
    line-height: 1.5 !important;
}}
ul[data-baseweb="menu"] li,
ul[data-baseweb="menu"] li span,
[data-baseweb="menu"] * {{
    font-size: {font_size} !important;
}}
div[data-baseweb="popover"] li,
div[data-baseweb="popover"] span {{
    font-size: {font_size} !important;
}}
div.vocab-hint {{
    font-size: {font_size} !important;
}}
section[data-testid="stMain"] textarea {{
    font-size: {font_size} !important;
    line-height: 1.7 !important;
}}
div[data-testid="stTextArea"] label {{
    font-size: {font_size} !important;
    margin-top: 0.5rem !important;
}}
details summary p,
details summary span,
section[data-testid="stMain"] details summary {{
    font-size: {font_size} !important;
    font-weight: 600;
}}

/* ════════════════════════════════════════════
   PART 1 · BUTTONS — scale with font, no fixed height
   ════════════════════════════════════════════ */
section[data-testid="stMain"] .stButton > button {{
    height: auto !important;
    min-height: 2.25rem;
    padding: 0.45rem 1rem !important;
    font-size: {font_size} !important;
    line-height: 1.5 !important;
    white-space: nowrap;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}}

/* ════════════════════════════════════════════
   RIGHT COLUMN
   ════════════════════════════════════════════ */
div[data-testid="column"]:nth-child(2) label {{
    font-size: 0.92rem !important;
}}
div[data-testid="column"]:nth-child(2) {{
    padding-left: 6px !important;
}}
div[data-testid="column"]:nth-child(2) > div:first-child {{
    background: #f7f9fc !important;
    border: 1px solid #dde3ec;
    border-radius: 12px;
    padding: 1.1rem 1.1rem 1.4rem !important;
    margin-top: 0.6rem !important;
}}
div[data-testid="column"]:nth-child(2) hr {{
    margin: 1rem 0 0.75rem 0 !important;
}}

/* ════════════════════════════════════════════
   VOCAB TOOLTIP
   ════════════════════════════════════════════ */
.vocab-tip {{
    background-color: #fef9c3;
    border-bottom: 1px dotted #888;
    cursor: help;
    position: relative;
    display: inline;
    padding: 0 1px;
}}
.vocab-tip .tiptext {{
    visibility: hidden;
    opacity: 0;
    background-color: #1e293b;
    color: #f8fafc;
    font-size: 0.8em;
    line-height: 1.45;
    text-align: left;
    border-radius: 7px;
    padding: 6px 10px;
    position: absolute;
    z-index: 9999;
    bottom: 130%;
    left: 50%;
    transform: translateX(-50%);
    white-space: nowrap;
    transition: opacity 0.15s ease;
    pointer-events: none;
    box-shadow: 0 2px 8px rgba(0,0,0,0.18);
}}
.vocab-tip:hover .tiptext,
.vocab-tip:focus .tiptext,
.vocab-tip:focus-within .tiptext {{
    visibility: visible;
    opacity: 1;
}}
.vocab-tip:focus-visible {{
    outline: 2px solid #1976d2;
    border-radius: 3px;
    outline-offset: 2px;
}}

/* ════════════════════════════════════════════
   PART 4 · SPACING
   ════════════════════════════════════════════ */
hr {{
    margin: 0.75rem 0 1.1rem 0;
    border-color: #e2e8f0;
}}
div[data-testid="stMainBlockContainer"] > div > div > div[data-testid="column"]:nth-child(1) > div > div:first-child {{
    margin-bottom: 0.6rem;
}}

/* ════════════════════════════════════════════
   RESPONSIVE — stack on small screens
   ════════════════════════════════════════════ */
@media (max-width: 760px) {{
    div[data-testid="stMainBlockContainer"] {{
        padding: 16px 12px 32px 12px !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        margin: 0 !important;
    }}
    div[data-testid="column"] {{
        width: 100% !important;
        flex: 100% !important;
    }}
    div[data-testid="column"]:nth-child(1) {{
        border-radius: 8px;
    }}
    div[data-testid="column"]:nth-child(2) > div:first-child {{
        margin-top: 1.5rem;
        border-radius: 10px;
    }}
}}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────
_network_svg = (
    '<svg aria-hidden="true" focusable="false"'
    ' style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;"'
    ' viewBox="0 0 1000 165" preserveAspectRatio="xMidYMid slice"'
    ' xmlns="http://www.w3.org/2000/svg">'
    '<defs>'
    '<filter id="hdr-glow" x="-80%" y="-80%" width="260%" height="260%">'
    '<feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur"/>'
    '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
    '</filter>'
    '<linearGradient id="txt-scrim" x1="0%" y1="0%" x2="100%" y2="0%">'
    '<stop offset="0%"   stop-color="#1a237e" stop-opacity="0.72"/>'
    '<stop offset="42%"  stop-color="#1a237e" stop-opacity="0.48"/>'
    '<stop offset="62%"  stop-color="#1a237e" stop-opacity="0.10"/>'
    '<stop offset="100%" stop-color="#1a237e" stop-opacity="0"/>'
    '</linearGradient>'
    '</defs>'
    '<g stroke="rgba(197,202,233,0.13)" stroke-width="1" fill="none">'
    '<line x1="48" y1="30" x2="95" y2="85"/>'
    '<line x1="48" y1="30" x2="195" y2="50"/>'
    '<line x1="95" y1="85" x2="145" y2="128"/>'
    '<line x1="95" y1="85" x2="195" y2="50"/>'
    '<line x1="145" y1="128" x2="310" y2="140"/>'
    '<line x1="195" y1="50" x2="340" y2="25"/>'
    '<line x1="195" y1="50" x2="310" y2="140"/>'
    '<line x1="340" y1="25" x2="430" y2="108"/>'
    '<line x1="340" y1="25" x2="510" y2="38"/>'
    '<line x1="430" y1="108" x2="510" y2="38"/>'
    '<line x1="430" y1="108" x2="505" y2="148"/>'
    '<line x1="510" y1="38" x2="615" y2="22"/>'
    '<line x1="510" y1="38" x2="580" y2="100"/>'
    '<line x1="580" y1="100" x2="505" y2="148"/>'
    '<line x1="580" y1="100" x2="660" y2="130"/>'
    '<line x1="615" y1="22" x2="700" y2="18"/>'
    '<line x1="615" y1="22" x2="660" y2="130"/>'
    '<line x1="700" y1="18" x2="780" y2="55"/>'
    '<line x1="700" y1="18" x2="800" y2="105"/>'
    '<line x1="780" y1="55" x2="800" y2="105"/>'
    '<line x1="780" y1="55" x2="900" y2="35"/>'
    '<line x1="800" y1="105" x2="870" y2="138"/>'
    '<line x1="900" y1="35" x2="960" y2="90"/>'
    '<line x1="870" y1="138" x2="960" y2="90"/>'
    '<line x1="310" y1="140" x2="505" y2="148"/>'
    '<line x1="660" y1="130" x2="870" y2="138"/>'
    '</g>'
    '<g fill="rgba(197,202,233,0.08)">'
    '<circle cx="510" cy="38" r="14"/>'
    '<circle cx="780" cy="55" r="14"/>'
    '<circle cx="580" cy="100" r="10"/>'
    '</g>'
    '<g fill="rgba(197,202,233,0.22)">'
    '<circle cx="48" cy="30" r="3"/>'
    '<circle cx="95" cy="85" r="3"/>'
    '<circle cx="145" cy="128" r="3"/>'
    '<circle cx="195" cy="50" r="2.5"/>'
    '<circle cx="310" cy="140" r="3"/>'
    '<circle cx="340" cy="25" r="2.5"/>'
    '<circle cx="430" cy="108" r="3"/>'
    '<circle cx="505" cy="148" r="3"/>'
    '<circle cx="615" cy="22" r="3"/>'
    '<circle cx="660" cy="130" r="3"/>'
    '<circle cx="700" cy="18" r="3"/>'
    '<circle cx="800" cy="105" r="3"/>'
    '<circle cx="870" cy="138" r="3"/>'
    '<circle cx="900" cy="35" r="3"/>'
    '<circle cx="960" cy="90" r="3"/>'
    '</g>'
    '<g fill="rgba(220,225,255,0.75)" filter="url(#hdr-glow)">'
    '<circle cx="510" cy="38" r="4.5"/>'
    '<circle cx="780" cy="55" r="4.5"/>'
    '<circle cx="580" cy="100" r="3.5"/>'
    '<circle cx="660" cy="130" r="3"/>'
    '<circle cx="900" cy="35" r="3"/>'
    '</g>'
    '<rect x="0" y="0" width="1000" height="165" fill="url(#txt-scrim)"/>'
    '</svg>'
)

st.markdown(
    '<div role="banner" style="'
    'position:relative;overflow:hidden;'
    'background:linear-gradient(135deg,#1a237e 0%,#283593 55%,#3949ab 100%);'
    'border-radius:12px;padding:38px 36px 32px 36px;margin-bottom:32px;">'
    + _network_svg +
    '<div style="position:relative;z-index:1;">'
    '<div class="banner-title" role="heading" aria-level="1" style="'
    'font-weight:800;color:#ffffff;'
    'letter-spacing:-0.5px;line-height:1.15;'
    'text-shadow:0 2px 10px rgba(0,0,0,0.4);">'
    '🤖 AI Literacy Prompt Explorer'
    '</div>'
    '<div class="banner-sub" style="color:#e8eaf6;margin-top:14px;'
    'line-height:1.5;max-width:700px;'
    'text-shadow:0 1px 6px rgba(0,0,0,0.25);">'
    'Learn how prompts shape AI outputs \u2014 and how to make them more inclusive, accurate, and useful.'
    '</div>'
    '<div style="margin-top:20px;font-size:1.5rem;letter-spacing:5px;opacity:0.65;">'
    '💬 &nbsp; 🧠 &nbsp; ⚖️ &nbsp; 🌍 &nbsp; 🎯'
    '</div>'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Progress tracker ───────────────────────────────────────────────
_total = 12
_explored = len(st.session_state.explored_scenarios)
_checked  = len(st.session_state.checked_scenarios)
_pct = int((_explored / _total) * 100)
st.markdown(
    f"""<div style="display:flex;align-items:center;gap:18px;margin-bottom:28px;flex-wrap:wrap;">
    <span style="font-size:0.95rem;color:#555;">
        📖 <strong>Scenarios explored:</strong> {_explored} / {_total}
    </span>
    <span style="font-size:0.95rem;color:#555;">
        ✅ <strong>Check My Thinking completed:</strong> {_checked} / {_total}
    </span>
    <div role="progressbar" aria-valuenow="{_pct}" aria-valuemin="0" aria-valuemax="100"
         aria-label="Scenarios explored: {_explored} of {_total} ({_pct}%)"
         style="flex:1;min-width:120px;background:#e0e0e0;border-radius:999px;height:8px;overflow:hidden;">
        <div style="width:{_pct}%;background:#3949ab;height:100%;border-radius:999px;transition:width 0.4s;"></div>
    </div>
    </div>""",
    unsafe_allow_html=True,
)

# ── Two-column layout ─────────────────────────────────────────────
col_main, col_support = st.columns([0.65, 0.35], gap="large")

# ════════════════════════════════════════════
# RIGHT: Support Panel
# ════════════════════════════════════════════
with col_support:
    with st.expander("👓 Display Supports"):
        st.radio(
            "Text Size",
            options=["Standard", "Larger Text", "Very Large Text"],
            key="font_choice",
        )
        st.radio(
            "Background",
            options=["Default", "Soft Green", "Soft Cream"],
            key="bg_choice",
        )

    st.markdown("""
<div class="vocab-hint" style="
    background:#e3f2fd;
    border-left:4px solid #1976d2;
    border-radius:6px;
    padding:8px 12px;
    margin:4px 0 6px 0;
    color:#0d47a1;
    line-height:1.4;
">
💡 Need help with a word? Open <strong>📘 Word Help</strong> below.
</div>
""", unsafe_allow_html=True)

    with st.expander("📘 Word Help"):
        st.markdown(f"""
**{tip("Prompt", TIPS["prompt"])}** — What you type or ask an AI.

**{tip("Identify", TIPS["identify"])}** — To find or spot something.

**{tip("Bias", TIPS["bias"])}** — When something treats people unfairly.

**{tip("Assumption", TIPS["assumption"])}** — A belief without checking.

**{tip("Stereotype", TIPS["stereotype"])}** — A fixed, often unfair idea about a group.

**{tip("Access", TIPS["access"])}** — Being able to use or get something.

**{tip("Equity", TIPS["equity"])}** — Everyone gets what they need to be fair.

**{tip("Responsible", TIPS["responsible"])}** — Choices that think about others.

**{tip("Reflection", TIPS["reflection"])}** — Thinking carefully about what you learned.

**{tip("Hallucination", TIPS["hallucination"])}** — When AI makes up facts that aren't true.
""", unsafe_allow_html=True)

    with st.expander("🧑‍🏫 Teacher Tools"):
        st.markdown("**Readability Analysis** *(not visible to students)*")
        # Load scenarios here for teacher panel (reuse after left col loads)
        with open("ai-prompt-explorer/data/scenarios.json") as f:
            _scenarios = json.load(f)
        _scenario_names = [s["scenario"] for s in _scenarios]
        _teacher_choice = st.selectbox(
            "Select scenario to analyse:",
            _scenario_names,
            key="teacher_scenario_select",
            label_visibility="collapsed",
        )
        _selected = next(s for s in _scenarios if s["scenario"] == _teacher_choice)
        _combined = _selected["prompt"].rstrip(".") + ". " + _selected["issue"].rstrip(".") + "."
        _grade = textstat.flesch_kincaid_grade(_combined)

        def _flag_hard_words(text):
            words = re.findall(r"[a-zA-Z]+", text)
            hard, seen = [], set()
            for word in words:
                lower = word.lower()
                if lower not in seen and textstat.syllable_count(lower) >= 3:
                    hard.append(word)
                    seen.add(lower)
            return hard

        _hard = _flag_hard_words(_combined)

        if _grade <= 4:
            st.success(f"Grade level: {_grade:.1f} — Suitable for 4th grade and below.")
        elif _grade <= 6:
            st.warning(f"Grade level: {_grade:.1f} — May challenge some students.")
        else:
            st.error(f"Grade level: {_grade:.1f} — Consider simplifying for younger readers.")

        if _hard:
            st.markdown("**Words with 3+ syllables:**")
            st.write(", ".join(_hard))
        else:
            st.write("No long words found.")

    # ── AI in the Real World ──────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🎬 AI in the Real World")
    st.markdown(
        '<p style="font-size:0.88rem;color:#555;margin:-4px 0 8px 0;">'
        'Short videos to learn more about AI and bias.</p>',
        unsafe_allow_html=True,
    )

    _VIDEOS = [
        {
            "id":    "nXurp5s7n6c",
            "url":   "https://www.youtube.com/watch?v=nXurp5s7n6c",
            "label": "How AI can encode and amplify bias in the real world.",
        },
        {
            "id":    "O1ZhWv84eWE",
            "url":   "https://www.youtube.com/watch?v=O1ZhWv84eWE",
            "label": "How robots are being designed to learn, collaborate, and interact with humans.",
        },
        {
            "id":    "QvRZuHQBTps",
            "url":   "https://www.youtube.com/watch?v=QvRZuHQBTps",
            "label": "What happens when AI doesn't recognise all faces equally.",
        },
    ]
    for v in _VIDEOS:
        thumb = f"https://img.youtube.com/vi/{v['id']}/mqdefault.jpg"
        st.markdown(
            f'<a href="{v["url"]}" target="_blank" rel="noopener noreferrer"'
            f' style="display:block;text-decoration:none;margin-bottom:12px;">'
            f'<div style="border-radius:8px;overflow:hidden;border:1px solid #dde3ec;'
            f'box-shadow:0 1px 4px rgba(0,0,0,0.08);max-width:88%;">'
            f'<img src="{thumb}" alt="Video thumbnail" loading="lazy"'
            f' style="width:100%;display:block;aspect-ratio:16/9;object-fit:cover;"/>'
            f'</div>'
            f'<p style="font-size:0.82rem;color:#444;margin:4px 0 0 1px;'
            f'line-height:1.4;max-width:88%;">{v["label"]}</p>'
            f'</a>',
            unsafe_allow_html=True,
        )

    # ── Voices in AI ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 💬 Voices in AI")

    _QUOTES = [
        {"text": "AI should help people see more possibilities, not fewer.",
         "name": "Jennifer Nolan"},
        {"text": "Artificial intelligence is not a substitute for human intelligence; it is a tool to amplify it.",
         "name": "Fei-Fei Li"},
        {"text": "We need to make sure AI works for everyone.",
         "name": "Tim Berners-Lee"},
        {"text": "The question is not what AI can do, but what it should do.",
         "name": "Stuart Russell"},
        {"text": "Creativity grows when different kinds of minds are included.",
         "name": "AI learning principle"},
        {"text": "A good prompt gives AI better directions. A good thinker checks the answer.",
         "name": "AI literacy principle"},
        {"text": "Technology is strongest when it helps more people participate.",
         "name": "Accessibility principle"},
        {"text": "If an answer seems too narrow, ask what voices or examples might be missing.",
         "name": "AI bias awareness principle"},
    ]
    _qi = st.session_state.quote_index % len(_QUOTES)
    _q  = _QUOTES[_qi]
    st.markdown(
        f'<div style="'
        f'background:linear-gradient(135deg,#1a237e 0%,#3949ab 100%);'
        f'border-radius:10px;padding:14px 16px 14px 16px;margin-bottom:8px;">'
        f'<p style="color:#e8eaf6;font-size:0.92rem;line-height:1.6;'
        f'font-style:italic;margin:0 0 10px 0;">'
        f'&#8220;{_q["text"]}&#8221;'
        f'</p>'
        f'<p style="color:#c5cae9;font-size:0.80rem;margin:0;font-weight:600;">'
        f'— {_q["name"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button("🔁 New Quote", key="next_quote", use_container_width=True):
        st.session_state.quote_index += 1
        st.rerun()

    # ── See It Differently ────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 👁️ See It Differently")
    st.markdown(
        '<p style="font-size:0.88rem;color:#555;margin:-4px 0 8px 0;line-height:1.4;">'
        'Look at this group of people. <strong>Who might be missing?</strong></p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<svg aria-label="A group of person silhouettes — some shown as solid shapes and some as dotted outlines, suggesting missing or overlooked people."'
        ' role="img" viewBox="0 0 220 80" xmlns="http://www.w3.org/2000/svg"'
        ' style="width:100%;max-width:260px;display:block;margin:0 auto 8px auto;">'
        '<defs>'
        '<style>'
        '.p-solid{fill:#3949ab;opacity:0.85;}'
        '.p-ghost{fill:none;stroke:#3949ab;stroke-width:1.5;stroke-dasharray:3,2;opacity:0.45;}'
        '</style>'
        '</defs>'
        '<g class="p-solid">'
        '<circle cx="22" cy="16" r="7"/><rect x="15" y="25" width="14" height="18" rx="4"/>'
        '<circle cx="55" cy="16" r="7"/><rect x="48" y="25" width="14" height="18" rx="4"/>'
        '<circle cx="110" cy="16" r="7"/><rect x="103" y="25" width="14" height="18" rx="4"/>'
        '<circle cx="165" cy="16" r="7"/><rect x="158" y="25" width="14" height="18" rx="4"/>'
        '</g>'
        '<g class="p-ghost">'
        '<circle cx="88" cy="16" r="7"/><rect x="81" y="25" width="14" height="18" rx="4"/>'
        '<circle cx="143" cy="16" r="7"/><rect x="136" y="25" width="14" height="18" rx="4"/>'
        '<circle cx="198" cy="16" r="7"/><rect x="191" y="25" width="14" height="18" rx="4"/>'
        '</g>'
        '<text x="110" y="62" text-anchor="middle" font-size="9" fill="#555" font-family="sans-serif">'
        'Solid = included &nbsp;&nbsp; Dotted = often left out'
        '</text>'
        '<line x1="10" y1="68" x2="210" y2="68" stroke="#dde3ec" stroke-width="0.5"/>'
        '<text x="110" y="78" text-anchor="middle" font-size="8.5" fill="#888" font-family="sans-serif">'
        'Who might an AI trained on this group overlook?'
        '</text>'
        '</svg>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="background:#f0f4ff;border-left:3px solid #3949ab;'
        'border-radius:6px;padding:8px 12px;font-size:0.84rem;color:#333;line-height:1.5;">'
        '🔍 <strong>Think:</strong> If an AI was only trained on the solid figures above, '
        'what kinds of people or needs might it miss?'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Decorative: Vague Prompt vs Clear Prompt ─────────────────
    st.markdown("---")
    st.markdown(
        '<svg aria-hidden="true" focusable="false" '
        'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 240" '
        'style="width:100%;max-width:260px;display:block;margin:4px auto 2px auto;">'

        # ── Left: tangled lines = vague prompt ──
        '<path stroke="#bccde6" stroke-width="1.4" fill="none" opacity="0.7" '
        'd="M10,30 L52,15 L34,58 L84,42 L64,82 L108,68"/>'
        '<path stroke="#bccde6" stroke-width="1.4" fill="none" opacity="0.7" '
        'd="M18,102 L68,90 L46,132 L96,120 L74,160 L112,146"/>'
        '<path stroke="#bccde6" stroke-width="1.4" fill="none" opacity="0.7" '
        'd="M10,178 L50,166 L30,205 L82,198"/>'
        '<line stroke="#c8d8ee" stroke-width="1.2" opacity="0.55" x1="66" y1="48" x2="22" y2="102"/>'
        '<line stroke="#c8d8ee" stroke-width="1.2" opacity="0.55" x1="90" y1="94" x2="42" y2="152"/>'
        '<circle fill="#adbfe0" opacity="0.65" cx="10"  cy="30"  r="2.5"/>'
        '<circle fill="#adbfe0" opacity="0.65" cx="52"  cy="15"  r="2.5"/>'
        '<circle fill="#adbfe0" opacity="0.65" cx="84"  cy="42"  r="2.5"/>'
        '<circle fill="#adbfe0" opacity="0.65" cx="108" cy="68"  r="2.5"/>'
        '<circle fill="#adbfe0" opacity="0.65" cx="18"  cy="102" r="2.5"/>'
        '<circle fill="#adbfe0" opacity="0.65" cx="96"  cy="120" r="2.5"/>'
        '<circle fill="#adbfe0" opacity="0.65" cx="112" cy="146" r="2.5"/>'
        '<circle fill="#adbfe0" opacity="0.65" cx="82"  cy="198" r="2.5"/>'
        '<circle fill="#adbfe0" opacity="0.55" cx="66"  cy="48"  r="2"/>'
        '<circle fill="#adbfe0" opacity="0.55" cx="22"  cy="102" r="2"/>'
        '<circle fill="#adbfe0" opacity="0.55" cx="90"  cy="94"  r="2"/>'
        '<circle fill="#adbfe0" opacity="0.55" cx="42"  cy="152" r="2"/>'

        # ── Divider ──
        '<line x1="130" y1="12" x2="130" y2="228" stroke="#d6e2f0" '
        'stroke-width="1.5" stroke-dasharray="5,4"/>'

        # ── Right: clean hierarchy = clear prompt ──
        '<line stroke="#7da4e0" stroke-width="1.5" opacity="0.85" x1="200" y1="22"  x2="172" y2="85"/>'
        '<line stroke="#7da4e0" stroke-width="1.5" opacity="0.85" x1="200" y1="22"  x2="228" y2="85"/>'
        '<line stroke="#7da4e0" stroke-width="1.5" opacity="0.85" x1="172" y1="85"  x2="152" y2="152"/>'
        '<line stroke="#7da4e0" stroke-width="1.5" opacity="0.85" x1="172" y1="85"  x2="200" y2="152"/>'
        '<line stroke="#7da4e0" stroke-width="1.5" opacity="0.85" x1="228" y1="85"  x2="200" y2="152"/>'
        '<line stroke="#7da4e0" stroke-width="1.5" opacity="0.85" x1="228" y1="85"  x2="248" y2="152"/>'
        '<line stroke="#7da4e0" stroke-width="1.5" opacity="0.85" x1="152" y1="152" x2="168" y2="218"/>'
        '<line stroke="#7da4e0" stroke-width="1.5" opacity="0.85" x1="248" y1="152" x2="232" y2="218"/>'
        '<line stroke="#7da4e0" stroke-width="1.5" opacity="0.85" x1="168" y1="218" x2="232" y2="218"/>'
        '<circle fill="#5c8fd4" opacity="0.9"  cx="200" cy="22"  r="5.5"/>'
        '<circle fill="#6f9edc" opacity="0.88" cx="172" cy="85"  r="4"/>'
        '<circle fill="#6f9edc" opacity="0.88" cx="228" cy="85"  r="4"/>'
        '<circle fill="#8fb2e8" opacity="0.85" cx="152" cy="152" r="3.2"/>'
        '<circle fill="#8fb2e8" opacity="0.85" cx="200" cy="152" r="3.2"/>'
        '<circle fill="#8fb2e8" opacity="0.85" cx="248" cy="152" r="3.2"/>'
        '<circle fill="#a5c4f0" opacity="0.82" cx="168" cy="218" r="2.5"/>'
        '<circle fill="#a5c4f0" opacity="0.82" cx="232" cy="218" r="2.5"/>'

        '</svg>',
        unsafe_allow_html=True,
    )

# ════════════════════════════════════════════
# LEFT: Main Learning Content
# ════════════════════════════════════════════
with col_main:
    st.markdown(
        "Explore how AI responses can change based on "
        + tip("prompts", TIPS["prompts"])
        + ", and "
        + tip("identify", TIPS["identify"])
        + " potential "
        + tip("bias", TIPS["bias"])
        + " or issues.",
        unsafe_allow_html=True,
    )

    st.markdown("")
    from pathlib import Path

    SCENARIOS_PATH = Path(__file__).parent / "data" / "scenarios.json"

    with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    scenario_names = [s["scenario"] for s in scenarios]

    choice = st.selectbox(
        "Choose a scenario:",
        scenario_names,
        help="A scenario is a real-life situation. Pick one to explore how AI might respond to it."
    )

    selected = next(s for s in scenarios if s["scenario"] == choice)

    st.markdown("### " + tip("Prompt", TIPS["prompt"]), unsafe_allow_html=True)
    st.write(selected["prompt"])

    # ── "So What?" takeaways — one per scenario ──────────────────
    SO_WHAT = {
        "Video Game Character Design": {
            "body": (
                "AI tends to create heroes that look like the ones it has seen most — "
                "which often means the same body type, background, and abilities over and over. "
                "But real heroes come in every shape, culture, and ability. "
                "When games show a wider range of characters, more players feel like they belong in the story."
            ),
            "action": "Next time you use AI, ask: Who is missing from this design — and what would change if the hero looked more like people in my community?",
        },
        "School Dress Code": {
            "body": (
                "AI often writes dress codes based on rules it has seen most — and those rules can unfairly target certain students. "
                "Fair dress codes explain their purpose and respect every student's identity and culture. "
                "When rules work for everyone, all students feel welcome."
            ),
            "action": "Next time you use AI, ask: Do these rules apply equally to all students, and do they respect every student's identity?",
        },
        "Sneaker Brand Marketing": {
            "body": (
                "AI builds ads from patterns it has seen — which often feature only certain body types and expensive lifestyles. "
                "That leaves most students out of the story. "
                "Inclusive ads send a clear message: this product is made for everyone."
            ),
            "action": "Next time you use AI, ask: Who is shown in this ad, and who is left out? Would every student feel included?",
        },
        "Music Recommendation System": {
            "body": (
                "AI music recommendations often reflect the most popular streaming data — which skews toward a small number of languages and countries. "
                "Every student's musical background matters. "
                "A truly helpful recommendation asks about your taste first, then suggests."
            ),
            "action": "Next time you use AI, ask: Does this recommendation reflect my actual taste and background, or just what's most popular on one platform?",
        },
        "School Discipline": {
            "body": (
                "The words used to describe a student's behavior can shape how they are treated — and AI can repeat unfair patterns from old school records. "
                "Describing behavior without making assumptions protects students from bias. "
                "Language matters more than most people realize."
            ),
            "action": "Next time you use AI, ask: Does this description make assumptions about who the student is, or does it stick to what actually happened?",
        },
        "Access to Technology": {
            "body": (
                "AI often designs systems that assume everyone has fast internet and a device at home — because that's what most of its training data reflects. "
                "Millions of students don't have that. "
                "Fair systems include everyone from the very start."
            ),
            "action": "Next time you use AI, ask: Does this design work for students without reliable internet or devices at home?",
        },
        "Student Voice in School Decisions": {
            "body": (
                "When AI writes school plans, it often leaves students out — because formal policy documents rarely include student voices. "
                "Rules made without student input often miss what students actually need. "
                "Your voice in school decisions is not just welcome — it's essential."
            ),
            "action": "Next time you use AI, ask: Does this plan include student input, or was it written only from an adult perspective?",
        },
        "Environmental Impact (NGSS)": {
            "body": (
                "AI environmental suggestions often focus on expensive solutions because that's what appears most in the sources it learned from. "
                "Low-cost, community-based actions can be just as powerful — and they're available to everyone. "
                "Real change often starts right in your own neighborhood."
            ),
            "action": "Next time you use AI, ask: Are these suggestions only for people with money, or can students in any neighborhood take these actions?",
        },
        "Coding & AI Systems": {
            "body": (
                "AI learning tools are often designed around speed and scores, because that's how most educational data measures success. "
                "But learning looks different for every student. "
                "A truly fair tool meets each learner where they are — not just where the data says they should be."
            ),
            "action": "Next time you use AI, ask: Does this tool work for students who learn differently, and does it measure more than just speed?",
        },
        "Disability & Accessibility": {
            "body": (
                "AI tends to design spaces based on what it has seen most — and most spaces in its training data were not built with accessibility in mind. "
                "Designing for everyone from the start, not as an afterthought, is what real inclusion looks like. "
                "When a space works for everyone, everyone benefits."
            ),
            "action": "Next time you use AI, ask: Does this design include everyone from the beginning, or are accessibility features added on at the end?",
        },
        "Social Media Trends": {
            "body": (
                "AI describes online popularity based on what social media platforms amplify most — followers, looks, and money. "
                "But influence can also look like kindness, creativity, and community. "
                "You get to decide what influence and connection mean to you."
            ),
            "action": "Next time you use AI, ask: Is this description of popularity realistic, or does it leave out the ways I actually connect with others?",
        },
        "Fairness in School Rules": {
            "body": (
                "AI often defines fairness as treating everyone exactly the same — but equity means giving each student what they actually need. "
                "Equal isn't always fair. "
                "The best rules help everyone succeed, not just those who already have advantages."
            ),
            "action": "Next time you use AI, ask: Does this rule treat everyone the same, or does it give each student what they need to succeed?",
        },
    }

    # Load scenarios
from pathlib import Path
SCENARIOS_PATH = Path(__file__).parent / "data" / "scenarios.json"

with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
    scenarios = json.load(f)

scenario_names = [s["scenario"] for s in scenarios]
choice = st.selectbox(
        "Choose a scenario:",
        scenario_names,
        help="A scenario is a real-life situation. Pick one to explore how AI might respond to it."
    )
selected = next(s for s in scenarios if s["scenario"] == choice)



st.markdown("### " + tip("Prompt", TIPS["prompt"]), unsafe_allow_html=True)
st.write(selected["prompt"])

    st.markdown("### Think About It")
    st.markdown(
        "What "
        + tip("assumptions", TIPS["assumptions"])
        + " or "
        + tip("biases", TIPS["biases"])
        + " might this "
        + tip("prompt", TIPS["prompt"])
        + " create?",
        unsafe_allow_html=True,
    )
    st.markdown(
        "How could this lead to "
        + tip("bias", TIPS["bias"])
        + " or incomplete results?",
        unsafe_allow_html=True,
    )

    st.markdown("### Possible Issue")
    st.write(selected["issue"])

    td = selected.get("training_data", "")
    if td:
        st.markdown(
            f"""<div style="background:#f3e5f5;border-left:4px solid #8e24aa;
            border-radius:8px;padding:12px 16px;margin:10px 0 4px 0;">
            <strong style="color:#6a1b9a;">🧩 Why AI Might Do This</strong>
            <p style="margin:6px 0 0 0;line-height:1.6;color:#333;">{td}</p>
            </div>""",
            unsafe_allow_html=True,
        )

    lm = selected.get("learn_more", {})
    if lm:
        with st.expander("📚 Learn More About This Scenario"):
            st.markdown("**What AI might do**")
            st.write(lm.get("ai_might", ""))
            st.markdown("**Why this can be a problem**")
            st.write(lm.get("why_problem", ""))
            st.markdown("**Try this instead**")
            st.info(lm.get("try_instead", ""))
            st.markdown("**Think about it**")
            st.write("💬 " + lm.get("think_about", ""))

    cmp = selected.get("compare", {})
    if cmp:
        with st.expander("🔍 Compare the Outputs"):
            st.markdown(
                "See how the AI's response changes depending on how specific and inclusive the prompt is.",
                unsafe_allow_html=False,
            )
            col_typ, col_imp = st.columns(2)
            with col_typ:
                st.markdown(
                    f"""<div style="background:#fce4ec;border-left:4px solid #e53935;
                    border-radius:8px;padding:14px 16px;min-height:140px;">
                    <strong style="font-size:1rem;">{cmp.get('typical_label','')}</strong>
                    <p style="margin-top:10px;line-height:1.6;">{cmp.get('typical_text','')}</p>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with col_imp:
                st.markdown(
                    f"""<div style="background:#e8f5e9;border-left:4px solid #43a047;
                    border-radius:8px;padding:14px 16px;min-height:140px;">
                    <strong style="font-size:1rem;">{cmp.get('improved_label','')}</strong>
                    <p style="margin-top:10px;line-height:1.6;">{cmp.get('improved_text','')}</p>
                    </div>""",
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    st.markdown("### Your Turn")

    st.markdown("**What kinds of bias or unfairness might show up here?** *(Choose all that apply)*")

    # Use scenario name in key so checkboxes reset when scenario changes
    sk = choice.replace(" ", "_")
    cb_race     = st.checkbox("Race or culture",                    key=f"cb_race_{sk}")
    cb_gender   = st.checkbox("Gender",                             key=f"cb_gender_{sk}")
    cb_dis      = st.checkbox("Disability or accessibility",        key=f"cb_dis_{sk}")
    cb_money    = st.checkbox("Money or access to resources",       key=f"cb_money_{sk}")
    cb_lang     = st.checkbox("Language or English learner needs",  key=f"cb_lang_{sk}")
    cb_voice    = st.checkbox("Student voice or choice",            key=f"cb_voice_{sk}")
    cb_old      = st.checkbox("Old information affecting new decisions", key=f"cb_old_{sk}")

    selected_bias = [
        label for checked, label in [
            (cb_race,   "Race or culture"),
            (cb_gender, "Gender"),
            (cb_dis,    "Disability or accessibility"),
            (cb_money,  "Money or access to resources"),
            (cb_lang,   "Language or English learner needs"),
            (cb_voice,  "Student voice or choice"),
            (cb_old,    "Old information affecting new decisions"),
        ] if checked
    ]

    st.markdown("")
    explanation = st.text_area(
        "Explain your thinking in 1–2 sentences.",
        key=f"explain_{sk}",
        help="Tell us why you chose those areas. There are no wrong answers!"
    )

    improved_prompt = st.text_area(
        "Rewrite the prompt to make it more fair, specific, or inclusive.",
        key=f"improve_{sk}",
        help="Try to give the AI clearer and fairer directions."
    )

    if st.button("✅ Check My Thinking", key=f"check_{sk}"):
        feedback = []

        # ── Checkbox feedback ──────────────────────────────────────
        if not selected_bias:
            feedback.append("🟡 Try choosing at least one area where bias or unfairness might appear.")
        else:
            feedback.append(f"🟢 Good start! You identified possible bias related to: **{', '.join(selected_bias)}**.")

        # ── Explanation feedback ───────────────────────────────────
        word_count_explain = len(explanation.strip().split())
        if word_count_explain < 6:
            feedback.append("🟡 Add one more detail explaining why this matters. Think about who might be affected and how.")
        elif word_count_explain >= 6:
            feedback.append("🟢 Nice explanation! You thought about why this issue matters.")

        # ── Improved prompt feedback (smarter detection) ───────────
        rw = improved_prompt.strip()
        rw_lower = rw.lower()
        rw_words = set(rw_lower.split())

        if rw == "":
            feedback.append("🟡 Try rewriting the prompt so the AI gets clearer and fairer directions.")
        else:
            signals = []

            # Representation: specific groups named
            identity_terms = {
                "she", "her", "girl", "woman", "female",
                "he", "him", "boy", "man", "male",
                "non-binary", "nonbinary", "they", "transgender",
                "black", "african", "latino", "latina", "latinx",
                "asian", "indigenous", "native", "arab", "middle eastern",
                "disability", "disabled", "wheelchair", "blind", "deaf",
                "neurodivergent", "autistic", "adhd",
                "low-income", "poor", "rural", "urban", "homeless",
                "immigrant", "refugee", "english learner", "bilingual", "multilingual",
                "culture", "cultural", "religion", "religious", "faith",
                "body", "bodies", "size", "weight", "appearance",
                "identity", "expression", "representation", "different identities",
                "elderly", "older", "young", "age",
            }
            if identity_terms & rw_words:
                signals.append("representation")

            # Challenging stereotypes
            stereotype_challenge = [
                "non-traditional", "any gender", "all abilities", "regardless",
                "without assuming", "challenge", "subvert", "break", "beyond",
                "not just", "more than", "instead of", "variety", "diverse",
                "different kinds", "all types", "all backgrounds", "every student",
            ]
            if any(phrase in rw_lower for phrase in stereotype_challenge):
                signals.append("stereotype-challenging")

            # Specificity: is the rewrite meaningfully longer than the original?
            original_words = len(selected["prompt"].split())
            rewrite_words = len(rw.split())
            if rewrite_words >= original_words + 5:
                signals.append("more specific")

            # Inclusion language (broader than before)
            inclusion_patterns = [
                "all students", "every student", "everyone", "inclusive",
                "include", "including", "equity", "equitable", "fair to",
                "regardless of", "no matter", "accessible", "accessibility",
                "different needs", "different backgrounds", "different abilities",
                "multiple", "variety of", "range of", "diverse",
            ]
            if any(phrase in rw_lower for phrase in inclusion_patterns):
                signals.append("inclusive language")

            if len(signals) >= 2:
                feedback.append(
                    "🟢 Strong revision! You are challenging common assumptions and giving the AI more inclusive, "
                    "specific directions. That kind of prompting leads to fairer results."
                )
            elif len(signals) == 1:
                feedback.append(
                    "🟢 Good thinking! Your revised prompt shows improvement. "
                    "See if you can also name specific groups of people or add more detail about who should be included."
                )
            else:
                feedback.append(
                    "🟡 You made a change — that is a good start! Try adding more detail about people, "
                    "identity, or different needs so the AI gives a more inclusive result."
                )

        st.session_state.checked_scenarios.add(choice)
        st.session_state.explored_scenarios.add(choice)
        for msg in feedback:
            st.markdown(msg)

    # ── Improve the Prompt ────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📝 Improve the Prompt")
    st.markdown("**How can you improve this prompt?** *(Choose all that apply)*")

    imp_detail   = st.checkbox("Add more detail",                              key=f"imp_detail_{sk}")
    imp_identity = st.checkbox("Include different identities or experiences",  key=f"imp_identity_{sk}")
    imp_stereo   = st.checkbox("Avoid stereotypes",                            key=f"imp_stereo_{sk}")
    imp_access   = st.checkbox("Include accessibility or different needs",     key=f"imp_access_{sk}")
    imp_clear    = st.checkbox("Give clearer instructions to the AI",          key=f"imp_clear_{sk}")
    imp_culture  = st.checkbox("Include different backgrounds or cultures",    key=f"imp_culture_{sk}")
    imp_voice    = st.checkbox("Include student voice or choice",              key=f"imp_voice_{sk}")
    imp_resources= st.checkbox("Consider access to resources",                 key=f"imp_resources_{sk}")

    selected_strategies = [
        label for checked, label in [
            (imp_detail,    "Add more detail"),
            (imp_identity,  "Include different identities or experiences"),
            (imp_stereo,    "Avoid stereotypes"),
            (imp_access,    "Include accessibility or different needs"),
            (imp_clear,     "Give clearer instructions to the AI"),
            (imp_culture,   "Include different backgrounds or cultures"),
            (imp_voice,     "Include student voice or choice"),
            (imp_resources, "Consider access to resources"),
        ] if checked
    ]

    improved_prompt2 = st.text_area(
        "Rewrite the prompt using at least one idea above.",
        key=f"improve2_{sk}",
        help="Use what you picked above to write a clearer, more inclusive prompt for the AI.",
    )

    if st.button("📝 Check My Prompt", key=f"check_prompt_{sk}"):
        imp_feedback = []

        # Strategy selection check
        if not selected_strategies:
            imp_feedback.append("🟡 Pick at least one strategy above to guide your revision.")
        else:
            imp_feedback.append(
                f"🟢 Good choices! You are using these strategies: **{', '.join(selected_strategies)}**."
            )

        # Prompt rewrite check
        rw2 = improved_prompt2.strip()
        if rw2 == "":
            imp_feedback.append("🟡 Try writing a revised prompt using the strategies you selected.")
        else:
            rw2_lower = rw2.lower()
            rw2_words = set(rw2_lower.split())

            signals2 = []

            identity2 = {
                "she", "her", "girl", "woman", "female", "he", "him", "boy", "man", "male",
                "non-binary", "they", "disability", "disabled", "wheelchair", "blind", "deaf",
                "neurodivergent", "autistic", "low-income", "rural", "urban", "immigrant",
                "refugee", "bilingual", "multilingual", "culture", "cultural", "religion",
                "religious", "body", "bodies", "size", "appearance", "identity", "expression",
                "representation", "elderly", "older", "young", "age", "student", "students",
            }
            if identity2 & rw2_words:
                signals2.append("representation")

            stereo_phrases = [
                "non-traditional", "any gender", "all abilities", "regardless",
                "without assuming", "challenge", "subvert", "beyond", "not just",
                "instead of", "variety", "diverse", "different kinds", "all types",
                "all backgrounds", "every student", "different people", "different experiences",
            ]
            if any(ph in rw2_lower for ph in stereo_phrases):
                signals2.append("stereotype-challenging")

            orig_len = len(selected["prompt"].split())
            if len(rw2.split()) >= orig_len + 5:
                signals2.append("more specific")

            inclusion2 = [
                "all students", "every student", "inclusive", "include", "including",
                "equitable", "fair to", "regardless of", "accessible", "accessibility",
                "different needs", "different backgrounds", "different abilities",
                "multiple", "variety of", "range of", "student voice", "student choice",
                "access to", "resources",
            ]
            if any(ph in rw2_lower for ph in inclusion2):
                signals2.append("inclusive language")

            if len(signals2) >= 2:
                imp_feedback.append(
                    "🟢 Strong revision! You challenged a common assumption and gave the AI "
                    "clearer, more specific directions. That leads to fairer and more useful results."
                )
            elif len(signals2) == 1:
                imp_feedback.append(
                    "🟢 Good work! Your revision shows real improvement. "
                    "See if you can also name specific groups of people, needs, or contexts."
                )
            else:
                imp_feedback.append(
                    "🟡 You made a start! Try including more detail about different people, "
                    "needs, or situations so the AI has clearer and fairer directions."
                )

        for msg in imp_feedback:
            st.markdown(msg)

    pass  # Quick Check and So What? rendered full-width below


# ── Quick Check — full-width three-column section ─────────────────
st.markdown(
    """<style>
    @media (max-width: 700px) {
        .qz-col-wrap { flex-direction: column !important; }
        .qz-col-divider { display: none !important; }
    }
    </style>""",
    unsafe_allow_html=True,
)

_qz_sk = choice.replace(" ", "_")

_QUIZ = [
    {
        "key":     f"quiz_q1_{_qz_sk}",
        "question": "1. Which prompt would likely give a more useful AI response?",
        "options": [
            "A vague prompt with few details",
            "A prompt with clear details and context",
        ],
        "correct": "A prompt with clear details and context",
        "explain_correct":   "Specific details help AI understand exactly what you need, making the response more useful and less likely to rely on assumptions.",
        "explain_incorrect": "Vague prompts leave too much to AI's interpretation, and AI will fill the gaps using patterns from its training data — which may not match what you actually need.",
    },
    {
        "key":     f"quiz_q2_{_qz_sk}",
        "question": "2. What is one reason AI might repeat stereotypes?",
        "options": [
            "It may reflect patterns from training data",
            "It always knows what is fair",
        ],
        "correct": "It may reflect patterns from training data",
        "explain_correct":   "AI learns from large amounts of existing text and images. If those sources contain stereotypes, the AI may repeat them — not because it intends to, but because those patterns were common in its training.",
        "explain_incorrect": "AI does not have an understanding of fairness. It produces outputs based on patterns in its training data, which can include biased or unequal representations.",
    },
    {
        "key":     f"quiz_q3_{_qz_sk}",
        "question": "3. What should you do if an AI output seems narrow or biased?",
        "options": [
            "Accept it without questioning",
            "Revise the prompt and check for missing perspectives",
        ],
        "correct": "Revise the prompt and check for missing perspectives",
        "explain_correct":   "Revising your prompt and asking who might be missing is exactly the right approach. More specific, inclusive prompts lead to better and fairer AI responses.",
        "explain_incorrect": "Accepting AI outputs without questioning them means biases can go unnoticed. Critical thinking about AI responses is an important skill.",
    },
]

st.markdown(
    f'<div style="margin:40px 0 0 0;border-top:2px solid #bae6fd;padding-top:28px;"></div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<p style="text-align:center;font-size:{font_size};font-weight:700;'
    f'color:#1a4a8a;margin:0 0 4px 0;">🧠 Quick Check</p>'
    f'<p style="text-align:center;font-size:calc({font_size} * 0.9);color:#555;margin:0 0 20px 0;">'
    f'Answer each question — you get feedback right away.</p>',
    unsafe_allow_html=True,
)

_qz_col1, _qz_col2, _qz_col3 = st.columns(3, gap="medium")
_qz_answers = {}

for _qz_col, _q in zip([_qz_col1, _qz_col2, _qz_col3], _QUIZ):
    with _qz_col:
        st.markdown(
            f'<div style="border-left:3px solid #dde8f8;padding-left:10px;'
            f'margin-bottom:6px;font-weight:600;font-size:calc({font_size}*0.92);color:#1a4a8a;">'
            f'{_q["question"]}</div>',
            unsafe_allow_html=True,
        )
        _qz_answers[_q["key"]] = st.radio(
            _q["question"],
            options=_q["options"],
            key=_q["key"],
            index=None,
            label_visibility="collapsed",
        )
        _val = _qz_answers[_q["key"]]
        if _val is not None:
            if _val == _q["correct"]:
                st.markdown(
                    f'<div style="background:#e8f5e9;border-left:4px solid #43a047;'
                    f'border-radius:6px;padding:8px 10px;margin:4px 0 0 0;'
                    f'font-size:calc({font_size}*0.88);">'
                    f'✅ <strong>Correct!</strong> {_q["explain_correct"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="background:#fff8e1;border-left:4px solid #f9a825;'
                    f'border-radius:6px;padding:8px 10px;margin:4px 0 0 0;'
                    f'font-size:calc({font_size}*0.88);">'
                    f'💡 <strong>Not quite.</strong> Correct: <em>{_q["correct"]}</em>. '
                    f'{_q["explain_incorrect"]}</div>',
                    unsafe_allow_html=True,
                )

st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)

_btn_gap1, _btn_submit_col, _btn_retry_col, _btn_gap2 = st.columns([1.5, 2, 2, 1.5])
with _btn_submit_col:
    _submit_quiz = st.button(
        "📊 Submit Quick Check",
        key=f"quiz_submit_{_qz_sk}",
        use_container_width=True,
    )
with _btn_retry_col:
    if st.button("🔄 Try Again", key=f"quiz_retry_{_qz_sk}", use_container_width=True):
        for _q in _QUIZ:
            if _q["key"] in st.session_state:
                del st.session_state[_q["key"]]
        st.rerun()

if _submit_quiz:
    _answered = [_q for _q in _QUIZ if _qz_answers[_q["key"]] is not None]
    if len(_answered) < 3:
        st.warning("Please answer all three questions before submitting.")
    else:
        _score = sum(1 for _q in _QUIZ if _qz_answers[_q["key"]] == _q["correct"])
        _pct = int((_score / 3) * 100)
        _sc1, _sc2, _sc3 = st.columns([1.5, 5, 1.5])
        with _sc2:
            st.markdown(
                f'<div role="status" aria-live="polite" style="background:#f3f4f6;'
                f'border-radius:8px;padding:14px 20px;margin:10px 0;text-align:center;'
                f'font-size:{font_size};">'
                f'<strong>You got {_score} out of 3 correct ({_pct}%)</strong></div>',
                unsafe_allow_html=True,
            )
            if _score == 3:
                st.success(
                    "🌟 Great work! You understand how prompts shape AI outputs. "
                    "Keep asking these kinds of questions whenever you use AI tools."
                )
            else:
                st.info(
                    "👍 Nice try! Review the explanations above, then hit **🔄 Try Again** "
                    "to have another go. You can retake as many times as you like."
                )


# ── So What? — full-width breakout section ────────────────────────
sw = SO_WHAT.get(choice, {})
if sw:
    st.markdown(
        '<div style="margin:40px 0 8px 0;border-top:2px solid #bae6fd;"></div>',
        unsafe_allow_html=True,
    )

    _sw_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="130" height="140" '
        'role="img" aria-label="A student figure with a lightbulb thought bubble, representing a thinking moment" '
        'viewBox="0 0 110 120">'
        '<circle cx="38" cy="18" r="13" fill="#fde68a" stroke="#b45309" stroke-width="2"/>'
        '<circle cx="33" cy="16" r="2" fill="#78350f"/>'
        '<circle cx="43" cy="16" r="2" fill="#78350f"/>'
        '<path d="M33 23 Q38 27 43 23" stroke="#b45309" stroke-width="1.5" fill="none" stroke-linecap="round"/>'
        '<line x1="38" y1="31" x2="38" y2="68" stroke="#1e40af" stroke-width="3" stroke-linecap="round"/>'
        '<line x1="38" y1="42" x2="22" y2="34" stroke="#1e40af" stroke-width="2.5" stroke-linecap="round"/>'
        '<line x1="22" y1="34" x2="26" y2="28" stroke="#1e40af" stroke-width="2.5" stroke-linecap="round"/>'
        '<line x1="38" y1="42" x2="56" y2="52" stroke="#1e40af" stroke-width="2.5" stroke-linecap="round"/>'
        '<line x1="38" y1="68" x2="28" y2="90" stroke="#1e40af" stroke-width="2.5" stroke-linecap="round"/>'
        '<line x1="38" y1="68" x2="48" y2="90" stroke="#1e40af" stroke-width="2.5" stroke-linecap="round"/>'
        '<circle cx="52" cy="22" r="3" fill="#e0f2fe" stroke="#7dd3fc" stroke-width="1"/>'
        '<circle cx="62" cy="14" r="5" fill="#e0f2fe" stroke="#7dd3fc" stroke-width="1"/>'
        '<circle cx="74" cy="8" r="7" fill="#e0f2fe" stroke="#7dd3fc" stroke-width="1"/>'
        '<ellipse cx="88" cy="22" rx="20" ry="16" fill="#e0f2fe" stroke="#7dd3fc" stroke-width="1.5"/>'
        '<circle cx="88" cy="20" r="6" fill="#fde68a" stroke="#b45309" stroke-width="1.2"/>'
        '<rect x="85" y="26" width="6" height="3" rx="1" fill="#b45309"/>'
        '<line x1="85" y1="28" x2="91" y2="28" stroke="#b45309" stroke-width="1"/>'
        '<line x1="88" y1="11" x2="88" y2="9" stroke="#b45309" stroke-width="1.2" stroke-linecap="round"/>'
        '<line x1="94" y1="13" x2="96" y2="11" stroke="#b45309" stroke-width="1.2" stroke-linecap="round"/>'
        '<line x1="82" y1="13" x2="80" y2="11" stroke="#b45309" stroke-width="1.2" stroke-linecap="round"/>'
        '</svg>'
    )

    _sw_body   = sw["body"].replace("'", "&#39;")
    _sw_action = sw["action"].replace("'", "&#39;")

    st.markdown(
        '<div style="'
        'background:#f0f9ff;'
        'border:2px solid #bae6fd;'
        'border-radius:16px;'
        'padding:32px 40px 28px 40px;'
        'margin:12px 0 24px 0;'
        'box-shadow:0 3px 16px rgba(14,165,233,0.09);'
        '">'

        '<div style="text-align:center;margin-bottom:22px;">'
        '<div style="font-size:2rem;line-height:1;">💡</div>'
        '<div style="font-size:1.35rem;font-weight:800;color:#0c4a6e;'
        'margin-top:8px;letter-spacing:-0.3px;">'
        'So What? Why Does This Matter?'
        '</div>'
        '</div>'

        '<div style="display:flex;align-items:flex-start;gap:32px;'
        'max-width:820px;margin:0 auto;">'

        '<div style="flex:1;min-width:0;">'
        f'<p style="margin:0 0 18px 0;line-height:1.85;font-size:1.05rem;">{_sw_body}</p>'
        '<div style="'
        'background:#fff7ed;'
        'border-left:5px solid #f97316;'
        'border-radius:0 10px 10px 0;'
        'padding:13px 18px;'
        'font-weight:700;'
        'color:#7c2d12;'
        'font-size:1.02rem;'
        'line-height:1.6;'
        '">'
        f'🔍 {_sw_action}'
        '</div>'
        '</div>'

        f'<div style="flex-shrink:0;padding-top:6px;" aria-hidden="true">{_sw_svg}</div>'

        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
