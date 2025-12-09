import streamlit as st
from logic import ai_suggest_mapping
from models import CashewConfig

def render_step3():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2 class="hero-text">Collega le tue Transazioni</h2>
        <p>Associa le categorie originali di Wallet con quelle nuove di Cashew. Usa l'IA per velocizzare il processo.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- TOP CONTROL BAR ---
    st.markdown('<div class="st-card">', unsafe_allow_html=True)
    c_search, c_ai = st.columns([3, 1], gap="medium")

    with c_search:
        search_query = st.text_input("🔍 Cerca categoria originale...", placeholder="Inizia a digitare...", label_visibility="collapsed")

    with c_ai:
        if st.button("✨ Auto-Mapping IA", type="primary", use_container_width=True, help="Usa l'intelligenza artificiale per suggerire le associazioni"):
            with st.spinner("L'IA sta analizzando le tue categorie..."):
                unique_cats = list({t.category for t in st.session_state.transactions})
                suggestions = ai_suggest_mapping(unique_cats, st.session_state.cashew_struct)
                for w_cat, res in suggestions.items():
                    # Only map if not already manually set? For now overwrite is fine or check if empty.
                    # Let's overwrite to be useful.
                    struct_ref = st.session_state.cashew_struct.get(res['main'], {})
                    st.session_state.mapping[w_cat] = CashewConfig(
                        main_category=res['main'],
                        sub_category=res['sub'],
                        color=struct_ref.get('color', '#9E9E9E'),
                        icon=struct_ref.get('icon', 'category_default.png')
                    )
                st.toast("Mapping automatico completato!", icon="✨")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # --- MAPPING GRID ---
    unique_cats = sorted(list({t.category for t in st.session_state.transactions}))
    cashew_mains = list(st.session_state.cashew_struct.keys())

    # Filter based on search
    if search_query:
        unique_cats = [c for c in unique_cats if search_query.lower() in c.lower()]

    if not unique_cats:
        st.info("Nessuna categoria trovata con questo nome.")
    else:
        # Use a container with specific height for scrolling
        with st.container(height=600, border=False):
            # We'll use a CSS grid layout via columns for each row
            for i, cat in enumerate(unique_cats):
                current = st.session_state.mapping.get(cat, CashewConfig(main_category="Altro"))

                # Visual grouping logic could go here (e.g. dividers between letters), but let's keep it clean.

                # Container for the row
                st.markdown(f"""
                <div style="
                    background-color: var(--surface);
                    border: 1px solid var(--border);
                    border-radius: 12px;
                    padding: 15px;
                    margin-bottom: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    flex-wrap: wrap;
                    gap: 15px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                """, unsafe_allow_html=True)

                # We need to break out of HTML to use Streamlit widgets.
                # Grid Layout: [Original Name] -> [Main Select] [Sub Select]

                # Close the opening div immediately? No, we can't wrap widgets in HTML blocks easily.
                # Strategy: Use st.columns inside a loop, but style them globally or via wrapper?
                # Streamlit doesn't let us put widgets inside `st.markdown`.
                # We will use st.columns but style the container AROUND them using a trick isn't easy.
                # Standard st.columns it is, but we can put a divider or background?
                # Actually, `st.container` with a border is supported now.

                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 2])

                    with c1:
                        st.caption("Originale")
                        st.markdown(f"**{cat}**")

                    with c2:
                        try: idx_m = cashew_mains.index(current.main_category)
                        except: idx_m = 0
                        new_main = st.selectbox(
                            "Categoria Principale",
                            cashew_mains,
                            index=idx_m,
                            key=f"m_{cat}_{i}",
                            label_visibility="collapsed"
                        )

                    with c3:
                        cashew_subs = [""] + st.session_state.cashew_struct.get(new_main, {}).get('subs', [])
                        # Ensure current sub is valid
                        curr_sub = current.sub_category
                        if curr_sub not in cashew_subs: curr_sub = ""

                        try: idx_s = cashew_subs.index(curr_sub)
                        except: idx_s = 0

                        new_sub = st.selectbox(
                            "Sottocategoria",
                            cashew_subs,
                            index=idx_s,
                            key=f"s_{cat}_{i}",
                            label_visibility="collapsed"
                        )

                    # Update State
                    struct_ref = st.session_state.cashew_struct.get(new_main, {})
                    st.session_state.mapping[cat] = CashewConfig(
                        main_category=new_main,
                        sub_category=new_sub,
                        color=struct_ref.get('color', '#9E9E9E'),
                        icon=struct_ref.get('icon', 'category_default.png')
                    )

    # --- NAVIGATION ---
    st.markdown("<br>", unsafe_allow_html=True)
    c_back, c_next = st.columns([1, 4])

    if c_back.button("⬅ Indietro", use_container_width=True):
        st.session_state.step = 2
        st.rerun()

    # Check if all mapped (optional validation visual)
    unmapped_count = sum(1 for c in unique_cats if st.session_state.mapping.get(c, CashewConfig(main_category="Altro")).main_category == "Altro")
    btn_label = "Avanti: Esporta Dati ➔"
    if unmapped_count > 0:
        btn_label += f" ({unmapped_count} come 'Altro')"

    if c_next.button(btn_label, type="primary", use_container_width=True):
        st.session_state.step = 4
        st.rerun()
