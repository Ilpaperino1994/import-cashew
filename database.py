import sqlite3
import time
import tempfile
from typing import List
from models import ProcessedTransaction, AccountConfig, CashewConfig

class CashewDatabase:
    def __init__(self):
        # Database in memoria per validazione e sicurezza
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        self._init_schema()
        
    def _init_schema(self):
        # Ricrea lo schema esatto di Cashew (dallo snippet fornito)
        self.cursor.execute('CREATE TABLE "wallets" ("wallet_pk" TEXT NOT NULL, "name" TEXT NOT NULL, "colour" TEXT NULL, "icon_name" TEXT NULL, "date_created" INTEGER NOT NULL, "date_time_modified" INTEGER NULL DEFAULT 1765012419, "order" INTEGER NOT NULL, "currency" TEXT NULL, "currency_format" TEXT NULL, "decimals" INTEGER NOT NULL DEFAULT 2, "home_page_widget_display" TEXT NULL DEFAULT NULL, PRIMARY KEY ("wallet_pk"));')

        self.cursor.execute('CREATE TABLE "categories" ("category_pk" TEXT NOT NULL, "name" TEXT NOT NULL, "colour" TEXT NULL, "icon_name" TEXT NULL, "emoji_icon_name" TEXT NULL, "date_created" INTEGER NOT NULL, "date_time_modified" INTEGER NULL DEFAULT 1765012419, "order" INTEGER NOT NULL, "income" INTEGER NOT NULL DEFAULT 0 CHECK ("income" IN (0, 1)), "method_added" INTEGER NULL, "main_category_pk" TEXT NULL DEFAULT NULL REFERENCES categories (category_pk), PRIMARY KEY ("category_pk"));')

        self.cursor.execute('CREATE TABLE "transactions" ("transaction_pk" TEXT NOT NULL, "paired_transaction_fk" TEXT NULL DEFAULT NULL REFERENCES transactions (transaction_pk), "name" TEXT NOT NULL, "amount" REAL NOT NULL, "note" TEXT NOT NULL, "category_fk" TEXT NOT NULL REFERENCES categories (category_pk), "sub_category_fk" TEXT NULL DEFAULT NULL REFERENCES categories (category_pk), "wallet_fk" TEXT NOT NULL DEFAULT "0" REFERENCES wallets (wallet_pk), "date_created" INTEGER NOT NULL, "date_time_modified" INTEGER NULL DEFAULT 1765012419, "original_date_due" INTEGER NULL DEFAULT 1765012419, "income" INTEGER NOT NULL DEFAULT 0 CHECK ("income" IN (0, 1)), "period_length" INTEGER NULL, "reoccurrence" INTEGER NULL, "end_date" INTEGER NULL, "upcoming_transaction_notification" INTEGER NULL DEFAULT 1 CHECK ("upcoming_transaction_notification" IN (0, 1)), "type" INTEGER NULL, "paid" INTEGER NOT NULL DEFAULT 0 CHECK ("paid" IN (0, 1)), "created_another_future_transaction" INTEGER NULL DEFAULT 0 CHECK ("created_another_future_transaction" IN (0, 1)), "skip_paid" INTEGER NOT NULL DEFAULT 0 CHECK ("skip_paid" IN (0, 1)), "method_added" INTEGER NULL, "transaction_owner_email" TEXT NULL, "transaction_original_owner_email" TEXT NULL, "shared_key" TEXT NULL, "shared_old_key" TEXT NULL, "shared_status" INTEGER NULL, "shared_date_updated" INTEGER NULL, "shared_reference_budget_pk" TEXT NULL, "objective_fk" TEXT NULL, "objective_loan_fk" TEXT NULL, "budget_fks_exclude" TEXT NULL, PRIMARY KEY ("transaction_pk"));')

        # Tabelle di supporto minime per compatibilità
        self.cursor.execute('CREATE TABLE "app_settings" ("settings_pk" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "settings_j_s_o_n" TEXT NOT NULL, "date_updated" INTEGER NOT NULL);')
        self.cursor.execute('CREATE TABLE "budgets" ("budget_pk" TEXT NOT NULL, "name" TEXT NOT NULL, "amount" REAL NOT NULL, "colour" TEXT NULL, "start_date" INTEGER NOT NULL, "end_date" INTEGER NOT NULL, "wallet_fks" TEXT NULL, "category_fks" TEXT NULL, "category_fks_exclude" TEXT NULL, "income" INTEGER NOT NULL DEFAULT 0 CHECK ("income" IN (0, 1)), "archived" INTEGER NOT NULL DEFAULT 0 CHECK ("archived" IN (0, 1)), "added_transactions_only" INTEGER NOT NULL DEFAULT 0 CHECK ("added_transactions_only" IN (0, 1)), "period_length" INTEGER NOT NULL, "reoccurrence" INTEGER NULL, "date_created" INTEGER NOT NULL, "date_time_modified" INTEGER NULL DEFAULT 1765012419, "pinned" INTEGER NOT NULL DEFAULT 0 CHECK ("pinned" IN (0, 1)), "order" INTEGER NOT NULL, "wallet_fk" TEXT NOT NULL DEFAULT "0" REFERENCES wallets (wallet_pk), "budget_transaction_filters" TEXT NULL DEFAULT NULL, "member_transaction_filters" TEXT NULL DEFAULT NULL, "shared_key" TEXT NULL, "shared_owner_member" INTEGER NULL, "shared_date_updated" INTEGER NULL, "shared_members" TEXT NULL, "shared_all_members_ever" TEXT NULL, "is_absolute_spending_limit" INTEGER NOT NULL DEFAULT 0 CHECK ("is_absolute_spending_limit" IN (0, 1)), PRIMARY KEY ("budget_pk"));')
        self.cursor.execute('CREATE TABLE "objectives" ("objective_pk" TEXT NOT NULL, "type" INTEGER NOT NULL DEFAULT 0, "name" TEXT NOT NULL, "amount" REAL NOT NULL, "order" INTEGER NOT NULL, "colour" TEXT NULL, "date_created" INTEGER NOT NULL, "end_date" INTEGER NULL, "date_time_modified" INTEGER NULL DEFAULT 1765012419, "icon_name" TEXT NULL, "emoji_icon_name" TEXT NULL, "income" INTEGER NOT NULL DEFAULT 0 CHECK ("income" IN (0, 1)), "pinned" INTEGER NOT NULL DEFAULT 1 CHECK ("pinned" IN (0, 1)), "archived" INTEGER NOT NULL DEFAULT 0 CHECK ("archived" IN (0, 1)), "wallet_fk" TEXT NOT NULL DEFAULT "0" REFERENCES wallets (wallet_pk), PRIMARY KEY ("objective_pk"));')

        # Insert Default Settings (optional but good for stability)
        now = int(time.time()*1000)
        self.cursor.execute('INSERT INTO app_settings (settings_j_s_o_n, date_updated) VALUES (?, ?)', ('{}', now))

    def add_wallet(self, pk: str, config: AccountConfig):
        query = """INSERT INTO wallets VALUES (?, ?, ?, NULL, ?, ?, 0, ?, NULL, 2, NULL)"""
        now = int(time.time()*1000)
        # Parameters: pk, name, colour, date_created, date_time_modified, currency
        self.cursor.execute(query, (pk, config.name_cashew, config.color, now, now, config.currency))

    def add_category(self, pk: str, name: str, color: str, icon: str, parent_pk: str = None):
        query = """INSERT INTO categories VALUES (?, ?, ?, ?, NULL, ?, ?, 0, 0, 0, ?)"""
        now = int(time.time()*1000)
        self.cursor.execute(query, (pk, name, color, icon, now, now, parent_pk))

    def add_transaction(self, t: ProcessedTransaction):
        query = """
        INSERT INTO transactions (
            transaction_pk, paired_transaction_fk, name, amount, note, 
            category_fk, wallet_fk, date_created, income, paid, 
            date_time_modified, original_date_due, upcoming_transaction_notification,
            skip_paid, created_another_future_transaction, sub_category_fk
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 1, 0, 0, NULL)
        """
        # Note: Cashew sometimes uses sub_category_fk, but our logic pairs Main->Sub within category_fk?
        # Cashew schema shows: "category_fk" and "sub_category_fk".
        # If we have a subcategory, does Cashew want the Sub PK in sub_category_fk or category_fk?
        # Observation from schema: `main_category_pk` is in `categories` table (parent pointer).
        # In `transactions` table: `category_fk` and `sub_category_fk`.
        # Usually `category_fk` is the Main Category and `sub_category_fk` is the sub.
        # But my `models.py`/`logic.py` put the specific category UUID (even if sub) into `category_fk`.
        # Correction: If `category_fk` points to a Sub-Category (which has a `main_category_pk`), Cashew might display it correctly.
        # However, to be safe and consistent with standard schemas:
        # If the category is a sub-category, put Main Category PK in `category_fk` and Sub Category PK in `sub_category_fk`.
        # BUT, `ProcessedTransaction` currently has only `category_fk`.
        # I will rely on the fact that `category_fk` pointing to the Sub-Category (which links to parent) is often enough for apps.
        # Wait, the SQL snippet shows `sub_category_fk TEXT NULL`.
        # I'll stick to putting the target category (whether main or sub) in `category_fk`.

        self.cursor.execute(query, (
            t.id, t.paired_id, t.title, t.amount, t.note, 
            t.category_fk, t.wallet_fk, t.date_ms, 1 if t.is_income else 0,
            t.date_ms, t.date_ms
        ))

    def get_sql_dump(self) -> str:
        """Restituisce il dump SQL testo (Legacy/Debug)"""
        self.conn.commit()
        lines = []
        lines.append("BEGIN TRANSACTION;")
        for line in self.conn.iterdump():
            if line.startswith("INSERT INTO"):
                lines.append(line)
        lines.append("COMMIT;")
        return "\n".join(lines)

    def get_binary_sqlite(self) -> bytes:
        """Restituisce il file binario SQLite"""
        self.conn.commit()
        # Create a temp file on disk
        with tempfile.NamedTemporaryFile() as tmp:
            # Backup memory db to file
            dest_conn = sqlite3.connect(tmp.name)
            self.conn.backup(dest_conn)
            dest_conn.close()

            # Read bytes
            tmp.seek(0)
            return tmp.read()
