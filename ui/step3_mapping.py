import streamlit as st
from logic import ai_suggest_mapping
from models import CashewConfig

def render_step3():
    st.markdown("### 🤖 Mapping Intelligente")
    st.caption("Collega le categorie del vecchio file con quelle nuove. Usa l'IA per suggerimenti rapidi.")

    # Controls
    with st.container(border=True):
        c_search, c_ai = st.columns([3, 1])
        with c_search:
            q = st.text_input("Filtra Categorie...", placeholder="Cerca...", label_visibility="collapsed")
        with c_ai:
            if st.button("✨ Auto-AI", type="primary", use_container_width=True):
                 with st.spinner("Elaborazione..."):
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
                    st.toast("Mapping completato!", icon="🤖")
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Grid List
    unique_cats = sorted(list({t.category for t in st.session_state.transactions}))
    if q: unique_cats = [c for c in unique_cats if q.lower() in c.lower()]
    cashew_mains = list(st.session_state.cashew_struct.keys())

    # We use a scrollable container
    with st.container(height=500, border=True):
        for i, cat in enumerate(unique_cats):
            current = st.session_state.mapping.get(cat, CashewConfig(main_category="Altro"))

            c_orig, c_arrow, c_main, c_sub = st.columns([2, 0.5, 2, 2])

            with c_orig:
                st.markdown(f"**{cat}**")
                st.caption("Originale")

            with c_arrow:
                st.markdown("➔", unsafe_allow_html=True) # Simple arrow

            with c_main:
                try: idx_m = cashew_mains.index(current.main_category)
                except: idx_m = 0
                new_main = st.selectbox("", cashew_mains, index=idx_m, key=f"m_{i}", label_visibility="collapsed")

            with c_sub:
                subs = [""] + st.session_state.cashew_struct.get(new_main, {}).get('subs', [])
                try: idx_s = subs.index(current.sub_category)
                except: idx_s = 0
                new_sub = st.selectbox("", subs, index=idx_s, key=f"s_{i}", label_visibility="collapsed")

            # Update
            struct_ref = st.session_state.cashew_struct.get(new_main, {})
            st.session_state.mapping[cat] = CashewConfig(
                main_category=new_main,
                sub_category=new_sub,
                color=struct_ref.get('color', '#9E9E9E'),
                icon=struct_ref.get('icon', '')
            )
            st.divider()

    st.markdown("<br>", unsafe_allow_html=True)
    c_prev, c_next = st.columns([1, 4])
    if c_prev.button("⬅ Indietro", use_container_width=True):
        st.session_state.step = 2
        st.rerun()
    if c_next.button("Avanti: Esporta ➔", type="primary", use_container_width=True):
        st.session_state.step = 4
        st.rerun()
