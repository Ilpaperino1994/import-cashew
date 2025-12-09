import streamlit as st
import pandas as pd
from models import AccountConfig
from logic import parse_csv_to_models

def render_step1():
    st.markdown("### 📤 Start Migration")

    # 1. Output Format Selection
    st.markdown("#### 1. Choose Output Format")
    col_choice, col_info = st.columns([2, 1])

    with col_choice:
        output_format = st.radio(
            "Select the format you want to generate:",
            options=["Cashew Database (.sqlite)", "CSV File"],
            index=0,
            help="Choose 'Cashew Database' to replace your current Cashew DB (Recommended). Choose 'CSV' if you want to import transactions manually."
        )
        st.session_state.output_format = "SQL" if "Database" in output_format else "CSV"

    with col_info:
        if st.session_state.output_format == "SQL":
            st.info("ℹ️ **SQL Mode:** Generates a full backup file. You can restore this in Cashew settings to instantly get all data.")
        else:
            st.info("ℹ️ **CSV Mode:** Generates a clean CSV. You might need to map columns manually in Cashew.")

    st.divider()

    # 2. Upload
    st.markdown("#### 2. Upload Wallet Export")
    uploaded = st.file_uploader("Drop your `wallet-export.csv` here", type=['csv'])

    if uploaded:
        try:
            ts = parse_csv_to_models(uploaded)
            st.session_state.transactions = ts

            # Setup accounts
            unique_accs = {t.account for t in ts}
            for acc in unique_accs:
                if acc not in st.session_state.accounts:
                    st.session_state.accounts[acc] = AccountConfig(name_cashew=acc)

            st.success(f"✅ Analysis complete! Found **{len(ts)}** transactions and **{len(unique_accs)}** accounts.")

            if st.button("Start Configuration ➔", type="primary"):
                st.session_state.step = 2
                st.rerun()
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            st.exception(e)
