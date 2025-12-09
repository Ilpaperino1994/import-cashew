import streamlit as st
import pandas as pd
from logic import DEFAULT_CASHEW_STRUCTURE

def render_step2():
    st.markdown("### 📂 Configura la Struttura delle Categorie")
    st.info("""
    **Guida:**
    Qui puoi definire l'albero delle categorie che desideri avere nella nuova app Cashew.

    1. A sinistra, gestisci le **Categorie Principali** (es. Cibo, Trasporti).
    2. A destra, personalizza i dettagli e aggiungi le **Sottocategorie** (es. Ristorante, Spesa, Benzina).

    💡 *Suggerimento: Una struttura ben organizzata renderà i tuoi report più utili!*
    """)

    col_nav, col_editor = st.columns([1, 3])

    with col_nav:
        st.markdown("#### Categorie Principali")
        # Add New Main Category
        new_cat = st.text_input("Nuova Categoria", placeholder="Nome...", label_visibility="collapsed")
        if st.button("➕ Aggiungi", use_container_width=True):
            if new_cat and new_cat not in st.session_state.cashew_struct:
                st.session_state.cashew_struct[new_cat] = {"subs": [], "color": "#9E9E9E", "icon": "category_default.png"}
                st.session_state.selected_cat_editor = new_cat
                st.rerun()

        st.markdown("---")

        # List of Categories
        for cat_name in list(st.session_state.cashew_struct.keys()):
            style = "primary" if st.session_state.selected_cat_editor == cat_name else "secondary"
            if st.button(cat_name, key=f"cat_btn_{cat_name}", use_container_width=True, type=style):
                st.session_state.selected_cat_editor = cat_name
                st.rerun()

    with col_editor:
        active_cat = st.session_state.selected_cat_editor
        if active_cat in st.session_state.cashew_struct:
            data = st.session_state.cashew_struct[active_cat]

            with st.container():
                st.markdown(f"#### Modifica: **{active_cat}**")

                c1, c2, c3 = st.columns([1, 2, 1])
                new_color = c1.color_picker("Colore", data['color'])
                new_icon = c2.text_input("Icona (nome file png)", data['icon'], help="Es. 'food.png'. Lascia default se non sei sicuro.")

                if c3.button("🗑️ Elimina", type="primary"):
                    del st.session_state.cashew_struct[active_cat]
                    # Select another category if available
                    keys = list(st.session_state.cashew_struct.keys())
                    if keys:
                        st.session_state.selected_cat_editor = keys[0]
                    else:
                        st.session_state.selected_cat_editor = ""
                    st.rerun()

                # Update struct in real-time
                if active_cat in st.session_state.cashew_struct:
                    st.session_state.cashew_struct[active_cat]['color'] = new_color
                    st.session_state.cashew_struct[active_cat]['icon'] = new_icon

                    st.markdown("##### Sottocategorie")
                    st.caption("Aggiungi qui le sottocategorie specifiche.")

                    # Table Editor for Subcategories
                    df_subs = pd.DataFrame({"Nome": data['subs']})
                    edited_df = st.data_editor(
                        df_subs,
                        num_rows="dynamic",
                        use_container_width=True,
                        key=f"subs_{active_cat}",
                        hide_index=True,
                        column_config={"Nome": st.column_config.TextColumn("Nome Sottocategoria")}
                    )

                    # Save changes
                    new_subs = [x.strip() for x in edited_df["Nome"].tolist() if x and x.strip()]
                    st.session_state.cashew_struct[active_cat]['subs'] = new_subs

    st.divider()
    c1, c2 = st.columns([1, 5])
    if c1.button("⬅ Indietro"):
        st.session_state.step = 1
        st.rerun()
    if c2.button("Avanti: Mappatura Dati ➔", type="primary"):
        st.session_state.step = 3
        st.rerun()
