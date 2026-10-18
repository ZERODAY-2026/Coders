import re
import pandas as pd
import streamlit as st

from snowflake_client import run_query
from gemma_client import ask_gemma

st.set_page_config(
    page_title="DataMind",
    page_icon="📊",
    layout="wide",
)

st.title("DataMind — AI Data Analyst")
st.write("Ask questions about real sales data from Snowflake.")

question = st.text_input(
    "Enter your question",
    placeholder="Which 10 products generate the highest revenue?",
)


def is_date_question(question):
    return bool(
        re.search(
            r"\b(19|20)\d{2}\b|\b(today|yesterday|last year|this year)\b",
            question,
            re.IGNORECASE,
        )
    )


if st.button("Run Analysis", type="primary"):
    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    if is_date_question(question):
        st.warning(
            "Date-based filtering is not supported yet. "
            "Please ask without a date or year."
        )
        st.stop()

    try:
        with st.spinner("Gemma is generating SQL..."):
            sql = ask_gemma(question, task="sql").strip()

        if sql.upper().startswith("UNSUPPORTED"):
            st.warning("This question is not supported yet.")
            st.stop()

        st.subheader("Generated SQL")
        st.code(sql, language="sql")

        with st.spinner("Executing query on Snowflake..."):
            columns, rows, query_id = run_query(sql)

        st.subheader("Snowflake Evidence")
        st.write("Query executed successfully.")
        st.code(query_id, language="text")

        if not rows:
            st.info("Snowflake returned no results.")
            st.stop()

        df = pd.DataFrame(rows, columns=columns)

        st.subheader("Actual Snowflake Results")
        st.dataframe(df, use_container_width=True)

        with st.spinner("Gemma is explaining the actual results..."):
            explanation = ask_gemma(
                question,
                data=rows,
                task="explain",
            )

        st.subheader("Gemma's Data-Based Explanation")
        st.write(explanation)

    except Exception as error:
        st.error(f"Analysis failed: {error}")
