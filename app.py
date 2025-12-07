import streamlit as st
import pandas as pd
import json
import uuid
import datetime
import time
import base64

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Wallet to Cashew Converter",
    page_icon="🥥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE MANAGEMENT (WIZARD LOGIC) ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'df_wallet' not in st.session_state: st.session_state.df_wallet = None
if 'cashew_struct' not in st.session_state:
    st.session_state.cashew_struct = {
        "Alimentari": ["Supermercato", "Minimarket", "Panificio"],
        "Ristorazione": ["Ristorante", "Bar", "Fast Food", "Delivery"],
        "Trasporti": ["Carburante", "Treno/Bus", "Parcheggio", "Manutenzione", "Assicurazione"],
        "Shopping": ["Abbigliamento", "Elettronica", "Casa", "Hobby"],
        "Abitazione": ["Affitto/Mutuo", "Luce", "Gas", "Acqua", "Internet"],
        "Salute": ["Farmacia", "Visite Mediche", "Sport"],
        "Intrattenimento": ["Cinema", "Streaming", "Viaggi", "Eventi"],
        "Reddito": ["Stipendio", "Rimborsi", "Bonus"],
        "Correzione saldo": [],
        "Altro": []
    }
if 'mapping_config' not in st.session_state: st.session_state.mapping_config = {}
if 'account_config' not in st.session_state: st.session_state.account_config = {}
if 'import_mode' not in st.session_state: st.session_state.import_mode = "SQL"

# --- 3. CSS & DESIGN SYSTEM ---
st.markdown("""
<style>
    /* Global Styles mimicking Cashew App */
    .stApp { background-color: #F2F6F8; font-family: 'Segoe UI', sans-serif; }
    
    /* Wizard Progress Bar */
    .wizard-container { display: flex; justify-content: space-between; margin-bottom: 30px; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.03); }
    .step-item { font-weight: bold; color: #B0BEC5; font-size: 0.9rem; }
    .step-active { color: #4CAF50; border-bottom: 3px solid #4CAF50; padding-bottom: 5px; }
    
    /* Cards for Mapping */
    .mapping-card {
        background-color: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        border: 1px solid #E0E0E0;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .mapping-card:hover { border-color: #4CAF50; transform: translateY(-2px); }
    
    .card-header { font-weight: 700; color: #37474F; font-size: 1.1rem; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; }
    .wallet-badge { background-color: #ECEFF1; color: #455A64; padding: 4px 8px; border-radius: 8px; font-size: 0.8rem; }
    
    /* Custom Buttons */
    div.stButton > button:first-child { border-radius: 12px; height: 3em; font-weight: 600; border: none; transition: 0.3s; }
    .primary-btn { background-color: #4CAF50 !important; color: white !important; }
    
    /* Headings */
    h1, h2, h3 { color: #263238; }
</style>
""", unsafe_allow_html=True)

# --- 4. FUNZIONI UTILI ---
def next_step(): st.session_state.step += 1
def prev_step(): st.session_state.step -= 1

def fix_encoding(text):
    if not isinstance(text, str): return text
    try: return text.encode('cp1252').decode('utf-8')
    except: return text

def parse_amount(value):
    if isinstance(value, (int, float)): return float(value)
    if pd.isna(value) or value == '': return 0.0
    val_str = str(value).replace('€', '').replace('$', '').strip()
    if ',' in val_str and '.' in val_str:
        if val_str.rfind(',') > val_str.rfind('.'): val_str = val_str.replace('.', '').replace(',', '.')
        else: val_str = val_str.replace(',', '')
    elif ',' in val_str: val_str = val_str.replace(',', '.')
    try: return float(val_str)
    except: return 0.0

def generate_uuid(): return str(uuid.uuid4())

def get_timestamp_ms(date_str):
    try:
        formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M"]
        for fmt in formats:
            try: return int(datetime.datetime.strptime(str(date_str)[:19], fmt).timestamp() * 1000)
            except: pass
        return int(time.time() * 1000)
    except: return int(time.time() * 1000)

