# Chat-Sheet

An interactive, chat-driven spreadsheet interface that lets you query and manipulate CSV data with natural language (AI-powered) or raw SQL, backed by an embedded SQLite database.

---

## Features

- **Load CSV files** into SQLite tables automatically, inferring schema.
- **Handle conflicts**: overwrite, rename, or skip if a table already exists.
- **List tables** currently in the database.
- **Execute raw SQL** against your data.
- **AI-powered SQL generation**: ask in plain English and get back a valid SQLite query + one-sentence explanation.
- **Single-script**: just `chat_sheet.py`, no other dependencies beyond the ones listed.

---

## Requirements

- Python **3.7** or higher  
- `pandas`  
- `openai`  
- `sqlite3` is part of the Python stdlib.

Install dependencies with:

```bash
pip install pandas openai
```

---

## Setup

1. **Clone or download** this repo (or just save `chat_sheet.py` into a folder).
2. **Set your OpenAI API key** in the environment:

   ```bash
   $Env:OPENAI_API_KEY = 'sk......'
   ```

3. (Optional) Remove any existing database if you want a fresh start:

   ```bash
   rm chat_sheet.db
   ```

---

## Usage

Run the interactive CLI:

```bash
python chat_sheet.py
```

You’ll see:

```
Chat-Sheet CLI. Type 'help' for commands.
>
```

### Commands

- `help`  
  Show available commands.

- `load <path/to/file.csv>`  
  Load a CSV file as a new table.  
  - Prompts if a table of that name already exists:
    - **O**verwrite  
    - **R**ename  
    - **S**kip

- `list`  
  List all tables in the database.

- `sql <SQL statement>`  
  Execute raw SQL and print the rows.

- `ai <natural language request>`  
  Ask the AI to generate a valid SQLite query from plain English, then execute it.  
  Example:
  ```text
  > ai show me the top 5 highest-paid employees
  Executing SQL:
   SELECT * FROM sample ORDER BY Salary DESC LIMIT 5;

   Explanation:
   SELECT * FROM sample ORDER BY Salary DESC LIMIT 5;
  This query selects all columns from the `sample` table, orders the result by `Salary` in descending order, and limits the output to the top 5 highest-paid employees.
  ('Bob', 25, 'Engineering', 85000)
  ('Alice', 30, 'HR', 70000)
  ('Charlie', 35, 'Marketing', 65000)
  ('QSF', 30, 'HR', 30000)
  ('asdasf', 30, 'HR', 20000)
  ```

- `exit` or `quit`  
  Exit the CLI.

---

## How It Works

1. **Loading CSV**  
   Uses `pandas.read_csv()` to ingest data and writes it into SQLite via `DataFrame.to_sql()`.

2. **Conflict Resolution**  
   Queries `sqlite_master` to see if a table exists, then prompts you to overwrite, rename, or skip.

3. **Chat Loop**  
   A simple `while True` REPL reads commands, parses the first word as the action, and dispatches accordingly.

4. **AI SQL Generation**  
   - Gathers schema via `PRAGMA table_info` for each table.  
   - Builds a prompt with schema + user request.  
   - Calls OpenAI’s ChatCompletion endpoint.  
   - Extracts the first line as SQL, prints it and the explanation, then executes it.

---

## Customization

- **Model**  
  By default, it uses `gpt-3.5-turbo`. Change the model name in `generate_sql_via_ai()` if you have access to another.

- **Database file**  
  Defaults to `chat_sheet.db`. Update `sqlite3.connect(...)` in `main()` to point elsewhere.

---


