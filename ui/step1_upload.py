import streamlit as st
from logic import parse_csv_to_models
from models import AccountConfig

def render_step1():
    # Hero Section
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem;">
        <h2 class="hero-text">Inizia la tua migrazione</h2>
        <p style="font-size: 1.2rem; max-width: 600px; margin: 0 auto;">
            Trasforma i tuoi dati Wallet by BudgetBakers in un formato perfettamente compatibile con Cashew.
            Mantieni la tua storia finanziaria intatta.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Main Grid
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown('<div class="st-card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown("### 1. Formato di Output")
        st.markdown("""
        <p style="margin-bottom: 2rem;">
            Scegli come vuoi esportare i tuoi dati. Il formato SQL è consigliato per un ripristino completo.
        </p>
        """, unsafe_allow_html=True)

        # Custom Selection Cards
        fmt = st.session_state.output_format

        # SQL Option
        if st.button("🗄️ Database Cashew (.sqlite)\n\nConsigliato: Include icone, colori e struttura completa.",
                     type="primary" if fmt == "SQL" else "secondary",
                     use_container_width=True,
                     key="btn_sql"):
            st.session_state.output_format = "SQL"
            st.rerun()

        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)

        # CSV Option
        if st.button("📄 File CSV Semplice\n\nBase: Solo dati grezzi. Perderai le associazioni visive.",
                     type="primary" if fmt == "CSV" else "secondary",
                     use_container_width=True,
                     key="btn_csv"):
            st.session_state.output_format = "CSV"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="st-card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown("### 2. Carica Export")
        st.markdown("""
        <p style="margin-bottom: 1.5rem;">
            Trascina qui il file <code>wallet-export.csv</code> originale.
        </p>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader("", type=['csv'], label_visibility="collapsed")

        if uploaded:
            try:
                with st.spinner("Analisi del file in corso..."):
                    ts = parse_csv_to_models(uploaded)
                    st.session_state.transactions = ts

                    # Setup accounts
                    unique_accs = {t.account for t in ts}
                    for acc in unique_accs:
                        if acc not in st.session_state.accounts:
                            st.session_state.accounts[acc] = AccountConfig(name_cashew=acc)

                # Success State inside the card
                st.markdown(f"""
                <div style="background-color: rgba(46, 204, 113, 0.1); padding: 15px; border-radius: 12px; border: 1px solid var(--primary); margin-top: 20px;">
                    <h4 style="color: var(--primary); margin: 0;">✅ Analisi Completata</h4>
                    <ul style="margin-bottom: 0; padding-left: 20px; color: var(--text-secondary);">
                        <li><b>{len(ts)}</b> transazioni trovate</li>
                        <li><b>{len(unique_accs)}</b> conti identificati</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Configura Categorie ➔", type="primary", use_container_width=True):
                    st.session_state.step = 2
                    st.rerun()

            except Exception as e:
                st.error(f"Errore: {str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)
