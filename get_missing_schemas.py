import sqlite3

def get_table_schema(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    row = cursor.fetchone()
    if row:
        print(f"--- Schema for {table_name} ---")
        print(row[0])
    else:
        print(f"Table {table_name} not found.")
    conn.close()

tables = ['associated_titles', 'category_budget_limits', 'delete_logs', 'scanner_templates']
for t in tables:
    get_table_schema('original-cashew-db.sql', t)