def smart_style_guess(name):
    name = name.lower()
    mapping = {
        "cibo": ("food.png", "#4CAF50"), "ristorante": ("restaurant.png", "#FF9800"), "bar": ("cafe.png", "#795548"),
        "spesa": ("groceries.png", "#8BC34A"), "alimentari": ("groceries.png", "#8BC34A"),
        "auto": ("car.png", "#F44336"), "benzina": ("fuel.png", "#D32F2F"), "trasporti": ("bus.png", "#E91E63"),
        "casa": ("house.png", "#607D8B"), "bollette": ("bills.png", "#FF5722"), "affitto": ("house.png", "#607D8B"),
        "salute": ("health.png", "#00BCD4"), "farmacia": ("pills.png", "#00BCD4"),
        "shopping": ("shopping.png", "#9C27B0"), "vestiti": ("clothes.png", "#673AB7"),
        "stipendio": ("salary.png", "#2196F3"), "viaggi": ("plane.png", "#03A9F4"), "regali": ("gift.png", "#E91E63")
    }
    for k, v in mapping.items():
        if k in name: return v
    return ("category_default.png", "#9E9E9E")

# --- 5. PROGRESS WIZARD UI ---
def render_wizard_header():
    steps = ["1. Upload", "2. Struttura", "3. Mappatura", "4. Export"]
    cols = st.columns(len(steps))
    with st.container():
        st.markdown('<div class="wizard-container">', unsafe_allow_html=True)
        html = ""
        for i, s in enumerate(steps):
            active_class = "step-active" if (i + 1) == st.session_state.step else ""
            html += f'<span class="step-item {active_class}">{s}</span>'
            if i < len(steps) - 1: html += '<span style="color:#ddd;"> &nbsp; ➔ &nbsp; </span>'
        st.markdown(html + '</div>', unsafe_allow_html=True)

render_wizard_header()

# =================================================================================
# STEP 1: UPLOAD & SETUP
# =================================================================================
if st.session_state.step == 1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.title("Benvenuto in Cashew Migrator")
        st.markdown("""
        Trasforma il tuo storico finanziario di **Wallet** in un formato perfetto per **Cashew**.
        
        Questa app permette di:
        - 🔗 **Unire i trasferimenti** automaticamente.
        - 🎨 **Personalizzare** colori e icone.
        - 📂 Creare una struttura di **sottocategorie** gerarchica.
        """)
        
        st.info("💡 **Consiglio:** Usa la modalità SQL per ottenere un database pulito e nativo.")

    with col2:
        st.markdown("### 🛠️ Configurazione Iniziale")
        
        # Scelta Modalità con UI migliorata
        mode_sel = st.radio("Metodo di Importazione", ["SQL (Consigliato - Reset Totale)", "CSV (Base - Aggiunta)"], index=0)
        st.session_state.import_mode = "SQL" if "SQL" in mode_sel else "CSV"
        
        if st.session_state.import_mode == "SQL":
            st.warning("⚠️ Il file SQL sostituirà interamente il database attuale di Cashew.")
        
        # Upload
        uploaded_file = st.file_uploader("Trascina qui il file `wallet.csv`", type=['csv'])
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file, sep=';')
                if len(df.columns) < 2:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=',')
                
                # Pre-processing
                for col in df.select_dtypes(include=['object']).columns:
                    df[col] = df[col].apply(fix_encoding)
                df['amount_clean'] = df['amount'].apply(parse_amount)
                
                st.session_state.df_wallet = df
                st.success(f"✅ File caricato: {len(df)} transazioni trovate.")
                
                if st.button("Inizia Configurazione ➔", type="primary"):
                    next_step()
                    st.rerun()
            except Exception as e:
                st.error(f"Errore nel file: {e}")

