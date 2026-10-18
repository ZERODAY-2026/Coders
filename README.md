# DataMind — AI Data Analyst

DataMind lets users ask questions about sales data in natural language.

## Tech Stack
- Python
- Streamlit
- Snowflake
- Google Gemma via Ollama

## Features
- Ask questions in a simple interface
- Fetch real data from Snowflake
- Display SQL queries and results
- Generate AI explanations using Gemma

## Setup
1. Install Python.
2. Install Ollama and download Gemma.
3. Install dependencies:

   pip install -r requirements.txt

4. Configure Snowflake credentials in `.env`.
5. Run the app:

   streamlit run app.py