import streamlit as st
import json
import textstat
import re
from pathlib import Path

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
    "prompt": "A question or instruction you give an AI to tell it what to do",
    "prompts": "Questions or instructions you give an AI to tell it what to do",
    "identify": "To find, spot, or name something",
    "bias": "When something is unfair and treats some people better or worse than others",
    "biases": "Ways something can be unfair to some people more than others",
    "assumption": "Something you think is true without checking first",
    "assumptions": "Things you think are true without checking first",
}

# ── Load scenarios ONCE ───────────────────────────────────────────
SCENARIOS_PATH = Path(__file__).parent / "data" / "scenarios.json"

with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
    scenarios = json.load(f)

scenario_names = [s["scenario"] for s in scenarios]

# ── Layout ───────────────────────────────────────────────────────
col_main, col_support = st.columns([0.65, 0.35])

# ════════════════════════════════════════════
# RIGHT PANEL (unchanged logic, trimmed)
# ════════════════════════════════════════════
with col_support:
    st.markdown("### 🧑‍🏫 Teacher Tools")

    _teacher_choice = st.selectbox(
        "Select scenario to analyse:",
        scenario_names,
        key="teacher_select",
    )

    _selected = next(s for s in scenarios if s["scenario"] == _teacher_choice)

    _combined = _selected["prompt"] + " " + _selected["issue"]
    _grade = textstat.flesch_kincaid_grade(_combined)

    st.write(f"Grade level: {_grade:.1f}")

# ════════════════════════════════════════════
# LEFT MAIN CONTENT (FIXED)
# ════════════════════════════════════════════
with col_main:
    st.markdown(
        "Explore how AI responses change based on "
        + tip("prompts", TIPS["prompts"])
        + " and "
        + tip("identify", TIPS["identify"])
        + " potential "
        + tip("bias", TIPS["bias"])
    )

    st.markdown("")

    # ── Scenario selection ───────────────────
    choice = st.selectbox(
        "Choose a scenario:",
        scenario_names,
    )

    selected = next(s for s in scenarios if s["scenario"] == choice)

    # ── Prompt ──────────────────────────────
    st.markdown("### " + tip("Prompt", TIPS["prompt"]), unsafe_allow_html=True)
    st.write(selected["prompt"])

    # ── Think About It ──────────────────────
    st.markdown("### Think About It")
    st.markdown(
        "What "
        + tip("assumptions", TIPS["assumptions"])
        + " or "
        + tip("biases", TIPS["biases"])
        + " might this prompt create?",
        unsafe_allow_html=True,
    )

    # ── Issue ───────────────────────────────
    st.markdown("### Possible Issue")
    st.write(selected["issue"])
