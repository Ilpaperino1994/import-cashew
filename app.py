import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from models import CashewConfig, AccountConfig, ProcessedTransaction
from logic import parse_csv_to_models, ai_suggest_mapping, generate_uuid, get_ts, DEFAULT_CASHEW_STRUCTURE
from database import CashewDatabase

# --- 1. CONFIGURAZIONE & STILE ---
st.set_page_config(page_title="Wallet to Cashew Migrator", page_icon="🥥", layout="wide")

st.markdown("""
<style>
    /* STILE GENERALE */
    .stApp { background-color: #F5F7FA; font-family: 'Segoe UI', sans-serif; }
    
    /* GUIDA BOX */
    .guide-box {
        background-color: #E3F2FD; border-left: 5px solid #2196F3;
        padding: 15px; border-radius: 5px; margin-bottom: 20px;
        color: #0D47A1; font-size: 0.95rem;
    }
    
    /* WIZARD HEADER */
    .wizard-step {
        display: inline-block; padding: 10px 20px; border-radius: 20px;
        background: white; color: #B0BEC5; font-weight: 600; margin-right: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #ECEFF1;
    }
    .wizard-active { background: #4CAF50; color: white; border: 1px solid #4CAF50; transform: scale(1.05); }
    
    /* CATEGORY EDITOR */
    .cat-selector {
        padding: 10px; cursor: pointer; border-radius: 8px; margin-bottom: 5px;
        background: white; border: 1px solid #eee; transition: all 0.2s;
        display: flex; align-items: center; justify-content: space-between;
    }
    .cat-selector:hover { border-color: #2196F3; background: #E3F2FD; }
    .cat-active { background-color: #2196F3; color: white; font-weight: bold; border-color: #2196F3; }
    
    /* MOBILE PREVIEW */
    .mobile-mockup {
        width: 320px; height: 550px; border: 14px solid #333; border-radius: 40px;
        background: white; margin: auto; padding: 20px; position: relative; overflow: hidden;
        box-shadow: 0 20px 40px rgba(0,0,0,0.2);
    }
    .mobile-notch {
        width: 150px; height: 25px; background: #333; position: absolute; 
        top: 0; left: 50%; transform: translateX(-50%); border-bottom-left-radius: 16px; border-bottom-right-radius: 16px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. STATE MANAGEMENT ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'transactions' not in st.session_state: st.session_state.transactions = []
if 'mapping' not in st.session_state: st.session_state.mapping = {}
if 'accounts' not in st.session_state: st.session_state.accounts = {}

# Struttura Dati Complessa: { "MainName": {"subs": [...], "color": "...", "icon": "..."} }
if 'cashew_struct' not in st.session_state:
    st.session_state.cashew_struct = DEFAULT_CASHEW_STRUCTURE.copy()

if 'selected_cat_editor' not in st.session_state: 
    st.session_state.selected_cat_editor = list(st.session_state.cashew_struct.keys())[0]

# --- 3. HELPER FUNCTIONS ---
def wizard_nav():
    steps = ["1. Importazione", "2. Struttura Categorie", "3. Mappatura & AI", "4. Export Finale"]
    cols = st.columns(len(steps))
    for i, s in enumerate(steps):
        style = "wizard-active" if st.session_state.step == i+1 else ""
        cols[i].markdown(f'<div class="wizard-step {style}">{s}</div>', unsafe_allow_html=True)
    st.markdown("---")

def next_step(): st.session_state.step += 1
def prev_step(): st.session_state.step -= 1

# =================================================================================
# STEP 1: IMPORTAZIONE & SPIEGAZIONE
# =================================================================================
if st.session_state.step == 1:
    wizard_nav()
    st.title("🥥 Migrazione Wallet ➡ Cashew")
    
    with st.expander("📘 **Come funziona questa App? (Leggi qui)**", expanded=True):
        st.markdown("""
        **A cosa serve?**
        Questa applicazione serve a trasferire tutto il tuo storico finanziario dall'app *Wallet by BudgetBakers* alla nuova app *Cashew*.
        
        **Perché usarla?**
        1. **Mantiene i Trasferimenti:** Unisce automaticamente le uscite e le entrate tra conti diversi (es. Prelievo Bancomat) in un unico movimento collegato.
        2. **Database Pulito:** Genera un file SQL che crea un database Cashew perfetto, con icone, colori e categorie ordinate, invece di un importazione CSV disordinata.
        3. **Intelligenza Artificiale:** Ti aiuta a collegare le tue vecchie categorie a quelle nuove senza doverlo fare a mano una per una.
        
        **Cosa ti serve?**
        * Il file `wallet.csv` esportato da BudgetBakers.
        * 5 minuti del tuo tempo per configurare le categorie.
        """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📤 Carica il tuo file")
        uploaded = st.file_uploader("Trascina qui il file `wallet.csv`", type=['csv'])
        
        if uploaded:
            try:
                ts = parse_csv_to_models(uploaded)
                st.session_state.transactions = ts
                
                # Setup conti
                unique_accs = {t.account for t in ts}
                for acc in unique_accs:
                    if acc not in st.session_state.accounts:
                        st.session_state.accounts[acc] = AccountConfig(name_cashew=acc)
                
                st.success(f"✅ Analisi completata! Trovate **{len(ts)}** transazioni e **{len(unique_accs)}** conti.")
                
                if st.button("Inizia la Configurazione ➔", type="primary"):
                    next_step()
                    st.rerun()
            except Exception as e:
                st.error(f"Errore nella lettura del file: {str(e)}")
    
    with col2:
        st.info("💡 **Modalità SQL (Consigliata)**\nQuesta app è progettata per generare un **Backup Completo (.sql)**.\n\nQuesto significa che quando lo importerai su Cashew, sostituirà i dati esistenti per darti una partenza pulita e senza errori.")

# =================================================================================
# STEP 2: STRUTTURA CATEGORIE (RIDISEGNATO)
# =================================================================================
elif st.session_state.step == 2:
    wizard_nav()
    st.title("📂 Organizza le tue Categorie")
    
    st.markdown("""
    <div class="guide-box">
        <b>Come funziona questa pagina:</b><br>
        Qui definisci l'albero delle categorie che vuoi avere su Cashew.<br>
        1. A sinistra selezioni una <b>Categoria Principale</b> (es. Alimentari).<br>
        2. A destra modifichi i suoi dettagli (Colore, Icona) e gestisci le sue <b>Sottocategorie</b> (es. Supermercato, Panificio).
    </div>
    """, unsafe_allow_html=True)
    
    col_sel, col_edit = st.columns([1, 2])
    
    # --- COLONNA SINISTRA: LISTA MASTER ---
    with col_sel:
        st.subheader("Categorie Principali")
        
        # Aggiungi Nuova
        new_cat_name = st.text_input("➕ Aggiungi Nuova", placeholder="Es. Animali Domestici")
        if st.button("Aggiungi"):
            if new_cat_name and new_cat_name not in st.session_state.cashew_struct:
                st.session_state.cashew_struct[new_cat_name] = {"subs": [], "color": "#9E9E9E", "icon": "category_default.png"}
                st.session_state.selected_cat_editor = new_cat_name
                st.rerun()

        st.markdown("---")
        
        # Lista Selezionabile
        for cat_name in list(st.session_state.cashew_struct.keys()):
            # Usiamo bottoni per simulare la selezione
            btn_style = "primary" if st.session_state.selected_cat_editor == cat_name else "secondary"
            if st.button(f"{cat_name}", key=f"btn_{cat_name}", use_container_width=True, type=btn_style):
                st.session_state.selected_cat_editor = cat_name
                st.rerun()

    # --- COLONNA DESTRA: EDITOR DETTAGLIO ---
    with col_edit:
        active_cat = st.session_state.selected_cat_editor
        if active_cat in st.session_state.cashew_struct:
            data = st.session_state.cashew_struct[active_cat]
            
            st.markdown(f"### ✏️ Modifica: **{active_cat}**")
            
            # Editor Stile
            c1, c2, c3 = st.columns([1, 2, 1])
            new_color = c1.color_picker("Colore", data['color'])
            new_icon = c2.text_input("Icona (.png)", data['icon'], help="Nome del file icona in Cashew (es. food.png, car.png)")
            
            if c3.button("🗑️ Elimina Categoria"):
                del st.session_state.cashew_struct[active_cat]
                st.session_state.selected_cat_editor = list(st.session_state.cashew_struct.keys())[0]
                st.rerun()
            
            # Aggiorna dati stile
            st.session_state.cashew_struct[active_cat]['color'] = new_color
            st.session_state.cashew_struct[active_cat]['icon'] = new_icon
            
            st.markdown("#### ↳ Sottocategorie")
            st.caption("Aggiungi qui sotto le specifiche (es. se la categoria è 'Auto', qui metti 'Benzina', 'Bollo', etc.)")
            
            # Editor Sottocategorie
            current_subs = pd.DataFrame({"Nome Sottocategoria": data['subs']})
            edited_subs = st.data_editor(current_subs, num_rows="dynamic", use_container_width=True, key=f"editor_{active_cat}")
            
            # Salvataggio Sottocategorie in tempo reale
            st.session_state.cashew_struct[active_cat]['subs'] = [
                x.strip() for x in edited_subs["Nome Sottocategoria"].tolist() if x and x.strip()
            ]

    st.markdown("---")
    c_prev, c_next = st.columns([1, 5])
    if c_prev.button("⬅ Indietro"): prev_step(); st.rerun()
    if c_next.button("Struttura completata, vai al Mapping ➔", type="primary"): next_step(); st.rerun()

# =================================================================================
# STEP 3: MAPPING AI
# =================================================================================
elif st.session_state.step == 3:
    wizard_nav()
    st.title("🤖 Collega i dati")
    
    st.markdown("""
    <div class="guide-box">
        Ora dobbiamo dire all'app come tradurre il "linguaggio" di Wallet in quello di Cashew.<br>
        Usa l'<b>Auto-Mapping</b> per far fare il lavoro sporco all'IA, poi controlla se tutto è corretto.
    </div>
    """, unsafe_allow_html=True)
    
    unique_cats = sorted(list({t.category for t in st.session_state.transactions}))
    
    # TRIGGER AI
    if st.button("✨ Esegui Auto-Mapping con Intelligenza Artificiale", type="primary", use_container_width=True):
        with st.spinner("Sto analizzando le tue spese..."):
            suggestions = ai_suggest_mapping(unique_cats, st.session_state.cashew_struct)
            for w_cat, res in suggestions.items():
                # Prendi colore/icona dalla struttura definita nello step 2
                struct_data = st.session_state.cashew_struct.get(res['main'], {})
                st.session_state.mapping[w_cat] = CashewConfig(
                    main_category=res['main'], 
                    sub_category=res['sub'],
                    color=struct_data.get('color', '#9E9E9E'),
                    icon=struct_data.get('icon', 'category_default.png')
                )
            st.success("Fatto! Controlla i risultati qui sotto.")
            st.rerun()

    st.markdown("### 🔍 Revisione Associazioni")
    
    search = st.text_input("Filtra categoria...", placeholder="Cerca...")
    filtered = [c for c in unique_cats if search.lower() in c.lower()]
    
    # GRID LAYOUT PER MAPPING
    with st.container(height=500):
        for cat in filtered:
            # Recupera config attuale o default
            curr = st.session_state.mapping.get(cat, CashewConfig(main_category="Altro"))
            
            with st.container():
                c1, c2, c3 = st.columns([2, 2, 2])
                
                # Nome Wallet
                c1.markdown(f"**{cat}**")
                c1.caption("Da Wallet")
                
                # Selezione Cashew Main
                opts_main = list(st.session_state.cashew_struct.keys())
                try: idx_m = opts_main.index(curr.main_category)
                except: idx_m = 0
                new_main = c2.selectbox("Categoria Cashew", opts_main, index=idx_m, key=f"m_{cat}", label_visibility="collapsed")
                
                # Selezione Cashew Sub (Dinamica)
                opts_sub = [""] + st.session_state.cashew_struct.get(new_main, {}).get('subs', [])
                try: idx_s = opts_sub.index(curr.sub_category)
                except: idx_s = 0
                new_sub = c3.selectbox("Sottocategoria", opts_sub, index=idx_s, key=f"s_{cat}", label_visibility="collapsed")
                
                # Update stato
                struct_ref = st.session_state.cashew_struct.get(new_main, {})
                st.session_state.mapping[cat] = CashewConfig(
                    main_category=new_main, 
                    sub_category=new_sub,
                    color=struct_ref.get('color', '#9E9E9E'), # Eredita colore dalla struttura
                    icon=struct_ref.get('icon', 'category_default.png') # Eredita icona
                )
                st.divider()

    c_prev, c_next = st.columns([1, 5])
    if c_prev.button("⬅ Indietro"): prev_step(); st.rerun()
    if c_next.button("Genera Anteprima e Esporta ➔", type="primary"): next_step(); st.rerun()

# =================================================================================
# STEP 4: DASHBOARD & EXPORT
# =================================================================================
elif st.session_state.step == 4:
    wizard_nav()
    st.title("🚀 Pronto al Decollo")
    
    # --- LOGICA DI GENERAZIONE ---
    db = CashewDatabase()
    
    # 1. Crea Conti
    w_uuids = {}
    for name, conf in st.session_state.accounts.items():
        uid = generate_uuid()
        w_uuids[name] = uid
        db.add_wallet(uid, conf)
        
    # 2. Crea Categorie (Main & Subs)
    c_uuids = {} 
    processed_main = set()
    
    # Scansiona il mapping per capire quali categorie servono davvero
    # (Ma per sicurezza creiamo tutta la struttura definita nello step 2)
    for main, data in st.session_state.cashew_struct.items():
        # Crea Main
        uid_m = generate_uuid()
        c_uuids[(main, "")] = uid_m
        db.add_category(uid_m, main, data['color'], data['icon'], None)
        
        # Crea Subs
        for sub in data['subs']:
            uid_s = generate_uuid()
            c_uuids[(main, sub)] = uid_s
            db.add_category(uid_s, sub, None, None, uid_m) # Le sub ereditano o non hanno icona

    # 3. Crea Transazioni
    final_trans = []
    for t in st.session_state.transactions:
        map_conf = st.session_state.mapping.get(t.category, CashewConfig(main_category="Altro"))
        
        # Trova UUID
        w_fk = w_uuids.get(t.account)
        if not w_fk: w_fk = list(w_uuids.values())[0] # Fallback
        
        c_fk = c_uuids.get((map_conf.main_category, map_conf.sub_category))
        if not c_fk: c_fk = c_uuids.get((map_conf.main_category, ""), "0")
        
        pt = ProcessedTransaction(
            id=generate_uuid(),
            date_ms=get_ts(t.date_str),
            amount=t.amount,
            title=map_conf.main_category if not t.is_transfer else "Trasferimento",
            note=f"{t.note} | {t.payee}" if t.payee else t.note,
            wallet_fk=w_fk,
            category_fk=c_fk,
            is_income=t.amount > 0
        )
        final_trans.append(pt)
        db.add_transaction(pt)

    # --- UI DASHBOARD ---
    col_stats, col_preview = st.columns([2, 1])
    
    with col_stats:
        st.subheader("📊 Anteprima Risultato")
        
        df_viz = pd.DataFrame([t.dict() for t in final_trans])
        if not df_viz.empty:
            expenses = df_viz[df_viz['amount'] < 0]
            fig = go.Figure(data=[go.Pie(labels=expenses['title'], values=expenses['amount'].abs(), hole=.4)])
            fig.update_layout(title="Distribuzione Spese in Cashew", height=350, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
            
            st.metric("Totale Transazioni", len(df_viz))
    
    with col_preview:
        st.subheader("📱 Anteprima App")
        st.markdown('<div class="mobile-mockup"><div class="mobile-notch"></div><br><br>', unsafe_allow_html=True)
        for t in final_trans[:6]:
            color = "#ef5350" if t.amount < 0 else "#66bb6a"
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:10px; border-bottom:1px solid #eee;">
                <div style="font-weight:bold; font-size:13px;">{t.title}</div>
                <div style="color:{color}; font-weight:bold;">{t.amount:.2f} €</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- DOWNLOAD ---
    st.markdown("---")
    st.success("✅ **Il file è pronto!**")
    
    c_down, c_info = st.columns([1, 2])
    with c_down:
        sql_data = db.get_sql_dump()
        st.download_button(
            label="💾 SCARICA BACKUP .SQL",
            data=sql_data,
            file_name="cashew_restore.sql",
            mime="text/x-sql",
            type="primary",
            use_container_width=True
        )
    
    with c_info:
        st.info("""
        **Istruzioni per l'importazione:**
        1. Invia il file `cashew_restore.sql` al tuo smartphone.
        2. Apri Cashew, vai su **Impostazioni** > **Backup e Ripristino**.
        3. Seleziona **Ripristina Backup** e scegli il file.
        """)