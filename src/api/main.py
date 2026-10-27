from contextlib import asynccontextmanager
from datetime import date,datetime
from typing import List, Optional
from fastapi import HTTPException
from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, bindparam
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
    FlightSearch
)
from src.api.security import verify_api_key
import random


# Charge le model en cache au demarrage de l'API
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
def predict_single_flight(payload: FlightPredictionInput,
                    db: Session = Depends(get_db),):
    """Prédit le retard d'un vol unique avec le modèle Scikit-Learn."""
    #return ml_manager.predict([payload])[0]
    retard=random.random() > 0.8
    r = PredictionOutput(predicted_delay_minutes=random.random()*30 if retard else 0, is_delayed=retard, delay_probability=random.random() if retard else 1)
    return r


@app.post("/predict-batch", response_model=BatchPredictionOutput, tags=["ML Inference"])
def predict_batch_flights(payload: BatchPredictionInput):
    """Prédit les retards pour un lot de vols en une seule requête."""
    return BatchPredictionOutput(predictions=ml_manager.predict(payload.flights))


@app.post("/flights", response_model=List[Flight], tags=["Flights Data"])
def get_flights(
    search:FlightSearch,
    db: Session = Depends(get_db),
):

    """  Récupère la liste des vols depuis PostgreSQL avec filtres optionnels."""
    try:
        if search.flight_date:
            date_obj = datetime.strptime(search.flight_date,"%Y-%m-%d" ).date()

            dow = (date_obj.weekday() + 1) % 8  # Start Sunday
            day = date_obj.day
            month = date_obj.month
            year= date_obj.year

        if search.airline_codes is not None and len(search.airline_codes)>0:
            code_cond = " AND (al.icao_code IN :airline_codes)"
        else:
            code_cond =''
        query = f"""
            SELECT
                f.flight_id,
                f.flight_icao, 
                al.icao_code as airline_icao, 
                al.iata_code AS airline_iata,
                al.airline_name,
                f.flight_number, 
                da.icao_code as dep_icao, 
                aa.icao_code as arr_icao, 
                da.iata_code as dep_iata, 
                aa.iata_code as arr_iata, 
                f.dep_time,
                f.arr_time,
                f.dow,
                :day as day,
                :month as month,
                :year as year,
                :flight_date as flight_date,
                da.country_code AS dep_country,
                da.lat AS dep_lat,
                da.lng as dep_lng,
                aa.country_code AS arr_country,
                aa.lat  AS arr_lat,
                aa.lng  AS arr_lng
            FROM gold.dim_flights f
            INNER JOIN gold.dim_airlines al ON f.airline_id=al.airline_id
            INNER JOIN gold.dim_airports da ON f.dep_airport_id=da.airport_id
            INNER JOIN gold.dim_airports aa ON f.arr_airport_id=aa.airport_id
            WHERE (:airline_name IS NULL OR al.airline_name ILIKE :airline_name)
            AND (:origin_airport IS NULL OR da.iata_code = :origin_airport)
            AND (:destination_airport IS NULL OR aa.iata_code  = :destination_airport)
            AND ((:start_hour IS NULL OR dep_time >= :start_hour) AND (:end_hour IS NULL OR dep_time < :end_hour))
            AND (:dow IS NULL OR dow = :dow)
            {code_cond}
            ORDER BY dep_time DESC NULLS LAST
            LIMIT :limit OFFSET :offset
        """

        if (search.airline_name is None and search.airline_codes is None) or search.destination_airport is None or search.origin_airport is None or search.flight_date is None : raise HTTPException("Manque un paramètre obligatoire")

        params = {
                        "airline_codes": search.airline_codes if search.airline_codes is not None else None,
                        "airline_name": f"'%{search.airline_name}%'" if search.airline_name else None,
                        "origin_airport": search.origin_airport,
                        "destination_airport": search.destination_airport,
                        "start_hour": f"{search.start_hour:02d}:00",
                        "end_hour":f"{search.end_hour:02d}:00",
                        "limit": search.limit,
                        "offset": search.offset,
                        "dow":dow,
                        "day":day,
                        "month":month,
                        "year":year,
                        "flight_date":search.flight_date
                    }
        stmt = text(query)
        if search.airline_codes:
            stmt = stmt.bindparams(
                bindparam("airline_codes", expanding=True)
            )
        rows = db.execute(
            stmt,
            params
        ).mappings().all()
        data=[Flight(**row) for row in rows]
        return data
    except Exception as e:
        print(e.message)
        raise HTTPException(f"Error getting Flights : {e}")


@app.get("/airports", response_model=List[Airport], tags=["Reference Data"])
def get_airports(
    country: str = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Récupère les aéroports depuis PostgreSQL."""
    try:
        query = """
            SELECT 0 as id, iata_code,icao_code, airport_name,'' as city, country_code as country,lat as latitude,lng as longitude
            FROM gold.dim_airports
            WHERE (:search IS NULL
                OR iata_code ILIKE :pattern
                OR airport_name ILIKE :pattern
                )
                AND (:country IS NULL OR country_code = :country)
                AND iata_code IS NOT NULL AND icao_code IS NOT NULL
            ORDER BY iata_code
        """
        pattern = f"%{search}%" if search else None
        rows = db.execute(text(query), {"search": search, "pattern": pattern, "country":country}).mappings().all()
        return [Airport(**row) for row in rows]
    except Exception as e:
        raise HTTPException(detail=f"Error getting Airports : {e}")


@app.get("/airlines", response_model=List[Airline], tags=["Reference Data"])
def get_airlines(search: Optional[str] = Query(None),db: Session = Depends(get_db)):
    """Récupère la liste des compagnies aériennes depuis PostgreSQL."""
    try:
        pattern = f"%{search}%" if search else None
        query = """SELECT iata_code, airline_name, icao_code 
                    FROM gold.dim_airlines 
                    WHERE iata_code is not null and icao_code is not null 
                    AND (:search IS NULL OR airline_name ILIKE :pattern) ORDER BY airline_name"""
        rows = db.execute(text(query),{"search": search, "pattern": pattern}).mappings().all()
        return [Airline(**row) for row in rows]
    except Exception as e:
        raise HTTPException(detail=f"Error getting Airlines : {e}")


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
