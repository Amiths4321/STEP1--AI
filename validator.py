# problem_definition/validator.py
# An AI that validates AI project ideas before you build them

import requests
import json

OLLAMA_HOST  = "http://10.22.39.192:11434"
OLLAMA_MODEL = "qwen2.5vl:latest"

# ── The 6 canvas questions ────────────────────────────────────────────────────

CANVAS_QUESTIONS = [
    ("user",    "Who exactly is the user? (job role, team, company type)"),
    ("pain",    "What specific problem do they face today? (be concrete)"),
    ("ai_need", "Why does this need AI? Could a spreadsheet or simple rule solve it?"),
    ("data",    "What data is available? (documents, databases, APIs, logs)"),
    ("metric",  "How will you measure success? (give a number and a timeframe)"),
    ("scope",   "What is explicitly OUT of scope for version 1?"),
]

def evaluate_problem(description: str) -> dict:
    """
    Takes a raw project idea and scores it across 5 dimensions.
    Returns structured evaluation with score, gaps, and suggestions.
    """
    prompt = f"""You are an AI project consultant who evaluates whether an AI project idea is well-defined.

Evaluate this project idea:
"{description}"

Score it on these 5 dimensions (0 to 10 each):
1. clarity       — Is the problem clearly stated?
2. user_defined  — Is the target user clearly identified?
3. data_ready    — Is data availability addressed?
4. metric_defined — Is there a measurable success metric?
5. ai_justified  — Is AI actually the right solution?

Also identify:
- gaps: list of what is missing
- recommendation: one of "proceed", "refine", "reconsider"
- reason: one sentence explaining recommendation

Respond ONLY in this JSON format:
{{
  "scores": {{
    "clarity": 0,
    "user_defined": 0,
    "data_ready": 0,
    "metric_defined": 0,
    "ai_justified": 0
  }},
  "overall": 0,
  "gaps": ["gap1", "gap2"],
  "recommendation": "proceed/refine/reconsider",
  "reason": "one sentence"
}}"""

    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt,
              "stream": False, "options": {"temperature": 0.1}},
        timeout=120
    )
    raw = resp.json()["response"].strip()

    # Parse JSON
    try:
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        # compute overall if not set
        scores  = result.get("scores", {})
        overall = sum(scores.values()) / len(scores) if scores else 0
        result["overall"] = round(overall, 1)
        return result
    except Exception:
        return {
            "scores": {},
            "overall": 0,
            "gaps": ["Could not parse evaluation"],
            "recommendation": "refine",
            "reason": "Please provide more detail about your project idea."
        }


def generate_problem_document(answers: dict) -> str:
    """
    Takes canvas answers and generates a structured
    Problem Definition Document.
    """
    canvas_text = "\n".join([
        f"{k.upper()}: {v}" for k, v in answers.items()
    ])

    prompt = f"""You are a senior AI solution architect.
Based on these answers, write a professional Problem Definition Document.

{canvas_text}

Write the document with these sections:
1. Executive Summary (2 sentences)
2. Problem Statement (specific, concrete)
3. Target Users
4. Proposed AI Solution (RAG / Agent / Fine-tuning — pick the right one and justify)
5. Data Requirements
6. Success Metrics (with numbers)
7. Out of Scope
8. Risks & Assumptions

Be concise and professional. Use bullet points where appropriate."""

    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt,
              "stream": False, "options": {"temperature": 0.2, "num_predict": 1024}},
        timeout=120
    )
    return resp.json()["response"].strip()


def suggest_clarifying_questions(description: str) -> list[str]:
    """Given a vague idea, suggest the right questions to ask."""
    prompt = f"""A client described this AI project idea:
"{description}"

Generate 5 specific clarifying questions an AI consultant would ask
to better understand and define this problem.

Return ONLY a JSON array of 5 question strings. Nothing else.
["question1", "question2", "question3", "question4", "question5"]"""

    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt,
              "stream": False, "options": {"temperature": 0.3}},
        timeout=120
    )
    raw = resp.json()["response"].strip()
    try:
        start = raw.find("[")
        end   = raw.rfind("]") + 1
        return json.loads(raw[start:end])
    except Exception:
        return ["Could not generate questions. Please try again."]