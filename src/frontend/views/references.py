import pandas as pd
import streamlit as st
from src.frontend.api_client import api_client


def _render_airlines() -> None:
    """ Affiche Reference Airlines """
    st.subheader("🛫 Table de référence : Airlines (`/airlines`)")
    try:
        data = api_client.get_airlines()
        df = pd.DataFrame(data)
        search = st.text_input("Rechercher une compagnie (code IATA ou nom)")
        if search and not df.empty:
            mask = (
                df["iata_code"].astype(str).str.contains(search, case=False, na=False)
                | df["airline_name"].astype(str).str.contains(search, case=False, na=False)
            )
            df = df[mask]
        st.dataframe(df, use_container_width=True)
        st.caption(f"{len(df)} compagnie(s) affichée(s).")
    except Exception as exc:
        st.error(f"Erreur lors de l'appel à `/airlines` : {exc}")


def _render_airports() -> None:
    """ Affiche Reference Airports """
    st.subheader("🌍 Table de référence : Airports (`/airports`)")
    search = st.text_input("Filtrer par code IATA, nom d'aéroport ou ville", placeholder="Ex: CDG, Paris, JFK...")
    try:
        data = api_client.get_airports(search=search if search else None)
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        st.caption(f"{len(df)} aéroport(s) trouvé(s).")

        if not df.empty and {"latitude", "longitude"}.issubset(df.columns):
            map_df = df.dropna(subset=["latitude", "longitude"])
            if not map_df.empty:
                st.markdown("#### 🗺️ Localisation des aéroports")
                st.map(map_df, latitude="latitude", longitude="longitude")
    except Exception as exc:
        st.error(f"Erreur lors de l'appel à `/airports` : {exc}")


def _render_flights() -> None:
    """ Affiche Reference Flights """
    st.subheader("✈️ Table de référence : Flights (`/flight`)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        airline_code = st.text_input("Code Compagnie (ex: AF)")
    with c2:
        origin_airport = st.text_input("Aéroport Départ (ex: CDG)")
    with c3:
        destination_airport = st.text_input("Aéroport Arrivée (ex: JFK)")
    with c4:
        limit = st.number_input("Limite de lignes", min_value=10, max_value=1000, value=100, step=50)

    try:
        data = api_client.get_flights(
            airline_code=airline_code or None,
            origin_airport=origin_airport or None,
            destination_airport=destination_airport or None,
            limit=int(limit),
        )
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        st.caption(f"{len(df)} vol(s) affiché(s).")
    except Exception as exc:
        st.error(f"Erreur lors de l'appel à `/flight` : {exc}")


def render(table_choice: str) -> None:
    st.title("📚 Tables de Référence")
    if table_choice == "Airlines":
        _render_airlines()
    elif table_choice == "Airports":
        _render_airports()
    else:
        _render_flights()
