import streamlit as st
import pandas as pd
import json
import difflib

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Wallet to Cashew Pro Converter",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS CUSTOM & STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    .main-header { font-size: 2.5rem; color: #2c3e50; font-weight: 700; margin-bottom: 0px; }
    .sub-header { font-size: 1.2rem; color: #7f8c8d; margin-bottom: 20px; }
    .card { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .mapping-row { border-bottom: 1px solid #eee; padding: 10px 0; }
    .highlight { color: #4CAF50; font-weight: bold; }
    /* Render buttons nicer */
    div.stButton > button:first-child { border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI UTILITÀ ---

def fix_encoding_issues(text):
    if not isinstance(text, str): return text
    try: return text.encode('cp1252').decode('utf-8')
    except: return text

def parse_amount(value):
    if isinstance(value, (int, float)): return float(value)
    if pd.isna(value) or value == '': return 0.0
    val_str = str(value).replace('€', '').replace('$', '').strip()
    # Gestione formati EU/US
    if ',' in val_str and '.' in val_str:
        if val_str.rfind(',') > val_str.rfind('.'): val_str = val_str.replace('.', '').replace(',', '.')
        else: val_str = val_str.replace(',', '')
    elif ',' in val_str: val_str = val_str.replace(',', '.')
    try: return float(val_str)
    except: return 0.0

def smart_guess_category(wallet_cat, cashew_structure):
    """
    Cerca la categoria Cashew più simile al nome della categoria Wallet.
    Ritorna (Category, Subcategory)
    """
    wallet_cat_lower = wallet_cat.lower()
    
    # 1. Cerca match esatto o parziale nelle Sottocategorie
    for main_cat, subs in cashew_structure.items():
        # Check Main Category Name
        if wallet_cat_lower in main_cat.lower():
            return main_cat, ""
        
        # Check Subcategories
        for sub in subs:
            if wallet_cat_lower in sub.lower() or sub.lower() in wallet_cat_lower:
                return main_cat, sub
                
    # 2. Fuzzy match se non trova nulla
    all_main_cats = list(cashew_structure.keys())
    matches = difflib.get_close_matches(wallet_cat, all_main_cats, n=1, cutoff=0.6)
    if matches:
        return matches[0], ""
        
    return None, None

# --- INIZIALIZZAZIONE SESSION STATE ---
# Struttura di default Cashew (Gerarchica)
if 'cashew_structure' not in st.session_state:
    st.session_state.cashew_structure = {
        "Alimentari": ["Supermercato", "Minimarket"],
        "Mangiare fuori": ["Ristorante", "Bar", "Fast Food"],
        "Trasporti": ["Benzina", "Treno", "Bus", "Parcheggio", "Manutenzione"],
        "Shopping": ["Vestiti", "Elettronica", "Casa"],
        "Divertimento": ["Cinema", "Streaming", "Hobby"],
        "Bollette": ["Luce", "Gas", "Internet", "Affitto"],
        "Salute": ["Farmacia", "Dottore", "Sport"],
        "Reddito": ["Stipendio", "Rimborsi", "Regali"],
        "Correzione saldo": [],
        "Altro": []
    }

# --- UI HEADER ---
st.markdown('<div class="main-header">🔄 Wallet to Cashew Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Strumento avanzato di migrazione dati finanziari</div>', unsafe_allow_html=True)

# --- SIDEBAR: GESTIONE CONFIGURAZIONE ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    st.info("💡 Suggerimento: Salva la tua configurazione per non dover rimappare tutto la prossima volta!")
    
    # Upload Config
    uploaded_config = st.file_uploader("📂 Carica file Mappatura (.json)", type=['json'])
    if uploaded_config is not None:
        try:
            data = json.load(uploaded_config)
            st.session_state.saved_mapping = data.get('mapping', {})
            st.session_state.saved_accounts = data.get('accounts', {})
            # Se nel json c'è anche la struttura categorie personalizzata
            if 'structure' in data:
                st.session_state.cashew_structure = data['structure']
            st.success("Configurazione caricata!")
        except:
            st.error("File JSON non valido.")

# --- STEP 1: UPLOAD DATA ---
st.markdown("### 1️⃣ Importazione Dati")
uploaded_file = st.file_uploader("Carica il file `wallet.csv`", type=['csv'])

if uploaded_file:
    # --- LETTURA FILE ---
    try:
        df = pd.read_csv(uploaded_file, sep=';')
        if len(df.columns) < 2:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=',')
        
        # Encoding Fix
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(fix_encoding_issues)
        
        df['amount_clean'] = df['amount'].apply(parse_amount)
        
        # Estrazione Liste Univoche
        unique_cats = sorted(df['category'].dropna().unique().tolist())
        unique_accs = sorted(df['account'].dropna().unique().tolist())
        
        # Statistiche rapide
        c1, c2, c3 = st.columns(3)
        c1.metric("Transazioni", len(df))
        c2.metric("Categorie Wallet", len(unique_cats))
        c3.metric("Conti Rilevati", len(unique_accs))

    except Exception as e:
        st.error(f"Errore lettura file: {e}")
        st.stop()

    # --- STEP 2: DEFINIZIONE STRUTTURA CASHEW ---
    st.markdown("---")
    st.markdown("### 2️⃣ Struttura Categorie Cashew")
    st.markdown("""
    Definisci qui le categorie e sottocategorie esatte che usi su Cashew. 
    Questa struttura verrà usata per creare i menu a tendina nel prossimo passaggio.
    """)
    
    with st.expander("🛠️ Modifica Struttura Categorie (Avanzato)", expanded=False):
        # Convertiamo il dict in DataFrame per l'editing
        flat_data = []
        for cat, subs in st.session_state.cashew_structure.items():
            if not subs:
                flat_data.append({"Categoria": cat, "Sottocategoria": ""})
            else:
                for sub in subs:
                    flat_data.append({"Categoria": cat, "Sottocategoria": sub})
        
        df_structure = pd.DataFrame(flat_data)
        edited_df = st.data_editor(df_structure, num_rows="dynamic", use_container_width=True)
        
        # Ricostruiamo il dict dalla tabella modificata
        new_structure = {}
        for _, row in edited_df.iterrows():
            c = row['Categoria'].strip()
            s = row['Sottocategoria'].strip() if row['Sottocategoria'] else ""
            if c:
                if c not in new_structure: new_structure[c] = []
                if s and s not in new_structure[c]: new_structure[c].append(s)
        
        st.session_state.cashew_structure = new_structure

    # --- STEP 3: MAPPATURA INTELLIGENTE ---
    st.markdown("---")
    st.markdown("### 3️⃣ Mappatura Categorie")
    
    col_filter, col_reset = st.columns([3, 1])
    filter_text = col_filter.text_input("🔍 Cerca categoria Wallet...", "")
    
    # Container scrollabile per le mappature
    with st.container(height=500):
        mapping_results = {} # Store results: key=wallet_cat, val={'main': .., 'sub': ..}
        
        # Recupera mapping salvato se esiste
        saved_map = st.session_state.get('saved_mapping', {})

        filtered_cats = [c for c in unique_cats if filter_text.lower() in c.lower()]
        
        for w_cat in filtered_cats:
            st.markdown(f"<div class='mapping-row'>", unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns([3, 0.5, 3, 3])
            
            c1.markdown(f"**{w_cat}**")
            c2.write("➡")
            
            # Logica di Pre-selezione:
            # 1. Mapping Salvato (JSON)
            # 2. Smart Guess (Nome simile)
            # 3. Default (Primo della lista)
            
            curr_main = saved_map.get(w_cat, {}).get('main')
            curr_sub = saved_map.get(w_cat, {}).get('sub')
            
            if not curr_main:
                guess_main, guess_sub = smart_guess_category(w_cat, st.session_state.cashew_structure)
                if guess_main:
                    curr_main = guess_main
                    curr_sub = guess_sub
            
            # Dropdown Main Category
            main_options = list(st.session_state.cashew_structure.keys())
            try:
                idx_main = main_options.index(curr_main) if curr_main in main_options else 0
            except: idx_main = 0
            
            sel_main = c3.selectbox(
                "Cat", main_options, index=idx_main, 
                key=f"m_{w_cat}", label_visibility="collapsed"
            )
            
            # Dropdown Sub Category (Dynamic based on Main)
            sub_options = [""] + st.session_state.cashew_structure.get(sel_main, [])
            try:
                idx_sub = sub_options.index(curr_sub) if curr_sub in sub_options else 0
            except: idx_sub = 0
            
            sel_sub = c4.selectbox(
                "Sub", sub_options, index=idx_sub, 
                key=f"s_{w_cat}", label_visibility="collapsed"
            )
            
            mapping_results[w_cat] = {'main': sel_main, 'sub': sel_sub}
            st.markdown("</div>", unsafe_allow_html=True)

    # --- STEP 4: ACCOUNT MAPPING ---
    st.markdown("### 4️⃣ Mappatura Conti")
    with st.expander("💳 Configura Nomi Conti", expanded=True):
        saved_accs = st.session_state.get('saved_accounts', {})
        acc_mapping_res = {}
        cols = st.columns(3)
        for i, acc in enumerate(unique_accs):
            val = saved_accs.get(acc, acc)
            acc_mapping_res[acc] = cols[i % 3].text_input(f"Wallet: {acc}", value=val)

    # --- STEP 5: ELABORAZIONE & ANTEPRIMA ---
    st.markdown("---")
    st.markdown("### 5️⃣ Anteprima e Export")
    
    include_payee = st.checkbox("Includi 'Payee' nelle note", value=True)
    
    if st.button("🔄 Genera Anteprima", type="primary"):
        processed_rows = []
        
        for index, row in df.iterrows():
            # Basic info
            orig_acc = row.get('account', '')
            target_acc = acc_mapping_res.get(orig_acc, orig_acc)
            amount = row['amount_clean']
            w_cat = row.get('category', '')
            w_note = str(row.get('note', '')) if not pd.isna(row.get('note', '')) else ""
            w_payee = str(row.get('payee', '')) if not pd.isna(row.get('payee', '')) else ""
            
            # Transfer Logic
            is_transfer = str(row.get('transfer', 'false')).lower() == 'true' or \
                          str(row.get('type', '')).upper() == 'TRANSFER'
            
            target_cat, target_sub, target_title = "", "", w_cat
            final_note = w_note

            if is_transfer:
                target_cat = "Correzione saldo"
                target_title = "Trasferimento"
                prefix = f"Trasferimento ({w_cat})" if w_cat != 'TRANSFER' else "Trasferimento"
                final_note = f"{prefix}\n{w_note}" if w_note else prefix
            else:
                # Get mapping
                if w_cat in mapping_results:
                    target_cat = mapping_results[w_cat]['main']
                    target_sub = mapping_results[w_cat]['sub']
                else:
                    target_cat = "Altro"
                
                # Payee Logic
                if include_payee and w_payee:
                    sep = " | " if final_note else ""
                    final_note += f"{sep}Payee: {w_payee}"

            new_row = {
                "account": target_acc,
                "amount": amount,
                "currency": row.get('currency', 'EUR'),
                "title": target_title,
                "note": final_note,
                "date": row.get('date', ''),
                "income": str(amount > 0).lower(),
                "category name": target_cat,
                "subcategory name": target_sub,
                # Default nulls
                "type": "null", "color": "", "icon": "", "emoji": "", "budget": "", "objective": ""
            }
            processed_rows.append(new_row)
        
        df_cashew = pd.DataFrame(processed_rows)
        
        # Visualizzazione Anteprima
        st.subheader("📊 Anteprima Dati")
        st.dataframe(df_cashew.head(100), use_container_width=True)
        
        # Creazione JSON Configurazione per il futuro
        config_export = {
            "mapping": mapping_results,
            "accounts": acc_mapping_res,
            "structure": st.session_state.cashew_structure
        }
        json_config = json.dumps(config_export, indent=2)
        
        c_down1, c_down2 = st.columns(2)
        
        # Download CSV
        csv_data = df_cashew.to_csv(index=False, sep=',', encoding='utf-8')
        c_down1.download_button(
            label="💾 SCARICA CSV CASHEW",
            data=csv_data,
            file_name="cashew_import.csv",
            mime="text/csv",
            type="primary"
        )
        
        # Download Config JSON
        c_down2.download_button(
            label="⚙️ Scarica Configurazione Mappatura",
            data=json_config,
            file_name="wallet_mapping_config.json",
            mime="application/json",
            help="Salva questo file e ricaricalo la prossima volta per non dover rifare la mappatura!"
        )

# Footer
st.markdown("---")
st.caption("Developed for personal finance migration.")