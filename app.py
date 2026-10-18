
from gemma_client import ask_gemma
import streamlit as st
import pandas as pd
from snowflake_client import run_query

st.set_page_config(
    page_title="DataMind",
    page_icon="📊",
    layout="wide"
)

st.title("DataMind — AI Data Analyst")
st.write("Ask questions about sales data.")

question = st.text_input(
    "Enter your question",
    placeholder="Which 5 products generate the highest revenue?"
)

if st.button("Run Analysis"):
    if question.strip():
        sql = """
        SELECT
            p.P_NAME AS PRODUCT,
            ROUND(
                SUM(l.L_EXTENDEDPRICE * (1 - l.L_DISCOUNT)), 2
            ) AS REVENUE
        FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM l
        JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.PART p
            ON l.L_PARTKEY = p.P_PARTKEY
        GROUP BY p.P_NAME
        ORDER BY REVENUE DESC
        LIMIT 5
        """

        try:
            with st.spinner("Fetching actual data from Snowflake..."):
                result = run_query(sql)

            df = pd.DataFrame(
                result,
                columns=["Product", "Revenue"]
            )

            st.subheader("SQL Query Executed")
            st.code(sql, language="sql")

            st.subheader("Actual Snowflake Results")
            st.dataframe(df, use_container_width=True)

            with st.spinner("Gemma is explaining the actual results..."):
                gemma_response = ask_gemma(question, result)

            st.subheader("Gemma's Data-Based Explanation")
            st.write(gemma_response)

        except Exception as e:
            st.error(f"Analysis failed: {e}")

    else:
        st.warning("Please enter a question.")
