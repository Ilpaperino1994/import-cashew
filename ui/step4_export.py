import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
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
        # Default
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
            # Resolve UUIDs
            # If we have a subcategory, we need to populate:
            # category_fk = Main Cat UUID
            # sub_category_fk = Sub Cat UUID

            main_uuid = c_uuids.get((main_cat_name, ""), "0")

            if sub_cat_name:
                sub_uuid = c_uuids.get((main_cat_name, sub_cat_name))
                if sub_uuid:
                    c_fk = main_uuid
                    s_fk = sub_uuid
                else:
                    # Fallback if sub not found
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
            # Prepare DataFrame matching original-cashew.csv format
            csv_rows = []

            # Lookup wallet names for CSV
            w_names = {v: k for k, v in w_uuids.items()}

            for pt in processed_list:
                # Convert date_ms to "YYYY-MM-DD HH:MM:SS.mmm"
                dt = datetime.datetime.fromtimestamp(pt.date_ms / 1000.0)
                date_fmt = dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                # Map config for color/icon
                # We need to look up color/icon from cashew_struct again or store it in ProcessedTransaction.
                # Since ProcessedTransaction doesn't have it, we check session state.
                cat_data = st.session_state.cashew_struct.get(pt.main_category_name, {})
                color = cat_data.get("color", "")
                icon = cat_data.get("icon", "")

                row = {
                    "account": w_names.get(pt.wallet_fk, "Unknown"),
                    "amount": pt.amount,
                    "currency": st.session_state.accounts.get(w_names.get(pt.wallet_fk), {}).currency, # Get currency from config
                    "title": pt.title,
                    "note": pt.note.replace("| nan", "").strip(), # Clean up notes
                    "date": date_fmt,
                    "income": "true" if pt.is_income else "false",
                    "type": "null", # Original has null for expenses
                    "category name": pt.main_category_name if not pt.title == "Trasferimento" else "Trasferimento",
                    "subcategory name": pt.sub_category_name if pt.sub_category_name else None,
                    "color": color, # Hex with 0xff prefix in example? Example says "0xff607d8b"
                    "icon": icon,
                    "emoji": None,
                    "budget": None,
                    "objective": None
                }

                # Fix color format if needed (Example: 0xff607d8b)
                # Input color is usually #RRGGBB.
                if row["color"] and row["color"].startswith("#"):
                     row["color"] = row["color"].replace("#", "0xff")

                csv_rows.append(row)

            csv_df = pd.DataFrame(csv_rows)
            # Reorder columns to match original-cashew.csv
            cols = ["account","amount","currency","title","note","date","income","type","category name","subcategory name","color","icon","emoji","budget","objective"]
            # Ensure all cols exist
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
            st.info("Importa questo file manualmente tramite la funzione CSV di Cashew (se disponibile) o usalo per le tue analisi Excel.")

    st.divider()
    c1, c2 = st.columns([1, 5])
    if c1.button("⬅ Indietro"):
        st.session_state.step = 3
        st.rerun()
