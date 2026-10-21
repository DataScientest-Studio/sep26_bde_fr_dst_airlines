from typing import Any, Dict, List, Optional
import requests
import streamlit as st
from src.frontend.config import API_KEY, API_URL


class APIClient:
    """Client HTTP pour interroger l'API FastAPI sécurisée par X-API-Key."""

    def __init__(self, base_url: str = API_URL, api_key: str = API_KEY) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        resp = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            params={k: v for k, v in (params or {}).items() if v is not None and v != ""},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Any:
        resp = requests.post(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def predict_single(self, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/predict", flight_data)

    def predict_batch(self, flights: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self._post("/predict-batch", {"flights": flights})

    def get_flights(
        self,
        airline_code: Optional[str] = None,
        origin_airport: Optional[str] = None,
        destination_airport: Optional[str] = None,
        flight_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        return self._get(
            "/flight",
            params={
                "airline_code": airline_code,
                "origin_airport": origin_airport,
                "destination_airport": destination_airport,
                "flight_date": flight_date,
                "limit": limit,
                "offset": offset,
            },
        )

    def get_airports(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._get("/airports", params={"search": search})

    def get_airlines(self) -> List[Dict[str, Any]]:
        return self._get("/airlines")

    def get_stats(
        self,
        airline_code: Optional[str] = None,
        origin_airport: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._get(
            "/stats",
            params={"airline_code": airline_code, "origin_airport": origin_airport},
        )


api_client = APIClient()


@st.cache_data(ttl=300, show_spinner=False)
def cached_airlines() -> List[Dict[str, Any]]:
    try:
        return api_client.get_airlines()
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def cached_airports() -> List[Dict[str, Any]]:
    try:
        return api_client.get_airports()
    except Exception:
        return []