# =================================================================================
# STEP 2: STRUTTURA CATEGORIE (GERARCHICA)
# =================================================================================
elif st.session_state.step == 2:
    st.title("📂 Struttura Categorie Cashew")
    st.markdown("Prima di mappare, definiamo **quali categorie** vuoi avere su Cashew. Organizzale come preferisci.")
    
    col_help, col_editor = st.columns([1, 2])
    
    with col_help:
        st.markdown("""
        **Come funziona:**
        1. Nella tabella a destra, scrivi le categorie principali (es. *Alimentari*).
        2. Accanto, scrivi la sottocategoria (es. *Supermercato*).
        3. Se una categoria non ha sottocategorie, lascia la seconda colonna vuota.
        
        ✨ *Puoi fare copia-incolla da Excel!*
        """)
        st.image("https://play-lh.googleusercontent.com/yvC8ZqgSqa6eHjKzLzFzXGzZq4xGqKqgZq4xGqKqgZq4xGqKqg=w240-h480-rw", width=150, caption="Stile Cashew")

    with col_editor:
        # Converti dict in df per l'editor
        current_data = []
        for main, subs in st.session_state.cashew_struct.items():
            if not subs: current_data.append({"Categoria Madre": main, "Sottocategoria": ""})
            for s in subs: current_data.append({"Categoria Madre": main, "Sottocategoria": s})
        
        df_struct = pd.DataFrame(current_data)
        edited_df = st.data_editor(df_struct, num_rows="dynamic", use_container_width=True, height=400)
        
    c1, c2 = st.columns([1, 5])
    if c1.button("⬅ Indietro"):
        prev_step()
        st.rerun()
    if c2.button("Conferma Struttura e Procedi ➔", type="primary"):
        # Salva struttura
        new_struct = {}
        for _, row in edited_df.iterrows():
            m = str(row["Categoria Madre"]).strip()
            s = str(row["Sottocategoria"]).strip()
            if m:
                if m not in new_struct: new_struct[m] = []
                if s and s not in new_struct[m]: new_struct[m].append(s)
        st.session_state.cashew_struct = new_struct
        next_step()
        st.rerun()

