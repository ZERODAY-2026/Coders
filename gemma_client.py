
import json
import re
import requests

MODEL = "gemma3:4b"
OLLAMA_URL = "http://localhost:11434/api/generate"

LINEITEM = "SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM"
PART = "SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.PART"

DATASET_TERMS = {
    "product", "products", "part", "parts",
    "brand", "brands", "manufacturer", "manufacturers",
    "type", "types", "revenue", "sales", "sale",
    "sold", "selling", "sell", "quantity", "quantities",
    "price", "prices", "discount", "discounts",
    "order", "orders", "shipment", "shipments", "shipped",
    "ship", "highest", "lowest", "top", "most", "least",
    "average", "total", "count", "sum", "compare",
    "comparison", "ranking", "rank", "expensive", "cheap",
    "popular", "year", "years", "month", "months",
    "date", "dates", "annual", "monthly", "quarter",
    "quarterly", "daily", "lineitem", "profit", "amount",
    "combined", "generate", "generated",
}

CLASSIFIER_PROMPT = """
You classify questions for DataMind.

Available data:

LINEITEM:
L_PARTKEY, L_EXTENDEDPRICE, L_DISCOUNT,
L_QUANTITY, L_ORDERKEY, L_SHIPDATE

PART:
P_PARTKEY, P_NAME, P_MFGR, P_BRAND, P_TYPE

Supported: product information, selling quantity, revenue,
discounts, order counts, rankings, totals, averages,
comparisons, and shipment-date analysis.

Selling quantity means SUM(L_QUANTITY).
Revenue means SUM(L_EXTENDEDPRICE * (1 - L_DISCOUNT)).

Unsupported: jokes, general knowledge, weather, personal advice,
unrelated coding questions, employee salaries, and questions
requiring unavailable columns or tables.

Return only JSON:
{"supported": true}
or
{"supported": false}

Do not answer the question.
"""


def call_gemma(prompt, json_mode=False):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
    }

    if json_mode:
        payload["format"] = "json"

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def is_supported_question(question):
    question = question.strip()

    if not question:
        return False

    words = set(re.findall(r"[a-z]+", question.lower()))

    # Questions containing dataset-related terms can proceed
    # to SQL generation. SQL validation still happens later.
    if words & DATASET_TERMS:
        return True

    try:
        result = call_gemma(
            CLASSIFIER_PROMPT + "\n\nUser question:\n" + question,
            json_mode=True,
        )
        classification = json.loads(result)
        return classification.get("supported") is True

    except (
        requests.RequestException,
        ValueError,
        TypeError,
    ):
        return False


def make_selling_sql(question):
    """
    Handle selling-quantity questions deterministically.
    Selling quantity = SUM(L_QUANTITY).
    Return None for other questions.
    """
    q = question.lower()

    selling_terms = (
        "sell", "selling", "sold", "top-selling",
        "top selling", "best-selling", "best selling",
    )

    if not any(term in q for term in selling_terms):
        return None

    # Extract N from phrases such as "top 10 selling products".
    match = re.search(r"\btop\s+(\d+)\b", q)
    limit = int(match.group(1)) if match else 10

    # Keep limits sensible.
    if limit < 1 or limit > 100:
        return "UNSUPPORTED"

    lineitem = LINEITEM
    part = PART

    # "sum of top 10 selling products" means:
    # rank products by quantity, then add those quantities.
    asks_for_sum = bool(
        re.search(r"\b(sum|total|combined)\b", q)
    )

    if asks_for_sum:
        return f"""
SELECT SUM(TOTAL_QUANTITY) AS COMBINED_QUANTITY
FROM (
    SELECT
        P.P_NAME,
        SUM(L.L_QUANTITY) AS TOTAL_QUANTITY
    FROM {lineitem} AS L
    JOIN {part} AS P
        ON L.L_PARTKEY = P.P_PARTKEY
    GROUP BY P.P_PARTKEY, P.P_NAME
    ORDER BY TOTAL_QUANTITY DESC
    LIMIT {limit}
) AS TOP_PRODUCTS
""".strip()

    return f"""
SELECT
    P.P_NAME AS PRODUCT_NAME,
    SUM(L.L_QUANTITY) AS TOTAL_QUANTITY
FROM {lineitem} AS L
JOIN {part} AS P
    ON L.L_PARTKEY = P.P_PARTKEY
GROUP BY P.P_PARTKEY, P.P_NAME
ORDER BY TOTAL_QUANTITY DESC
LIMIT {limit}
""".strip()


def ask_gemma(question, data=None, task="sql"):
    question = question.strip()

    if task == "sql":
        # Use reliable SQL templates for selling-quantity questions.
        selling_sql = make_selling_sql(question)
        if selling_sql is not None:
            return selling_sql

        prompt = f"""
Generate exactly one read-only Snowflake SELECT query.

Approved tables:
{LINEITEM}
{PART}

Allowed columns:
LINEITEM: L_PARTKEY, L_EXTENDEDPRICE, L_DISCOUNT,
L_QUANTITY, L_ORDERKEY, L_SHIPDATE

PART: P_PARTKEY, P_NAME, P_MFGR, P_BRAND, P_TYPE

Rules:
1. Return SQL only, starting with SELECT, or UNSUPPORTED.
2. Use only approved tables and columns.
3. Join tables using L.L_PARTKEY = P.P_PARTKEY.
4. Selling quantity is SUM(L.L_QUANTITY).
5. Revenue is SUM(L.L_EXTENDEDPRICE * (1 - L.L_DISCOUNT)).
6. Product revenue must be grouped by product name and key.
7. For top N questions, rank by the metric the user asked for.
8. For a year filter, use L.L_SHIPDATE with a correct date range.
9. For year-wise revenue, group by YEAR(L.L_SHIPDATE).
10. For month-wise revenue, group by year and month.
11. If asked for the sum of a top-N ranking, first select the
    top N groups, then sum the requested metric outside that query.
12. Never invent columns or tables.
13. Exact time-of-day questions are unsupported.
14. Do not use CTEs or multiple SQL statements.

User question: {question}
"""

    elif task == "explain":
        prompt = f"""
You are DataMind, a careful data analyst.

Explain using ONLY the actual Snowflake results below.
Do not invent values, dates, rankings, or facts.
If the results are empty, say that no matching records were returned.

User question:
{question}

Actual Snowflake results:
{json.dumps(data, default=str)}
"""
    else:
        raise ValueError("Unknown task. Use 'sql' or 'explain'.")

    answer = call_gemma(prompt)

    if task == "sql":
        answer = re.sub(
            r"^```(?:sql)?\s*|\s*```$",
            "",
            answer,
            flags=re.IGNORECASE,
        ).strip()

        if answer.upper().startswith("UNSUPPORTED"):
            return "UNSUPPORTED"

        if not re.match(r"(?is)^SELECT\b", answer):
            raise ValueError(
                "Gemma did not return SQL starting with SELECT."
            )

        answer = answer.rstrip(";").strip()

    return answer
