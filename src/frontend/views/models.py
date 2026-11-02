import streamlit as st
from src.frontend.api_client import api_client, cached_models
from datetime import date,datetime, timedelta
import pandas as pd
import json

@st.dialog("Confirmation")
def confirm_deploy(model_name):

    st.warning(
        f"Voulez-vous vraiment déployer '{model_name}' ?"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Confirmer"):
            response = api_client.deploy_model(model_name)
            st.success("Déploiement lancé")
            st.rerun()

    with col2:
        if st.button("❌ Annuler"):
            st.rerun()


def render() -> None:

    st.title("Gestion des modèles")
    st.caption(
        "Getions des modèle diponibles (entrainés)"
        "(Modèle Scikit-Learn)."
    )

    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame()

    
    try:

        with st.spinner("Recherche des modèles..."):

            result = api_client.get_models()
            df = pd.DataFrame(result)

            if not df.empty:
                #df["selected"]=False
                st.session_state.df = df
            else:
                st.session_state.df = None

    except Exception as exc:
        st.error(
            f"Erreur lors de l'appel à /models : {exc}"
        )

    # affichage permanent du tableau
    if not st.session_state.df.empty:

        st.subheader(
            f"{len(st.session_state.df)} modèle(s) trouvé(s)"
        )
        st.badge("Selectionnez le modèle à activer et cliquer sur le bouton 'Activer' situé sous la liste")

        event = st.dataframe(
            st.session_state.df,
            hide_index=True,
            column_config={
                "model_name": st.column_config.TextColumn("Nom"),
                "model_type": st.column_config.TextColumn("Type"),
                "trained_at": st.column_config.TextColumn("Date entraînement"),
                "roc_auc": st.column_config.NumberColumn("ROC AUC"),
                "f1": st.column_config.NumberColumn("F1 Score"),
                "precision": st.column_config.NumberColumn("Précision"),
                "recall": st.column_config.NumberColumn("Rappel"),
                "online": st.column_config.CheckboxColumn("En ligne"),
            },
            selection_mode="single-row",
            on_select="rerun",
            use_container_width=True
        )
    else:
        st.subheader(f"Aucun modèle trouvé" )

    # On a selectionné un modele -> Affiche le bouton deployer
    if event.selection.rows:
        idx = event.selection.rows[0]

        model = st.session_state.df.iloc[idx]

        st.info( f"Modèle sélectionné : {model['model_name']}" )

        if st.button("🚀 Déployer"):
            # Confirme le deploiement
            confirm_deploy(model['model_name'])