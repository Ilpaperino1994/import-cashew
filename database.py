import sqlite3
import time
import tempfile
from typing import List, Optional
from models import ProcessedTransaction, AccountConfig, CashewConfig

class CashewDatabase:
    def __init__(self):
        # Database in memoria per validazione e sicurezza
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        self._init_schema()
        
    def _init_schema(self):
        # 1. Wallets
        self.cursor.execute('CREATE TABLE "wallets" ("wallet_pk" TEXT NOT NULL, "name" TEXT NOT NULL, "colour" TEXT NULL, "icon_name" TEXT NULL, "date_created" INTEGER NOT NULL, "date_time_modified" INTEGER NULL DEFAULT 1765012419, "order" INTEGER NOT NULL, "currency" TEXT NULL, "currency_format" TEXT NULL, "decimals" INTEGER NOT NULL DEFAULT 2, "home_page_widget_display" TEXT NULL DEFAULT NULL, PRIMARY KEY ("wallet_pk"));')

        # 2. Categories
        self.cursor.execute('CREATE TABLE "categories" ("category_pk" TEXT NOT NULL, "name" TEXT NOT NULL, "colour" TEXT NULL, "icon_name" TEXT NULL, "emoji_icon_name" TEXT NULL, "date_created" INTEGER NOT NULL, "date_time_modified" INTEGER NULL DEFAULT 1765012419, "order" INTEGER NOT NULL, "income" INTEGER NOT NULL DEFAULT 0 CHECK ("income" IN (0, 1)), "method_added" INTEGER NULL, "main_category_pk" TEXT NULL DEFAULT NULL REFERENCES categories (category_pk), PRIMARY KEY ("category_pk"));')

        # 3. Transactions
        self.cursor.execute('CREATE TABLE "transactions" ("transaction_pk" TEXT NOT NULL, "paired_transaction_fk" TEXT NULL DEFAULT NULL REFERENCES transactions (transaction_pk), "name" TEXT NOT NULL, "amount" REAL NOT NULL, "note" TEXT NOT NULL, "category_fk" TEXT NOT NULL REFERENCES categories (category_pk), "sub_category_fk" TEXT NULL DEFAULT NULL REFERENCES categories (category_pk), "wallet_fk" TEXT NOT NULL DEFAULT "0" REFERENCES wallets (wallet_pk), "date_created" INTEGER NOT NULL, "date_time_modified" INTEGER NULL DEFAULT 1765012419, "original_date_due" INTEGER NULL DEFAULT 1765012419, "income" INTEGER NOT NULL DEFAULT 0 CHECK ("income" IN (0, 1)), "period_length" INTEGER NULL, "reoccurrence" INTEGER NULL, "end_date" INTEGER NULL, "upcoming_transaction_notification" INTEGER NULL DEFAULT 1 CHECK ("upcoming_transaction_notification" IN (0, 1)), "type" INTEGER NULL, "paid" INTEGER NOT NULL DEFAULT 0 CHECK ("paid" IN (0, 1)), "created_another_future_transaction" INTEGER NULL DEFAULT 0 CHECK ("created_another_future_transaction" IN (0, 1)), "skip_paid" INTEGER NOT NULL DEFAULT 0 CHECK ("skip_paid" IN (0, 1)), "method_added" INTEGER NULL, "transaction_owner_email" TEXT NULL, "transaction_original_owner_email" TEXT NULL, "shared_key" TEXT NULL, "shared_old_key" TEXT NULL, "shared_status" INTEGER NULL, "shared_date_updated" INTEGER NULL, "shared_reference_budget_pk" TEXT NULL, "objective_fk" TEXT NULL, "objective_loan_fk" TEXT NULL, "budget_fks_exclude" TEXT NULL, PRIMARY KEY ("transaction_pk"));')

        # 4. Budgets & Objectives
        self.cursor.execute('CREATE TABLE "budgets" ("budget_pk" TEXT NOT NULL, "name" TEXT NOT NULL, "amount" REAL NOT NULL, "colour" TEXT NULL, "start_date" INTEGER NOT NULL, "end_date" INTEGER NOT NULL, "wallet_fks" TEXT NULL, "category_fks" TEXT NULL, "category_fks_exclude" TEXT NULL, "income" INTEGER NOT NULL DEFAULT 0 CHECK ("income" IN (0, 1)), "archived" INTEGER NOT NULL DEFAULT 0 CHECK ("archived" IN (0, 1)), "added_transactions_only" INTEGER NOT NULL DEFAULT 0 CHECK ("added_transactions_only" IN (0, 1)), "period_length" INTEGER NOT NULL, "reoccurrence" INTEGER NULL, "date_created" INTEGER NOT NULL, "date_time_modified" INTEGER NULL DEFAULT 1765012419, "pinned" INTEGER NOT NULL DEFAULT 0 CHECK ("pinned" IN (0, 1)), "order" INTEGER NOT NULL, "wallet_fk" TEXT NOT NULL DEFAULT "0" REFERENCES wallets (wallet_pk), "budget_transaction_filters" TEXT NULL DEFAULT NULL, "member_transaction_filters" TEXT NULL DEFAULT NULL, "shared_key" TEXT NULL, "shared_owner_member" INTEGER NULL, "shared_date_updated" INTEGER NULL, "shared_members" TEXT NULL, "shared_all_members_ever" TEXT NULL, "is_absolute_spending_limit" INTEGER NOT NULL DEFAULT 0 CHECK ("is_absolute_spending_limit" IN (0, 1)), PRIMARY KEY ("budget_pk"));')
        self.cursor.execute('CREATE TABLE "objectives" ("objective_pk" TEXT NOT NULL, "type" INTEGER NOT NULL DEFAULT 0, "name" TEXT NOT NULL, "amount" REAL NOT NULL, "order" INTEGER NOT NULL, "colour" TEXT NULL, "date_created" INTEGER NOT NULL, "end_date" INTEGER NULL, "date_time_modified" INTEGER NULL DEFAULT 1765012419, "icon_name" TEXT NULL, "emoji_icon_name" TEXT NULL, "income" INTEGER NOT NULL DEFAULT 0 CHECK ("income" IN (0, 1)), "pinned" INTEGER NOT NULL DEFAULT 1 CHECK ("pinned" IN (0, 1)), "archived" INTEGER NOT NULL DEFAULT 0 CHECK ("archived" IN (0, 1)), "wallet_fk" TEXT NOT NULL DEFAULT "0" REFERENCES wallets (wallet_pk), PRIMARY KEY ("objective_pk"));')

        # 5. Missing Aux Tables
        self.cursor.execute('CREATE TABLE "app_settings" ("settings_pk" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "settings_j_s_o_n" TEXT NOT NULL, "date_updated" INTEGER NOT NULL);')
        self.cursor.execute('CREATE TABLE "associated_titles" ("associated_title_pk" TEXT NOT NULL, "category_fk" TEXT NOT NULL REFERENCES categories (category_pk), "title" TEXT NOT NULL, "date_created" INTEGER NOT NULL, "date_time_modified" INTEGER NULL DEFAULT 1765012419, "order" INTEGER NOT NULL, "is_exact_match" INTEGER NOT NULL DEFAULT 0 CHECK ("is_exact_match" IN (0, 1)), PRIMARY KEY ("associated_title_pk"));')
        self.cursor.execute('CREATE TABLE "category_budget_limits" ("category_limit_pk" TEXT NOT NULL, "category_fk" TEXT NOT NULL REFERENCES categories (category_pk), "budget_fk" TEXT NOT NULL REFERENCES budgets (budget_pk), "amount" REAL NOT NULL, "date_time_modified" INTEGER NULL DEFAULT 1765012419, "wallet_fk" TEXT NOT NULL DEFAULT "0" REFERENCES wallets (wallet_pk), PRIMARY KEY ("category_limit_pk"));')
        self.cursor.execute('CREATE TABLE "delete_logs" ("delete_log_pk" TEXT NOT NULL, "entry_pk" TEXT NOT NULL, "type" INTEGER NOT NULL, "date_time_modified" INTEGER NOT NULL DEFAULT 1765012419, PRIMARY KEY ("delete_log_pk"));')
        self.cursor.execute('CREATE TABLE "scanner_templates" ("scanner_template_pk" TEXT NOT NULL, "date_created" INTEGER NOT NULL, "date_time_modified" INTEGER NULL DEFAULT 1765012419, "template_name" TEXT NOT NULL, "contains" TEXT NOT NULL, "title_transaction_before" TEXT NOT NULL, "title_transaction_after" TEXT NOT NULL, "amount_transaction_before" TEXT NOT NULL, "amount_transaction_after" TEXT NOT NULL, "default_category_fk" TEXT NOT NULL REFERENCES categories (category_pk), "wallet_fk" TEXT NOT NULL DEFAULT "0" REFERENCES wallets (wallet_pk), "ignore" INTEGER NOT NULL DEFAULT 0 CHECK ("ignore" IN (0, 1)), PRIMARY KEY ("scanner_template_pk"));')

        # Insert Default Settings
        now = int(time.time()*1000)
        self.cursor.execute('INSERT INTO app_settings (settings_j_s_o_n, date_updated) VALUES (?, ?)', ('{}', now))

    def add_wallet(self, pk: str, config: AccountConfig):
        query = """INSERT INTO wallets VALUES (?, ?, ?, NULL, ?, ?, 0, ?, NULL, 2, NULL)"""
        now = int(time.time()*1000)
        self.cursor.execute(query, (pk, config.name_cashew, config.color, now, now, config.currency))

    def add_category(self, pk: str, name: str, color: str, icon: str, parent_pk: str = None, income: bool = False):
        query = """INSERT INTO categories VALUES (?, ?, ?, ?, NULL, ?, ?, 0, ?, 0, ?)"""
        now = int(time.time()*1000)

        # Logic for income detection: explicitly passed OR name is 'Reddito' (case insensitive)
        is_income = 1 if (income or name.lower() == "reddito") else 0

        self.cursor.execute(query, (pk, name, color, icon, now, now, is_income, parent_pk))

    def add_transaction(self, t: ProcessedTransaction):
        query = """
        INSERT INTO transactions (
            transaction_pk, paired_transaction_fk, name, amount, note, 
            category_fk, wallet_fk, date_created, income, paid, 
            date_time_modified, original_date_due, upcoming_transaction_notification,
            skip_paid, created_another_future_transaction, sub_category_fk
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 1, 0, 0, ?)
        """
        self.cursor.execute(query, (
            t.id, t.paired_id, t.title, t.amount, t.note, 
            t.category_fk, t.wallet_fk, t.date_ms, 1 if t.is_income else 0,
            t.date_ms, t.date_ms, t.sub_category_fk
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
        with tempfile.NamedTemporaryFile() as tmp:
            dest_conn = sqlite3.connect(tmp.name)
            self.conn.backup(dest_conn)
            dest_conn.close()
            tmp.seek(0)
            return tmp.read()
