import streamlit as st
import pandas as pd
from logic import DEFAULT_CASHEW_STRUCTURE

def render_step2():
    st.markdown('<div class="st-card">', unsafe_allow_html=True)
    st.markdown("### 📂 Struttura Categorie")
    st.caption("Definisci le categorie che vuoi usare in Cashew. A sinistra le principali, a destra i dettagli.")
    st.markdown('</div>', unsafe_allow_html=True)

    col_nav, col_editor = st.columns([1, 2], gap="large")

    with col_nav:
        st.markdown("**Categorie Principali**")

        # Add New
        with st.form("new_cat_form", clear_on_submit=True):
            new_cat = st.text_input("Nuova", placeholder="Es. Viaggi...", label_visibility="collapsed")
            if st.form_submit_button("➕ Aggiungi", use_container_width=True):
                if new_cat and new_cat not in st.session_state.cashew_struct:
                    st.session_state.cashew_struct[new_cat] = {"subs": [], "color": "#9E9E9E", "icon": "category_default.png"}
                    st.session_state.selected_cat_editor = new_cat
                    st.rerun()

        st.markdown("---")

        # Scrollable list simulation
        for cat_name in list(st.session_state.cashew_struct.keys()):
            style = "primary" if st.session_state.selected_cat_editor == cat_name else "secondary"
            # Using columns to create a "list item" feel
            if st.button(f"{cat_name}", key=f"cat_btn_{cat_name}", use_container_width=True, type=style):
                st.session_state.selected_cat_editor = cat_name
                st.rerun()

    with col_editor:
        active_cat = st.session_state.selected_cat_editor
        if active_cat in st.session_state.cashew_struct:
            data = st.session_state.cashew_struct[active_cat]

            # Card-like container for editor
            st.markdown(f"""
            <div style="background-color: var(--card-bg); padding: 20px; border-radius: 12px; border: 1px solid var(--border-color);">
                <h3 style="margin-top:0;">{active_cat}</h3>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns([1, 2, 1])
            new_color = c1.color_picker("Colore", data['color'])
            new_icon = c2.text_input("Icona PNG", data['icon'])

            if c3.button("🗑️ Elimina", type="primary", use_container_width=True):
                del st.session_state.cashew_struct[active_cat]
                keys = list(st.session_state.cashew_struct.keys())
                st.session_state.selected_cat_editor = keys[0] if keys else ""
                st.rerun()

            # Update State
            st.session_state.cashew_struct[active_cat]['color'] = new_color
            st.session_state.cashew_struct[active_cat]['icon'] = new_icon

            st.markdown("##### Sottocategorie")
            # Table Editor
            df_subs = pd.DataFrame({"Nome": data['subs']})
            edited_df = st.data_editor(
                df_subs,
                num_rows="dynamic",
                use_container_width=True,
                key=f"subs_{active_cat}",
                hide_index=True,
                column_config={"Nome": st.column_config.TextColumn("Nome")}
            )

            new_subs = [x.strip() for x in edited_df["Nome"].tolist() if x and x.strip()]
            st.session_state.cashew_struct[active_cat]['subs'] = new_subs

            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    c1, c2 = st.columns([1, 4])
    if c1.button("⬅ Indietro", use_container_width=True):
        st.session_state.step = 1
        st.rerun()
    if c2.button("Avanti: Mappatura ➔", type="primary", use_container_width=True):
        st.session_state.step = 3
        st.rerun()
