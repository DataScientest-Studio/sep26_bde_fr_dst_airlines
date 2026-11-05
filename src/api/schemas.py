from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date, datetime



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

class FlightToPredict(BaseModel):
    """ Store flight to predict """
    airline_icao: str = Field(description="Airline ICAO Code")
    dep_icao: str = Field(description="Departure Airport ICAO Code")
    arr_icao: str = Field(description="Arrival Airport ICAO Code")
    flight_date: date = Field(description="Arrival date")
    # dep_time: str = Field(description="Scheduled departure time (HH:MM)")  # for departure weather, once UTC times are loaded
    arr_time: str = Field(description="Scheduled arrival time, Paris local time (HH:MM)")
    model_name: Optional[str] = Field(default=None, description="Model to use, empty for deployed model")



class FlightPrediction(BaseModel):
    """ Store prediction result """
    is_delayed: bool = Field(description="True if delay probability >= 0.5")
    delay_probability: float = Field(description="Probability of arrival delay > 15 min")
    model_name: str = Field(description="Model used for the prediction")

class ModelInfo(BaseModel):
    """ Store trained model information """
    model_name: str = Field(description="Model name (type_YYYYMMDD_HHMM)")
    model_type: str = Field(description="rf or xgb")
    trained_at: datetime = Field(description="Training date (UTC)")
    roc_auc: Optional[float] = Field(default=None, description="ROC AUC on test set")
    f1: Optional[float] = Field(default=None, description="F1 on delay class")
    precision: Optional[float] = Field(default=None, description="Precision on delay class")
    recall: Optional[float] = Field(default=None, description="Recall on delay class")
    online: bool = Field(description="True for the model used by the API")

class DelayStats(BaseModel):
    """ Store delay statistics of one group (arrival hour, airline or departure airport) """
    arr_hour_local: Optional[int] = Field(default=None, description="Scheduled arrival hour, Paris local time")
    airline_icao: Optional[str] = Field(default=None, description="Airline ICAO code")
    adep: Optional[str] = Field(default=None, description="Departure airport ICAO code")
    nb_flights: int = Field(description="Number of flights")
    nb_delayed: int = Field(description="Number of flights delayed (> 15 min)")
    delay_rate: float = Field(description="Share of delayed flights (0 to 1)")
    avg_delay_min: Optional[float] = Field(default=None, description="Average delay of delayed flights (minutes)")
