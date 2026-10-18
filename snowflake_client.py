import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database="SNOWFLAKE_SAMPLE_DATA",
        schema="TPCH_SF1",
        role=os.getenv("SNOWFLAKE_ROLE")
    )

def run_query(sql):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()