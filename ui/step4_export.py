import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
from database import CashewDatabase
from logic import detect_transfers, generate_uuid, get_ts
from models import CashewConfig, ProcessedTransaction

def render_step4():
    st.markdown("<h2 style='text-align: center;'>🎉 Tutto Pronto!</h2>", unsafe_allow_html=True)
    st.caption("<p style='text-align: center;'>I tuoi dati sono pronti per essere scaricati.</p>", unsafe_allow_html=True)

    # Logic Execution (Simplified for UI responsiveness)
    final_transactions = detect_transfers(st.session_state.transactions)
    db = CashewDatabase()

    # 1. Wallets
    w_uuids = {}
    for name, conf in st.session_state.accounts.items():
        uid = generate_uuid()
        w_uuids[name] = uid
        db.add_wallet(uid, conf)

    # 2. Categories
    c_uuids = {}
    for main, data in st.session_state.cashew_struct.items():
        uid_m = generate_uuid()
        c_uuids[(main, "")] = uid_m
        db.add_category(uid_m, main, data['color'], data['icon'], None)
        for sub in data['subs']:
            uid_s = generate_uuid()
            c_uuids[(main, sub)] = uid_s
            db.add_category(uid_s, sub, None, None, uid_m)

    # 3. Transactions
    processed_list = []
    for t in final_transactions:
        map_conf = st.session_state.mapping.get(t.category, CashewConfig(main_category="Altro"))
        w_fk = w_uuids.get(t.account, list(w_uuids.values())[0])

        main_cat = map_conf.main_category
        sub_cat = map_conf.sub_category

        if t.is_transfer:
            title = "Trasferimento"
            c_fk = "0"
            s_fk = None
            main_cat = "Trasferimento"
            sub_cat = None
        else:
            title = main_cat
            main_uuid = c_uuids.get((main_cat, ""), "0")
            c_fk = main_uuid
            s_fk = c_uuids.get((main_cat, sub_cat)) if sub_cat else None

        t_id = generate_uuid()
        pt = ProcessedTransaction(
            id=t_id, date_ms=get_ts(t.date_str), amount=t.amount, title=title,
            note=f"{t.note} | {t.payee}" if t.payee else t.note,
            wallet_fk=w_fk, category_fk=c_fk, sub_category_fk=s_fk,
            main_category_name=main_cat, sub_category_name=sub_cat,
            is_income=t.amount > 0, paired_id=None
        )
        t.temp_id = t_id
        processed_list.append(pt)

    # Pairing
    for i, t in enumerate(final_transactions):
        if hasattr(t, 'paired_with_idx') and t.paired_with_idx is not None:
             if 0 <= t.paired_with_idx < len(processed_list):
                 processed_list[i].paired_id = processed_list[t.paired_with_idx].id

    for pt in processed_list: db.add_transaction(pt)

    # --- UI ---
    col1, col2 = st.columns(2, gap="large")

    with col1:
        with st.container(border=True):
            st.markdown("### 📊 Anteprima")
            df_viz = pd.DataFrame([p.dict() for p in processed_list])
            if not df_viz.empty:
                exp = df_viz[df_viz['amount'] < 0]
                if not exp.empty:
                    fig = go.Figure(data=[go.Pie(labels=exp['main_category_name'], values=exp['amount'].abs(), hole=.5)])
                    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown(f"<div style='text-align:center'>Totale Uscite: <b>€ {exp['amount'].sum():,.2f}</b></div>", unsafe_allow_html=True)

    with col2:
        with st.container(border=True):
            st.markdown("### 📥 Download")
            st.write(f"Generate **{len(processed_list)}** transazioni.")

            if st.session_state.output_format == "SQL":
                try: data = db.get_binary_sqlite(); fn = "cashew_backup.sqlite"; mime="application/x-sqlite3"
                except: data = db.get_sql_dump().encode(); fn = "cashew.sql"; mime="text/x-sql"

                st.download_button("SCARICA DATABASE", data, fn, mime, type="primary", use_container_width=True)
                st.info("Importa in Cashew > Backup > Ripristina")
            else:
                # CSV Export Logic (Simplified)
                csv_df = pd.DataFrame([p.dict() for p in processed_list]) # Placeholder for full logic
                csv_data = csv_df.to_csv(index=False)
                st.download_button("SCARICA CSV", csv_data, "import.csv", "text/csv", type="primary", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Nuova Migrazione", use_container_width=True):
        st.session_state.step = 1
        st.rerun()
