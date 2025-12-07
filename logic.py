import pandas as pd
import uuid
import datetime
import time
from typing import List, Dict
from thefuzz import process # Libreria per AI/Fuzzy matching
from models import WalletTransaction, ProcessedTransaction

# --- PERFORMANCE CACHING ---
# Usiamo st.cache_data in app.py wrappando queste funzioni

def fix_encoding(text):
    if not isinstance(text, str): return text
    try: return text.encode('cp1252').decode('utf-8')
    except: return text

def parse_csv_to_models(file_buffer) -> List[WalletTransaction]:
    """Legge il CSV e restituisce una lista di oggetti Pydantic validati"""
    try:
        df = pd.read_csv(file_buffer, sep=';')
        if len(df.columns) < 2:
            file_buffer.seek(0)
            df = pd.read_csv(file_buffer, sep=',')
    except Exception as e:
        raise ValueError(f"Impossibile leggere il file: {str(e)}")

    transactions = []
    for _, row in df.iterrows():
        # Pulizia encoding
        clean_row = {k: fix_encoding(v) for k, v in row.to_dict().items()}
        
        # Logica transfer
        is_transf = str(clean_row.get('transfer', 'false')).lower() == 'true' or \
                    str(clean_row.get('type', '')).upper() == 'TRANSFER'
        
        # Creazione Modello
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
        except Exception as e:
            # Skip righe corrotte ma non crashare
            print(f"Skipping row: {e}")
            continue
            
    return transactions

def ai_suggest_mapping(wallet_cats: List[str], cashew_structure: Dict[str, List[str]]) -> Dict[str, dict]:
    """
    Usa 'thefuzz' (Levenshtein Distance) per trovare il match migliore.
    Restituisce un dizionario: { 'Benzina': {'main': 'Trasporti', 'sub': 'Carburante'} }
    """
    suggestions = {}
    
    # Appiattiamo la struttura Cashew per la ricerca: "Trasporti > Carburante"
    flat_cashew = []
    lookup_map = {} # "Trasporti > Carburante" -> ("Trasporti", "Carburante")
    
    for main, subs in cashew_structure.items():
        # Aggiungi categoria madre
        flat_cashew.append(main)
        lookup_map[main] = (main, "")
        for sub in subs:
            combo = f"{main} {sub}" # Usiamo spazio per matching migliore
            flat_cashew.append(combo)
            lookup_map[combo] = (main, sub)
            
    for w_cat in wallet_cats:
        # Trova il miglior match con score > 60
        best_match, score = process.extractOne(w_cat, flat_cashew)
        
        if score > 60:
            m, s = lookup_map[best_match]
            suggestions[w_cat] = {"main": m, "sub": s}
        else:
            # Fallback intelligente su keywords
            lower_cat = w_cat.lower()
            if "stipendio" in lower_cat: suggestions[w_cat] = {"main": "Reddito", "sub": "Stipendio"}
            elif "supermercato" in lower_cat: suggestions[w_cat] = {"main": "Alimentari", "sub": "Supermercato"}
            else: suggestions[w_cat] = {"main": "Altro", "sub": ""}
            
    return suggestions

def generate_uuid():
    return str(uuid.uuid4())

def get_ts(date_str):
    try:
        dt = datetime.datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
        return int(dt.timestamp() * 1000)
    except:
        return int(time.time() * 1000)