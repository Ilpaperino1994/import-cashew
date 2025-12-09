import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
from database import CashewDatabase
from logic import detect_transfers, generate_uuid, get_ts
from models import CashewConfig, ProcessedTransaction

def render_step4():
    st.markdown('<div class="st-card">', unsafe_allow_html=True)
    st.markdown("### 🚀 Pronti al Decollo")
    st.caption("I tuoi dati sono stati elaborati e sono pronti per essere trasferiti.")
    st.markdown('</div>', unsafe_allow_html=True)

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
        main_cat_name = map_conf.main_category
        sub_cat_name = map_conf.sub_category if map_conf.sub_category else None

        if t.is_transfer:
            title = "Trasferimento"
            c_fk = "0"
            s_fk = None
            main_cat_name = "Trasferimento"
            sub_cat_name = None
        else:
            title = main_cat_name
            main_uuid = c_uuids.get((main_cat_name, ""), "0")

            if sub_cat_name:
                sub_uuid = c_uuids.get((main_cat_name, sub_cat_name))
                if sub_uuid:
                    c_fk = main_uuid
                    s_fk = sub_uuid
                else:
                    c_fk = main_uuid
                    s_fk = None
            else:
                c_fk = main_uuid
                s_fk = None

        t_id = generate_uuid()

        pt = ProcessedTransaction(
            id=t_id,
            date_ms=get_ts(t.date_str),
            amount=t.amount,
            title=title,
            note=f"{t.note} | {t.payee}" if t.payee else t.note,
            wallet_fk=w_fk,
            category_fk=c_fk,
            sub_category_fk=s_fk,
            main_category_name=main_cat_name,
            sub_category_name=sub_cat_name,
            is_income=t.amount > 0,
            paired_id=None
        )

        t.temp_id = t_id
        processed_list.append(pt)

    # Second pass for pairing
    for i, t in enumerate(final_transactions):
        if hasattr(t, 'paired_with_idx') and t.paired_with_idx is not None:
            if 0 <= t.paired_with_idx < len(processed_list):
                processed_list[i].paired_id = processed_list[t.paired_with_idx].id

    # Insert into DB
    for pt in processed_list:
        db.add_transaction(pt)

    # --- UI ---

    col1, col2 = st.columns([1, 1], gap="medium")

    with col1:
        st.markdown('<div class="st-card">', unsafe_allow_html=True)
        st.subheader("📊 Anteprima")
        df_viz = pd.DataFrame([p.dict() for p in processed_list])
        if not df_viz.empty:
            expenses = df_viz[df_viz['amount'] < 0]
            if not expenses.empty:
                fig = go.Figure(data=[go.Pie(labels=expenses['title'], values=expenses['amount'].abs(), hole=.4)])
                fig.update_layout(
                    title="Spese per Categoria",
                    height=300,
                    margin=dict(t=40, b=0, l=0, r=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#E0E0E0')
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nessuna spesa trovata.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="st-card">', unsafe_allow_html=True)
        st.subheader("💾 Download")
        st.write(f"Abbiamo generato **{len(processed_list)}** transazioni.")

        if st.session_state.output_format == "SQL":
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
            <small style="opacity: 0.7;">
            <b>Istruzioni:</b><br>
            1. Scarica il file sul telefono.<br>
            2. Apri Cashew > Impostazioni > Backup.<br>
            3. Seleziona "Ripristina Backup".
            </small>
            """, unsafe_allow_html=True)

        else:
            # CSV Export
            csv_rows = []
            w_names = {v: k for k, v in w_uuids.items()}

            for pt in processed_list:
                dt = datetime.datetime.fromtimestamp(pt.date_ms / 1000.0)
                date_fmt = dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                cat_data = st.session_state.cashew_struct.get(pt.main_category_name, {})
                color = cat_data.get("color", "")
                icon = cat_data.get("icon", "")

                row = {
                    "account": w_names.get(pt.wallet_fk, "Unknown"),
                    "amount": pt.amount,
                    "currency": st.session_state.accounts.get(w_names.get(pt.wallet_fk), {}).currency,
                    "title": pt.title,
                    "note": pt.note.replace("| nan", "").strip(),
                    "date": date_fmt,
                    "income": "true" if pt.is_income else "false",
                    "type": "null",
                    "category name": pt.main_category_name if not pt.title == "Trasferimento" else "Trasferimento",
                    "subcategory name": pt.sub_category_name if pt.sub_category_name else None,
                    "color": color.replace("#", "0xff") if color and color.startswith("#") else color,
                    "icon": icon,
                    "emoji": None,
                    "budget": None,
                    "objective": None
                }
                csv_rows.append(row)

            csv_df = pd.DataFrame(csv_rows)
            cols = ["account","amount","currency","title","note","date","income","type","category name","subcategory name","color","icon","emoji","budget","objective"]
            for c in cols:
                if c not in csv_df.columns: csv_df[c] = None
            csv_df = csv_df[cols]

            csv_data = csv_df.to_csv(index=False)

            st.download_button(
                label="📥 Scarica CSV",
                data=csv_data,
                file_name="cashew_import.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
            st.info("Importa manualmente in Cashew.")

        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    if st.button("⬅ Ricomincia", use_container_width=True):
        st.session_state.step = 3
        st.rerun()
