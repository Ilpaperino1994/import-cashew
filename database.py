import sqlite3
import time
from typing import List
from models import ProcessedTransaction, AccountConfig, CashewConfig

class CashewDatabase:
    def __init__(self):
        # Database in memoria per validazione e sicurezza
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        self._init_schema()
        
    def _init_schema(self):
        # Ricrea lo schema minimo di Cashew
        self.cursor.execute('CREATE TABLE "wallets" ("wallet_pk" TEXT, "name" TEXT, "colour" TEXT, "date_created" INTEGER, "archived" INTEGER, "exclude_from_total" INTEGER, "currency" TEXT, "exclude_from_stats" INTEGER, "order" INTEGER, "goal_amount" REAL, "goal_date" INTEGER);')
        self.cursor.execute('CREATE TABLE "categories" ("category_pk" TEXT, "name" TEXT, "colour" TEXT, "icon_name" TEXT, "emoji_icon_name" TEXT, "date_created" INTEGER, "date_time_modified" INTEGER, "order" INTEGER, "income" INTEGER, "method_added" INTEGER, "main_category_pk" TEXT);')
        self.cursor.execute('CREATE TABLE "transactions" ("transaction_pk" TEXT, "paired_transaction_fk" TEXT, "name" TEXT, "amount" REAL, "note" TEXT, "category_fk" TEXT, "sub_category_fk" TEXT, "wallet_fk" TEXT, "date_created" INTEGER, "date_time_modified" INTEGER, "original_date_due" INTEGER, "income" INTEGER, "period_length" INTEGER, "reoccurrence" INTEGER, "end_date" INTEGER, "upcoming_transaction_notification" INTEGER, "type" INTEGER, "paid" INTEGER, "created_another_future_transaction" INTEGER, "skip_paid" INTEGER, "method_added" INTEGER, "transaction_owner_email" TEXT, "transaction_original_owner_email" TEXT, "shared_key" TEXT, "shared_old_key" TEXT, "shared_status" INTEGER, "shared_date_updated" INTEGER, "shared_reference_budget_pk" TEXT, "objective_fk" TEXT, "objective_loan_fk" TEXT, "budget_fks_exclude" TEXT);')

    def add_wallet(self, pk: str, config: AccountConfig):
        query = """INSERT INTO wallets VALUES (?, ?, ?, ?, 1, 0, ?, 0, 0, NULL, NULL)"""
        now = int(time.time()*1000)
        # SQLite parametrizzato: Previene SQL Injection e errori di sintassi
        self.cursor.execute(query, (pk, config.name_cashew, config.color, now, config.currency))

    def add_category(self, pk: str, name: str, color: str, icon: str, parent_pk: str = None):
        query = """INSERT INTO categories VALUES (?, ?, ?, ?, NULL, ?, 1765015012, 0, 0, 0, ?)"""
        now = int(time.time()*1000)
        self.cursor.execute(query, (pk, name, color, icon, now, parent_pk))

    def add_transaction(self, t: ProcessedTransaction):
        query = """
        INSERT INTO transactions (
            transaction_pk, paired_transaction_fk, name, amount, note, 
            category_fk, wallet_fk, date_created, income, paid, 
            date_time_modified, original_date_due, upcoming_transaction_notification,
            skip_paid, created_another_future_transaction
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1765015012, 1765015012, 1, 0, 0)
        """
        # Nota: usiamo parametri named o posizionali. Qui posizionali per brevità.
        self.cursor.execute(query, (
            t.id, t.paired_id, t.title, t.amount, t.note, 
            t.category_fk, t.wallet_fk, t.date_ms, 1 if t.is_income else 0
        ))

    def get_sql_dump(self) -> str:
        """Restituisce il dump SQL completo per l'importazione"""
        self.conn.commit()
        lines = []
        lines.append("BEGIN TRANSACTION;")
        lines.append("DELETE FROM wallets;")
        lines.append("DELETE FROM categories;")
        lines.append("DELETE FROM transactions;")
        
        for line in self.conn.iterdump():
            if line.startswith("INSERT INTO"):
                lines.append(line)
        
        lines.append("COMMIT;")
        return "\n".join(lines)