from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class FlightPredictionInput(BaseModel):
    airline_code: str = Field(..., example="AF", description="Code IATA de la compagnie")
    origin_airport: str = Field(..., example="CDG", description="Aéroport de départ")
    destination_airport: str = Field(..., example="JFK", description="Aéroport d'arrivée")
    month: int = Field(..., ge=1, le=12, example=7)
    day_of_week: int = Field(..., ge=1, le=7, example=5)
    scheduled_departure_hour: int = Field(..., ge=0, le=23, example=14)
    distance: float = Field(..., gt=0, example=5834.0)


class BatchPredictionInput(BaseModel):
    flights: List[FlightPredictionInput]


class PredictionOutput(BaseModel):
    predicted_delay_minutes: float
    is_delayed: bool
    delay_probability: Optional[float] = None


class BatchPredictionOutput(BaseModel):
    predictions: List[PredictionOutput]


class Airport(BaseModel):
    id:Optional[int]
    iata_code:Optional[str]
    icao_code: Optional[str]
    airport_name: str
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Airline(BaseModel):
    iata_code: str
    name: str
    icao_code:str


class Flight(BaseModel):
    flight_id: Optional[int] = None
    start_time: Optional[date] = None
    end_time: Optional[date] = None
    airline_icao: str
    flight_number: Optional[str] = None
    origin_airport: str
    destination_airport: str
    


class StatsOut(BaseModel):
    total_flights: int
    avg_departure_delay: float
    avg_arrival_delay: float
    delayed_flights_rate: float
    cancellation_rate: float
