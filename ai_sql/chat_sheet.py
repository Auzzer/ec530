#!/usr/bin/env python3
"""
chat_sheet.py

An interactive, chat-driven spreadsheet interface backed by SQLite.
Features:
  - Load CSV into tables
  - Resolve name conflicts
  - List tables
  - Execute raw SQL
  - AI-powered SQL generation via OpenAI
"""

import argparse
import logging
import os
import re
import sqlite3
from pathlib import Path

import pandas as pd
from openai import OpenAI, OpenAIError


def setup_logging(level: str) -> None:
    """Configure root logger with timestamped, leveled output."""
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=getattr(logging, level.upper(), logging.INFO),
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for DB path and API key."""
    parser = argparse.ArgumentParser(
        description="Chat-driven spreadsheet via SQLite + OpenAI"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("chat_sheet.db"),
        help="SQLite database file to use (default: chat_sheet.db)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="OpenAI API key (overrides OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    return parser.parse_args()


def load_csv_to_sqlite(
    conn: sqlite3.Connection, csv_path: Path, if_exists: str = "fail"
) -> None:
    """
    Load a CSV file into SQLite.
    - Infers table name from filename (stem of csv_path)
    - Uses pandas.to_sql with the given if_exists behavior
    """
    table = csv_path.stem
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        logging.error("CSV file not found: %s", csv_path)
        return

    try:
        df.to_sql(table, conn, if_exists=if_exists, index=False)
        logging.info("Loaded '%s' into table '%s'.", csv_path, table)
    except ValueError as ve:
        logging.error("Failed to load CSV: %s", ve)


def list_tables(conn: sqlite3.Connection) -> None:
    """List all tables in the SQLite database."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cur]
    if tables:
        logging.info("Tables: %s", ", ".join(tables))
    else:
        logging.info("No tables found.")


def execute_sql(conn: sqlite3.Connection, sql: str) -> None:
    """Execute raw SQL and print results."""
    try:
        rows = conn.execute(sql).fetchall()
        for row in rows:
            print(row)
    except sqlite3.Error as e:
        logging.error("SQL error: %s", e)


def generate_sql_via_ai(
    conn: sqlite3.Connection, user_query: str, client: OpenAI
) -> None:
    """Use OpenAI to translate natural language into SQL and run it."""
    # 1) Build schema context
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    schema_parts = []
    for (t,) in tables:
        cols = conn.execute(f"PRAGMA table_info({t})").fetchall()
        col_names = [c[1] for c in cols]
        schema_parts.append(f"{t}({', '.join(col_names)})")
    schema = "; ".join(schema_parts)

    # 2) Prepare system & user messages
    system_msg = (
        "You are an AI assistant that converts plain-English questions "
        "into valid SQLite queries."
    )
    user_msg = (
        f"Database schema: {schema}\n"
        f"User request: {user_query}\n"
        "Respond with a single valid SQL query, then a one-sentence "
        "explanation on the next line."
    )

    # 3) Call the API
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0,
        )
    except OpenAIError as e:
        logging.error("OpenAI API error: %s", e)
        return

    # 4) Strip Markdown fences, extract SQL & explanation
    raw = resp.choices[0].message.content or ""
    m = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", raw)
    if m:
        sql = m.group(1).strip()
        explanation = "\n".join(raw.splitlines()[1:])
    else:
        # fallback: first non-fence line as SQL
        lines = [ln for ln in raw.splitlines() if ln and not ln.startswith("```")]
        sql = lines[0].strip() if lines else ""
        explanation = "\n".join(lines[1:]) if len(lines) > 1 else ""

    if not sql:
        logging.warning("Could not parse SQL from AI response.")
        return

    print("Executing SQL:\n", sql)
    print("\n Explanation:\n", explanation)

    # 5) Execute and display results
    execute_sql(conn, sql)


def main():
    args = parse_args()
    setup_logging(args.log_level)

    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.error("OpenAI API key not provided.")
        return

    client = OpenAI(api_key=api_key)
    conn = sqlite3.connect(str(args.db))

    logging.info("Starting Chat-Sheet (DB: %s)", args.db)
    try:
        while True:
            raw = input("> ").strip()
            if not raw:
                continue
            cmd, *rest = raw.split(maxsplit=1)
            arg = rest[0] if rest else ""

            if cmd in ("exit", "quit"):
                break
            if cmd == "help":
                print(
                    "Commands:\n"
                    "  load <file.csv> [append|replace|fail]\n"
                    "  list\n"
                    "  sql <SQL>\n"
                    "  ai <natural language>\n"
                    "  help\n"
                    "  exit"
                )
            elif cmd == "load":
                parts = arg.split()
                path = Path(parts[0])
                mode = parts[1] if len(parts) > 1 else "fail"
                load_csv_to_sqlite(conn, path, if_exists=mode)
            elif cmd == "list":
                list_tables(conn)
            elif cmd == "sql":
                execute_sql(conn, arg)
            elif cmd == "ai":
                generate_sql_via_ai(conn, arg, client)
            else:
                logging.warning("Unknown command: %s", cmd)
    finally:
        conn.close()
        logging.info("Goodbye.")


if __name__ == "__main__":
    main()
