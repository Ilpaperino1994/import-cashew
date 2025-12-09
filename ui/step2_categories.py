import streamlit as st
import pandas as pd
from logic import DEFAULT_CASHEW_STRUCTURE

def render_step2():
    st.markdown("### 📂 Configure Categories")
    st.info("Define the structure you want in Cashew. You can map your old categories to these later.")

    col_nav, col_editor = st.columns([1, 3])

    with col_nav:
        st.caption("Main Categories")
        # Add New Main Category
        new_cat = st.text_input("New Category", placeholder="Name...", label_visibility="collapsed")
        if st.button("➕ Add", use_container_width=True):
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
                st.markdown(f"#### Edit: {active_cat}")
                c1, c2, c3 = st.columns([1, 1, 1])
                new_color = c1.color_picker("Color", data['color'])
                new_icon = c2.text_input("Icon (png name)", data['icon'])

                if c3.button("🗑️ Delete", type="primary"):
                    del st.session_state.cashew_struct[active_cat]
                    st.session_state.selected_cat_editor = list(st.session_state.cashew_struct.keys())[0]
                    st.rerun()

                st.session_state.cashew_struct[active_cat]['color'] = new_color
                st.session_state.cashew_struct[active_cat]['icon'] = new_icon

                st.markdown("##### Subcategories")
                # Table Editor for Subcategories
                df_subs = pd.DataFrame({"Name": data['subs']})
                edited_df = st.data_editor(df_subs, num_rows="dynamic", use_container_width=True, key=f"subs_{active_cat}", hide_index=True)

                # Save changes
                new_subs = [x.strip() for x in edited_df["Name"].tolist() if x and x.strip()]
                st.session_state.cashew_struct[active_cat]['subs'] = new_subs

    st.divider()
    c1, c2 = st.columns([1, 5])
    if c1.button("⬅ Back"):
        st.session_state.step = 1
        st.rerun()
    if c2.button("Next: Mapping ➔", type="primary"):
        st.session_state.step = 3
        st.rerun()
