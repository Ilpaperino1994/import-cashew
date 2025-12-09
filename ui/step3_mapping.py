import streamlit as st
from logic import ai_suggest_mapping
from models import CashewConfig

def render_step3():
    st.markdown("### 🤖 Map Data")
    st.info("Link your Wallet categories (left) to Cashew categories (right).")

    unique_cats = sorted(list({t.category for t in st.session_state.transactions}))

    # Auto-Mapping Action
    if st.button("✨ Run AI Auto-Mapping", type="primary"):
        with st.spinner("Analyzing..."):
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

    st.divider()

    # Mapping Interface
    # Use a grid/table approach for speed

    # Create lists for Selectbox
    cashew_mains = list(st.session_state.cashew_struct.keys())

    # Pagination or Scrollable container
    with st.container(height=600):
        for i, cat in enumerate(unique_cats):
            current = st.session_state.mapping.get(cat, CashewConfig(main_category="Altro"))

            c1, c2, c3 = st.columns([2, 2, 2])
            c1.markdown(f"**{cat}**")

            # Main Category
            try: idx_m = cashew_mains.index(current.main_category)
            except: idx_m = 0
            new_main = c2.selectbox("Main", cashew_mains, index=idx_m, key=f"m_{i}", label_visibility="collapsed")

            # Sub Category
            cashew_subs = [""] + st.session_state.cashew_struct.get(new_main, {}).get('subs', [])
            try: idx_s = cashew_subs.index(current.sub_category)
            except: idx_s = 0
            new_sub = c3.selectbox("Sub", cashew_subs, index=idx_s, key=f"s_{i}", label_visibility="collapsed")

            # Update State
            struct_ref = st.session_state.cashew_struct.get(new_main, {})
            st.session_state.mapping[cat] = CashewConfig(
                main_category=new_main,
                sub_category=new_sub,
                color=struct_ref.get('color', '#9E9E9E'),
                icon=struct_ref.get('icon', 'category_default.png')
            )
            st.divider()

    c1, c2 = st.columns([1, 5])
    if c1.button("⬅ Back"):
        st.session_state.step = 2
        st.rerun()
    if c2.button("Next: Export ➔", type="primary"):
        st.session_state.step = 4
        st.rerun()
