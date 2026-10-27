import streamlit as st
from src.frontend.api_client import api_client, cached_airlines, cached_airports
from datetime import date,datetime, timedelta
import pandas as pd
def render() -> None:
    st.title("🎯 Prédiction d'un vol")
    st.caption("Inférence en temps réel via l'endpoint FastAPI `POST /predict` (Modèle Scikit-Learn).")
    result=None
    airlines = cached_airlines()
    origine_airports = cached_airports()
    dest_airports = list(filter(lambda x: x["iata_code"] in ("BVA","CDG","ORY") ,origine_airports))

    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame()
    if "selected_rows" not in st.session_state:
        st.session_state.selected_rows = []
    with st.form("single_flight_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            origin_airport = st.selectbox("Aéroport de départ", options=origine_airports, index=0, format_func=lambda x: f"{x['iata_code']} - {x['airport_name']}")
            airline_codes = st.multiselect("Compagnie aérienne (IATA)", options=airlines,format_func=lambda x: f"{x['airline_name']}")
        with col2:
            destination_airport = st.selectbox(
                "Aéroport d'arrivée",
                options=dest_airports,
                index=min(1, len(dest_airports) - 1), format_func=lambda x: f"{x['iata_code']} - {x['airport_name']}"
            )
        with col3:
            date_vol = st.date_input("Date du vol", min_value=date.today(), max_value=date.today()+ timedelta(days=14))
            start_hour, end_hour = st.slider("Heure de départ prévue (0-23h)", min_value=0, max_value=23, value=(8,17))

        submitted = st.form_submit_button("🚀 Lancer la recherche des Vols", use_container_width=True, type="primary")

    if submitted:
        
        try:
            with st.spinner("Recherche des vols en cours..."):
                result = api_client.get_flights(airline_codes=list(map(lambda x:x["icao_code"],airline_codes)),origin_airport=origin_airport["iata_code"],
                    destination_airport=destination_airport["iata_code"],flight_date=date_vol.isoformat() ,
                    start_hour= int(start_hour) if start_hour else None,end_hour=int(end_hour) if end_hour else None)
                df = pd.DataFrame(result)
                if not df.empty:
                    df = df.sort_values("dep_time")
                    df["retard"] = None
                    
                    df = df[
                        [
                            "flight_icao",
                            "airline_name",
                            "flight_number",
                            "dep_icao",
                            "arr_icao",
                            "dep_time",
                            "arr_time",
                        ]
                    ]
                
                
                st.session_state.df = df
                st.session_state.df["retard"] = None
        except Exception as exc:
            st.error(f"Erreur lors de l'appel à `/flights` : {exc}")
    if st.session_state.df is not None and not st.session_state.df.empty:
        st.subheader(f"{len(st.session_state.df)} Vol(s) Trouvés - {origin_airport['airport_name']} -> {destination_airport['airport_name']}")
        if st.button("Estimer si mon/mes vols seront en retard"):

            selected_rows = flight_grid.selection.rows
            for idx in selected_rows:
                row = st.session_state.df.iloc[idx]

                response = api_client.predict_single(row.to_dict())

                result = response.json()["value"]

                st.session_state.df.loc[idx, "retard"] = result
                st.rerun()


        flight_grid=st.dataframe(st.session_state.df,
                    column_config={
                    "flight_id": None,  # cachée
                    "flight_icao": st.column_config.TextColumn("Vol"),
                    "flight_number": None,
                    "airline_name": st.column_config.TextColumn("Compagnie"),
                    "airline_icao": None,
                    "dep_icao": None,
                    "arr_icao": None,
                    "dep_iata": st.column_config.TextColumn("Aéroport d'origine" ),
                    "arr_iata": st.column_config.TextColumn("Aéroport d'Arrivée" ),
                    "dep_time": st.column_config.TextColumn("Heure départ prévue" ),
                    "arr_time": st.column_config.TextColumn("Heure d'arrivée prévue" ),
                    "retard":st.column_config.TextColumn("Retard Prévu?" ),
                },
                selection_mode="multi-row",
                hide_index=True,

                )


    