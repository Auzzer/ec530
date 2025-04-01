import sqlite3
import pandas as pd
import logging
import os

# Setup logging to capture errors in error_log.txt
logging.basicConfig(filename='error_log.txt',
                    level=logging.ERROR,
                    format='%(asctime)s %(levelname)s: %(message)s')

def infer_sqlite_type(series):
    """
    Infer the SQLite data type for a pandas Series.
    """
    if pd.api.types.is_integer_dtype(series):
        return "INTEGER"
    elif pd.api.types.is_float_dtype(series):
        return "REAL"
    else:
        return "TEXT"

def create_table_from_dataframe(conn, df, table_name):
    """
    Create a SQLite table with a schema inferred from the dataframe.
    """
    columns = df.columns
    schema_parts = []
    for col in columns:
        dtype = infer_sqlite_type(df[col])
        schema_parts.append(f'"{col}" {dtype}')
    schema_str = ", ".join(schema_parts)
    create_table_sql = f'CREATE TABLE "{table_name}" ({schema_str});'
    
    try:
        cur = conn.cursor()
        cur.execute(create_table_sql)
        conn.commit()
        print(f"Table '{table_name}' created successfully.")
    except Exception as e:
        logging.error(f"Error creating table {table_name}: {str(e)}")
        print(f"Error creating table '{table_name}'. Check error_log.txt for details.")

def table_exists(conn, table_name):
    """
    Check if a table exists in the SQLite database.
    """
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
    return cur.fetchone() is not None

def drop_table(conn, table_name):
    """
    Drop an existing table from the SQLite database.
    """
    try:
        cur = conn.cursor()
        cur.execute(f'DROP TABLE IF EXISTS "{table_name}";')
        conn.commit()
        print(f"Table '{table_name}' dropped.")
    except Exception as e:
        logging.error(f"Error dropping table {table_name}: {str(e)}")
        print(f"Error dropping table '{table_name}'. Check error_log.txt for details.")

def load_csv_to_db(conn):
    """
    Load a CSV file into the SQLite database by:
      - Reading the CSV with pandas.
      - Inferring the schema and creating the table dynamically.
      - Inserting the CSV data into the created table.
    """
    csv_path = input("Enter CSV file path: ").strip()
    if not os.path.isfile(csv_path):
        print("CSV file not found.")
        return
    table_name = input("Enter desired table name: ").strip()
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logging.error(f"Error reading CSV file {csv_path}: {str(e)}")
        print("Error reading CSV file. Check error_log.txt for details.")
        return

    if table_exists(conn, table_name):
        print(f"Table '{table_name}' already exists.")
        choice = input("Do you want to Overwrite (O), Rename (R), or Skip (S) this table? ").strip().upper()
        if choice == 'O':
            drop_table(conn, table_name)
        elif choice == 'R':
            new_table_name = input("Enter new table name: ").strip()
            table_name = new_table_name
        elif choice == 'S':
            print("Skipping CSV load.")
            return
        else:
            print("Invalid choice. Skipping CSV load.")
            return

    create_table_from_dataframe(conn, df, table_name)
    try:
        # Use if_exists='append' to insert data after table creation
        df.to_sql(table_name, conn, if_exists='append', index=False)
        print(f"Data inserted into table '{table_name}' successfully.")
    except Exception as e:
        logging.error(f"Error inserting data into table {table_name}: {str(e)}")
        print("Error inserting data into table. Check error_log.txt for details.")

def list_tables(conn):
    """
    List all tables in the SQLite database.
    """
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    if tables:
        print("Existing tables:")
        for table in tables:
            print(" - " + table[0])
    else:
        print("No tables found in the database.")

def run_sql_query(conn):
    """
    Execute a SQL query entered by the user and print the results.
    """
    query = input("Enter your SQL query: ").strip()
    try:
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        if rows:
            for row in rows:
                print(row)
        else:
            print("Query executed successfully. No rows returned.")
    except Exception as e:
        logging.error(f"Error executing query '{query}': {str(e)}")
        print("Error executing query. Check error_log.txt for details.")

def convert_natural_language_to_sql():
    """
    Simulate converting a natural language query into a SQL statement.
    In a real implementation, this function might call an LLM API.
    """
    nl_query = input("Enter your natural language query: ").strip()
    # For demonstration, a simple hard-coded example mapping is provided.
    if "top 5 products by total revenue this month" in nl_query.lower():
        sql_query = """
        SELECT p.product_name, SUM(s.revenue) AS total_revenue
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        WHERE strftime('%Y-%m', s.sale_date) = strftime('%Y-%m', 'now')
        GROUP BY p.product_name
        ORDER BY total_revenue DESC
        LIMIT 5;
        """
        print("Generated SQL query:")
        print(sql_query)
        return sql_query
    else:
        print("No mapping found for the provided natural language query.")
        return None

def main():
    """
    Main CLI loop for interacting with the SQLite database.
    Options include:
      1. Loading a CSV file.
      2. Listing existing tables.
      3. Running a SQL query.
      4. Converting a natural language query to SQL.
      5. Exiting the application.
    """
    db_path = "example.db"
    conn = sqlite3.connect(db_path)
    print("Connected to SQLite database.")

    while True:
        print("\nOptions:")
        print("1. Load CSV into database")
        print("2. List tables")
        print("3. Run a SQL query")
        print("4. Convert natural language query to SQL")
        print("5. Exit")
        choice = input("Enter your choice (1-5): ").strip()

        if choice == "1":
            load_csv_to_db(conn)
        elif choice == "2":
            list_tables(conn)
        elif choice == "3":
            run_sql_query(conn)
        elif choice == "4":
            sql_query = convert_natural_language_to_sql()
            if sql_query:
                run_now = input("Do you want to execute the generated SQL query? (Y/N): ").strip().upper()
                if run_now == "Y":
                    try:
                        cur = conn.cursor()
                        cur.execute(sql_query)
                        rows = cur.fetchall()
                        if rows:
                            for row in rows:
                                print(row)
                        else:
                            print("Query executed successfully. No rows returned.")
                    except Exception as e:
                        logging.error(f"Error executing generated query: {str(e)}")
                        print("Error executing generated query. Check error_log.txt for details.")
        elif choice == "5":
            print("Exiting the assistant.")
            break
        else:
            print("Invalid option. Please try again.")

    conn.close()

if __name__ == "__main__":
    main()
