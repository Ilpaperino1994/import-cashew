import streamlit as st
import pandas as pd
from models import AccountConfig
from logic import parse_csv_to_models

def render_step1():
    st.markdown("### 📤 Inizia la Migrazione")

    # 1. Output Format Selection
    st.markdown("#### 1. Scegli il formato di output")

    st.info("""
    Questa applicazione ti permette di convertire i dati esportati da **Wallet by BudgetBakers** per importarli in **Cashew**.

    Puoi scegliere tra due modalità di esportazione:
    """)

    col_choice, col_info = st.columns([2, 1])

    with col_choice:
        output_format = st.radio(
            "Seleziona il formato che vuoi generare:",
            options=["Database Cashew (.sqlite) [Consigliato]", "File CSV"],
            index=0,
            help="Scegli 'Database Cashew' per sostituire il tuo attuale DB Cashew (backup completo). Scegli 'CSV' se vuoi importare le transazioni manualmente."
        )
        st.session_state.output_format = "SQL" if "Database" in output_format else "CSV"

    with col_info:
        if st.session_state.output_format == "SQL":
            st.success("""
            **ℹ️ Modalità SQL (Consigliata)**

            Genera un **backup completo (.sqlite)** pronto per essere ripristinato.

            **Vantaggi:**
            - Importa Categorie, Colori, Icone e Conti.
            - Collega automaticamente i trasferimenti.
            - È il metodo più veloce e pulito.
            """)
        else:
            st.warning("""
            **ℹ️ Modalità CSV**

            Genera un semplice file **.csv**.

            **Attenzione:**
            - Dovrai mappare manualmente le colonne in Cashew.
            - Colori e Icone non verranno importati.
            - I trasferimenti potrebbero non essere collegati correttamente.
            """)

    st.divider()

    # 2. Upload
    st.markdown("#### 2. Carica il file di Wallet")
    st.markdown("Esporta i tuoi dati da Wallet in formato CSV e caricalo qui sotto.")
    uploaded = st.file_uploader("Trascina qui il file `wallet-export.csv`", type=['csv'])

    if uploaded:
        try:
            ts = parse_csv_to_models(uploaded)
            st.session_state.transactions = ts

            # Setup accounts
            unique_accs = {t.account for t in ts}
            for acc in unique_accs:
                if acc not in st.session_state.accounts:
                    st.session_state.accounts[acc] = AccountConfig(name_cashew=acc)

            st.success(f"✅ Analisi completata! Trovate **{len(ts)}** transazioni e **{len(unique_accs)}** conti.")

            if st.button("Inizia la Configurazione ➔", type="primary"):
                st.session_state.step = 2
                st.rerun()
        except Exception as e:
            st.error(f"Errore nella lettura del file: {str(e)}")
            st.exception(e)
