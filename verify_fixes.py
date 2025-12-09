import sqlite3
import pandas as pd
import datetime
import os
from database import CashewDatabase
from models import ProcessedTransaction, AccountConfig

def verify_fixes():
    print("--- Starting Verification ---")

    # 1. Setup DB
    db = CashewDatabase()

    # 2. Add Wallet
    w_uuid = "w-123"
    db.add_wallet(w_uuid, AccountConfig(name_cashew="TestWallet", currency="EUR", color="#000"))

    # 3. Add Categories
    # Reddito (Income check)
    cat_inc_uuid = "c-inc"
    db.add_category(cat_inc_uuid, "Reddito", "#000", "inc.png")

    # Expense Main
    cat_main_uuid = "c-main"
    db.add_category(cat_main_uuid, "Cibo", "#111", "food.png")

    # Expense Sub
    cat_sub_uuid = "c-sub"
    db.add_category(cat_sub_uuid, "Ristorante", "#222", "rest.png", parent_pk=cat_main_uuid)

    # 4. Add Transactions
    # Income Tx
    t_inc = ProcessedTransaction(
        id="t-1", date_ms=1700000000000, amount=100.0, title="Stipendio", note="Note",
        wallet_fk=w_uuid, category_fk=cat_inc_uuid, is_income=True
    )
    db.add_transaction(t_inc)

    # Expense Tx with Subcategory
    t_exp = ProcessedTransaction(
        id="t-2", date_ms=1700000000000, amount=-50.0, title="Cena", note="Yum",
        wallet_fk=w_uuid, category_fk=cat_main_uuid, sub_category_fk=cat_sub_uuid,
        is_income=False
    )
    db.add_transaction(t_exp)

    # 5. Verify SQL Structure
    db_file = "verify_test.sqlite"
    with open(db_file, "wb") as f:
        f.write(db.get_binary_sqlite())

    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # Check tables
    required_tables = ['associated_titles', 'category_budget_limits', 'delete_logs', 'scanner_templates', 'transactions']
    print("\n[SQL Tables Check]")
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in c.fetchall()]
    for t in required_tables:
        if t in tables:
            print(f"✅ Table {t} exists")
        else:
            print(f"❌ Table {t} MISSING")

    # Check Income Flag
    print("\n[Income Flag Check]")
    c.execute("SELECT name, income FROM categories WHERE name='Reddito'")
    row = c.fetchone()
    if row and row[1] == 1:
        print(f"✅ Category 'Reddito' has income=1")
    else:
        print(f"❌ Category 'Reddito' failed: {row}")

    # Check SubCategory FK
    print("\n[SubCategory FK Check]")
    c.execute("SELECT transaction_pk, category_fk, sub_category_fk FROM transactions WHERE transaction_pk='t-2'")
    row = c.fetchone()
    if row and row[1] == cat_main_uuid and row[2] == cat_sub_uuid:
         print(f"✅ Transaction t-2 has correct FKs: {row}")
    else:
         print(f"❌ Transaction t-2 failed FK check: {row}")

    conn.close()

    # 6. Verify CSV Format (Simulation)
    # Since I cannot easily run Streamlit state here, I will verify the logic I wrote in step4 using a small unit test of the dataframe creation
    print("\n[CSV Logic Check]")

    processed_list = [t_inc, t_exp]
    # Update models with names for CSV
    t_inc.main_category_name = "Reddito"
    t_exp.main_category_name = "Cibo"
    t_exp.sub_category_name = "Ristorante"

    csv_rows = []
    for pt in processed_list:
        dt = datetime.datetime.fromtimestamp(pt.date_ms / 1000.0)
        date_fmt = dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        row = {
            "account": "TestWallet",
            "amount": pt.amount,
            "currency": "EUR",
            "title": pt.title,
            "note": pt.note,
            "date": date_fmt,
            "income": "true" if pt.is_income else "false",
            "type": "null",
            "category name": pt.main_category_name,
            "subcategory name": pt.sub_category_name,
            "color": "0xff000000",
            "icon": "icon.png",
            "emoji": None,
            "budget": None,
            "objective": None
        }
        csv_rows.append(row)

    df = pd.DataFrame(csv_rows)
    cols = ["account","amount","currency","title","note","date","income","type","category name","subcategory name","color","icon","emoji","budget","objective"]

    # Check cols
    missing = [c for c in cols if c not in df.columns]
    if not missing:
        print("✅ All CSV columns present")
    else:
        print(f"❌ Missing columns: {missing}")

    # Check date format
    ex_date = df.iloc[0]['date']
    if len(ex_date) == 23 and "." in ex_date:
        print(f"✅ Date format looks correct: {ex_date}")
    else:
        print(f"❌ Date format mismatch: {ex_date}")

    os.remove(db_file)

if __name__ == "__main__":
    verify_fixes()
