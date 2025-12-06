import streamlit as st
import pandas as pd
import io

# --- CONFIGURAZIONE PAGINA (Deve essere la prima istruzione) ---
st.set_page_config(
    page_title="Wallet to Cashew Converter",
    page_icon="💸",
    layout="centered", # Layout centrato per focalizzare l'attenzione
    initial_sidebar_state="expanded"
)

# --- CSS CUSTOM PER MIGLIORARE L'ESTETICA ---
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    h1 {
        color: #2c3e50;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
        border-color: #45a049;
    }
    .step-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .highlight {
        color: #e91e63;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI LOGICA (Invariate) ---
def fix_encoding_issues(text):
    if not isinstance(text, str): return text
    try:
        return text.encode('cp1252').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

def parse_amount(value):
    if isinstance(value, (int, float)): return float(value)
    if pd.isna(value) or value == '': return 0.0
    value = str(value).replace('€', '').replace('$', '').strip()
    if ',' in value and '.' in value:
        if value.rfind(',') > value.rfind('.'): value = value.replace('.', '').replace(',', '.')
        else: value = value.replace(',', '')
    elif ',' in value: value = value.replace(',', '.')
    try: return float(value)
    except ValueError: return 0.0

# --- HEADER E INTRODUZIONE ---
st.title("💸 Wallet ➡ Cashew")
st.markdown("""
**Benvenuto!** Questo strumento ti aiuta a trasferire la tua vita finanziaria da *Wallet by BudgetBakers* a *Cashew* senza perdere nemmeno un centesimo.
Segui i **3 passaggi** qui sotto per convertire il tuo file.
""")

# --- SIDEBAR: GUIDA E INFO ---
with st.sidebar:
    st.header("📘 Guida Rapida")
    st.markdown("""
    1. **Esporta** i dati da Wallet (formato CSV).
    2. **Carica** il file qui a destra.
    3. **Personalizza** le categorie e gli account.
    4. **Scarica** il file pronto per Cashew.
    
    ---
    **Nota sulla Privacy:**
    I tuoi dati vengono elaborati *solo* nella memoria temporanea di questa sessione e non vengono salvati da nessuna parte.
    """)
    st.info("💡 Suggerimento: Cashew gestisce le categorie in modo diverso da Wallet. Usa lo step 2 per riorganizzarle al meglio.")

# --- STEP 1: UPLOAD ---
st.markdown("### 1️⃣ Carica il file Wallet")
uploaded_file = st.file_uploader(
    "Trascina qui il file `wallet.csv` o clicca per selezionarlo", 
    type=['csv'],
    help="Il file deve essere l'esportazione standard CSV di Wallet by BudgetBakers."
)

if uploaded_file is not None:
    # Lettura e Pulizia Iniziale
    try:
        df_wallet = pd.read_csv(uploaded_file, sep=';')
        if len(df_wallet.columns) < 2:
            uploaded_file.seek(0)
            df_wallet = pd.read_csv(uploaded_file, sep=',')
        
        # Encoding Fix
        cols_to_fix = ['note', 'payee', 'category', 'account', 'labels', 'type', 'payment_type']
        for col in cols_to_fix:
            if col in df_wallet.columns:
                df_wallet[col] = df_wallet[col].apply(fix_encoding_issues)
        
        df_wallet['amount_clean'] = df_wallet['amount'].apply(parse_amount)
        
        # Metrics Visuali
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Transazioni Trovate", len(df_wallet))
        col_m2.metric("Data Inizio", df_wallet['date'].min()[:10])
        col_m3.metric("Data Fine", df_wallet['date'].max()[:10])
        
        st.success("✅ File analizzato correttamente! Procedi sotto per configurare la conversione.")

    except Exception as e:
        st.error(f"⚠️ C'è stato un problema con il file: {e}")
        st.stop()

    # --- STEP 2: CONFIGURAZIONE (WIZARD) ---
    st.markdown("---")
    st.markdown("### 2️⃣ Personalizza i Dati")
    st.markdown("Cashew ha bisogno di sapere come tradurre i tuoi vecchi dati. Configura le mappature qui sotto.")

    # Liste univoche
    unique_accounts = sorted(df_wallet['account'].dropna().unique().tolist())
    unique_categories = sorted(df_wallet['category'].dropna().unique().tolist())
    unique_labels = sorted(df_wallet['labels'].dropna().unique().tolist())

    # Tabs per organizzare meglio lo spazio
    tab_cats, tab_accs, tab_lbls = st.tabs(["📂 Categorie", "💳 Account", "🏷️ Etichette (Opzionale)"])

    # --- TAB CATEGORIE ---
    with tab_cats:
        st.info("Qui puoi decidere in quale Categoria (e Sottocategoria) di Cashew finiranno le tue spese di Wallet.")
        
        # Input categorie personalizzate
        with st.expander("➕ Gestisci le Categorie disponibili su Cashew", expanded=False):
            st.markdown("Aggiungi qui le categorie che hai già creato (o vuoi creare) su Cashew.")
            c1, c2 = st.columns(2)
            default_cats = ["Mangiare", "Alimentari", "Shopping", "Trasporti", "Divertimento", "Bollette e tasse", "Regali", "Bellezza", "Lavoro", "Viaggi", "Reddito", "Correzione saldo", "Salute", "Casa", "Altro"]
            default_subs = ["Supermercato", "Ristorante", "Benzina", "Abbonamenti", "Stipendio", "Mutuo"]
            
            edited_cats = c1.data_editor(pd.DataFrame(default_cats, columns=["Categoria"]), num_rows="dynamic", key="ed_cats")
            edited_subs = c2.data_editor(pd.DataFrame(default_subs, columns=["Sottocategoria"]), num_rows="dynamic", key="ed_subs")
            
            final_cashew_cats = sorted(edited_cats["Categoria"].unique().tolist())
            final_cashew_subs = [""] + sorted(edited_subs["Sottocategoria"].unique().tolist())

        # Mapping Table
        st.markdown("#### Collega le categorie")
        category_mapping = []
        
        # Usiamo un container con scroll se la lista è lunga (simulato tramite expander o limitando visivamente)
        for cat in unique_categories:
            # Layout a card per ogni riga
            with st.container():
                c_src, c_arrow, c_dest_main, c_dest_sub = st.columns([3, 0.5, 3, 3])
                c_src.markdown(f"**{cat}**")
                c_arrow.markdown("➡")
                
                # Auto-select logic
                def_idx = final_cashew_cats.index(cat) if cat in final_cashew_cats else 0
                
                sel_cat = c_dest_main.selectbox("", final_cashew_cats, index=def_idx, key=f"c_{cat}", label_visibility="collapsed", help="Categoria principale in Cashew")
                sel_sub = c_dest_sub.selectbox("", final_cashew_subs, index=0, key=f"s_{cat}", label_visibility="collapsed", help="Sottocategoria in Cashew (Opzionale)")
                
                category_mapping.append({"Wallet Category": cat, "Cashew Category": sel_cat, "Cashew Subcategory": sel_sub})
                st.divider() # Linea separatrice leggera

        df_cat_map = pd.DataFrame(category_mapping)

    # --- TAB ACCOUNT ---
    with tab_accs:
        st.info("Assicurati che i nomi degli account coincidano con quelli che hai creato su Cashew, altrimenti ne verranno creati di nuovi.")
        account_mapping = {}
        for acc in unique_accounts:
            c1, c2 = st.columns([1, 2])
            c1.markdown(f"Dall'account: **{acc}**")
            account_mapping[acc] = c2.text_input(f"Rinomina in:", value=acc, key=f"acc_{acc}", help=f"Come si chiama l'account '{acc}' su Cashew?")

    # --- TAB LABELS ---
    with tab_lbls:
        st.write("Le Etichette hanno la precedenza sulle Categorie. Utile se usavi le etichette per gestire le vacanze o progetti specifici.")
        label_mapping = []
        if unique_labels:
            for lbl in unique_labels:
                c1, c2, c3 = st.columns([2, 2, 2])
                c1.markdown(f"🏷️ **{lbl}**")
                l_cat = c2.selectbox("Categoria", ["(Usa Mapping Categoria)"] + final_cashew_cats, key=f"l_{lbl}")
                l_sub = c3.selectbox("Sottocategoria", final_cashew_subs, key=f"ls_{lbl}")
                
                if l_cat != "(Usa Mapping Categoria)":
                    label_mapping.append({"Wallet Label": lbl, "Cashew Category": l_cat, "Cashew Subcategory": l_sub})
        else:
            st.caption("Nessuna etichetta trovata nel file.")
        df_lbl_map = pd.DataFrame(label_mapping)

    # --- STEP 3: OUTPUT ---
    st.markdown("---")
    st.markdown("### 3️⃣ Scarica e Importa")
    
    col_out_1, col_out_2 = st.columns([3, 1])
    with col_out_1:
        st.markdown("Tutto pronto? Clicca il pulsante per generare il file.")
        include_payee = st.checkbox("📝 Includi il Beneficiario (es. 'Conad') nelle note", value=True, help="Consigliato. Poiché il titolo della transazione sarà la Categoria, questo ti permette di sapere chi hai pagato leggendo le note.")
    
    with col_out_2:
        # Spazio vuoto per allineamento
        pass

    if st.button("🚀 CONVERTI ORA", type="primary"):
        # --- ELABORAZIONE DATI (Logic Core) ---
        output_rows = []
        cat_map_dict = df_cat_map.set_index("Wallet Category").to_dict('index')
        lbl_map_dict = df_lbl_map.set_index("Wallet Label").to_dict('index') if not df_lbl_map.empty else {}

        progress_bar = st.progress(0)
        total_rows = len(df_wallet)

        for i, (index, row) in enumerate(df_wallet.iterrows()):
            # Update progress bar every 10%
            if i % (max(1, total_rows // 10)) == 0:
                progress_bar.progress(int((i / total_rows) * 100))

            # Logic extraction
            orig_acc = row.get('account', '')
            target_acc = account_mapping.get(orig_acc, orig_acc)
            
            is_transfer = str(row.get('transfer', 'false')).lower() == 'true' or str(row.get('type', '')).upper() == 'TRANSFER'
            w_cat = row.get('category', '')
            w_lbl = row.get('labels', '')
            w_payee = row.get('payee', '') if not pd.isna(row.get('payee', '')) else ""
            w_note = row.get('note', '') if not pd.isna(row.get('note', '')) else ""

            # Default targets
            target_cat, target_sub, target_title, target_note = "", "", w_cat, w_note

            if is_transfer:
                target_cat = "Correzione saldo"
                target_title = "Trasferimento"
                trans_text = f"Trasferimento ({w_cat})" if w_cat != 'TRANSFER' else "Trasferimento"
                target_note = f"{trans_text}\n{w_note}" if w_note else trans_text
            else:
                # Priority: Label > Category > Default
                match = False
                if w_lbl in lbl_map_dict:
                    target_cat = lbl_map_dict[w_lbl]["Cashew Category"]
                    target_sub = lbl_map_dict[w_lbl]["Cashew Subcategory"]
                    match = True
                
                if not match and w_cat in cat_map_dict:
                    target_cat = cat_map_dict[w_cat]["Cashew Category"]
                    target_sub = cat_map_dict[w_cat]["Cashew Subcategory"]
                elif not match:
                    target_cat = "Altro"

                # Payee in note logic
                if include_payee and w_payee:
                    sep = " | " if target_note else ""
                    target_note += f"{sep}Payee: {w_payee}"
                if w_lbl and not pd.isna(w_lbl):
                    sep = " " if target_note else ""
                    target_note += f"{sep}#{w_lbl}"

            amount = row['amount_clean']
            new_row = {
                "account": target_acc,
                "amount": amount,
                "currency": row.get('currency', 'EUR'),
                "title": target_title,
                "note": target_note,
                "date": row.get('date', ''),
                "income": str(amount > 0).lower(),
                "type": "null",
                "category name": target_cat,
                "subcategory name": target_sub,
                "color": "", "icon": "", "emoji": "", "budget": "", "objective": ""
            }
            output_rows.append(new_row)

        progress_bar.progress(100)
        df_cashew = pd.DataFrame(output_rows)
        
        # Success Area
        st.balloons()
        st.markdown("### 🎉 Conversione Completata!")
        st.success(f"File generato con {len(df_cashew)} transazioni.")
        
        # Download
        csv_data = df_cashew.to_csv(index=False, sep=',', encoding='utf-8')
        st.download_button(
            label="💾 CLICCA QUI PER SCARICARE CASHEW.CSV",
            data=csv_data,
            file_name="cashew_import.csv",
            mime="text/csv",
            help="Importa questo file in Cashew > Settings > Import & Export"
        )