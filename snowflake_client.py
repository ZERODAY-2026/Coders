
import os
import re

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

ALLOWED_TABLES = {
    "SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM",
    "SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.PART",
}


def get_connection():
    required = [
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_WAREHOUSE",
        "SNOWFLAKE_ROLE",
    ]

    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError(
            "Missing Snowflake configuration: " + ", ".join(missing)
        )

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database="SNOWFLAKE_SAMPLE_DATA",
        schema="TPCH_SF1",
        role=os.getenv("SNOWFLAKE_ROLE"),
        session_parameters={
            "STATEMENT_TIMEOUT_IN_SECONDS": 30
        },
    )


def validate_sql(sql):
    sql = sql.strip()
    sql = re.sub(
        r"^```(?:sql)?\s*|\s*```$",
        "",
        sql,
        flags=re.IGNORECASE,
    ).strip().rstrip(";").strip()

    if not re.match(r"(?is)^SELECT\b", sql):
        raise ValueError("Only SELECT queries are allowed.")

    if ";" in sql or "--" in sql or "/*" in sql or "*/" in sql:
        raise ValueError(
            "Multiple statements or SQL comments are not allowed."
        )

    forbidden = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|"
        r"MERGE|COPY|PUT|REMOVE|GRANT|REVOKE|CALL|EXECUTE|"
        r"USE|EXEC|INTO)\b",
        re.IGNORECASE,
    )

    if forbidden.search(sql):
        raise ValueError("Unsafe SQL operation rejected.")

    tables = re.findall(
        r"\b(?:FROM|JOIN)\s+([A-Z0-9_.]+)",
        sql,
        flags=re.IGNORECASE,
    )

    if not tables:
        raise ValueError("No approved table found.")

    for table in tables:
        if table.upper() not in ALLOWED_TABLES:
            raise ValueError(f"Table not allowed: {table}")

    return sql


def run_query(sql):
    sql = validate_sql(sql)
    conn = get_connection()
    cursor = None

    try:
        cursor = conn.cursor()
        cursor.execute(sql)

        columns = [item[0] for item in cursor.description]
        rows = cursor.fetchall()
        query_id = cursor.sfqid

        return columns, rows, query_id

    finally:
        if cursor is not None:
            cursor.close()
        conn.close()
