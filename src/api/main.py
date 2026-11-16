from contextlib import asynccontextmanager
from datetime import date,datetime
from typing import List, Optional
from fastapi import HTTPException
from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, bindparam
from sqlalchemy.orm import Session
import logging
import os
import re
import shutil

from api.config import settings
from api.database import get_db
from api.ml_model import ml_manager
from api.schemas import (
    Airline,
    Airport,
    BatchPredictionInput,
    BatchPredictionOutput,
    Flight,
    FlightPredictionInput,
    PredictionOutput,
    DelayStats,
    FlightSearch,
    ModelInfo
)
from api.security import verify_api_key

logger = logging.getLogger(__name__)


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
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)


@app.post("/predict", response_model=PredictionOutput, tags=["ML Inference"])
def predict_single_flight(payload: FlightPredictionInput):
    """Prédit le retard d'un vol unique avec le modèle Scikit-Learn."""
    return ml_manager.predict([payload])[0]



@app.post("/predict-batch", response_model=BatchPredictionOutput, tags=["ML Inference"])
def predict_batch_flights(payload: BatchPredictionInput):
    """Prédit les retards pour un lot de vols en une seule requête."""
    return BatchPredictionOutput(predictions=ml_manager.predict(payload.flights))


@app.post("/flights", response_model=List[Flight], tags=["Flights Data"])
def get_flights(
    search:FlightSearch,
    db: Session = Depends(get_db),
):

    """Récupère la liste des vols depuis PostgreSQL avec filtres."""
    if (
        (search.airline_name is None and not search.airline_codes)
        or search.destination_airport is None
        or search.origin_airport is None
        or search.flight_date is None
    ):
        raise HTTPException(
            status_code=422,
            detail="Paramètres obligatoires : airline_name ou airline_codes, origin_airport, destination_airport, flight_date.",
        )

    try:
        date_obj = datetime.strptime(search.flight_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=422, detail="flight_date doit être au format YYYY-MM-DD.")

    # Postgres EXTRACT(DOW) : dimanche = 0 ... samedi = 6
    dow = (date_obj.weekday() + 1) % 7

    code_cond = " AND (al.icao_code IN :airline_codes)" if search.airline_codes else ""
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

    params = {
        "airline_codes": search.airline_codes,
        "airline_name": f"%{search.airline_name}%" if search.airline_name else None,
        "origin_airport": search.origin_airport,
        "destination_airport": search.destination_airport,
        "start_hour": f"{search.start_hour:02d}:00" if search.start_hour is not None else None,
        "end_hour": f"{search.end_hour:02d}:00" if search.end_hour is not None else None,
        "limit": search.limit,
        "offset": search.offset,
        "dow": dow,
        "day": date_obj.day,
        "month": date_obj.month,
        "year": date_obj.year,
        "flight_date": search.flight_date,
    }
    stmt = text(query)
    if search.airline_codes:
        stmt = stmt.bindparams(bindparam("airline_codes", expanding=True))

    try:
        rows = db.execute(stmt, params).mappings().all()
        return [Flight(**row) for row in rows]
    except Exception:
        logger.exception("Erreur lors de la récupération des vols")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des vols.")


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
        logger.exception("Erreur lors de la récupération des aéroports")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des aéroports.")


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
        logger.exception("Erreur lors de la récupération des compagnies")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des compagnies.")


@app.get("/stats/hour", response_model=List[DelayStats], tags=["Analytics"])
def get_stats_hour(db: Session = Depends(get_db)):
    """Delay statistics per scheduled arrival hour (Paris local time)."""
    rows = db.execute(text("SELECT * FROM marts.mrt_delay_by_hour")).mappings().all()
    return [DelayStats(**row) for row in rows]


@app.get("/stats/airline", response_model=List[DelayStats], tags=["Analytics"])
def get_stats_airline(db: Session = Depends(get_db)):
    """Delay statistics per airline."""
    rows = db.execute(text("SELECT * FROM marts.mrt_delay_by_airline")).mappings().all()
    return [DelayStats(**row) for row in rows]


@app.get("/stats/airport", response_model=List[DelayStats], tags=["Analytics"])
def get_stats_airport(db: Session = Depends(get_db)):
    """Delay statistics per departure airport."""
    rows = db.execute(text("SELECT * FROM marts.mrt_delay_by_airport")).mappings().all()
    return [DelayStats(**row) for row in rows]

@app.get("/models", response_model=List[ModelInfo], tags=["ML Inference"])
def get_models(db: Session = Depends(get_db)):
    """Liste les modèles entraînés (ml.model_runs)."""
    query = """
        SELECT model_name, model_type, trained_at, roc_auc, f1, precision, recall, online
        FROM ml.model_runs
        ORDER BY trained_at DESC
    """
    rows = db.execute(text(query)).mappings().all()
    return [ModelInfo(**row) for row in rows]

@app.post("/models/{model_name}/deploy", tags=["ML Inference"])
def deploy_model(model_name: str, db: Session = Depends(get_db)):
    """Deploy a model from ml.model_runs and reload it in the API."""
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", model_name):
        raise HTTPException(status_code=422, detail="Nom de modèle invalide.")
    row = db.execute(
        text("SELECT model_name FROM ml.model_runs WHERE model_name = :name"),
        {"name": model_name},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Unknown model: {model_name}")

    models_dir = os.path.dirname(settings.MODEL_PATH)
    path = os.path.join(models_dir, f"{model_name}.joblib")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Model file not found: {path}")

    tmp = settings.MODEL_PATH + ".tmp"
    shutil.copy2(path, tmp)
    os.replace(tmp, settings.MODEL_PATH)

    db.execute(text("UPDATE ml.model_runs SET online = false WHERE online"))
    db.execute(
        text("UPDATE ml.model_runs SET online = true, deployed_at = now() WHERE model_name = :name"),
        {"name": model_name},
    )
    db.commit()

    ml_manager.load_model()
    return {"model_name": model_name, "online": True}
