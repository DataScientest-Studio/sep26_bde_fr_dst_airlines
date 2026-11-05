import pandas as pd
import plotly.express as px
import streamlit as st
from src.frontend.api_client import api_client


def _render_model_stats() -> None:
    st.subheader("Scores des modèles entraînés")

    models = api_client.get_models()
    df = pd.DataFrame(models)

    if df.empty:
        st.info("Aucun modèle entraîné.")
        return

    fig = px.bar(df, x="model_name", y="roc_auc", title="AUC par modèle")
    st.plotly_chart(fig, use_container_width=True)

    fig = px.bar(df, x="model_name", y="recall", title="Rappel par modèle (retards détectés)")
    st.plotly_chart(fig, use_container_width=True)


def _render_data_stats() -> None:
    st.subheader("Retards à l'arrivée (> 15 min)")

    # Delay rate per arrival hour
    df_hour = pd.DataFrame(api_client.get_stats_hour())
    df_hour = df_hour.sort_values("arr_hour_local")
    fig = px.bar(df_hour, x="arr_hour_local", y="delay_rate",
                 title="Taux de retard par heure d'arrivée (heure de Paris)")
    st.plotly_chart(fig, use_container_width=True)

    # Delay rate per airline (airlines with at least 200 flights)
    df_airline = pd.DataFrame(api_client.get_stats_airline())
    df_airline = df_airline[df_airline["nb_flights"] >= 200]
    df_airline = df_airline.sort_values("delay_rate", ascending=False)
    fig = px.bar(df_airline, x="airline_icao", y="delay_rate",
                 title="Taux de retard par compagnie (200 vols minimum)")
    st.plotly_chart(fig, use_container_width=True)

    # Delay rate per departure airport (airports with at least 200 flights)
    df_airport = pd.DataFrame(api_client.get_stats_airport())
    df_airport = df_airport[df_airport["nb_flights"] >= 200]
    df_airport = df_airport.sort_values("delay_rate", ascending=False)
    fig = px.bar(df_airport, x="adep", y="delay_rate",
                 title="Taux de retard par aéroport de départ (200 vols minimum)")
    st.plotly_chart(fig, use_container_width=True)


def render(sub_section: str) -> None:
    st.title("Statistiques")
    if sub_section == "Modèle (Graphiques)":
        _render_model_stats()
    else:
        _render_data_stats()