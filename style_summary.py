from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
import json
import os

# -----------------------------
# INITIALIZE LLM ONCE
# -----------------------------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.4,
    groq_api_key=os.getenv("GROQ_API_KEY", "")
)

prompt = PromptTemplate(
    input_variables=["preferences"],
    template = """
You are an AI that rewrites user preferences into a natural,
first-person personal style description.

Write ONE short paragraph as if the USER is describing their own style.
Use simple, clear English.
Sound natural and realistic.

Rules:
- Always write in first person (I / my).
- Do NOT recommend outfits.
- Do NOT use bullet points.
- Do NOT mention JSON, keys, or data.
- Respect all preferences exactly as given.
- If an occasion is marked as difficult, mention it as a challenge,
  not as something the user has already mastered.
- Keep the tone honest, grounded, and human.

User preferences:
{preferences}

Output:
A single first-person paragraph describing my personal style.
"""
)

def generate_style_paragraph(preferences: dict) -> str:
    formatted_prompt = prompt.format(
        preferences=json.dumps(preferences, indent=2)
    )
    response = llm.invoke(formatted_prompt)
    return response.content
