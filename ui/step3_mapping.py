import streamlit as st
from logic import ai_suggest_mapping
from models import CashewConfig

def render_step3():
    st.markdown('<div class="st-card">', unsafe_allow_html=True)
    c_head, c_btn = st.columns([3, 1])
    with c_head:
        st.markdown("### 🤖 Mappatura Categorie")
        st.caption("Collega le categorie originali (Wallet) con le nuove (Cashew).")
    with c_btn:
        if st.button("✨ Auto-Mapping IA", type="primary", use_container_width=True):
            with st.spinner("L'IA sta lavorando..."):
                unique_cats = list({t.category for t in st.session_state.transactions})
                suggestions = ai_suggest_mapping(unique_cats, st.session_state.cashew_struct)
                for w_cat, res in suggestions.items():
                    struct_ref = st.session_state.cashew_struct.get(res['main'], {})
                    st.session_state.mapping[w_cat] = CashewConfig(
                        main_category=res['main'],
                        sub_category=res['sub'],
                        color=struct_ref.get('color', '#9E9E9E'),
                        icon=struct_ref.get('icon', 'category_default.png')
                    )
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    unique_cats = sorted(list({t.category for t in st.session_state.transactions}))
    cashew_mains = list(st.session_state.cashew_struct.keys())

    # Mapping Grid
    with st.container(height=600):
        for i, cat in enumerate(unique_cats):
            current = st.session_state.mapping.get(cat, CashewConfig(main_category="Altro"))

            # Row Card Style
            st.markdown(f"""
            <div style="
                background-color: var(--card-bg);
                padding: 15px;
                border-radius: 8px;
                border: 1px solid var(--border-color);
                margin-bottom: 10px;
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 10px;
            ">
                <div style="flex: 1; min-width: 150px;">
                    <small style="opacity: 0.5;">Originale</small><br>
                    <strong>{cat}</strong>
                </div>
                <div style="flex: 0 0 auto;">➡️</div>
            """, unsafe_allow_html=True)

            # Using columns inside container is tricky with HTML injection above,
            # so we break out of HTML to render widgets, then close HTML?
            # No, Streamlit widgets cannot be inside HTML strings.
            # Alternative: Use columns directly with CSS styling applied to the container or columns?
            # Let's use standard columns but maybe visual separation.

            # Reverting to pure Streamlit columns for interactivity, but styled nicely.

            c1, c2, c3 = st.columns([2, 2, 2])

            with c1:
                st.markdown(f"**{cat}**")

            with c2:
                try: idx_m = cashew_mains.index(current.main_category)
                except: idx_m = 0
                new_main = st.selectbox("", cashew_mains, index=idx_m, key=f"m_{i}", label_visibility="collapsed")

            with c3:
                cashew_subs = [""] + st.session_state.cashew_struct.get(new_main, {}).get('subs', [])
                try: idx_s = cashew_subs.index(current.sub_category)
                except: idx_s = 0
                new_sub = st.selectbox("", cashew_subs, index=idx_s, key=f"s_{i}", label_visibility="collapsed")

            # Update State
            struct_ref = st.session_state.cashew_struct.get(new_main, {})
            st.session_state.mapping[cat] = CashewConfig(
                main_category=new_main,
                sub_category=new_sub,
                color=struct_ref.get('color', '#9E9E9E'),
                icon=struct_ref.get('icon', 'category_default.png')
            )
            st.markdown("<hr style='margin: 5px 0; border-color: #333;'>", unsafe_allow_html=True)

    st.divider()
    c1, c2 = st.columns([1, 4])
    if c1.button("⬅ Indietro", use_container_width=True):
        st.session_state.step = 2
        st.rerun()
    if c2.button("Avanti: Esporta ➔", type="primary", use_container_width=True):
        st.session_state.step = 4
        st.rerun()
