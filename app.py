import streamlit as st
import copy
from models import DEFAULT_CASHEW_STRUCTURE
from ui.step1_upload import render_step1
from ui.step2_categories import render_step2
from ui.step3_mapping import render_step3
from ui.step4_export import render_step4

# --- CONFIG & STYLE ---
st.set_page_config(page_title="Wallet to Cashew Migrator", page_icon="🥥", layout="wide")

# CSS for Dark Mode Support and Custom Styling
st.markdown("""
<style>
    /* Global */
    .stApp {
        transition: background-color 0.3s;
    }
    
    /* Wizard Steps */
    .wizard-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
        background: var(--background-color);
        padding: 10px;
        border-radius: 10px;
        border: 1px solid var(--secondary-background-color);
    }
    .wizard-step {
        flex: 1;
        text-align: center;
        padding: 10px;
        margin: 0 5px;
        border-radius: 8px;
        color: var(--text-color);
        opacity: 0.5;
        font-weight: 600;
        border: 1px solid transparent;
    }
    .wizard-active {
        background-color: #4CAF50;
        color: white;
        opacity: 1;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    /* Card/Box Style */
    .box {
        background-color: var(--secondary-background-color);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- STATE ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'transactions' not in st.session_state: st.session_state.transactions = []
if 'mapping' not in st.session_state: st.session_state.mapping = {}
if 'accounts' not in st.session_state: st.session_state.accounts = {}
if 'cashew_struct' not in st.session_state: st.session_state.cashew_struct = copy.deepcopy(DEFAULT_CASHEW_STRUCTURE)
if 'selected_cat_editor' not in st.session_state: st.session_state.selected_cat_editor = list(st.session_state.cashew_struct.keys())[0]
if 'output_format' not in st.session_state: st.session_state.output_format = "SQL"

# --- HEADER ---
st.title("🥥 Wallet to Cashew Migrator")

steps = ["1. Upload", "2. Categories", "3. Mapping", "4. Export"]
cols = st.columns(len(steps))
for i, s in enumerate(steps):
    active = "wizard-active" if st.session_state.step == i + 1 else ""
    cols[i].markdown(f'<div class="wizard-step {active}">{s}</div>', unsafe_allow_html=True)
st.markdown("---")

# --- ROUTER ---
if st.session_state.step == 1:
    render_step1()
elif st.session_state.step == 2:
    render_step2()
elif st.session_state.step == 3:
    render_step3()
elif st.session_state.step == 4:
    render_step4()
