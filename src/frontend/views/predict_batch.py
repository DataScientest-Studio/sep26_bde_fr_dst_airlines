import pandas as pd
import streamlit as st
from src.frontend.api_client import api_client

REQUIRED_COLUMNS = [
    "airline_code",
    "origin_airport",
    "destination_airport",
    "month",
    "day_of_week",
    "scheduled_departure_hour",
    "distance",
]


def render() -> None:
    st.title("📦 Prédiction plusieurs vols (Batch)")
    st.caption("Inférence par lot via l'endpoint FastAPI `POST /predict-batch`.")

    mode = st.radio(
        "Source des vols à prédire :",
        options=["Tableau interactif", "Import fichier CSV"],
        horizontal=True,
    )

    default_df = pd.DataFrame(
        [
            {
                "airline_code": "AF",
                "origin_airport": "CDG",
                "destination_airport": "JFK",
                "month": 7,
                "day_of_week": 5,
                "scheduled_departure_hour": 14,
                "distance": 5834.0,
            },
            {
                "airline_code": "DL",
                "origin_airport": "ATL",
                "destination_airport": "LAX",
                "month": 12,
                "day_of_week": 1,
                "scheduled_departure_hour": 19,
                "distance": 3130.0,
            },
        ]
    )

    input_df = default_df
    if mode == "Import fichier CSV":
        uploaded = st.file_uploader("Chargez un fichier CSV contenant les colonnes requises", type=["csv"])
        st.caption(f"Colonnes attendues : `{', '.join(REQUIRED_COLUMNS)}`")
        if uploaded is not None:
            input_df = pd.read_csv(uploaded)
    else:
        st.info("Vous pouvez ajouter, modifier ou supprimer des lignes directement dans le tableau ci-dessous :")
        input_df = st.data_editor(default_df, num_rows="dynamic", use_container_width=True)

    if st.button("🚀 Exécuter la prédiction par lot", type="primary", use_container_width=True):
        missing = [c for c in REQUIRED_COLUMNS if c not in input_df.columns]
        if missing:
            st.error(f"Colonnes manquantes : {missing}")
            return

        flights_payload = input_df[REQUIRED_COLUMNS].to_dict(orient="records")
        try:
            with st.spinner(f"Inférence de {len(flights_payload)} vol(s) sur `/predict-batch`..."):
                response = api_client.predict_batch(flights_payload)

            preds = pd.DataFrame(response.get("predictions", []))
            result_df = pd.concat([input_df.reset_index(drop=True), preds], axis=1)

            st.success(f"✅ {len(result_df)} prédictions réalisées avec succès.")
            st.dataframe(result_df, use_container_width=True)

            csv_bytes = result_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Télécharger les résultats (CSV)",
                data=csv_bytes,
                file_name="predictions_vols.csv",
                mime="text/csv",
            )
        except Exception as exc:
            st.error(f"Erreur lors de l'appel à `/predict-batch` : {exc}")
