import streamlit as st
from src.frontend.api_client import api_client, cached_airlines, cached_airports
from datetime import date,datetime, timedelta
import pandas as pd
import json
def render() -> None:

    st.title("🎯 Prédiction d'un vol")
    st.caption(
        "Inférence en temps réel via l'endpoint FastAPI `POST /predict` "
        "(Modèle Scikit-Learn)."
    )

    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame()

    airlines = cached_airlines()
    origine_airports = cached_airports()

    dest_airports = [
        x for x in origine_airports
        if x["iata_code"] in ("BVA", "CDG", "ORY")
    ]

    with st.form("single_flight_form"):

        col1, col2, col3 = st.columns(3)

        with col1:
            origin_airport = st.selectbox(
                "Aéroport de départ",
                options=origine_airports,
                format_func=lambda x: (
                    f"{x['iata_code']} - {x['airport_name']}"
                )
            )

            airline_codes = st.multiselect(
                "Compagnie aérienne",
                options=airlines,
                format_func=lambda x: x["airline_name"]
            )

        with col2:
            destination_airport = st.selectbox(
                "Aéroport d'arrivée",
                options=dest_airports,
                index=min(1, len(dest_airports) - 1),
                format_func=lambda x: (
                    f"{x['iata_code']} - {x['airport_name']}"
                )
            )

        with col3:
            date_vol = st.date_input(
                "Date du vol",
                min_value=date.today(),
                max_value=date.today() + timedelta(days=14)
            )

            start_hour, end_hour = st.slider(
                "Heure de départ prévue",
                min_value=0,
                max_value=23,
                value=(8, 17)
            )

        submitted = st.form_submit_button(
            "🚀 Lancer la recherche des vols",
            type="primary",
            use_container_width=True
        )

    if submitted:

        try:

            with st.spinner("Recherche des vols..."):

                result = api_client.get_flights(
                    airline_codes=[
                        x["icao_code"]
                        for x in airline_codes
                    ],
                    origin_airport=origin_airport["iata_code"],
                    destination_airport=destination_airport["iata_code"],
                    flight_date=date_vol.isoformat(),
                    start_hour=start_hour,
                    end_hour=end_hour
                )

                df = pd.DataFrame(result)

                if not df.empty:

                    df = df.sort_values("dep_time")

                    df["selected"] = False
                    df["retard"] = ""

                    df = df[
                        [
                            "selected",
                            "flight_id",
                            "flight_icao",
                            "airline_name",
                            "flight_number",
                            "dep_icao",
                            "arr_icao",
                            "dep_time",
                            "arr_time",
                            "retard",
                            "airline_icao",
                            "airline_iata",
                            "dep_iata",
                            "arr_iata",
                            "dow",
                            "month",
                            "day",
                            "year",
                            "flight_date",
                            "dep_country",
                            "dep_lat",
                            "dep_lng",
                            "arr_country",
                            "arr_lat",
                            "arr_lng"
                        ]
                    ]

                st.session_state.df = df

        except Exception as exc:
            st.error(
                f"Erreur lors de l'appel à /flights : {exc}"
            )

    # affichage permanent du tableau
    if not st.session_state.df.empty:

        st.subheader(
            f"{len(st.session_state.df)} vol(s) trouvé(s)"
        )
        st.badge("Selectionnez les vols et cliquer sur le bouton situé sous la liste")
        edited_df = st.data_editor(
            st.session_state.df,
            hide_index=True,
            column_config={
                "selected": st.column_config.CheckboxColumn(
                    "Sélection"
                ),
                "flight_icao": st.column_config.TextColumn("Vol"),
                "airline_name": st.column_config.TextColumn(
                    "Compagnie"
                ),
                "dep_time": st.column_config.TextColumn(
                    "Départ"
                ),
                "arr_time": st.column_config.TextColumn(
                    "Arrivée"
                ),
                "retard": st.column_config.TextColumn(
                    "Retard prévu ?"
                ),
                "flight_id":None,
                "airline_icao":None,
                "airline_iata":None,
                "dep_icao":None,
                "arr_icao":None,
                "dep_iata":None,
                "arr_iata":None,
                "dow":None,
                "month":None,
                "day":None,
                "year":None,
                "flight_date":None,
                "dep_country":None,
                "dep_lat":None,
                "dep_lng":None,
                "arr_country":None,
                "arr_lat":None,
                "arr_lng":None
            },
            disabled=[
                "flight_icao",
                "airline_name",
                "flight_number",
                "dep_icao",
                "arr_icao",
                "dep_time",
                "arr_time",
                "retard",
            ],
        )

        selected_rows = edited_df[
            edited_df["selected"]
        ]

        if not selected_rows.empty:

            if st.button(
                f"Estimer le retard ({len(selected_rows)} vol(s))"
            ):

                with st.spinner("Prédiction..."):
                    payload = {
                        "flights": []
                    }
                    resp=""
                    for idx, row in selected_rows.iterrows():
                        try:
                            data = row

                            flight = data.drop(
                                ["selected", "retard"],
                                errors="ignore"
                            ).to_dict()

                            payload={
                                "flight": flight
                            }


                            response = api_client.predict_single(
                                payload
                            )
                            prediction = f"Retard prévu ({round(response["delay_probability"]*100)}%)" if response["is_delayed"] else "A L'heure"

                            st.session_state.df.loc[
                                idx,
                                "retard"
                            ] = prediction
                        except Exception as e:
                            st.session_state.df.loc[
                                idx,
                                "retard"
                            ] = f"ERROR {e}"+ resp

                st.rerun()
    else:
        st.subheader(
                    f"Aucun vol trouvé"
                )