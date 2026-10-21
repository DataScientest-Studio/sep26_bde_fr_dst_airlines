import streamlit as st
from src.frontend.api_client import api_client, cached_airlines, cached_airports


def render() -> None:
    st.title("🎯 Prédiction d'un vol")
    st.caption("Inférence en temps réel via l'endpoint FastAPI `POST /predict` (Modèle Scikit-Learn).")

    airlines = cached_airlines()
    airports = cached_airports()

    airline_options = [a["iata_code"] for a in airlines] if airlines else ["AF", "DL", "AA", "UA", "BA"]
    airport_options = [a["iata_code"] for a in airports] if airports else ["CDG", "JFK", "LHR", "ATL", "LAX", "ORD"]

    with st.form("single_flight_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            airline_code = st.selectbox("Compagnie aérienne (IATA)", options=airline_options)
            origin_airport = st.selectbox("Aéroport de départ", options=airport_options, index=0)
        with col2:
            destination_airport = st.selectbox(
                "Aéroport d'arrivée",
                options=airport_options,
                index=min(1, len(airport_options) - 1),
            )
            distance = st.number_input("Distance (km / miles)", min_value=50.0, max_value=20000.0, value=5834.0, step=50.0)
        with col3:
            month = st.slider("Mois du vol", min_value=1, max_value=12, value=7)
            day_of_week = st.slider("Jour de la semaine (1=Lun ... 7=Dim)", min_value=1, max_value=7, value=5)
            scheduled_departure_hour = st.slider("Heure de départ prévue (0-23h)", min_value=0, max_value=23, value=14)

        submitted = st.form_submit_button("🚀 Lancer la prédiction", use_container_width=True, type="primary")

    if submitted:
        payload = {
            "airline_code": airline_code,
            "origin_airport": origin_airport,
            "destination_airport": destination_airport,
            "month": int(month),
            "day_of_week": int(day_of_week),
            "scheduled_departure_hour": int(scheduled_departure_hour),
            "distance": float(distance),
        }
        try:
            with st.spinner("Appel à `/predict` en cours..."):
                result = api_client.predict_single(payload)

            st.subheader("Résultat de l'inférence")
            m1, m2, m3 = st.columns(3)
            is_delayed = result.get("is_delayed", False)
            delay_min = result.get("predicted_delay_minutes", 0.0)
            prob = result.get("delay_probability")

            m1.metric("Statut prédit", "⚠️ En retard" if is_delayed else "✅ À l'heure")
            m2.metric("Retard estimé (min)", f"{delay_min:.1f} min")
            m3.metric("Probabilité de retard", f"{prob * 100:.1f} %" if prob is not None else "N/A")

            if is_delayed:
                st.warning(f"Le modèle prévoit un retard d'environ **{delay_min:.1f} minutes** sur le vol {airline_code} ({origin_airport} → {destination_airport}).")
            else:
                st.success(f"Le vol {airline_code} ({origin_airport} → {destination_airport}) est prévu à l'heure.")
        except Exception as exc:
            st.error(f"Erreur lors de l'appel à `/predict` : {exc}")
