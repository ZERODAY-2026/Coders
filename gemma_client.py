
import requests
import json


def ask_gemma(question: str, data: list) -> str:
    prompt = f"""
You are DataMind, an AI data analyst.

User question: {question}

Actual Snowflake data:
{json.dumps(data, default=str)}

Explain the results using only this data.
Do not invent numbers or unsupported facts.
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "gemma3:4b",
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )

    response.raise_for_status()
    return response.json()["response"]
