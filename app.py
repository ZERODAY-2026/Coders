
import html

import pandas as pd
import streamlit as st
from streamlit_mic_recorder import speech_to_text

from gemma_client import ask_gemma, is_supported_question
from snowflake_client import run_query


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="DataMind | AI Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "question_input" not in st.session_state:
    st.session_state.question_input = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_voice_text" not in st.session_state:
    st.session_state.last_voice_text = ""


# --------------------------------------------------
# HELPER: SAVE CHAT HISTORY
# --------------------------------------------------

def save_to_history(question, answer):
    """Save each question and answer once."""
    entry = {
        "question": question.strip(),
        "answer": str(answer),
    }

    if not st.session_state.chat_history:
        st.session_state.chat_history.append(entry)
    elif st.session_state.chat_history[-1] != entry:
        st.session_state.chat_history.append(entry)


# --------------------------------------------------
# STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
    @import url(
      'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    html, body, [class*="css"] {
        font-family: Inter, sans-serif;
    }

    .stApp {
        background: #0a0f1c;
        color: #edf2ff;
    }

    [data-testid="stSidebar"] {
        background: #10182a;
        border-right: 1px solid #24314a;
    }

    .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .hero {
        padding: 30px;
        border-radius: 20px;
        border: 1px solid #2a4169;
        background: linear-gradient(120deg, #172b51, #141d33 72%, #182c42);
        margin-bottom: 25px;
    }

    .hero-tag {
        color: #bcd0ff;
        background: #253d66;
        border: 1px solid #3c5787;
        padding: 6px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
    }

    .hero h1 {
        font-size: 35px;
        font-weight: 800;
        color: white;
        margin: 17px 0 8px;
    }

    .hero p, .muted {
        color: #aebdd5;
        font-size: 13px;
        line-height: 1.8;
    }

    .section-title {
        font-size: 21px;
        font-weight: 700;
        margin: 22px 0 7px;
    }

    div[data-testid="stTextInput"] input {
        background: #131d30;
        color: white;
        border: 1px solid #344563;
        border-radius: 11px;
        min-height: 48px;
    }

    div.stButton > button {
        background: #6688ff;
        color: white;
        border: 1px solid #6688ff;
        border-radius: 10px;
        min-height: 44px;
        font-weight: 700;
    }

    div.stButton > button:hover {
        background: #829cff;
        color: white;
        border-color: #829cff;
    }

    div[data-testid="stMetric"] {
        background: #121c2f;
        border: 1px solid #293953;
        border-radius: 14px;
        padding: 16px;
    }

    .result-card, .explanation-card {
        background: #121c2f;
        border: 1px solid #2b3b58;
        border-radius: 15px;
        padding: 19px 21px;
        margin: 12px 0 18px;
    }

    .result-label {
        color: #9eafd0;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 9px;
    }

    .result-value {
        color: white;
        font-size: 29px;
        font-weight: 800;
        overflow-wrap: anywhere;
    }

    .explanation-heading {
        color: #d9e4ff;
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 10px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #293953;
        border-radius: 12px;
        overflow: hidden;
    }

    hr {
        border-color: #27344b;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.markdown("## ✦ DataMind")
    st.caption("AI-POWERED DATA ANALYTICS")
    st.divider()

    st.markdown("**AVAILABLE TABLES**")
    st.caption("PART — product information")
    st.caption("LINEITEM — pricing, quantity and shipment dates")

    st.divider()

    st.markdown("**SUPPORTED ANALYSIS**")
    st.caption("• Top-selling products by quantity")
    st.caption("• Revenue and quantity totals")
    st.caption("• Product and brand comparisons")
    st.caption("• Shipment dates and date ranges")

    st.divider()

    st.markdown("## 💬 Chat History")
    st.caption("Questions and answers from this session")

    if st.session_state.chat_history:
        total = len(st.session_state.chat_history)

        for index in range(total - 1, -1, -1):
            item = st.session_state.chat_history[index]
            question_preview = item["question"].replace("\n", " ")

            if len(question_preview) > 35:
                question_preview = question_preview[:35] + "..."

            with st.expander(
                f"Q{index + 1}: {question_preview}",
                expanded=False,
            ):
                st.markdown("**Your question**")
                st.write(item["question"])

                st.markdown("**DataMind's answer**")
                st.write(item["answer"])

        if st.button("🗑️ Clear chat history"):
            st.session_state.chat_history = []
            st.rerun()

    else:
        st.caption("Your questions and answers will appear here.")

    st.divider()
    st.caption("Streamlit · Gemma · Snowflake")


# --------------------------------------------------
# HERO
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <span class="hero-tag">AI DATA ANALYST</span>
        <h1>Turn questions into insights.</h1>
        <p>
            Ask about products, selling quantities, revenue and shipment dates.
            Type or speak your question. DataMind queries Snowflake and
            explains actual results.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-title">Ask DataMind</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="muted">Try: top selling products, total quantity sold, '
    'combined quantity of the top 10, or revenue by year.</p>',
    unsafe_allow_html=True,
)


# --------------------------------------------------
# VOICE INPUT
# --------------------------------------------------

st.markdown("### 🎙️ Ask using your voice")

try:
    voice_text = speech_to_text(
        language="en-IN",
        start_prompt="🎙️ Start speaking",
        stop_prompt="⏹️ Stop recording",
        just_once=True,
        key="datamind_speech_input",
    )

    if isinstance(voice_text, str) and voice_text.strip():
        transcript = voice_text.strip()

        if transcript != st.session_state.last_voice_text:
            st.session_state.last_voice_text = transcript
            st.session_state.question_input = transcript
            st.success("Speech converted to text!")

except Exception:
    st.warning(
        "Voice input is unavailable. You can still type your question."
    )


# --------------------------------------------------
# QUESTION INPUT
# --------------------------------------------------

question = st.text_input(
    "Your question",
    placeholder="What are the top 10 selling products?",
    key="question_input",
    label_visibility="collapsed",
)

run_analysis = st.button("✦ Run analysis", type="primary")


# --------------------------------------------------
# ANALYSIS
# --------------------------------------------------

if run_analysis:
    question = question.strip()

    if not question:
        st.warning("Please type or speak a question first.")

    else:
        try:
            # Check whether the question is supported.
            with st.spinner("Checking your question..."):
                supported = is_supported_question(question)

            if not supported:
                answer = (
                    "UNSUPPORTED — This question is outside "
                    "the supported dataset."
                )

                st.warning(answer)
                save_to_history(question, answer)

            else:
                # Generate SQL.
                with st.spinner("Generating SQL..."):
                    sql = ask_gemma(question, task="sql").strip()

                # Save unsupported SQL-generation responses too.
                if sql.upper().startswith("UNSUPPORTED"):
                    answer = (
                        "UNSUPPORTED — This question cannot be answered "
                        "using the available data."
                    )

                    st.warning(answer)
                    save_to_history(question, answer)

                else:
                    with st.expander("View generated SQL"):
                        st.code(sql, language="sql")

                    # Query Snowflake.
                    with st.spinner("Executing query on Snowflake..."):
                        columns, rows, query_id = run_query(sql)

                    st.markdown(
                        '<div class="section-title">Your results</div>',
                        unsafe_allow_html=True,
                    )

                    st.caption(f"Snowflake Query ID: {query_id}")

                    if not rows:
                        answer = "No matching records were returned by Snowflake."

                        st.info(answer)
                        save_to_history(question, answer)

                    else:
                        df = pd.DataFrame(rows, columns=columns)

                        numeric_columns = df.select_dtypes(
                            include="number"
                        ).columns

                        if len(df) == 1 and len(numeric_columns) == 1:
                            column = numeric_columns[0]
                            value = df.iloc[0][column]

                            if pd.notna(value):
                                formatted_value = f"{value:,.2f}"

                                st.markdown(
                                    f"""
                                    <div class="result-card">
                                        <div class="result-label">
                                            {html.escape(str(column).replace("_", " "))}
                                        </div>
                                        <div class="result-value">
                                            {html.escape(formatted_value)}
                                        </div>
                                        <div class="muted">
                                            Calculated from actual Snowflake results
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                        first, second, third = st.columns(3)

                        first.metric("Rows returned", f"{len(df):,}")
                        second.metric("Columns returned", f"{len(df.columns):,}")
                        third.metric("Data source", "Snowflake")

                        st.markdown("#### 📋 Detailed data")

                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=True,
                        )

                        # Explain the actual results using Gemma.
                        with st.spinner("Gemma is explaining the results..."):
                            explanation = ask_gemma(
                                question,
                                data=rows,
                                task="explain",
                            )

                        explanation = str(explanation)

                        st.markdown("#### ✨ AI explanation")

                        st.markdown(
                            f"""
                            <div class="explanation-card">
                                <div class="explanation-heading">
                                    What the data tells us
                                </div>
                                <div style="color:#d4deef;line-height:1.8;">
                                    {html.escape(explanation)}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.download_button(
                            "⬇️ Download results as CSV",
                            data=df.to_csv(index=False).encode("utf-8"),
                            file_name="datamind_results.csv",
                            mime="text/csv",
                        )

                        # Store the successful question and answer.
                        save_to_history(question, explanation)

                        st.success(
                            "Question and answer saved in Chat History."
                        )

                        with st.expander("Technical details"):
                            st.code(sql, language="sql")
                            st.write("Snowflake Query ID")
                            st.code(str(query_id))

        except Exception as error:
            st.error(f"Analysis failed: {error}")


# --------------------------------------------------
# EXAMPLE QUESTIONS
# --------------------------------------------------

if not run_analysis:
    st.markdown(
        '<div class="section-title">Try these questions</div>',
        unsafe_allow_html=True,
    )

    examples = [
        "What are the top selling products?",
        "What are the top 10 selling products?",
        "Give me the sum of the top 10 selling products.",
        "Which products generate the highest revenue?",
    ]

    for example in examples:
        st.markdown(
            '<div class="result-card" style="padding:13px 17px;">'
            f'{html.escape(example)}</div>',
            unsafe_allow_html=True,
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.markdown(
    '<p class="muted" style="text-align:center;">'
    'DataMind · AI-assisted analytics on Snowflake data</p>',
    unsafe_allow_html=True,
)
