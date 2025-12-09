import streamlit as st
from logic import parse_csv_to_models
from models import AccountConfig

def render_step1():
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        with st.container(border=True):
            st.markdown("### 1. Formato di Output")
            st.caption("Scegli come vuoi esportare i tuoi dati.")

            # Visual Selection using Columns instead of radio
            fmt = st.session_state.output_format

            c_sql, c_csv = st.columns(2)
            with c_sql:
                is_sql = fmt == "SQL"
                if st.button("🗄️\n\nDatabase SQL", key="btn_sql", type="primary" if is_sql else "secondary", use_container_width=True, help="Consigliato per Cashew"):
                    st.session_state.output_format = "SQL"
                    st.rerun()

            with c_csv:
                is_csv = fmt == "CSV"
                if st.button("📄\n\nFile CSV", key="btn_csv", type="primary" if is_csv else "secondary", use_container_width=True, help="Solo dati grezzi"):
                    st.session_state.output_format = "CSV"
                    st.rerun()

            if fmt == "SQL":
                st.success("✅ **Ottima scelta!** Il formato SQL preserva icone, colori e struttura.", icon="✅")
            else:
                st.warning("⚠️ **Attenzione:** Il CSV non include colori o icone.", icon="⚠️")

    with col_right:
        with st.container(border=True):
            st.markdown("### 2. Carica Export")
            st.caption("Trascina qui il file `wallet-export.csv` originale.")

            uploaded = st.file_uploader("", type=['csv'], label_visibility="collapsed")

            if uploaded:
                try:
                    with st.spinner("Analisi in corso..."):
                        ts = parse_csv_to_models(uploaded)
                        st.session_state.transactions = ts

                        # Setup accounts
                        unique_accs = {t.account for t in ts}
                        for acc in unique_accs:
                            if acc not in st.session_state.accounts:
                                st.session_state.accounts[acc] = AccountConfig(name_cashew=acc)

                    st.markdown("---")
                    st.markdown(f"**Risultato Analisi:**")
                    c1, c2 = st.columns(2)
                    c1.metric("Transazioni", len(ts))
                    c2.metric("Conti", len(unique_accs))

                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Prosegui alla Configurazione ➔", type="primary", use_container_width=True):
                        st.session_state.step = 2
                        st.rerun()

                except Exception as e:
                    st.error(f"Errore nel file: {str(e)}")
