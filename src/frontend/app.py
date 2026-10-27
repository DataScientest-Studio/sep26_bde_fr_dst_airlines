import streamlit as st
from src.frontend.auth import check_google_auth, render_user_sidebar
from src.frontend.views import predict_batch, predict_single, references, statistics
from streamlit_option_menu import option_menu

st.write(st.__version__)

st.set_page_config(
    page_title="Liora Airlines — Dashboard & ML",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    # 1. Authentification Google obligatoire
    if not check_google_auth():
        st.stop()

    # 2. Menu de navigation latéral
    with st.sidebar:
        st.title("✈️ Liora Airlines")
        st.caption("Projet Data Engineer SEP26")

        main_section = option_menu(
            menu_title="Navigation",
            options=[
                    "Prédiction un vol",
                    "Prédiction plusieurs vols",
                    "Statistiques",
                    "Références",],
            icons=["bullseye",  
                    "boxes",    
                    "bar-chart",
                    "book" ],
            default_index=0,
            orientation="horizontal"
        )
        
        stat_sub = None
        ref_sub = None

        if main_section == "Statistiques":
            stat_sub = st.selectbox(
                "Sous-menu Statistiques",
                options=["Modèle (Graphiques)", "Data"],
            )
        elif main_section == "Références":
            ref_sub = st.selectbox(
                "Table à afficher",
                options=["Airlines", "Airports", "Flights"],
            )

    render_user_sidebar()

    # 3. Routage vers la vue sélectionnée
    if main_section == "Prédiction un vol":
        predict_single.render()
    elif main_section == "Prédiction plusieurs vols":
        predict_batch.render()
    elif main_section == "Statistiques":
        statistics.render(stat_sub or "Modèle (Graphiques)")
    elif main_section == "Références":
        references.render(ref_sub or "Airlines")


if __name__ == "__main__":
    main()
