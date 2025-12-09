import streamlit as st
import pandas as pd
from models import AccountConfig
from logic import parse_csv_to_models

def render_step1():
    # Card 1: Format Selection
    with st.container():
        st.markdown('<div class="st-card">', unsafe_allow_html=True)
        st.markdown("### 1. Scegli il formato di output")

        c1, c2 = st.columns([1, 1])
        with c1:
            st.info("I file di Wallet by BudgetBakers non sono compatibili direttamente con Cashew. Questo tool li converte per te.", icon="ℹ️")

        output_format = st.radio(
            "Formato Desiderato",
            options=["Database Cashew (.sqlite)", "File CSV"],
            index=0,
            horizontal=True,
            label_visibility="collapsed"
        )
        st.session_state.output_format = "SQL" if "Database" in output_format else "CSV"

        if st.session_state.output_format == "SQL":
            st.caption("✅ **Consigliato:** Crea un backup completo importabile che include colori, icone e struttura.")
        else:
            st.caption("⚠️ **CSV Base:** Utile solo per analisi manuali. Perderai colori e icone.")

        st.markdown('</div>', unsafe_allow_html=True)

    # Card 2: Upload
    with st.container():
        st.markdown('<div class="st-card">', unsafe_allow_html=True)
        st.markdown("### 2. Carica il file CSV")

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

                st.success(f"**Ottimo!** Abbiamo letto {len(ts)} transazioni da {len(unique_accs)} conti diversi.")

                st.markdown("---")
                col_next, _ = st.columns([1, 3])
                if col_next.button("Configura Categorie ➔", type="primary", use_container_width=True):
                    st.session_state.step = 2
                    st.rerun()

            except Exception as e:
                st.error(f"Errore nella lettura del file: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)
