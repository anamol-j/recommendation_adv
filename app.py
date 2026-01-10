import streamlit as st
from question_bank import get_random_questions
from style_summary import generate_style_paragraph  # LLM function

st.set_page_config(page_title="Style Preferences", layout="centered")
st.title("Personal Style Questionnaire")

# -----------------------------
# LOAD QUESTIONS ONLY ONCE
# -----------------------------
if "questions" not in st.session_state:
    st.session_state.questions = get_random_questions(total=6)

questions = st.session_state.questions

responses = {}

# -----------------------------
# RENDER QUESTIONS
# -----------------------------
for q in questions:
    if q["type"] == "radio":
        responses[q["id"]] = st.radio(
            q["label"], q["options"], key=q["id"]
        )
    elif q["type"] == "multiselect":
        responses[q["id"]] = st.multiselect(
            q["label"], q["options"], key=q["id"]
        )
    elif q["type"] == "text":
        responses[q["id"]] = st.text_input(
            q["label"], key=q["id"]
        )

# -----------------------------
# SUBMIT BUTTON (ONLY TRIGGER)
# -----------------------------
if st.button("Submit"):
    st.subheader("Collected Preferences (JSON)")
    st.json(responses)

    # 🔥 LLM RUNS ONLY HERE
    with st.spinner("Generating style summary..."):
        style_paragraph = generate_style_paragraph(responses)

    st.subheader("Generated Style Summary")
    st.write(style_paragraph)
