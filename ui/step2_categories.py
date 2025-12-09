import streamlit as st
import pandas as pd
from logic import DEFAULT_CASHEW_STRUCTURE

def render_step2():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2 class="hero-text">Organizza le tue Categorie</h2>
        <p>Definisci la struttura di destinazione per Cashew. Crea, modifica o elimina categorie e sottocategorie.</p>
    </div>
    """, unsafe_allow_html=True)

    col_list, col_edit = st.columns([1, 2], gap="large")

    # --- LISTA CATEGORIE (SIDEBAR) ---
    with col_list:
        st.markdown('<div class="st-card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown("### Categorie Principali")

        # New Category Input
        c_in, c_btn = st.columns([3, 1])
        with c_in:
            new_cat_name = st.text_input("Nuova Categoria", placeholder="Es. Casa...", label_visibility="collapsed", key="new_cat_input")
        with c_btn:
            if st.button("➕", use_container_width=True, help="Aggiungi Categoria"):
                if new_cat_name and new_cat_name not in st.session_state.cashew_struct:
                    st.session_state.cashew_struct[new_cat_name] = {"subs": [], "color": "#9E9E9E", "icon": "category_default.png"}
                    st.session_state.selected_cat_editor = new_cat_name
                    st.rerun()

        st.markdown("---")

        # List of Categories as Cards/Buttons
        cats = list(st.session_state.cashew_struct.keys())
        for cat in cats:
            is_active = (st.session_state.selected_cat_editor == cat)
            # Visual indicator for active state
            if st.button(
                f"{'🟢 ' if is_active else ''}{cat}",
                key=f"sel_{cat}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.selected_cat_editor = cat
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # --- EDITOR (MAIN) ---
    with col_edit:
        active_cat = st.session_state.selected_cat_editor
        if active_cat and active_cat in st.session_state.cashew_struct:
            data = st.session_state.cashew_struct[active_cat]

            st.markdown('<div class="st-card">', unsafe_allow_html=True)

            # Header with Delete
            c_head, c_del = st.columns([3, 1])
            with c_head:
                st.markdown(f"<h2 style='margin:0; color: {data.get('color', '#fff')}'>{active_cat}</h2>", unsafe_allow_html=True)
            with c_del:
                if st.button("🗑️ Elimina", key=f"del_{active_cat}", type="secondary", use_container_width=True):
                    del st.session_state.cashew_struct[active_cat]
                    keys = list(st.session_state.cashew_struct.keys())
                    st.session_state.selected_cat_editor = keys[0] if keys else ""
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            # Properties Grid
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown("**Colore Categoria**")
                new_color = st.color_picker("Colore", data.get('color', '#9E9E9E'), label_visibility="collapsed")
            with c2:
                st.markdown("**Nome Icona (PNG)**")
                new_icon = st.text_input("Icona", data.get('icon', ''), label_visibility="collapsed")

            # Update State immediately
            st.session_state.cashew_struct[active_cat]['color'] = new_color
            st.session_state.cashew_struct[active_cat]['icon'] = new_icon

            st.markdown("---")
            st.markdown("### Sottocategorie")
            st.caption("Aggiungi o rimuovi sottocategorie usando la tabella qui sotto.")

            df_subs = pd.DataFrame({"Sottocategorie": data['subs']})
            edited_df = st.data_editor(
                df_subs,
                num_rows="dynamic",
                use_container_width=True,
                key=f"editor_{active_cat}",
                hide_index=True,
                column_config={
                    "Sottocategorie": st.column_config.TextColumn(
                        "Nome",
                        help="Nome della sottocategoria",
                        required=True
                    )
                }
            )

            # Sync subs back to state
            new_subs_list = [x.strip() for x in edited_df["Sottocategorie"].tolist() if x and x.strip()]
            st.session_state.cashew_struct[active_cat]['subs'] = new_subs_list

            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Seleziona o crea una categoria per iniziare.")

    # Navigation Footer
    st.markdown("<br>", unsafe_allow_html=True)
    c_back, c_next = st.columns([1, 4])
    if c_back.button("⬅ Indietro", use_container_width=True):
        st.session_state.step = 1
        st.rerun()
    if c_next.button("Avanti: Mappatura Intelligente ➔", type="primary", use_container_width=True):
        st.session_state.step = 3
        st.rerun()
