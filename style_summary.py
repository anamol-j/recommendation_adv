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
You are an AI that condenses user preferences into a compact,
first-person personal style profile optimized for understanding
fashion preferences.

Write ONE short paragraph as if the USER is describing their own style.

The paragraph must be:
- Short (4–6 sentences maximum)
- Information-dense but natural
- Clear about style, fit, colors, and occasions

Rules:
- Always write in first person (I / my).
- Do NOT recommend outfits.
- Do NOT use bullet points.
- Do NOT mention JSON, keys, or data.
- Respect all preferences exactly as given.
- Clearly state style type (e.g., classic, casual, streetwear, minimal).
- Clearly state fit preference (e.g., slim, relaxed, oversized).
- Clearly state color preference (e.g., neutrals, dark tones, bold colors).
- Mention main occasions I dress for.
- If an occasion is marked as difficult, mention it as a challenge,
  not as something I have already mastered.
- Keep language simple, grounded, and factual rather than emotional.

User preferences:
{preferences}

Output:
A single first-person paragraph that clearly summarizes my personal style
and dressing priorities in a concise, searchable way.
"""
)

def generate_style_paragraph(preferences: dict) -> str:
    formatted_prompt = prompt.format(
        preferences=json.dumps(preferences, indent=2)
    )
    response = llm.invoke(formatted_prompt)
    return response.content
