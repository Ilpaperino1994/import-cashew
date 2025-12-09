import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from database import CashewDatabase
from logic import detect_transfers, generate_uuid, get_ts
from models import CashewConfig, ProcessedTransaction

def render_step4():
    st.markdown("### 🚀 Esportazione Finale")

    # 1. Processing Logic
    final_transactions = detect_transfers(st.session_state.transactions)

    # b. Prepare Database
    db = CashewDatabase()

    # Add Wallets
    w_uuids = {}
    for name, conf in st.session_state.accounts.items():
        uid = generate_uuid()
        w_uuids[name] = uid
        db.add_wallet(uid, conf)

    # Add Categories
    c_uuids = {}
    for main, data in st.session_state.cashew_struct.items():
        uid_m = generate_uuid()
        c_uuids[(main, "")] = uid_m
        db.add_category(uid_m, main, data['color'], data['icon'], None)
        for sub in data['subs']:
            uid_s = generate_uuid()
            c_uuids[(main, sub)] = uid_s
            db.add_category(uid_s, sub, None, None, uid_m)

    # Add Transactions
    processed_list = []
    for t in final_transactions:
        map_conf = st.session_state.mapping.get(t.category, CashewConfig(main_category="Altro"))

        # Link Wallet
        w_fk = w_uuids.get(t.account)
        if not w_fk: w_fk = list(w_uuids.values())[0]

        # Link Category (or force Transfer)
        if t.is_transfer:
            title = "Trasferimento"
            c_fk = "0"
        else:
            title = map_conf.main_category
            c_fk = c_uuids.get((map_conf.main_category, map_conf.sub_category))
            if not c_fk: c_fk = c_uuids.get((map_conf.main_category, ""), "0")

        t_id = generate_uuid()

        pt = ProcessedTransaction(
            id=t_id,
            date_ms=get_ts(t.date_str),
            amount=t.amount,
            title=title,
            note=f"{t.note} | {t.payee}" if t.payee else t.note,
            wallet_fk=w_fk,
            category_fk=c_fk,
            is_income=t.amount > 0,
            paired_id=None
        )

        # Store temporary to link pairs
        t.temp_id = t_id
        processed_list.append(pt)

    # Second pass for pairing
    for i, t in enumerate(final_transactions):
        if hasattr(t, 'paired_with_idx') and t.paired_with_idx is not None:
            # Check bounds just in case
            if 0 <= t.paired_with_idx < len(processed_list):
                processed_list[i].paired_id = processed_list[t.paired_with_idx].id

    # Insert into DB
    for pt in processed_list:
        db.add_transaction(pt)

    # --- UI ---
    st.success(f"🎉 Tutto pronto! Abbiamo processato **{len(processed_list)}** transazioni.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📊 Anteprima Dati")
        df_viz = pd.DataFrame([p.dict() for p in processed_list])
        if not df_viz.empty:
            expenses = df_viz[df_viz['amount'] < 0]
            if not expenses.empty:
                fig = go.Figure(data=[go.Pie(labels=expenses['title'], values=expenses['amount'].abs(), hole=.4)])
                fig.update_layout(title="Distribuzione Spese", height=300, margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nessuna spesa trovata per generare il grafico.")

    with col2:
        st.subheader("💾 Scarica il File")

        if st.session_state.output_format == "SQL":
            # Binary SQL Export
            try:
                sql_data = db.get_binary_sqlite()
                file_name = "cashew_backup.sqlite"
                mime = "application/x-sqlite3"
            except AttributeError:
                sql_data = db.get_sql_dump().encode('utf-8')
                file_name = "cashew_restore.sql"
                mime = "text/x-sql"

            st.download_button(
                label="📥 Scarica Database (.sqlite)",
                data=sql_data,
                file_name=file_name,
                mime=mime,
                type="primary",
                use_container_width=True
            )

            st.markdown("""
            **Come importare su Cashew:**
            1. Scarica il file sul tuo telefono.
            2. Apri **Cashew** e vai su **Impostazioni**.
            3. Seleziona **Backup e Ripristino**.
            4. Scegli **Ripristina Backup** e seleziona il file scaricato.
            """)

        else:
            # CSV Export
            csv_data = pd.DataFrame([p.dict() for p in processed_list]).to_csv(index=False)
            st.download_button(
                label="📥 Scarica CSV",
                data=csv_data,
                file_name="cashew_import.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
            st.info("Importa questo file manualmente tramite la funzione CSV di Cashew (se disponibile) o usalo per le tue analisi Excel.")

    st.divider()
    c1, c2 = st.columns([1, 5])
    if c1.button("⬅ Indietro"):
        st.session_state.step = 3
        st.rerun()
