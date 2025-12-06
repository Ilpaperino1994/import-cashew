import streamlit as st
import pandas as pd
import io
import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Converter: Wallet to Cashew", layout="wide")

st.title("🔄 Converter: Wallet by BudgetBakers ➡ Cashew")
st.markdown("""
Questa app converte il file CSV esportato da **Wallet by BudgetBakers** nel formato importabile da **Cashew**.
Permette di mappare account, categorie ed etichette, e gestisce correttamente i trasferimenti e la codifica dei caratteri.
""")

# --- FUNZIONI DI UTILITÀ ---

def fix_encoding_issues(text):
    """
    Tenta di correggere errori comuni di codifica (Mojibake).
    Esempio: 'DecÃ²' -> 'Decò'
    """
    if not isinstance(text, str):
        return text
    try:
        # Tenta di codificare in cp1252 e decodificare in utf-8
        # Questo risolve il caso in cui UTF-8 è stato letto come CP1252/Latin-1
        return text.encode('cp1252').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

def parse_amount(value):
    """Converte stringhe valuta (es. '-1.234,56') in float."""
    if isinstance(value, (int, float)):
        return float(value)
    if pd.isna(value) or value == '':
        return 0.0
    
    # Rimuovi spazi e simboli valuta se presenti (anche se il csv di solito è pulito)
    value = str(value).replace('€', '').replace('$', '').strip()
    
    # Gestione formato europeo: 1.000,00 -> rimuovi . sostituisci , con .
    # Gestione formato US: 1,000.00 -> rimuovi ,
    
    if ',' in value and '.' in value:
        if value.rfind(',') > value.rfind('.'): # Formato Europeo 1.234,56
            value = value.replace('.', '').replace(',', '.')
        else: # Formato US 1,234.56
            value = value.replace(',', '')
    elif ',' in value: # Solo virgola (es. 12,50) -> Europeo
        value = value.replace(',', '.')
    
    try:
        return float(value)
    except ValueError:
        return 0.0

# --- SEZIONE 1: CARICAMENTO FILE ---
st.sidebar.header("1. Carica File")
uploaded_file = st.sidebar.file_uploader("Carica export Wallet (.csv)", type=['csv'])

