import streamlit as st
import json
import textstat
import re
from pathlib import Path

# ── Helpers ─────────────────────────────────────────
def tip(word, definition):
    return f"**{word}**"

TIPS = {
    "prompt": "A question or instruction you give an AI",
    "prompts": "Questions or instructions you give an AI",
    "identify": "To find or spot something",
    "bias": "When something is unfair",
    "biases": "Ways something can be unfair",
    "assumptions": "Things you think are true without checking",
}

# ── Load scenarios (ONLY ONCE) ──────────────────────
SCENARIOS_PATH = Path(__file__).parent / "data" / "scenarios.json"

with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
    scenarios = json.load(f)

scenario_names = [s["scenario"] for s in scenarios]

# ── Layout ─────────────────────────────────────────
col_main, col_support = st.columns([0.65, 0.35])

# ==================================================
# RIGHT PANEL (Teacher Tools)
# ==================================================
with col_support:
    st.header("🧑‍🏫 Teacher Tools")

    teacher_choice = st.selectbox(
        "Select scenario to analyse:",
        scenario_names,
        key="teacher_select",
    )

    teacher_selected = next(s for s in scenarios if s["scenario"] == teacher_choice)

    combined = teacher_selected["prompt"] + " " + teacher_selected["issue"]
    grade = textstat.flesch_kincaid_grade(combined)

    st.write(f"📊 Grade level: {grade:.1f}")

    def flag_hard_words(text):
        words = re.findall(r"[a-zA-Z]+", text)
        return [w for w in words if textstat.syllable_count(w) >= 3]

    hard_words = flag_hard_words(combined)

    if hard_words:
        st.write("Hard words:", ", ".join(hard_words))

# ==================================================
# LEFT PANEL (Student Experience)
# ==================================================
with col_main:
    st.title("🤖 AI Literacy Prompt Explorer")

    st.write(
        "Explore how AI responses change based on prompts and identify bias."
    )

    st.markdown("---")

    # ── Scenario selection ──────────────────────
    choice = st.selectbox("Choose a scenario:", scenario_names)

    selected = next(s for s in scenarios if s["scenario"] == choice)

    # ── Prompt ────────────────────────────────
    st.markdown("### Prompt")
    st.write(selected["prompt"])

    # ── Think About It ────────────────────────
    st.markdown("### Think About It")
    st.write(
        "What assumptions or biases might this prompt create?"
    )

    # ── Issue ─────────────────────────────────
    st.markdown("### Possible Issue")
    st.write(selected["issue"])

    # ── Student Reflection ────────────────────
    st.markdown("---")
    st.markdown("### Your Turn")

    explanation = st.text_area("Explain your thinking:")
    improved_prompt = st.text_area("Rewrite the prompt:")

    if st.button("Check My Thinking"):
        if explanation:
            st.success("Nice thinking!")
        else:
            st.warning("Try adding an explanation.")

        if improved_prompt:
            st.success("Good revision!")
        else:
            st.warning("Try rewriting the prompt.")
