import streamlit as st
import pandas as pd
import json
import difflib
import uuid
import datetime
import time

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Ultimate Wallet to Cashew Migrator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS & STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .main-header { font-size: 2.5rem; color: #2c3e50; font-weight: 800; }
    .sub-header { font-size: 1.2rem; color: #7f8c8d; margin-bottom: 20px; }
    .card { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .pro-badge { background-color: #e3f2fd; color: #1565c0; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
    .vs-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
    .vs-table th { text-align: left; background: #eee; padding: 8px; }
    .vs-table td { border-bottom: 1px solid #ddd; padding: 8px; }
</style>
""", unsafe_allow_html=True)

# --- LOGICA CORE ---

def generate_uuid():
    return str(uuid.uuid4())

def get_timestamp_ms(date_str):
    """Converte stringa data (YYYY-MM-DD HH:MM:SS) in Unix Timestamp MS"""
    try:
        if pd.isna(date_str): return int(time.time() * 1000)
        # Tenta formati comuni
        formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M"]
        dt_obj = None
        for fmt in formats:
            try:
                dt_obj = datetime.datetime.strptime(str(date_str)[:19], fmt)
                break
            except: pass
        
        if dt_obj:
            return int(dt_obj.timestamp() * 1000)
        return int(time.time() * 1000)
    except:
        return int(time.time() * 1000)

def fix_encoding(text):
    if not isinstance(text, str): return text
    try: return text.encode('cp1252').decode('utf-8')
    except: return text

def parse_amount(value):
    if isinstance(value, (int, float)): return float(value)
    val_str = str(value).replace('€', '').replace('$', '').strip()
    if ',' in val_str and '.' in val_str:
        if val_str.rfind(',') > val_str.rfind('.'): val_str = val_str.replace('.', '').replace(',', '.')
        else: val_str = val_str.replace(',', '')
    elif ',' in val_str: val_str = val_str.replace(',', '.')
    try: return float(val_str)
    except: return 0.0

def smart_style_guess(name):
    """Restituisce (colore, icona) basandosi sul nome"""
    name = name.lower()
    
    # Mappatura keywords -> (Icona Cashew, Colore Hex)
    keywords = {
        "cibo": ("food.png", "#4CAF50"), "mangiare": ("food.png", "#4CAF50"), "ristorante": ("restaurant.png", "#FF9800"),
        "spesa": ("groceries.png", "#8BC34A"), "alimentari": ("groceries.png", "#8BC34A"),
        "auto": ("car.png", "#F44336"), "benzina": ("fuel.png", "#D32F2F"), "trasporti": ("bus.png", "#E91E63"),
        "casa": ("house.png", "#795548"), "bollette": ("bills.png", "#FF5722"), "affitto": ("house.png", "#795548"),
        "salute": ("health.png", "#00BCD4"), "farmacia": ("health.png", "#00BCD4"),
        "shopping": ("shopping.png", "#9C27B0"), "vestiti": ("clothes.png", "#673AB7"),
        "stipendio": ("salary.png", "#2196F3"), "reddito": ("money.png", "#4CAF50"),
        "divertimento": ("entertainment.png", "#FFC107"), "viaggi": ("plane.png", "#03A9F4"),
        "regali": ("gift.png", "#E91E63"), "sport": ("sport.png", "#FFEB3B")
    }
    
    for k, v in keywords.items():
        if k in name:
            return v
    
    return ("category_default.png", "#9E9E9E") # Default grigio

# --- STRUTTURA DATABASE CASHEW (Scheletro) ---
# Usiamo questo per inizializzare le categorie
DEFAULT_STRUCTURE = {
    "Alimentari": ["Supermercato", "Minimarket"],
    "Mangiare fuori": ["Ristorante", "Bar", "Fast Food"],
    "Trasporti": ["Benzina", "Treno", "Bus", "Manutenzione"],
    "Shopping": ["Abbigliamento", "Elettronica", "Casa"],
    "Casa & Bollette": ["Luce", "Gas", "Internet", "Affitto"],
    "Salute & Benessere": ["Farmacia", "Medico", "Sport"],
    "Divertimento": ["Cinema", "Hobby", "Viaggi"],
    "Reddito": ["Stipendio", "Rimborsi", "Extra"],
    "Altro": []
}

# --- HEADER APP ---
st.markdown('<div class="main-header">🚀 Ultimate Migrator: Wallet ➡ Cashew</div>', unsafe_allow_html=True)

# --- STEP 0: SCELTA FORMATO (CRUCIALE) ---
with st.container():
    st.markdown("### 🛠️ Step 1: Scegli il metodo di importazione")
    st.markdown("Prima di iniziare, decidi come vuoi importare i dati. Leggi attentamente le differenze.")
    
    col_mode1, col_mode2 = st.columns(2)
    
    mode = st.radio("Seleziona Modalità:", ["SQL (Consigliato - Reset Totale)", "CSV (Base - Aggiunta)"], horizontal=True)
    
    is_sql_mode = "SQL" in mode

    with st.expander("ℹ️ Confronto dettagliato tra SQL e CSV (Clicca per leggere)", expanded=True):
        st.markdown("""
        | Caratteristica | 🏆 SQL (Backup Restore) | 📄 CSV (Import Standard) |
        | :--- | :--- | :--- |
        | **Risultato Finale** | **App pulita e perfetta** | Dati aggiunti all'esistente |
        | **Trasferimenti** | ✅ **Uniti e collegati** | ⚠️ Due transazioni separate |
        | **Categorie** | ✅ Colori e Icone personalizzati | ❌ Solo nomi (colori casuali) |
        | **Gerarchia** | ✅ Categorie e Sottocategorie native | ⚠️ Spesso appiattite o da sistemare |
        | **Conti** | ✅ Supporto Valuta multipla | ✅ Supporto base |
        | **Rischio** | ⚠️ **Sovrascrive i dati attuali** | ✅ Aggiunge senza cancellare |
        """)
        
    if is_sql_mode:
        st.warning("⚠️ **ATTENZIONE:** L'importazione SQL sostituirà completamente il database attuale di Cashew. Usalo se vuoi partire con una installazione pulita importando tutto il tuo storico.")
    else:
        st.info("ℹ️ Il CSV è utile se vuoi solo aggiungere vecchie transazioni a un utilizzo già in corso di Cashew.")

# --- STEP 1: CARICAMENTO FILE ---
st.markdown("### 📂 Step 2: Carica Export Wallet")
uploaded_file = st.file_uploader("Carica `wallet.csv`", type=['csv'])

if uploaded_file:
    # Lettura
    try:
        df = pd.read_csv(uploaded_file, sep=';')
        if len(df.columns) < 2:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=',')
        
        # Pulizia base
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(fix_encoding)
        df['amount_clean'] = df['amount'].apply(parse_amount)
        
        unique_cats = sorted(df['category'].dropna().unique().tolist())
        unique_accs = sorted(df['account'].dropna().unique().tolist())
        
        st.success(f"File letto: {len(df)} transazioni trovate.")

    except Exception as e:
        st.error(f"Errore: {e}")
        st.stop()

    # --- STEP 3: MAPPATURA (UI DINAMICA) ---
    
    # 3.1 SETUP STRUTTURA CATEGORIE (Comune a SQL e CSV)
    st.markdown("### 🎨 Step 3: Categorie & Stile")
    st.markdown("Definisci la struttura delle categorie su Cashew.")
    
    # Init session state structure
    if 'cashew_struct' not in st.session_state:
        st.session_state.cashew_struct = DEFAULT_STRUCTURE

    # Editor Struttura
    with st.expander("Gestisci Struttura Categorie (Aggiungi/Rimuovi)", expanded=False):
        # Flatten for editor
        flat_list = []
        for m, subs in st.session_state.cashew_struct.items():
            if not subs: flat_list.append({"Main": m, "Sub": ""})
            for s in subs: flat_list.append({"Main": m, "Sub": s})
        
        edited_df = st.data_editor(pd.DataFrame(flat_list), num_rows="dynamic", use_container_width=True)
        
        # Rebuild
        new_struct = {}
        for _, r in edited_df.iterrows():
            m, s = r['Main'].strip(), r['Sub'].strip() if r['Sub'] else ""
            if m:
                if m not in new_struct: new_struct[m] = []
                if s and s not in new_struct[m]: new_struct[m].append(s)
        st.session_state.cashew_struct = new_struct

    # Mappatura Wallet -> Cashew
    st.markdown("#### Collega le categorie di Wallet")
    mapping_res = {} # Key: wallet_cat -> Val: {main, sub, color, icon}
    
    col_search, _ = st.columns([1,2])
    search_q = col_search.text_input("Cerca categoria...", "")
    
    # Container mappatura
    with st.container(height=500):
        cats_to_show = [c for c in unique_cats if search_q.lower() in c.lower()]
        
        for w_cat in cats_to_show:
            st.markdown(f"**{w_cat}**")
            c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
            
            # Smart Guess
            guess_icon, guess_color = smart_style_guess(w_cat)
            
            # Select Main
            main_opts = list(st.session_state.cashew_struct.keys())
            # Simple match
            def_idx = 0
            for i, m in enumerate(main_opts):
                if w_cat.lower() in m.lower(): def_idx = i; break
            
            sel_main = c1.selectbox("Categoria", main_opts, index=def_idx, key=f"m_{w_cat}", label_visibility="collapsed")
            
            # Select Sub
            sub_opts = [""] + st.session_state.cashew_struct.get(sel_main, [])
            sel_sub = c2.selectbox("Sotto-Cat", sub_opts, key=f"s_{w_cat}", label_visibility="collapsed")
            
            # Extra SQL options
            sel_color = guess_color
            sel_icon = guess_icon
            
            if is_sql_mode:
                sel_color = c3.color_picker("Colore", value=guess_color, key=f"col_{w_cat}", label_visibility="collapsed")
                # Icon text input (sarebbe troppo lungo fare un selectbox con tutte le icone)
                sel_icon = c4.text_input("Icona (.png)", value=guess_icon, key=f"ico_{w_cat}", label_visibility="collapsed", help="Es: food.png, car.png, shopping.png")
            
            mapping_res[w_cat] = {
                "main": sel_main, "sub": sel_sub, 
                "color": sel_color, "icon": sel_icon
            }
            st.divider()

    # 3.2 SETUP ACCOUNT (CONTI)
    st.markdown("### 💳 Step 4: Conti e Valute")
    acc_config = {}
    
    col_accs = st.columns(2)
    for i, acc in enumerate(unique_accs):
        with col_accs[i % 2]:
            st.markdown(f"Conto Originale: **{acc}**")
            c_name, c_curr, c_col = st.columns([2, 1, 1])
            
            n_name = c_name.text_input("Nome Cashew", value=acc, key=f"an_{acc}")
            n_curr = "EUR"
            n_color = "#607D8B"
            
            if is_sql_mode:
                n_curr = c_curr.selectbox("Valuta", ["EUR", "USD", "GBP", "CHF"], key=f"ac_{acc}")
                n_color = c_col.color_picker("Colore", value="#607D8B", key=f"acol_{acc}")
            
            acc_config[acc] = {"name": n_name, "currency": n_curr, "color": n_color}
            st.write("---")

    # --- STEP 4: GENERAZIONE ---
    st.markdown("### 🚀 Step 5: Generazione File")
    
    if st.button("GENERA FILE DI MIGRAZIONE", type="primary"):
        
        # --- GENERATORE CSV CLASSICO ---
        if not is_sql_mode:
            csv_rows = []
            for _, row in df.iterrows():
                # ... (Logica CSV simile alla precedente versione) ...
                # Semplificata per brevità qui, userà mapping_res
                w_cat = row.get('category', '')
                map_data = mapping_res.get(w_cat, {"main": "Altro", "sub": ""})
                
                new_row = {
                    "account": acc_config.get(row.get('account'), {}).get('name', row.get('account')),
                    "amount": row['amount_clean'],
                    "currency": row.get('currency', 'EUR'),
                    "title": w_cat,
                    "note": str(row.get('note', '')),
                    "date": row.get('date', ''),
                    "income": str(row['amount_clean'] > 0).lower(),
                    "category name": map_data['main'],
                    "subcategory name": map_data['sub']
                }
                csv_rows.append(new_row)
            
            res_df = pd.DataFrame(csv_rows)
            st.download_button("Scarica CSV", res_df.to_csv(index=False), "cashew_import.csv", "text/csv")
            
        # --- GENERATORE SQL (POWER MODE) ---
        else:
            st.info("⏳ Elaborazione SQL in corso... Creazione database virtuale...")
            
            # 1. Preparazione UUIDs per Categorie e Conti
            # Mappa (MainCat, SubCat) -> UUID
            cat_uuids = {} 
            acc_uuids = {}
            
            sql_script = "BEGIN TRANSACTION;\n"
            
            # --- TABELLA WALLETS (Conti) ---
            sql_script += "-- WALLETS --\n"
            sql_script += "DELETE FROM wallets;\n"
            
            for orig_acc, conf in acc_config.items():
                w_uuid = generate_uuid()
                acc_uuids[orig_acc] = w_uuid
                now_ms = int(time.time() * 1000)
                
                # INSERT wallet
                sql_script += f"INSERT INTO \"wallets\" VALUES('{w_uuid}','{conf['name']}',{conf['color']},{now_ms},1,0,'{conf['currency']}',0,0,NULL,NULL);\n"

            # --- TABELLA CATEGORIES ---
            sql_script += "\n-- CATEGORIES --\n"
            sql_script += "DELETE FROM categories;\n"
            
            # Dobbiamo creare prima le MAIN, poi le SUB
            processed_main = set()
            
            # Analizziamo tutte le categorie mappate per assicurarci di creare tutto
            # Prima passata: Crea Main Categories univoche
            for w_cat, conf in mapping_res.items():
                m_name = conf['main']
                if m_name not in processed_main:
                    m_uuid = generate_uuid()
                    cat_uuids[(m_name, "")] = m_uuid # Key: (Main, "")
                    now_ms = int(time.time() * 1000)
                    
                    # Colore/Icona prendiamo dal primo che capita o default
                    m_col = conf['color'] 
                    m_ico = conf['icon']
                    
                    sql_script += f"INSERT INTO \"categories\" VALUES('{m_uuid}','{m_name}','{m_col}','{m_ico}',NULL,{now_ms},1765015012,0,0,0,NULL);\n"
                    processed_main.add(m_name)
            
            # Seconda passata: Crea Sub Categories
            for w_cat, conf in mapping_res.items():
                m_name = conf['main']
                s_name = conf['sub']
                
                if s_name:
                    s_key = (m_name, s_name)
                    if s_key not in cat_uuids:
                        s_uuid = generate_uuid()
                        cat_uuids[s_key] = s_uuid
                        parent_uuid = cat_uuids.get((m_name, ""), "0")
                        now_ms = int(time.time() * 1000)
                        
                        # Subcat eredita stile o custom? Cashew le subcat spesso non hanno icona, usano la main
                        sql_script += f"INSERT INTO \"categories\" VALUES('{s_uuid}','{s_name}',NULL,NULL,NULL,{now_ms},1765015012,0,0,0,'{parent_uuid}');\n"

            # --- TABELLA TRANSACTIONS ---
            sql_script += "\n-- TRANSACTIONS --\n"
            sql_script += "DELETE FROM transactions;\n"
            
            # Pre-processing per Transfers
            # Dobbiamo identificare le coppie.
            # Convertiamo df in lista di dict per manipolazione facile
            trans_list = []
            
            for idx, row in df.iterrows():
                # Dati base
                orig_acc = row.get('account')
                amount = row['amount_clean']
                date_str = row.get('date', '')
                ts = get_timestamp_ms(date_str)
                is_transfer = str(row.get('transfer', 'false')).lower() == 'true' or str(row.get('type', '')).upper() == 'TRANSFER'
                
                # Categoria ID
                w_cat = row.get('category', '')
                map_conf = mapping_res.get(w_cat, {"main": "Altro", "sub": ""})
                
                # Recupera UUID categoria
                # Se c'è sub, usa sub UUID, altrimenti Main UUID
                cat_key = (map_conf['main'], map_conf['sub'])
                cat_fk = cat_uuids.get(cat_key)
                if not cat_fk: 
                    cat_fk = cat_uuids.get((map_conf['main'], ""), "0") # Fallback main
                
                # Wallet FK
                w_fk = acc_uuids.get(orig_acc, "0")
                
                t_uuid = generate_uuid()
                
                trans_obj = {
                    "id": t_uuid,
                    "date_ms": ts,
                    "amount": amount,
                    "note": str(row.get('note', '')),
                    "payee": str(row.get('payee', '')),
                    "wallet_fk": w_fk,
                    "category_fk": cat_fk,
                    "is_transfer": is_transfer,
                    "orig_idx": idx, # Per debugging
                    "paired_id": "NULL",
                    "title": map_conf['main'] # Titolo = Nome categoria come richiesto
                }
                trans_list.append(trans_obj)

            # Logic Pairing Transfer
            # Cerchiamo transazioni con stesso importo assoluto, stessa data (approx), conti diversi, flag transfer
            # Per semplicità, iteriamo e cerchiamo match
            matched_ids = set()
            
            for i, t1 in enumerate(trans_list):
                if t1['is_transfer'] and t1['id'] not in matched_ids:
                    # Cerca il suo paio
                    for j, t2 in enumerate(trans_list):
                        if i == j: continue
                        if t2['id'] in matched_ids: continue
                        if not t2['is_transfer']: continue
                        
                        # Logica match: Somma deve essere 0 (es. -50 e +50), date vicine
                        # Wallet export ha date precise al secondo, dovrebbero matchare
                        # Per sicurezza usiamo un delta di 60 secondi
                        amount_match = abs(t1['amount'] + t2['amount']) < 0.01
                        time_match = abs(t1['date_ms'] - t2['date_ms']) < 60000 
                        
                        if amount_match and time_match:
                            # Trovato!
                            t1['paired_id'] = f"'{t2['id']}'"
                            t2['paired_id'] = f"'{t1['id']}'"
                            t1['title'] = "Trasferimento"
                            t2['title'] = "Trasferimento"
                            # Per i transfer la categoria è meglio "Correzione saldo" (se esiste) o vuota
                            # Qui lasciamo quella mappata o forziamo se vuoi
                            
                            matched_ids.add(t1['id'])
                            matched_ids.add(t2['id'])
                            break

            # Scrittura SQL Transazioni
            for t in trans_list:
                # Componi note
                final_note = t['note']
                if t['payee'] and t['payee'] != 'nan':
                     final_note += f" | {t['payee']}"
                
                # Escape stringhe SQL
                final_note = final_note.replace("'", "''")
                title = t['title'].replace("'", "''")
                
                income_flag = 1 if t['amount'] > 0 else 0
                
                sql = f"""INSERT INTO "transactions" VALUES('{t['id']}',{t['paired_id']},'{title}',{t['amount']},'{final_note}','{t['category_fk']}',NULL,'{t['wallet_fk']}',{t['date_ms']},1765015012,1765015012,{income_flag},NULL,NULL,NULL,1,NULL,1,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);"""
                sql_script += sql + "\n"
                
            sql_script += "COMMIT;\n"
            
            st.balloons()
            st.success("✅ File SQL Generato con successo!")
            st.download_button("💾 SCARICA BACKUP SQL (cashew_restore.sql)", sql_script, "cashew_restore.sql", "text/x-sql")
            
            st.warning("""
            **Come importare su Cashew:**
            1. Scarica il file `.sql`.
            2. Apri Cashew sul telefono.
            3. Vai su **Impostazioni** > **Backup e Ripristino**.
            4. Seleziona **Ripristina Backup**.
            5. Scegli questo file.
            (Nota: Cashew potrebbe richiedere che il file sia zippato o avere estensione .backup a seconda della versione, prova prima così).
            """)