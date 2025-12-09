from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
import time

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

class WalletTransaction(BaseModel):
    """Rappresenta una riga grezza dal CSV di Wallet"""
    account: str
    category: str
    amount: float
    currency: str = "EUR"
    note: Optional[str] = ""
    payee: Optional[str] = ""
    date_str: str = Field(alias="date")
    is_transfer: bool = False
    temp_id: Optional[str] = None # For processing
    paired_with_idx: Optional[int] = None # For processing

    @validator('amount', pre=True)
    def parse_amount(cls, v):
        if isinstance(v, (int, float)): return float(v)
        val_str = str(v).replace('€', '').replace('$', '').strip()
        # Gestione formato europeo vs US
        if ',' in val_str and '.' in val_str:
            if val_str.rfind(',') > val_str.rfind('.'): 
                val_str = val_str.replace('.', '').replace(',', '.')
            else: 
                val_str = val_str.replace(',', '')
        elif ',' in val_str: 
            val_str = val_str.replace(',', '.')
        try: return float(val_str)
        except: return 0.0

class CashewConfig(BaseModel):
    """Configurazione di mappatura per una categoria"""
    main_category: str
    sub_category: str = ""
    color: str = "#9E9E9E"
    icon: str = "category_default.png"

class AccountConfig(BaseModel):
    """Configurazione per i conti"""
    name_cashew: str
    currency: str = "EUR"
    color: str = "#607D8B"

class ProcessedTransaction(BaseModel):
    """Transazione pronta per il DB Cashew"""
    id: str
    date_ms: int
    amount: float
    title: str
    note: str
    wallet_fk: str
    category_fk: str
    is_income: bool
    paired_id: Optional[str] = None # Per i transfer
