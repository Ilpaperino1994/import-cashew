import pandas as pd
import uuid
import datetime
import time
from typing import List, Dict
from thefuzz import process
from models import WalletTransaction, CashewConfig

# --- DEFAULT CONFIGURATION RICCA ---
DEFAULT_CASHEW_STRUCTURE = {
    "Alimentari": {
        "subs": ["Supermercato", "Minimarket", "Panificio", "Macelleria"],
        "color": "#4CAF50", "icon": "groceries.png"
    },
    "Ristorazione": {
        "subs": ["Ristorante", "Bar", "Fast Food", "Delivery", "Caffè"],
        "color": "#FF9800", "icon": "food.png"
    },
    "Trasporti": {
        "subs": ["Carburante", "Mezzi Pubblici", "Treno", "Taxi", "Parcheggio", "Manutenzione", "Assicurazione"],
        "color": "#F44336", "icon": "car.png"
    },
    "Abitazione": {
        "subs": ["Affitto", "Mutuo", "Luce", "Gas", "Acqua", "Internet", "Condominio", "Riparazioni"],
        "color": "#795548", "icon": "house.png"
    },
    "Shopping": {
        "subs": ["Abbigliamento", "Elettronica", "Casa", "Hobby", "Libri", "Regali"],
        "color": "#9C27B0", "icon": "shopping.png"
    },
    "Salute & Benessere": {
        "subs": ["Farmacia", "Medico", "Dentista", "Sport", "Barbiere/Parrucchiere"],
        "color": "#00BCD4", "icon": "health.png"
    },
    "Intrattenimento": {
        "subs": ["Cinema", "Streaming (Netflix/Spotify)", "Viaggi", "Hotel", "Eventi"],
        "color": "#E91E63", "icon": "entertainment.png"
    },
    "Reddito": {
        "subs": ["Stipendio", "Rimborsi", "Bonus", "Vendite"],
        "color": "#2196F3", "icon": "salary.png"
    },
    "Finanza": {
        "subs": ["Tasse", "Multe", "Commissioni", "Investimenti"],
        "color": "#607D8B", "icon": "bank.png"
    },
    "Correzione saldo": {
        "subs": [],
        "color": "#9E9E9E", "icon": "charts.png"
    }
}

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