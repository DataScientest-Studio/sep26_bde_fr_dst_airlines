from contextlib import asynccontextmanager
from datetime import date
from typing import List, Optional

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.config import settings
from src.api.database import get_db
from src.api.ml_model import ml_manager
from src.api.schemas import (
    Airline,
    Airport,
    BatchPredictionInput,
    BatchPredictionOutput,
    Flight,
    FlightPredictionInput,
    PredictionOutput,
    StatsOut,
)
from src.api.security import verify_api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    ml_manager.load_model()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API d'inférence ML (Scikit-Learn) et de requêtage PostgreSQL pour Streamlit",
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key)],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/predict", response_model=PredictionOutput, tags=["ML Inference"])
def predict_single_flight(payload: FlightPredictionInput):
    """Prédit le retard d'un vol unique avec le modèle Scikit-Learn."""
    return ml_manager.predict([payload])[0]


@app.post("/predict-batch", response_model=BatchPredictionOutput, tags=["ML Inference"])
def predict_batch_flights(payload: BatchPredictionInput):
    """Prédit les retards pour un lot de vols en une seule requête."""
    return BatchPredictionOutput(predictions=ml_manager.predict(payload.flights))


@app.get("/flight", response_model=List[Flight], tags=["Flights Data"])
def get_flights(
    airline_code: Optional[str] = Query(None),
    origin_airport: Optional[str] = Query(None),
    destination_airport: Optional[str] = Query(None),
    start_hour: Optional[int] = Query(None),
    end_hour: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Récupère la liste des vols depuis PostgreSQL avec filtres optionnels."""
    query = """
        SELECT
            flight_id,
            flight_icao, 
            airline_icao, 
            flight_number, 
            dep_iata, 
            arr_iata, 
            arr_time, 
            dep_time
        FROM silver.stg_flights
        WHERE (:airline_code IS NULL OR airline_icao = :airline_code)
          AND (:origin_airport IS NULL OR dep_iata = :origin_airport)
          AND (:destination_airport IS NULL OR arr_iata = :destination_airport)
          AND ((:start_hour IS NULL OR dep_time >= :start_time) OR (:end_hour IS NULL OR arr_time <= :end_time))
        ORDER BY dep_time DESC NULLS LAST
        LIMIT :limit OFFSET :offset
    """
    rows = db.execute(
        text(query),
        {
            "airline_code": airline_code,
            "origin_airport": origin_airport,
            "destination_airport": destination_airport,
            "start_hour": start_hour,
            "end_hour":end_hour,
            "limit": limit,
            "offset": offset,
        },
    ).mappings().all()
    return [Flight(**row) for row in rows]


@app.get("/airports", response_model=List[Airport], tags=["Reference Data"])
def get_airports(
    country: str = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Récupère les aéroports depuis PostgreSQL."""
    query = """
        SELECT 0 as id, iata_code,icao_code, name as airport_name,'' as city, country_code as country,lat as latitude,lng as longitude
        FROM raw.airlabs_airports
        WHERE (:search IS NULL
               OR iata_code ILIKE :pattern
               OR name ILIKE :pattern
               )
               AND (:country IS NULL OR country_code = :country)
               AND iata_code IS NOT NULL AND icao_code IS NOT NULL
        ORDER BY iata_code
    """
    pattern = f"%{search}%" if search else None
    rows = db.execute(text(query), {"search": search, "pattern": pattern, "country":country}).mappings().all()
    return [Airport(**row) for row in rows]


@app.get("/airlines", response_model=List[Airline], tags=["Reference Data"])
def get_airlines(search: Optional[str] = Query(None),db: Session = Depends(get_db)):
    """Récupère la liste des compagnies aériennes depuis PostgreSQL."""
    pattern = f"%{search}%" if search else None
    query = "SELECT iata_code, name, icao_code FROM raw.airlabs_airlines WHERE iata_code is not null and icao_code is not null AND (:search IS NULL OR name ILIKE :pattern) ORDER BY name"
    rows = db.execute(text(query),{"search": search, "pattern": pattern}).mappings().all()
    return [Airline(**row) for row in rows]


@app.get("/stats", response_model=StatsOut, tags=["Analytics"])
def get_stats(
    airline_code: Optional[str] = Query(None),
    origin_airport: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Calcule les statistiques agrégées des vols depuis PostgreSQL."""
    query = """
        SELECT
            COUNT(*) AS total_flights,
            COALESCE(AVG(departure_delay), 0.0) AS avg_departure_delay,
            COALESCE(AVG(arrival_delay), 0.0) AS avg_arrival_delay,
            COALESCE(AVG(CASE WHEN arrival_delay >= 15 THEN 1.0 ELSE 0.0 END), 0.0) AS delayed_flights_rate,
            COALESCE(AVG(CASE WHEN cancelled = TRUE THEN 1.0 ELSE 0.0 END), 0.0) AS cancellation_rate
        FROM silver.flights
        WHERE (:airline_code IS NULL OR airline_code = :airline_code)
          AND (:origin_airport IS NULL OR origin_airport = :origin_airport)
    """
    row = db.execute(
        text(query),
        {"airline_code": airline_code, "origin_airport": origin_airport},
    ).mappings().first()
    return StatsOut(**row)
