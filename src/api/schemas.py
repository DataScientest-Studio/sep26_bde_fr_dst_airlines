from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field



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
    airline_iata:Optional[str] =Field( default=None, description="Airline IATA Code")
    airline_name:Optional[str] =Field( default=None, description="Airline Name")
    flight_number:Optional[str] =Field( default=None, description="Flight Number"), 
    dep_icao:Optional[str] =Field( default=None, description="Departure Airport IATA Code")
    arr_icao:Optional[str] =Field( default=None, description="Arrival Airport IATA Code")
    arr_time:Optional[str] =Field( default=None, description="Arrival Time")
    dep_time:Optional[str] =Field( default=None, description="Departure Time")
    dep_iata:Optional[str] =Field( default=None, description="Departure Airport IATA Code")
    arr_iata:Optional[str] =Field( default=None, description="Arrival Airport IATA Code")
    dow:Optional[int] =Field(  description="Day of week")
    month:Optional[int]=Field(  description="Month of flight")
    day:Optional[int]=Field(  description="Day of flight")
    year:Optional[int]=Field(  description="Year of flight")
    flight_date:Optional[str] =Field( default=None, description="Departure Date of flight")
    dep_country:Optional[str] =Field( default=None, description="Country ISOCode of Departure airport")
    dep_lat:Optional[str] =Field( default=None, description="Latitude of departure Airport")
    dep_lng:Optional[str] =Field( default=None, description="Longitude of departure Airport")
    arr_country:Optional[str] =Field( default=None, description="Country ISOCode of Arrival airport")
    arr_lat:Optional[str] =Field( default=None, description="Latitude of arrival Airport")
    arr_lng:Optional[str] =Field( default=None, description="Longitude of arrival Airport")
    
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


class FlightPredictionInput(BaseModel):
    flight:Flight
    


class BatchPredictionInput(BaseModel):
    flights: List[FlightPredictionInput]


class PredictionOutput(BaseModel):
    predicted_delay_minutes: float
    is_delayed: bool
    delay_probability: Optional[float] = None


class BatchPredictionOutput(BaseModel):
    predictions: List[PredictionOutput]

