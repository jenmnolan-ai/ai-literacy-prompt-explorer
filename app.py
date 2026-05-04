import streamlit as st
import json

st.title("AI Literacy Prompt Explorer")

st.write("Explore how AI responses can change based on prompts, and identify potential bias or issues.")

# Load scenarios
with open("data/scenarios.json") as f:
    scenarios = json.load(f)

# Select scenario
scenario_names = [s["scenario"] for s in scenarios]
choice = st.selectbox("Choose a scenario:", scenario_names)

selected = next(s for s in scenarios if s["scenario"] == choice)

st.subheader("Prompt")
st.write(selected["prompt"])

st.subheader("Think About It")
st.write("What assumptions might this prompt create?")
st.write("How could this lead to bias or incomplete results?")

st.subheader("Possible Issue")
st.write(selected["issue"])

st.subheader("Reflection")
st.text_area("How would you improve this prompt?")
