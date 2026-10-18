# DataMind — AI Data Analyst

DataMind is an open-source AI data analyst that lets users ask natural-language questions about sales data. It uses Google Gemma through Ollama to generate SQL, Snowflake to execute queries on real data, and Gemma again to explain the results.

## Features

- Ask sales-related questions in natural language.
- Generate and display SQL queries.
- Execute queries against Snowflake.
- Display actual query results in a table.
- Explain results using Gemma, grounded in returned data.
- Reject unsupported questions instead of intentionally inventing answers.
- Display Snowflake query execution evidence when available.

## Tech Stack

- **Language:** Python
- **UI:** Streamlit
- **Database:** Snowflake
- **AI model:** Google Gemma (`gemma3:4b`)
- **Local model runtime:** Ollama

## Architecture

1. The user enters a question in the Streamlit interface.
2. Gemma interprets the question and generates a SQL query.
3. The application validates the generated SQL.
4. The Snowflake client executes the query against the sample dataset.
5. Streamlit displays the SQL and actual results.
6. Gemma explains the results returned by Snowflake.

```text
User Question
     |
     v
Streamlit (app.py)
     |
     v
Gemma via Ollama (gemma_client.py)
     |
     v
SQL Validation
     |
     v
Snowflake (snowflake_client.py)
     |
     v
Actual Results
     |
     v
Gemma Explanation
     |
     v
Results displayed to user
```

## Data Source

DataMind currently uses Snowflake's sample dataset:

- **Database:** `SNOWFLAKE_SAMPLE_DATA`
- **Schema:** `TPCH_SF1`
- **Tables:** `LINEITEM`, `PART`

The application uses these tables to calculate product revenue from line-item prices and discounts.

The sample data is hosted by Snowflake; this repository does not need to include a local copy. Check Snowflake's documentation for data access and applicable usage terms.

## Requirements

- Python installed on your computer
- A Snowflake account with access to `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`
- Ollama installed
- The `gemma3:4b` model downloaded through Ollama

## Setup and Run

### 1. Clone the repository

```bash
git clone https://github.com/ZERODAY-2026/Coders.git
cd Coders
```

### 2. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Install and start Gemma

Install Ollama, then download the model:

```bash
ollama pull gemma3:4b
```

Ensure the Ollama service is running before using the application.

### 5. Configure Snowflake credentials

Create a `.env` file in the project root:

```env
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_ROLE=your_role
```

Replace the example values with your own Snowflake credentials. Never commit `.env` or expose passwords, tokens, or other secrets.

### 6. Run DataMind

```bash
streamlit run app.py
```

Open the local URL shown in the terminal.

## Current Scope and Limitations

- The current implementation focuses on product-revenue questions using `LINEITEM` and `PART`.
- Date/year-based filtering is currently unsupported.
- Employee and salary questions are outside the supported dataset.
- Generated SQL must be validated before execution.
- Answers depend on the data returned by Snowflake and should not be treated as independently verified business advice.

## Troubleshooting

- **Ollama connection error:** Ensure Ollama is installed, the service is running, and `gemma3:4b` is available.
- **Snowflake connection error:** Check the `.env` values, warehouse, role, and dataset permissions.
- **SQL compilation error:** Check the generated query's table names and column names.
- **Missing dependency:** Activate the virtual environment and run `python -m pip install -r requirements.txt`.

## Security

- Keep `.env` out of Git.
- Do not commit `.venv/`, credentials, or local secrets.
- Only execute validated, read-only queries.

## License

This project is intended to be open source. Add the chosen open-source license in a `LICENSE` file before publishing the final submission.
