import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
from database import CashewDatabase
from logic import detect_transfers, generate_uuid, get_ts
from models import CashewConfig, ProcessedTransaction

def render_step4():
    # Hero Success Section
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem; animation: fadeIn 1s;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🚀</div>
        <h2 class="hero-text">Tutto Pronto!</h2>
        <p>I tuoi dati sono stati elaborati, convertiti e ottimizzati.</p>
    </div>
    """, unsafe_allow_html=True)

    # 1. Processing Logic (Execute only once typically, but here it's reactive)
    # Ideally should be cached or done in transition, but for simplicity:
    final_transactions = detect_transfers(st.session_state.transactions)

    # b. Prepare Database
    db = CashewDatabase()

    # [Logic same as before, preserving functionality]
    w_uuids = {}
    for name, conf in st.session_state.accounts.items():
        uid = generate_uuid()
        w_uuids[name] = uid
        db.add_wallet(uid, conf)

    c_uuids = {}
    for main, data in st.session_state.cashew_struct.items():
        uid_m = generate_uuid()
        c_uuids[(main, "")] = uid_m
        db.add_category(uid_m, main, data['color'], data['icon'], None)
        for sub in data['subs']:
            uid_s = generate_uuid()
            c_uuids[(main, sub)] = uid_s
            db.add_category(uid_s, sub, None, None, uid_m)

    processed_list = []
    for t in final_transactions:
        map_conf = st.session_state.mapping.get(t.category, CashewConfig(main_category="Altro"))
        w_fk = w_uuids.get(t.account)
        if not w_fk: w_fk = list(w_uuids.values())[0]

        main_cat_name = map_conf.main_category
        sub_cat_name = map_conf.sub_category if map_conf.sub_category else None

        if t.is_transfer:
            title = "Trasferimento"
            c_fk = "0" # Cashew standard for transfers? Or specific ID. Usually internal logic handles.
            # Actually Cashew might use specific category for transfer or NULL.
            # Logic provided previously used "0" or specific. Sticking to previous logic.
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

    for i, t in enumerate(final_transactions):
        if hasattr(t, 'paired_with_idx') and t.paired_with_idx is not None:
            if 0 <= t.paired_with_idx < len(processed_list):
                processed_list[i].paired_id = processed_list[t.paired_with_idx].id

    for pt in processed_list:
        db.add_transaction(pt)

    # --- UI GRID ---
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="st-card" style="height: 100%;">', unsafe_allow_html=True)
        st.subheader("📊 Anteprima Rapida")

        df_viz = pd.DataFrame([p.dict() for p in processed_list])
        if not df_viz.empty:
            expenses = df_viz[df_viz['amount'] < 0]
            if not expenses.empty:
                # Custom Plotly Theme
                fig = go.Figure(data=[go.Pie(
                    labels=expenses['main_category_name'],
                    values=expenses['amount'].abs(),
                    hole=.6,
                    textinfo='none', # Cleaner look
                    hoverinfo='label+percent+value',
                    marker=dict(colors=['#2ECC71', '#3498DB', '#9B59B6', '#F1C40F', '#E74C3C', '#34495E'])
                )])
                fig.update_layout(
                    title="Distribuzione Spese",
                    title_font_color="#FFFFFF",
                    height=350,
                    margin=dict(t=50, b=20, l=20, r=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=True,
                    legend=dict(font=dict(color='#B0BEC5'))
                )
                st.plotly_chart(fig, use_container_width=True)

                total_exp = expenses['amount'].sum()
                st.markdown(f"<div style='text-align: center; margin-top: -10px;'><h3>Totale Spese: <span style='color: #FF5252'>€ {total_exp:,.2f}</span></h3></div>", unsafe_allow_html=True)
            else:
                st.info("Nessuna spesa rilevata nei dati.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="st-card" style="height: 100%; display: flex; flex-direction: column; justify-content: center;">', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="text-align: center;">
            <h3 style="margin-bottom: 2rem;">📥 Scarica il tuo File</h3>
            <p style="margin-bottom: 2rem;">Hai generato <b>{len(processed_list)}</b> transazioni pronte per l'importazione.</p>
        </div>
        """, unsafe_allow_html=True)

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
                label="SCARICA DATABASE COMPLETO",
                data=sql_data,
                file_name=file_name,
                mime=mime,
                type="primary",
                use_container_width=True
            )

            st.markdown("""
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; margin-top: 20px; text-align: left;">
                <small>
                <b>Come importare:</b><br>
                1. Trasferisci il file sul tuo dispositivo.<br>
                2. Apri <b>Cashew</b> > Impostazioni > Backup & Ripristino.<br>
                3. Seleziona <b>Ripristina Backup</b> e scegli questo file.
                </small>
            </div>
            """, unsafe_allow_html=True)

        else:
            # CSV Logic
            csv_rows = []
            w_names = {v: k for k, v in w_uuids.items()}

            # [CSV Generation Logic same as before]
            for pt in processed_list:
                dt = datetime.datetime.fromtimestamp(pt.date_ms / 1000.0)
                date_fmt = dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                cat_data = st.session_state.cashew_struct.get(pt.main_category_name, {})
                color = cat_data.get("color", "")
                row = {
                    "account": w_names.get(pt.wallet_fk, "Unknown"),
                    "amount": pt.amount,
                    "currency": st.session_state.accounts.get(w_names.get(pt.wallet_fk), {}).currency,
                    "title": pt.title,
                    "note": pt.note.replace("| nan", "").strip(),
                    "date": date_fmt,
                    "income": "true" if pt.is_income else "false",
                    "type": "null",
                    "category name": pt.main_category_name,
                    "subcategory name": pt.sub_category_name,
                    "color": color.replace("#", "0xff") if color else color,
                    "icon": cat_data.get("icon", ""),
                    "emoji": None, "budget": None, "objective": None
                }
                csv_rows.append(row)

            csv_df = pd.DataFrame(csv_rows)
            # Ensure columns exist
            for c in ["account","amount","currency","title","note","date","income","type","category name","subcategory name","color","icon","emoji","budget","objective"]:
                if c not in csv_df.columns: csv_df[c] = None

            csv_data = csv_df.to_csv(index=False)

            st.download_button(
                label="SCARICA CSV",
                data=csv_data,
                file_name="cashew_import.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    if st.button("⬅ Nuova Migrazione", use_container_width=True):
        st.session_state.step = 1
        st.session_state.transactions = []
        st.session_state.mapping = {}
        st.rerun()
