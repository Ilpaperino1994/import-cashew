import streamlit as st
import pandas as pd
from logic import DEFAULT_CASHEW_STRUCTURE

def render_step2():
    st.markdown("### 📂 Gestione Categorie")
    st.caption("Organizza la struttura delle tue finanze. Modifica i colori e le icone per un look perfetto.")

    col_nav, col_edit = st.columns([1, 2], gap="large")

    # --- SIDEBAR NAV ---
    with col_nav:
        with st.container(border=True):
            st.markdown("**Categorie Principali**")

            # Add New
            with st.columns([3, 1])[0]: # Small trick to keep input compact
                new_cat = st.text_input("Nuova Categoria", placeholder="Nome...", label_visibility="collapsed")
            if st.button("➕ Aggiungi", use_container_width=True):
                if new_cat and new_cat not in st.session_state.cashew_struct:
                    st.session_state.cashew_struct[new_cat] = {"subs": [], "color": "#9E9E9E", "icon": "category_default.png"}
                    st.session_state.selected_cat_editor = new_cat
                    st.rerun()

            st.markdown("---")

            # List
            cats = list(st.session_state.cashew_struct.keys())
            for cat in cats:
                active = st.session_state.selected_cat_editor == cat
                if st.button(f"{'🔹 ' if active else ''}{cat}", key=f"nav_{cat}", use_container_width=True, type="primary" if active else "secondary"):
                    st.session_state.selected_cat_editor = cat
                    st.rerun()

    # --- MAIN EDITOR ---
    with col_edit:
        active_cat = st.session_state.selected_cat_editor
        if active_cat in st.session_state.cashew_struct:
            data = st.session_state.cashew_struct[active_cat]

            with st.container(border=True):
                # Header
                c_tit, c_del = st.columns([3, 1])
                with c_tit:
                    st.subheader(active_cat)
                with c_del:
                    if st.button("🗑️ Elimina", type="primary", use_container_width=True): # Red styling usually via type primary in some themes, or we assume secondary
                        del st.session_state.cashew_struct[active_cat]
                        keys = list(st.session_state.cashew_struct.keys())
                        st.session_state.selected_cat_editor = keys[0] if keys else ""
                        st.rerun()

                # Props
                c1, c2 = st.columns(2)
                with c1:
                    new_color = st.color_picker("Colore", data['color'])
                    st.session_state.cashew_struct[active_cat]['color'] = new_color
                with c2:
                    new_icon = st.text_input("Icona PNG", data['icon'])
                    st.session_state.cashew_struct[active_cat]['icon'] = new_icon

                st.markdown("#### Sottocategorie")

                # Data Editor
                df_subs = pd.DataFrame({"Nome": data['subs']})
                edited_df = st.data_editor(
                    df_subs,
                    num_rows="dynamic",
                    use_container_width=True,
                    key=f"editor_{active_cat}",
                    hide_index=True,
                    column_config={"Nome": st.column_config.TextColumn("Nome Sottocategoria")}
                )

                new_subs = [x.strip() for x in edited_df["Nome"].tolist() if x and x.strip()]
                st.session_state.cashew_struct[active_cat]['subs'] = new_subs

    st.markdown("<br>", unsafe_allow_html=True)
    c_prev, c_next = st.columns([1, 4])
    if c_prev.button("⬅ Indietro", use_container_width=True):
        st.session_state.step = 1
        st.rerun()
    if c_next.button("Avanti: Mapping ➔", type="primary", use_container_width=True):
        st.session_state.step = 3
        st.rerun()
