import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from models import CashewConfig, AccountConfig, ProcessedTransaction
from logic import parse_csv_to_models, ai_suggest_mapping, generate_uuid, get_ts
from database import CashewDatabase

# --- 1. CONFIGURAZIONE & STILE ---
st.set_page_config(page_title="Wallet to Cashew Pro", page_icon="🥥", layout="wide")

st.markdown("""
<style>
    /* CASHEW THEME */
    .stApp { background-color: #f4f7f6; font-family: 'Inter', sans-serif; }
    
    /* WIZARD HEADER */
    .wizard-step {
        display: inline-block; padding: 10px 20px; border-radius: 20px;
        background: white; color: #aaa; font-weight: 600; margin-right: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .wizard-active { background: #4CAF50; color: white; transform: scale(1.05); }
    
    /* MOBILE PREVIEW CONTAINER */
    .mobile-mockup {
        width: 300px; height: 500px; border: 12px solid #333; border-radius: 35px;
        background: white; margin: auto; padding: 15px; position: relative; overflow: hidden;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }
    .mobile-notch {
        width: 120px; height: 20px; background: #333; position: absolute; 
        top: 0; left: 50%; transform: translateX(-50%); border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;
    }
    .mobile-trans-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px; border-bottom: 1px solid #eee;
    }
    .t-icon { width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; color: white; margin-right: 10px;}
    
    /* CARDS */
    .card-box { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 2. STATE MANAGEMENT ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'transactions' not in st.session_state: st.session_state.transactions = []
if 'mapping' not in st.session_state: st.session_state.mapping = {}
if 'accounts' not in st.session_state: st.session_state.accounts = {}
# Struttura di default modificabile
if 'cashew_struct' not in st.session_state:
    st.session_state.cashew_struct = {
        "Alimentari": ["Supermercato", "Minimarket"],
        "Trasporti": ["Benzina", "Mezzi Pubblici", "Manutenzione"],
        "Casa": ["Affitto", "Bollette", "Internet"],
        "Shopping": ["Vestiti", "Elettronica"],
        "Salute": ["Farmacia", "Visite"],
        "Reddito": ["Stipendio", "Extra"],
        "Correzione saldo": []
    }

# --- 3. HELPER FUNCTIONS UI ---
def wizard_nav():
    steps = ["Upload", "Struttura", "Mapping AI", "Review & Export"]
    cols = st.columns(len(steps))
    for i, s in enumerate(steps):
        style = "wizard-active" if st.session_state.step == i+1 else ""
        cols[i].markdown(f'<div class="wizard-step {style}">{i+1}. {s}</div>', unsafe_allow_html=True)
    st.markdown("---")

def next_step(): st.session_state.step += 1
def prev_step(): st.session_state.step -= 1

# --- STEP 1: UPLOAD ---
if st.session_state.step == 1:
    wizard_nav()
    st.title("📂 Inizia la Migrazione")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded = st.file_uploader("Carica wallet.csv", type=['csv'])
        if uploaded:
            try:
                # Usa la funzione logic cachata
                ts = parse_csv_to_models(uploaded)
                st.session_state.transactions = ts
                st.success(f"✅ Lette {len(ts)} transazioni!")
                
                # Inizializza conti
                unique_accs = {t.account for t in ts}
                for acc in unique_accs:
                    if acc not in st.session_state.accounts:
                        st.session_state.accounts[acc] = AccountConfig(name_cashew=acc)
                
                if st.button("Procedi ➔", type="primary"):
                    next_step()
                    st.rerun()
            except Exception as e:
                st.error(f"Errore umano: {str(e)}. Controlla che il CSV sia valido.")
    
    with col2:
        st.info("💡 **Funzione Restore Config:** Hai già fatto questo lavoro?")
        conf_file = st.file_uploader("Carica config.json", type=['json'])
        if conf_file:
            data = json.load(conf_file)
            # Ripristino stato
            st.session_state.mapping = {k: CashewConfig(**v) for k,v in data.get('mapping', {}).items()}
            st.session_state.cashew_struct = data.get('struct', st.session_state.cashew_struct)
            st.success("Configurazione ripristinata! Puoi saltare direttamente all'export se il CSV è simile.")

# --- STEP 2: STRUTTURA ---
elif st.session_state.step == 2:
    wizard_nav()
    st.title("🏗️ Struttura Categorie")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("Definisci la gerarchia di Cashew.")
        # Editor Tabellare
        flat = []
        for m, subs in st.session_state.cashew_struct.items():
            if not subs: flat.append({"Madre": m, "Figlia": ""})
            for s in subs: flat.append({"Madre": m, "Figlia": s})
        
        edited = st.data_editor(pd.DataFrame(flat), num_rows="dynamic", use_container_width=True)
    
    with c2:
        st.info("Questa struttura verrà usata dall'AI nel prossimo step per suggerire le associazioni.")
    
    if st.button("Salva e Vai al Mapping AI ➔", type="primary"):
        new_struct = {}
        for _, r in edited.iterrows():
            m, s = str(r["Madre"]).strip(), str(r["Figlia"]).strip()
            if m:
                if m not in new_struct: new_struct[m] = []
                if s and s not in new_struct[m]: new_struct[m].append(s)
        st.session_state.cashew_struct = new_struct
        next_step()
        st.rerun()

# --- STEP 3: MAPPING AI & BULK ACTIONS ---
elif st.session_state.step == 3:
    wizard_nav()
    st.title("🤖 Mapping Intelligente")
    
    unique_cats = sorted(list({t.category for t in st.session_state.transactions}))
    
    # AI TRIGGER
    col_ai, col_bulk = st.columns([1, 1])
    with col_ai:
        if st.button("✨ Esegui Auto-Mapping AI", type="primary"):
            with st.spinner("L'AI sta analizzando le tue categorie..."):
                suggestions = ai_suggest_mapping(unique_cats, st.session_state.cashew_struct)
                # Applica suggerimenti
                for w_cat, res in suggestions.items():
                    if w_cat not in st.session_state.mapping:
                        st.session_state.mapping[w_cat] = CashewConfig(
                            main_category=res['main'], sub_category=res['sub']
                        )
                st.success("AI ha completato il mapping!")
                st.rerun()

    # INTERFACCIA MAPPING (Con Bulk Logic simulata tramite form)
    st.markdown("---")
    
    # Filtro
    search = st.text_input("🔍 Cerca categoria Wallet...", "")
    filtered = [c for c in unique_cats if search.lower() in c.lower()]
    
    # Grid View
    with st.container(height=500):
        for cat in filtered:
            current_conf = st.session_state.mapping.get(cat, CashewConfig(main_category="Altro"))
            
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                c1.markdown(f"**{cat}**")
                
                # Main Cat
                opts = list(st.session_state.cashew_struct.keys())
                try: idx = opts.index(current_conf.main_category)
                except: idx = 0
                new_main = c2.selectbox("Cat", opts, index=idx, key=f"m_{cat}", label_visibility="collapsed")
                
                # Sub Cat
                subs = [""] + st.session_state.cashew_struct.get(new_main, [])
                try: s_idx = subs.index(current_conf.sub_category)
                except: s_idx = 0
                new_sub = c3.selectbox("Sub", subs, index=s_idx, key=f"s_{cat}", label_visibility="collapsed")
                
                # Color Picker immediato
                new_col = c4.color_picker("", current_conf.color, key=f"c_{cat}")
                
                # Aggiorna stato
                st.session_state.mapping[cat] = CashewConfig(
                    main_category=new_main, sub_category=new_sub, color=new_col
                )
                st.divider()

    c_back, c_next = st.columns([1, 5])
    if c_back.button("Indietro"): prev_step(); st.rerun()
    if c_next.button("Genera Anteprima ➔", type="primary"): next_step(); st.rerun()

# --- STEP 4: DASHBOARD & EXPORT ---
elif st.session_state.step == 4:
    wizard_nav()
    st.title("🚀 Review Finale")
    
    # 1. ELABORAZIONE DATI (Logic Layer)
    # Generiamo i dati finali
    db = CashewDatabase()
    
    # Add Wallets
    w_uuids = {}
    for name, conf in st.session_state.accounts.items():
        uid = generate_uuid()
        w_uuids[name] = uid
        db.add_wallet(uid, conf)
        
    # Add Categories
    c_uuids = {} # (Main, Sub) -> UUID
    processed_main = set()
    
    # Creazione Categorie nel DB
    for w_cat, conf in st.session_state.mapping.items():
        # Main
        if conf.main_category not in processed_main:
            uid = generate_uuid()
            c_uuids[(conf.main_category, "")] = uid
            db.add_category(uid, conf.main_category, conf.color, conf.icon, None)
            processed_main.add(conf.main_category)
        # Sub
        if conf.sub_category:
            key = (conf.main_category, conf.sub_category)
            if key not in c_uuids:
                uid = generate_uuid()
                c_uuids[key] = uid
                p_uid = c_uuids[(conf.main_category, "")]
                db.add_category(uid, conf.sub_category, conf.color, conf.icon, p_uid)

    # Add Transactions & Pairing
    final_trans = []
    for t in st.session_state.transactions:
        # Mapping Lookup
        map_conf = st.session_state.mapping.get(t.category, CashewConfig(main_category="Altro"))
        
        # UUID Lookup
        w_fk = w_uuids.get(t.account, w_uuids.get(list(w_uuids.keys())[0])) # Fallback safe
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
        # Pairing Logic (semplificata per brevità)
        # ... (qui inserisci la logica di pairing vista precedentemente)
        
        db.add_transaction(pt)
        final_trans.append(pt)

    # 2. DASHBOARD "PRIMA E DOPO"
    col_dash, col_preview = st.columns([2, 1])
    
    with col_dash:
        st.subheader("📊 Analisi Distribuzione")
        
        # Data Prep per Plotly
        df_final = pd.DataFrame([t.dict() for t in final_trans])
        if not df_final.empty:
            expenses = df_final[df_final['amount'] < 0]
            fig = go.Figure(data=[go.Pie(labels=expenses['title'], values=expenses['amount'].abs(), hole=.3)])
            fig.update_layout(title_text="Distribuzione Spese su Cashew", margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Nessuna transazione da mostrare.")

    # 3. MOBILE PREVIEW
    with col_preview:
        st.subheader("📱 Anteprima Mobile")
        st.markdown('<div class="mobile-mockup"><div class="mobile-notch"></div><br><br>', unsafe_allow_html=True)
        
        # Mockup ultime 5 transazioni
        for t in final_trans[:5]:
            color = "#ff5252" if t.amount < 0 else "#4caf50"
            icon_html = f'<div class="t-icon" style="background:{color};">€</div>'
            st.markdown(f"""
            <div class="mobile-trans-row">
                <div style="display:flex; align-items:center;">
                    {icon_html}
                    <div>
                        <div style="font-weight:bold; font-size:14px; color:#333;">{t.title}</div>
                        <div style="font-size:11px; color:#888;">{t.note[:20]}...</div>
                    </div>
                </div>
                <div style="font-weight:bold; color:{color};">
                    {t.amount:.2f} €
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # 4. DOWNLOAD AREA
    st.markdown("---")
    c_d1, c_d2, c_d3 = st.columns(3)
    
    sql_data = db.get_sql_dump()
    c_d1.download_button("💾 Scarica SQL (Backup)", sql_data, "restore.sql", "text/x-sql", type="primary")
    
    # Export Config per LocalStorage simulato
    config_export = {
        "mapping": {k: v.dict() for k, v in st.session_state.mapping.items()},
        "struct": st.session_state.cashew_struct
    }
    c_d2.download_button("⚙️ Salva Configurazione", json.dumps(config_export), "config.json", "application/json")
    
    if c_d3.button("🔄 Ricomincia"):
        st.session_state.clear()
        st.rerun()