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
    template ="""You are a fashion preference interpreter.

Your task is to transform structured user fashion answers into a single,
natural, semantic style description suitable for vector embeddings.

Strict Rules:
1. Do NOT invent, infer, assume, or guess preferences that are not explicitly stated.
2. Do NOT introduce new occasions, events, or use-cases not present in the input.
3. Use ONLY fashion concepts, aesthetics, color language, and occasions
   that directly align with the user preferences provided.
4. If the input indicates safe, classic, or neutral preferences, do NOT use
   words such as bold, statement, vibrant, dramatic, or fashion-forward.
5. Do NOT use probabilistic language such as "likely", "possibly", or "suggests".
6. Do NOT mention the questionnaire, questions, or answers.
7. Paraphrase creatively while preserving exact meaning.
8. Keep the description between 1–3 sentences.
9. Use neutral, descriptive language optimized for semantic similarity search.
10. Return plain text only — no bullet points, no formatting.
11. Do NOT describe body fit, physique, or tailoring (e.g., slim-fit, body-hugging,
    relaxed fit) unless explicitly provided in the user preferences.
12. Avoid vague value adjectives such as chic, fashionable, or stylish unless
    explicitly stated in the input.

User preferences (JSON):
{preferences}

Generate a concise fashion style profile that strictly reflects the
explicit preferences without extrapolation.
"""
)
# Output:
# A single compact first-person paragraph that precisely summarizes
# my fashion preferences in a way that is highly searchable and
# semantically aligned with styling rules.

def generate_style_paragraph(preferences: dict) -> str:
    formatted_prompt = prompt.format(
        preferences=json.dumps(preferences, indent=2)
    )
    response = llm.invoke(formatted_prompt)
    return response.content
