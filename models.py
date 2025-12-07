from pydantic import BaseModel, Field, validator
from typing import Optional, List
import time

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