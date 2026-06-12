# problem_definition/validator_app.py
# streamlit run problem_definition/validator_app.py

import streamlit as st
import json
import os
from pathlib import Path
from validator import (
    evaluate_problem, generate_problem_document,
    suggest_clarifying_questions, CANVAS_QUESTIONS
)

st.set_page_config(
    page_title="AI Project Validator",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 AI Project Validator")
st.caption("Define your problem properly before writing a single line of code.")

tab1, tab2, tab3 = st.tabs([
    "1️⃣  Quick Validate",
    "2️⃣  Full Canvas",
    "3️⃣  Learn by Example"
])

# ── Tab 1: Quick Validate ─────────────────────────────────────────────────────
with tab1:
    st.subheader("Paste your project idea")
    st.caption("Describe your AI project in plain English. The validator will score it.")

    idea = st.text_area(
        "Your idea:",
        placeholder="e.g. We want to build an AI chatbot to help employees...",
        height=120
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Validate idea", type="primary", use_container_width=True):
            if idea.strip():
                with st.spinner("Evaluating..."):
                    result = evaluate_problem(idea)

                # Score display
                st.divider()
                overall = result.get("overall", 0)
                color   = "green" if overall >= 7 else "orange" if overall >= 5 else "red"
                rec     = result.get("recommendation", "refine")

                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.metric("Overall Score", f"{overall}/10")
                    rec_icon = {"proceed": "✅", "refine": "⚠️", "reconsider": "❌"}.get(rec, "⚠️")
                    st.metric("Recommendation", f"{rec_icon} {rec.upper()}")

                with col_b:
                    scores = result.get("scores", {})
                    for dim, score in scores.items():
                        label = dim.replace("_", " ").title()
                        st.progress(score / 10, text=f"{label}: {score}/10")

                # Gaps
                gaps = result.get("gaps", [])
                if gaps:
                    st.warning("**Gaps found:**\n" + "\n".join(f"- {g}" for g in gaps))

                st.info(f"**Why:** {result.get('reason', '')}")

    with col2:
        if st.button("Get clarifying questions", use_container_width=True):
            if idea.strip():
                with st.spinner("Generating questions..."):
                    questions = suggest_clarifying_questions(idea)
                st.divider()
                st.markdown("**Ask your client or yourself:**")
                for i, q in enumerate(questions, 1):
                    st.markdown(f"{i}. {q}")

# ── Tab 2: Full Canvas ────────────────────────────────────────────────────────
with tab2:
    st.subheader("Problem Definition Canvas")
    st.caption("Answer all 6 questions to generate a professional Problem Definition Document.")

    answers = {}
    for key, question in CANVAS_QUESTIONS:
        answers[key] = st.text_area(
            question,
            key=f"canvas_{key}",
            height=80,
            placeholder="Be specific..."
        )

    if st.button("Generate Problem Definition Document", type="primary"):
        filled = {k: v for k, v in answers.items() if v.strip()}
        if len(filled) < 4:
            st.warning("Please answer at least 4 questions for a meaningful document.")
        else:
            with st.spinner("Generating document..."):
                doc = generate_problem_document(filled)

            st.divider()
            st.markdown(doc)

            # Save option
            Path("problem_definition/outputs").mkdir(parents=True, exist_ok=True)
            fname = "problem_definition/outputs/problem_definition.md"
            with open(fname, "w") as f:
                f.write(doc)
            st.success(f"Saved to {fname}")

# ── Tab 3: Learn by Example ───────────────────────────────────────────────────
with tab3:
    st.subheader("Learn from good vs bad definitions")

    examples = {
        "❌ Bad — Vague": {
            "idea": "Let's build an AI chatbot for our company.",
            "lesson": "No user defined, no problem stated, no metric, no data mentioned. Could mean anything."
        },
        "❌ Bad — AI Not Needed": {
            "idea": "We want AI to check if invoice totals match line item sums.",
            "lesson": "A simple formula =SUM() solves this. AI adds cost and complexity with no benefit."
        },
        "⚠️ Partial — Missing Metric": {
            "idea": "HR gets too many repetitive questions. We want an AI to answer them automatically and save HR time.",
            "lesson": "Good user and pain, but 'save time' is not measurable. By how much? From what baseline?"
        },
        "✅ Good — Well Defined": {
            "idea": "HR receives 50 employee queries per day. 80% are about leave and payroll policies — answered from the same 3 documents. We want to reduce HR response time from 4 hours to under 5 minutes for these queries. Data: HR policy PDF, payroll FAQ, leave policy doc.",
            "lesson": "Clear user (HR), clear pain (4hr response), clear data (3 docs), clear metric (5 min), clear scope (leave and payroll only)."
        },
    }

    for label, ex in examples.items():
        with st.expander(label):
            st.markdown(f"**Idea:** {ex['idea']}")
            st.info(f"**Lesson:** {ex['lesson']}")

            if st.button(f"Validate this example", key=label):
                with st.spinner("Evaluating..."):
                    result = evaluate_problem(ex["idea"])
                scores = result.get("scores", {})
                for dim, score in scores.items():
                    st.progress(score / 10, text=f"{dim.replace('_',' ').title()}: {score}/10")
                st.caption(f"Overall: {result['overall']}/10 — {result['recommendation'].upper()}")