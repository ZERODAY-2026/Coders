import json
import re
import requests


MODEL = "gemma3:4b"
OLLAMA_URL = "http://localhost:11434/api/generate"

ALLOWED_TABLES = """
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.PART
"""


def ask_gemma(question: str, data=None, task="sql") -> str:
    question = question.strip()

    if task == "sql":
        # Reject questions outside the currently supported scope.
        if re.search(
            r"\b(employee|employees|salary|salaries|payroll)\b",
            question,
            re.IGNORECASE,
        ):
            return "UNSUPPORTED"

        if re.search(
            r"\b(19|20)\d{2}\b|\b(today|yesterday|last year|"
            r"this year|in \d{1,2}/\d{1,2})\b",
            question,
            re.IGNORECASE,
        ):
            return "UNSUPPORTED"

        prompt = f"""
You generate read-only SQL for Snowflake.

Allowed tables (use these EXACT fully qualified names):
{ALLOWED_TABLES}

Allowed columns:
LINEITEM: L_PARTKEY, L_EXTENDEDPRICE, L_DISCOUNT,
          L_QUANTITY, L_ORDERKEY, L_SHIPDATE
PART: P_PARTKEY, P_NAME, P_MFGR, P_BRAND, P_TYPE

Rules:
1. Return exactly one SELECT query, or UNSUPPORTED.
2. Never use INSERT, UPDATE, DELETE, DROP, CREATE, or other
   modifying statements.
3. Always use the complete table names listed above.
4. Join tables using L.L_PARTKEY = P.P_PARTKEY.
5. Product revenue means:
   SUM(L.L_EXTENDEDPRICE * (1 - L.L_DISCOUNT))
6. For product revenue, group by P.P_NAME.
7. If the question asks for top N products, use LIMIT N.
8. Do not invent table names or columns.
9. Date-based questions are unsupported.
10. Return SQL only, without Markdown fences or explanations.

User question: {question}
"""

    else:
        prompt = f"""
You are DataMind, a careful data analyst.

Answer the user's question using ONLY the actual Snowflake
query results below. Do not invent numbers or unsupported facts.
Explain what the results show clearly.

User question: {question}

Actual Snowflake results:
{json.dumps(data, default=str)}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()

    answer = response.json()["response"].strip()

    if task == "sql":
        answer = re.sub(
            r"^```(?:sql)?\s*|\s*```$",
            "",
            answer,
            flags=re.IGNORECASE,
        ).strip()

        if answer.upper().startswith("UNSUPPORTED"):
            return "UNSUPPORTED"

    return answer
