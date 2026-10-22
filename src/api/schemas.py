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
    """ Store Airport information """
    id:Optional[int]=Field( default=None, description="Unique internal airport identifier"),
    iata_code:Optional[str]=Field( default=None, description="Airpoert IATA Code"),
    icao_code: Optional[str]=Field( default=None, description="Airport ICAO Code"),
    airport_name: str=Field( default=None, description="Airport Name"),
    city: Optional[str] = Field( default=None, description="City of Airport"),
    country: Optional[str] = Field( default=None, description="Country ISO Code of Airport"),
    latitude: Optional[float] =Field( default=None, description="Airport Latitude"),
    longitude: Optional[float] =Field( default=None, description="Airport Longitude")


class Airline(BaseModel):
    """ Store Airline information """
    iata_code: str =Field( default=None, description="Airline IATA Code"),
    airline_name: str=Field( default=None, description="Airline Name"),
    icao_code:str=Field( default=None, description="ICAO Code")


class Flight(BaseModel):
    """ Store Flight response """
    flight_id: Optional[str] =Field( default=None, description="Unique internal flight identifier")
    flight_icao:Optional[str] =Field( default=None, description="Flight ICAO Code") 
    airline_icao:Optional[str] =Field( default=None, description="Airline ICAO Code")
    airline_name:Optional[str] =Field( default=None, description="Airline Name")
    flight_number:Optional[str] =Field( default=None, description="Flight Number"), 
    dep_icao:Optional[str] =Field( default=None, description="Departure Airport IATA Code")
    arr_icao:Optional[str] =Field( default=None, description="Arrival Airport IATA Code")
    arr_time:Optional[str] =Field( default=None, description="Arrival Time")
    dep_time:Optional[str] =Field( default=None, description="Departure Time")
    
class FlightSearch(BaseModel):
    airline_name: str | None = None
    airline_codes: List | None = None
    origin_airport: str | None = None
    destination_airport: str | None = None
    start_hour: int | None = None
    end_hour: int | None = None
    flight_date: str | None = None,
    limit:int = 100,
    offset:int=0

class StatsOut(BaseModel):
    """ Store Statistics """
    total_flights: int
    avg_departure_delay: float
    avg_arrival_delay: float
    delayed_flights_rate: float
    cancellation_rate: float
