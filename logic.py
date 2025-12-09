import pandas as pd
import uuid
import datetime
import time
from typing import List, Dict
from thefuzz import process
from models import WalletTransaction, CashewConfig, DEFAULT_CASHEW_STRUCTURE

def fix_encoding(text):
    if not isinstance(text, str): return text
    try: return text.encode('cp1252').decode('utf-8')
    except: return text

def parse_csv_to_models(file_buffer) -> List[WalletTransaction]:
    try:
        df = pd.read_csv(file_buffer, sep=';')
        if len(df.columns) < 2:
            file_buffer.seek(0)
            df = pd.read_csv(file_buffer, sep=',')
    except Exception as e:
        raise ValueError(f"Impossibile leggere il file. Assicurati sia un CSV valido. Errore: {str(e)}")

    transactions = []
    for _, row in df.iterrows():
        clean_row = {k: fix_encoding(v) for k, v in row.to_dict().items()}
        is_transf = str(clean_row.get('transfer', 'false')).lower() == 'true' or \
                    str(clean_row.get('type', '')).upper() == 'TRANSFER'
        
        try:
            t = WalletTransaction(
                account=clean_row.get('account', 'Unknown'),
                category=clean_row.get('category', 'Uncategorized'),
                amount=clean_row.get('amount', 0),
                currency=clean_row.get('currency', 'EUR'),
                note=str(clean_row.get('note', '')),
                payee=str(clean_row.get('payee', '')),
                date=str(clean_row.get('date', '')),
                is_transfer=is_transf
            )
            transactions.append(t)
        except: continue
    return transactions

def ai_suggest_mapping(wallet_cats: List[str], cashew_structure: Dict) -> Dict[str, dict]:
    """Suggerisce il mapping basandosi sulla struttura complessa (Main -> Subs)"""
    suggestions = {}
    flat_cashew = []
    lookup_map = {} 
    
    for main, data in cashew_structure.items():
        flat_cashew.append(main)
        lookup_map[main] = (main, "")
        for sub in data['subs']:
            combo = f"{main} {sub}"
            flat_cashew.append(combo)
            lookup_map[combo] = (main, sub)
            
    for w_cat in wallet_cats:
        best_match, score = process.extractOne(w_cat, flat_cashew)
        if score > 60:
            m, s = lookup_map[best_match]
            suggestions[w_cat] = {"main": m, "sub": s}
        else:
            suggestions[w_cat] = {"main": "Altro", "sub": ""}
    return suggestions

def generate_uuid(): return str(uuid.uuid4())

def get_ts(date_str):
    try:
        dt = datetime.datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
        return int(dt.timestamp() * 1000)
    except:
        return int(time.time() * 1000)

def detect_transfers(transactions: List[WalletTransaction]) -> List[WalletTransaction]:
    """
    Identifica le coppie di trasferimenti (Entrata/Uscita) e imposta i riferimenti.
    Restituisce la lista aggiornata.
    """
    # Reset
    for t in transactions:
        t.paired_with_idx = None

    # Separate candidates
    # We only look at transactions marked as transfer
    # NOTE: Wallet CSV has 'transfer' column. If true, we try to pair.

    # Sort by date for easier matching window
    # We work on indices to link them back

    # We need a way to efficiently find matches.
    # Logic: For each outgoing transfer, look for an incoming transfer with:
    # 1. Same Amount (absolute value)
    # 2. Different Account
    # 3. Same Time (or very close, e.g. < 1 min, Wallet exports are usually precise)

    # Optimization: Dictionary by "Amount_Date"

    # Create lookup for incomes
    incomes = {} # Key: (abs(amount), date_str), Value: List of indices

    for i, t in enumerate(transactions):
        if t.is_transfer and t.amount > 0:
            key = (abs(t.amount), t.date_str)
            if key not in incomes: incomes[key] = []
            incomes[key].append(i)

    # Match expenses
    for i, t in enumerate(transactions):
        if t.is_transfer and t.amount < 0:
            key = (abs(t.amount), t.date_str)

            # Check for direct match
            if key in incomes and incomes[key]:
                # Take the first available match
                match_idx = incomes[key].pop(0)

                # Link both ways
                t.paired_with_idx = match_idx
                transactions[match_idx].paired_with_idx = i

                # Check account?
                # Usually transfers are between different accounts.
                # If same account, it might be a mistake or correction, but we link anyway.

    return transactions
