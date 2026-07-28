import os
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_secret(key):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key)


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("Missing required env var: GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-flash-latest")


@st.cache_data
def generate_executive_insight(company_name, company_skills, market_skills, missing_skills):
    """
    Generate an executive-level workforce intelligence interpretation.
    The model only interprets the precomputed statistics passed in — it
    never queries the database or calculates any numbers itself.
    """
    system_instruction = """You are a Senior Workforce Intelligence Consultant.
Your audience is an HR Director.
Your task is not to repeat the statistics already shown in the dashboard.
Instead, produce four sections:

1. Hiring Focus
2. Market Comparison
3. Recommendation
4. Strategic Risk

Base every statement only on the supplied statistics.
Do not invent facts, percentages, companies, technologies, or business strategies that are not present in the provided data.
Keep the tone professional, concise, executive, and actionable.
Limit the response to approximately 180 words."""

    prompt = f"""{system_instruction}

Company: {company_name}
Company's current skills (from job postings): {', '.join(company_skills) if company_skills else 'None detected'}
Overall market skills (top in-demand, all companies): {', '.join(market_skills) if market_skills else 'None available'}
Market skills this company is missing: {', '.join(missing_skills) if missing_skills else 'None — full coverage'}
"""
    response = model.generate_content(prompt)
    return response.text.strip()


if __name__ == "__main__":
    test_insight = generate_executive_insight(
        "Test Company",
        ["Python", "SQL"],
        ["Python", "SQL", "Power BI", "AWS", "Tableau", "Excel", "Azure"],
        ["AWS", "Tableau", "Excel"]
    )
    print(test_insight)