# =================================================================================
# STEP 3: MAPPATURA VISIVA (CARDS)
# =================================================================================
elif st.session_state.step == 3:
    st.title("🎨 Mappatura Intelligente")
    st.markdown("Collega le categorie di Wallet a quelle di Cashew che hai appena definito.")
    
    # 1. MAPPATURA CONTI
    with st.expander("💳 Configurazione Conti (Clicca per espandere)", expanded=True):
        unique_accs = sorted(st.session_state.df_wallet['account'].dropna().unique().tolist())
        cols = st.columns(len(unique_accs) if len(unique_accs) < 4 else 3)
        for i, acc in enumerate(unique_accs):
            with cols[i % 3]:
                st.markdown(f"**{acc}**")
                n_name = st.text_input("Nome su Cashew", value=acc, key=f"n_{acc}", label_visibility="collapsed")
                n_curr = "EUR"
                n_col = "#607D8B"
                if st.session_state.import_mode == "SQL":
                    c_cur, c_col = st.columns(2)
                    n_curr = c_cur.selectbox("Valuta", ["EUR", "USD", "GBP"], key=f"c_{acc}", label_visibility="collapsed")
                    n_col = c_col.color_picker("Colore", "#607D8B", key=f"cl_{acc}", label_visibility="collapsed")
                
                st.session_state.account_config[acc] = {"name": n_name, "currency": n_curr, "color": n_col}

    # 2. MAPPATURA CATEGORIE (GRID VIEW)
    st.markdown("---")
    st.subheader("Collega Categorie")
    
    unique_cats = sorted(st.session_state.df_wallet['category'].dropna().unique().tolist())
    search = st.text_input("🔍 Cerca categoria...", placeholder="Digita per filtrare...")
    
    filtered_cats = [c for c in unique_cats if search.lower() in c.lower()]
    
    # Grid Layout Logic
    cols_per_row = 3
    rows = [filtered_cats[i:i + cols_per_row] for i in range(0, len(filtered_cats), cols_per_row)]

    for row_cats in rows:
        cols = st.columns(cols_per_row)
        for idx, w_cat in enumerate(row_cats):
            with cols[idx]:
                # CARD CONTAINER START
                st.markdown(f"""
                <div class="mapping-card">
                    <div class="card-header">
                        <span>{w_cat}</span>
                        <span class="wallet-badge">Wallet</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # Logic inside card
                guess_icon, guess_color = smart_style_guess(w_cat)
                
                # Main Category Select
                main_opts = list(st.session_state.cashew_struct.keys())
                # Smart Match
                def_idx = 0
                for i, m in enumerate(main_opts):
                    if w_cat.lower() in m.lower(): def_idx = i; break
                
                sel_main = st.selectbox("Categoria", main_opts, index=def_idx, key=f"m_{w_cat}", label_visibility="collapsed")
                
                # Sub Category Select
                sub_opts = [""] + st.session_state.cashew_struct.get(sel_main, [])
                sel_sub = st.selectbox("Sottocategoria", sub_opts, key=f"s_{w_cat}", label_visibility="collapsed", placeholder="Sottocategoria...")
                
                # SQL Extras
                sel_col = guess_color
                sel_ico = guess_icon
                if st.session_state.import_mode == "SQL":
                    c_style1, c_style2 = st.columns([1, 3])
                    sel_col = c_style1.color_picker("Colore", guess_color, key=f"co_{w_cat}", label_visibility="collapsed")
                    sel_ico = c_style2.text_input("Icona (.png)", value=guess_icon, key=f"ic_{w_cat}", label_visibility="collapsed")
                
                # Save to session
                st.session_state.mapping_config[w_cat] = {
                    "main": sel_main, "sub": sel_sub, "color": sel_col, "icon": sel_ico
                }
                
                st.markdown("</div>", unsafe_allow_html=True) 
                # CARD CONTAINER END

    c1, c2 = st.columns([1, 5])
    if c1.button("⬅ Indietro"):
        prev_step()
        st.rerun()
    if c2.button("Genera File Finale 🚀", type="primary"):
        next_step()
        st.rerun()

# =================================================================================
# STEP 4: EXPORT & DOWNLOAD
# =================================================================================
elif st.session_state.step == 4:
    st.title("🎉 Tutto Pronto!")
    st.markdown("Il tuo file di migrazione è stato generato.")
    
    df = st.session_state.df_wallet
    mapping = st.session_state.mapping_config
    accs = st.session_state.account_config
    is_sql = st.session_state.import_mode == "SQL"
    
    # --- LOGICA DI GENERAZIONE ---
    
    if is_sql:
        # SQL GENERATION LOGIC
        script = "BEGIN TRANSACTION;\nDELETE FROM wallets;\nDELETE FROM categories;\nDELETE FROM transactions;\n"
        
        # UUID Maps
        cat_uuids = {} 
        acc_uuids = {}
        now_ms = int(time.time() * 1000)
        
        # 1. Wallets
        for orig_acc, conf in accs.items():
            uid = generate_uuid()
            acc_uuids[orig_acc] = uid
            script += f"INSERT INTO \"wallets\" VALUES('{uid}','{conf['name']}',{conf['color']},{now_ms},1,0,'{conf['currency']}',0,0,NULL,NULL);\n"
            
        # 2. Categories
        processed_main = set()
        # Create Main
        for w_cat, conf in mapping.items():
            m_name = conf['main']
            if m_name not in processed_main:
                uid = generate_uuid()
                cat_uuids[(m_name, "")] = uid
                script += f"INSERT INTO \"categories\" VALUES('{uid}','{m_name}','{conf['color']}','{conf['icon']}',NULL,{now_ms},1765015012,0,0,0,NULL);\n"
                processed_main.add(m_name)
        # Create Subs
        for w_cat, conf in mapping.items():
            m_name = conf['main']
            s_name = conf['sub']
            if s_name:
                key = (m_name, s_name)
                if key not in cat_uuids:
                    uid = generate_uuid()
                    cat_uuids[key] = uid
                    p_uid = cat_uuids.get((m_name, ""), "0")
                    script += f"INSERT INTO \"categories\" VALUES('{uid}','{s_name}',NULL,NULL,NULL,{now_ms},1765015012,0,0,0,'{p_uid}');\n"

        # 3. Transactions
        trans_list = []
        for idx, row in df.iterrows():
            w_cat = row.get('category', '')
            conf = mapping.get(w_cat, {"main": "Altro", "sub": ""})
            
            # IDs
            w_fk = acc_uuids.get(row.get('account'), "0")
            c_fk = cat_uuids.get((conf['main'], conf['sub']))
            if not c_fk: c_fk = cat_uuids.get((conf['main'], ""), "0")
            
            # Info
            is_transf = str(row.get('transfer', 'false')).lower() == 'true' or str(row.get('type', '')).upper() == 'TRANSFER'
            note = str(row.get('note', ''))
            payee = str(row.get('payee', ''))
            if payee and payee != 'nan': note += f" | {payee}"
            
            t_obj = {
                "id": generate_uuid(),
                "date": get_timestamp_ms(row.get('date', '')),
                "amount": row['amount_clean'],
                "title": conf['main'],
                "note": note,
                "w_fk": w_fk,
                "c_fk": c_fk,
                "is_transfer": is_transf,
                "paired": "NULL"
            }
            trans_list.append(t_obj)
            
        # Pairing Logic
        matched = set()
        for i, t1 in enumerate(trans_list):
            if t1['is_transfer'] and t1['id'] not in matched:
                for j, t2 in enumerate(trans_list):
                    if i==j or t2['id'] in matched or not t2['is_transfer']: continue
                    if abs(t1['amount'] + t2['amount']) < 0.01 and abs(t1['date'] - t2['date']) < 60000:
                        t1['paired'] = f"'{t2['id']}'"
                        t2['paired'] = f"'{t1['id']}'"
                        t1['title'] = "Trasferimento"
                        t2['title'] = "Trasferimento"
                        matched.add(t1['id'])
                        matched.add(t2['id'])
                        break
        
        # Write Trans
        for t in trans_list:
            clean_note = t['note'].replace("'", "''")
            clean_title = t['title'].replace("'", "''")
            inc = 1 if t['amount'] > 0 else 0
            script += f"INSERT INTO \"transactions\" VALUES('{t['id']}',{t['paired']},'{clean_title}',{t['amount']},'{clean_note}','{t['c_fk']}',NULL,'{t['w_fk']}',{t['date']},1765015012,1765015012,{inc},NULL,NULL,NULL,1,NULL,1,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);\n"
            
        script += "COMMIT;"
        final_data = script
        file_name = "cashew_restore.sql"
        mime = "text/x-sql"
        
    else:
        # CSV MODE (Semplificata)
        out_rows = []
        for _, row in df.iterrows():
            w_cat = row.get('category', '')
            conf = mapping.get(w_cat, {"main": "Altro", "sub": ""})
            acc_info = accs.get(row.get('account'), {})
            out_rows.append({
                "account": acc_info.get("name", row.get('account')),
                "amount": row['amount_clean'],
                "currency": "EUR",
                "title": conf['main'],
                "note": str(row.get('note', '')),
                "date": row.get('date', ''),
                "category name": conf['main'],
                "subcategory name": conf['sub']
            })
        final_data = pd.DataFrame(out_rows).to_csv(index=False)
        file_name = "cashew_import.csv"
        mime = "text/csv"

    # --- UI DOWNLOAD ---
    col_res1, col_res2 = st.columns([1, 1])
    with col_res1:
        st.success("✅ Generazione completata con successo!")
        st.metric("Totale Transazioni", len(df))
        
    with col_res2:
        st.markdown("### 👇 Scarica il file")
        st.download_button(
            label=f"💾 SCARICA {file_name.upper()}",
            data=final_data,
            file_name=file_name,
            mime=mime,
            type="primary"
        )
        
        if is_sql:
            st.info("""
            **Come importare:**
            1. Invia questo file al tuo telefono.
            2. Apri Cashew > Impostazioni > Backup e Ripristino.
            3. Seleziona **Ripristina Backup** e scegli il file.
            """)
            
    if st.button("🔄 Ricomincia da capo"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()