if uploaded_file is not None:
    # Lettura del file
    try:
        # Wallet usa spesso il ; come separatore
        df_wallet = pd.read_csv(uploaded_file, sep=';')
        
        # Se le colonne sembrano sbagliate, prova con la virgola
        if len(df_wallet.columns) < 2:
            uploaded_file.seek(0)
            df_wallet = pd.read_csv(uploaded_file, sep=',')
            
        st.success(f"File caricato con successo! {len(df_wallet)} transazioni trovate.")
        
        # 1.1 Fix Encoding sulle colonne stringa
        st.info("Applicazione correzione caratteri (es. DecÃ² -> Decò)...")
        cols_to_fix = ['note', 'payee', 'category', 'account', 'labels', 'type', 'payment_type']
        for col in cols_to_fix:
            if col in df_wallet.columns:
                df_wallet[col] = df_wallet[col].apply(fix_encoding_issues)

        # Anteprima dati grezzi
        with st.expander("Vedi dati originali (primi 5 righi)"):
            st.dataframe(df_wallet.head())

    except Exception as e:
        st.error(f"Errore nella lettura del file: {e}")
        st.stop()

    # --- SEZIONE 2: PREPARAZIONE DATI ---
    
    # Pulizia importi
    df_wallet['amount_clean'] = df_wallet['amount'].apply(parse_amount)
    
    # Estrazione liste univoche per i mapping
    unique_accounts = df_wallet['account'].dropna().unique().tolist()
    unique_categories = df_wallet['category'].dropna().unique().tolist()
    
    # Estrazione labels (possono essere multiple separate da spazio o virgola?)
    # Assumiamo siano stringhe intere per ora, o separate da un carattere se necessario
    unique_labels = df_wallet['labels'].dropna().unique().tolist()

    # --- SEZIONE 3: PERSONALIZZAZIONE CASHEW (CATEGORIE & ACCOUNT) ---
    st.header("🛠️ 2. Personalizzazione Categorie e Account")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Categorie Cashew")
        # Categorie default fornite dall'utente
        default_cashew_cats = [
            "Mangiare", "Alimentari", "Shopping", "Trasporti", "Divertimento",
            "Bollette e tasse", "Regali", "Bellezza", "Lavoro", "Viaggi", 
            "Reddito", "Correzione saldo", "Salute", "Casa", "Altro"
        ]
        
        # Editor per aggiungere/rimuovere categorie Cashew
        cashew_cats_df = pd.DataFrame(default_cashew_cats, columns=["Categoria Cashew"])
        edited_cashew_cats = st.data_editor(cashew_cats_df, num_rows="dynamic", key="editor_cats")
        final_cashew_cats = sorted(edited_cashew_cats["Categoria Cashew"].unique().tolist())
    
    with col2:
        st.subheader("Sottocategorie (Opzionale)")
        st.markdown("Definisci alcune sottocategorie comuni se vuoi usarle nei mapping.")
        default_subs = ["Supermercato", "Ristorante", "Benzina", "Abbonamenti", "Stipendio", "Mutuo"]
        cashew_subs_df = pd.DataFrame(default_subs, columns=["Sottocategoria Cashew"])
        edited_cashew_subs = st.data_editor(cashew_subs_df, num_rows="dynamic", key="editor_subs")
        final_cashew_subs = sorted(edited_cashew_subs["Sottocategoria Cashew"].unique().tolist())
        final_cashew_subs.insert(0, "") # Opzione vuota

    # --- SEZIONE 4: MAPPING ---
    st.header("🔗 3. Mappatura Dati")
    st.markdown("Collega i dati di Wallet a quelli di Cashew.")

    tabs = st.tabs(["Mappatura Account", "Mappatura Categorie", "Mappatura Labels (Avanzato)"])

    # 4.1 Mappatura Account
    with tabs[0]:
        st.write("Rinomina gli account di Wallet per corrispondere a quelli di Cashew.")
        account_mapping = {}
        for acc in unique_accounts:
            account_mapping[acc] = st.text_input(f"Account Wallet: **{acc}**", value=acc, key=f"acc_{acc}")

    # 4.2 Mappatura Categorie
    with tabs[1]:
        st.write("Associa ogni categoria di Wallet a una Categoria e Sottocategoria di Cashew.")
        st.write("**Nota:** Se la transazione è un 'Trasferimento', verrà gestita automaticamente nella logica successiva, ma puoi comunque mapparla qui per sicurezza.")
        
        category_mapping = []
        for cat in unique_categories:
            col_a, col_b, col_c = st.columns([2, 2, 2])
            with col_a:
                st.write(f"📂 **{cat}**")
            with col_b:
                # Pre-selezione intelligente se il nome corrisponde
                try:
                    default_idx = final_cashew_cats.index(cat)
                except ValueError:
                    default_idx = 0
                
                c_cat = st.selectbox("Cat. Cashew", final_cashew_cats, index=default_idx, key=f"cat_main_{cat}", label_visibility="collapsed")
            with col_c:
                c_sub = st.selectbox("Sub-Cat. Cashew", final_cashew_subs, index=0, key=f"cat_sub_{cat}", label_visibility="collapsed")
            
            category_mapping.append({
                "Wallet Category": cat,
                "Cashew Category": c_cat,
                "Cashew Subcategory": c_sub
            })
        
        df_cat_map = pd.DataFrame(category_mapping)

    # 4.3 Mappatura Labels
    with tabs[2]:
        st.write("Le Labels hanno priorità sulle Categorie. Se una transazione ha questa label, userà questa mappatura.")
        label_mapping = []
        
        if len(unique_labels) > 0:
            for lbl in unique_labels:
                col_a, col_b, col_c = st.columns([2, 2, 2])
                with col_a:
                    st.write(f"🏷️ **{lbl}**")
                with col_b:
                    c_cat = st.selectbox("Cat. Cashew", ["(Usa Mapping Categoria)"] + final_cashew_cats, index=0, key=f"lbl_main_{lbl}", label_visibility="collapsed")
                with col_c:
                    c_sub = st.selectbox("Sub-Cat. Cashew", final_cashew_subs, index=0, key=f"lbl_sub_{lbl}", label_visibility="collapsed")
                
                if c_cat != "(Usa Mapping Categoria)":
                    label_mapping.append({
                        "Wallet Label": lbl,
                        "Cashew Category": c_cat,
                        "Cashew Subcategory": c_sub
                    })
        else:
            st.info("Nessuna label trovata nel file caricato.")
            
        df_lbl_map = pd.DataFrame(label_mapping)

    # --- SEZIONE 5: ELABORAZIONE ---
    st.header("🚀 4. Generazione File")
    
    include_payee_in_note = st.checkbox("Includi 'Payee' (Beneficiario) nella nota? (Consigliato per non perdere il dato)", value=True)
    
    if st.button("Converti File"):
        output_rows = []
        
        # Dizionari di lookup veloci
        cat_map_dict = df_cat_map.set_index("Wallet Category").to_dict('index')
        lbl_map_dict = {}
        if not df_lbl_map.empty:
            lbl_map_dict = df_lbl_map.set_index("Wallet Label").to_dict('index')

        for index, row in df_wallet.iterrows():
            # 1. Account
            orig_acc = row.get('account', '')
            target_acc = account_mapping.get(orig_acc, orig_acc)
            
            # 2. Date
            orig_date = row.get('date', '')
            # Wallet format standard: YYYY-MM-DD HH:MM:SS
            # Cashew format: YYYY-MM-DD HH:MM:SS.000 (o simile)
            
            # 3. Logic: Transfer vs Normal
            is_transfer = str(row.get('transfer', 'false')).lower() == 'true' or \
                          str(row.get('type', '')).upper() == 'TRANSFER'
            
            w_cat = row.get('category', '')
            w_lbl = row.get('labels', '')
            w_payee = row.get('payee', '')
            if pd.isna(w_payee): w_payee = ""
            
            w_note = row.get('note', '')
            if pd.isna(w_note): w_note = ""

            target_cat = ""
            target_sub = ""
            target_title = ""
            target_note = w_note
            
            # --- LOGICA DI ASSEGNAZIONE CATEGORIA ---
            # Priorità 1: Transfer
            if is_transfer:
                target_cat = "Correzione saldo"
                target_title = "Trasferimento"
                # Formattazione nota trasferimento
                transfer_note_part = f"Trasferimento ({w_cat})" if w_cat != 'TRANSFER' else "Trasferimento"
                if w_note:
                    target_note = f"{transfer_note_part}\n{w_note}"
                else:
                    target_note = transfer_note_part
            
            else:
                # Priorità 2: Labels
                match_found = False
                if w_lbl in lbl_map_dict:
                    target_cat = lbl_map_dict[w_lbl]["Cashew Category"]
                    target_sub = lbl_map_dict[w_lbl]["Cashew Subcategory"]
                    match_found = True
                
                # Priorità 3: Category Mapping
                if not match_found and w_cat in cat_map_dict:
                    target_cat = cat_map_dict[w_cat]["Cashew Category"]
                    target_sub = cat_map_dict[w_cat]["Cashew Subcategory"]
                elif not match_found:
                    # Fallback
                    target_cat = "Altro" 

                # Requirement: Title = Wallet Category
                target_title = w_cat
                
                # Payee logic
                if include_payee_in_note and w_payee:
                    if target_note:
                        target_note = f"{target_note} | Payee: {w_payee}"
                    else:
                        target_note = f"Payee: {w_payee}"
                    
                    # Se c'è anche una label, aggiungiamola alla nota per completezza
                    if w_lbl and not pd.isna(w_lbl):
                         target_note = f"{target_note} #{w_lbl}"

            # 4. Amount & Type
            amount = row['amount_clean']
            is_income = amount > 0
            
            # 5. Costruzione riga Cashew
            # Colonne Cashew: account,amount,currency,title,note,date,income,type,category name,subcategory name,color,icon,emoji,budget,objective
            
            new_row = {
                "account": target_acc,
                "amount": amount,
                "currency": row.get('currency', 'EUR'),
                "title": target_title,
                "note": target_note,
                "date": orig_date,
                "income": str(is_income).lower(), # Cashew usa 'true'/'false' minuscolo nel csv spesso
                "type": "null", # Default null unless specific debt type
                "category name": target_cat,
                "subcategory name": target_sub,
                "color": "", # Lasciare vuoto per default app
                "icon": "",
                "emoji": "",
                "budget": "",
                "objective": ""
            }
            output_rows.append(new_row)
            
        df_cashew = pd.DataFrame(output_rows)
        
        # Anteprima risultato
        st.subheader("Anteprima Output Cashew")
        st.dataframe(df_cashew.head())
        
        # Download
        csv_data = df_cashew.to_csv(index=False, sep=',', encoding='utf-8')
        st.download_button(
            label="💾 Scarica cashew.csv",
            data=csv_data,
            file_name="cashew_import.csv",
            mime="text/csv"
        )

# Istruzioni Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### Guida Rapida")
st.sidebar.info(
    """
    1. Carica il file `wallet.csv`.
    2. Nella sezione "Personalizzazione", aggiungi le categorie che usi su Cashew.
    3. Mappa gli Account (es. 'Contanti' -> 'Cash').
    4. Mappa le Categorie e/o le Label.
    5. Scarica il file e importalo in Cashew (Settings > Import & Export).
    """
)