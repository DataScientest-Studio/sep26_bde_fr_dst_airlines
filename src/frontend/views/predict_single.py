import streamlit as st
from src.frontend.api_client import api_client, cached_airlines, cached_airports
from datetime import date,datetime, timedelta
import pandas as pd
def render() -> None:
    st.title("🎯 Prédiction d'un vol")
    st.caption("Inférence en temps réel via l'endpoint FastAPI `POST /predict` (Modèle Scikit-Learn).")

    airlines = cached_airlines()
    origine_airports = cached_airports()
    dest_airports = list(filter(lambda x: x["iata_code"] in ("BVA","CDG","ORY") ,origine_airports))


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
                df = df.sort_values("dep_time")
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
                st.subheader(f"{len(result)} Vol(s) Trouvés - {origin_airport['airport_name']} -> {destination_airport['airport_name']}")
                st.dataframe(df, column_config={
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
    },
    hide_index=True)
            
            # st.subheader("Résultat de l'inférence")
            # m1, m2, m3 = st.columns(3)
            # is_delayed = result.get("is_delayed", False)
            # delay_min = result.get("predicted_delay_minutes", 0.0)
            # prob = result.get("delay_probability")

            # m1.metric("Statut prédit", "⚠️ En retard" if is_delayed else "✅ À l'heure")
            # m2.metric("Retard estimé (min)", f"{delay_min:.1f} min")
            # m3.metric("Probabilité de retard", f"{prob * 100:.1f} %" if prob is not None else "N/A")

            # if is_delayed:
            #     st.warning(f"Le modèle prévoit un retard d'environ **{delay_min:.1f} minutes** sur le vol {airline_code} ({origin_airport} → {destination_airport}).")
            # else:
            #     st.success(f"Le vol {airline_code} ({origin_airport} → {destination_airport}) est prévu à l'heure.")
        except Exception as exc:
            st.error(f"Erreur lors de l'appel à `/flights` : {exc}")
