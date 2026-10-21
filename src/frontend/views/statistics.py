import pandas as pd
import plotly.express as px
import streamlit as st
from src.frontend.api_client import api_client, cached_airlines, cached_airports


def _render_model_stats() -> None:
    st.subheader("📈 Analyse & Graphiques du Modèle IA (Scikit-Learn)")
    st.caption("Visualisation du comportement du modèle sur une grille de scénarios via `/predict-batch` et importance des variables.")

    col1, col2 = st.columns(2)
    with col1:
        airline = st.text_input("Compagnie de référence", value="AF")
        origin = st.text_input("Origine de référence", value="CDG")
    with col2:
        destination = st.text_input("Destination de référence", value="JFK")
        distance = st.number_input("Distance (km)", value=5834.0, min_value=100.0)

    if st.button("Générer les courbes de réponse du modèle (0h - 23h)", type="primary"):
        scenarios = [
            {
                "airline_code": airline,
                "origin_airport": origin,
                "destination_airport": destination,
                "month": 7,
                "day_of_week": 5,
                "scheduled_departure_hour": h,
                "distance": float(distance),
            }
            for h in range(24)
        ]
        try:
            res = api_client.predict_batch(scenarios)
            df_sim = pd.DataFrame(scenarios)
            df_preds = pd.DataFrame(res.get("predictions", []))
            df_plot = pd.concat([df_sim, df_preds], axis=1)

            c1, c2 = st.columns(2)
            with c1:
                fig_delay = px.line(
                    df_plot,
                    x="scheduled_departure_hour",
                    y="predicted_delay_minutes",
                    markers=True,
                    title="Retard prédit selon l'heure de départ",
                    labels={
                        "scheduled_departure_hour": "Heure de départ prévue",
                        "predicted_delay_minutes": "Retard prédit (min)",
                    },
                )
                st.plotly_chart(fig_delay, use_container_width=True)

            with c2:
                if "delay_probability" in df_plot.columns and df_plot["delay_probability"].notna().any():
                    fig_prob = px.bar(
                        df_plot,
                        x="scheduled_departure_hour",
                        y="delay_probability",
                        title="Probabilité de retard par heure de départ",
                    )
                    st.plotly_chart(fig_prob, use_container_width=True)
                else:
                    fig_status = px.pie(
                        df_plot,
                        names="is_delayed",
                        title="Répartition Retard vs À l'heure sur 24h",
                    )
                    st.plotly_chart(fig_status, use_container_width=True)
        except Exception as exc:
            st.warning(f"Impossible d'interroger le modèle sur `/predict-batch` : {exc}")


def _render_data_stats() -> None:
    st.subheader("📊 Statistiques des Données (PostgreSQL)")
    st.caption("Indicateurs agrégés calculés depuis PostgreSQL via `GET /stats` et `GET /flight`.")

    airlines = cached_airlines()
    airports = cached_airports()

    f1, f2 = st.columns(2)
    with f1:
        airline_filter = st.selectbox(
            "Filtrer par compagnie",
            options=["Toutes"] + [a["iata_code"] for a in airlines],
        )
    with f2:
        airport_filter = st.selectbox(
            "Filtrer par aéroport de départ",
            options=["Tous"] + [a["iata_code"] for a in airports],
        )

    selected_airline = None if airline_filter == "Toutes" else airline_filter
    selected_airport = None if airport_filter == "Tous" else airport_filter

    try:
        stats = api_client.get_stats(airline_code=selected_airline, origin_airport=selected_airport)
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total Vols", f"{stats.get('total_flights', 0):,}")
        k2.metric("Retard moyen départ", f"{stats.get('avg_departure_delay', 0.0):.1f} min")
        k3.metric("Retard moyen arrivée", f"{stats.get('avg_arrival_delay', 0.0):.1f} min")
        k4.metric("Taux de retard (≥15m)", f"{stats.get('delayed_flights_rate', 0.0) * 100:.1f} %")
        k5.metric("Taux d'annulation", f"{stats.get('cancellation_rate', 0.0) * 100:.1f} %")
    except Exception as exc:
        st.error(f"Erreur lors de la récupération de `/stats` : {exc}")
        return

    st.markdown("---")
    try:
        flights = api_client.get_flights(
            airline_code=selected_airline,
            origin_airport=selected_airport,
            limit=500,
        )
        if not flights:
            st.info("Aucun vol trouvé pour ces filtres.")
            return

        df_flights = pd.DataFrame(flights)
        g1, g2 = st.columns(2)
        with g1:
            if "arrival_delay" in df_flights.columns:
                fig_hist = px.histogram(
                    df_flights,
                    x="arrival_delay",
                    nbins=40,
                    title="Distribution des retards à l'arrivée (min)",
                )
                st.plotly_chart(fig_hist, use_container_width=True)
        with g2:
            if {"airline_code", "arrival_delay"}.issubset(df_flights.columns):
                avg_by_airline = (
                    df_flights.groupby("airline_code", as_index=False)["arrival_delay"]
                    .mean()
                    .sort_values("arrival_delay", ascending=False)
                )
                fig_bar = px.bar(
                    avg_by_airline,
                    x="airline_code",
                    y="arrival_delay",
                    color="arrival_delay",
                    title="Retard moyen à l'arrivée par compagnie",
                )
                st.plotly_chart(fig_bar, use_container_width=True)
    except Exception as exc:
        st.error(f"Erreur lors de la récupération des vols pour les graphiques : {exc}")


def render(sub_section: str) -> None:
    st.title("📊 Statistiques")
    if sub_section == "Modèle (Graphiques)":
        _render_model_stats()
    else:
        _render_data_stats()
