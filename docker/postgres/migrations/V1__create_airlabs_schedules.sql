CREATE SCHEMA IF NOT EXISTS raw;

GRANT ALL PRIVILEGES ON SCHEMA raw TO batch;
GRANT ALL PRIVILEGES ON SCHEMA raw TO herve;
GRANT ALL PRIVILEGES ON SCHEMA raw TO pascal;

CREATE TABLE IF NOT EXISTS raw.airlabs_schedules (
id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
airline_icao VARCHAR(10),
flight_icao VARCHAR(20),
flight_number VARCHAR(20),
dep_iata VARCHAR(10),
dep_time TIMESTAMPTZ,
arr_iata VARCHAR(10),
arr_time TIMESTAMPTZ,
arr_estimated TIMESTAMPTZ,
arr_actual TIMESTAMPTZ,
cs_flight_iata VARCHAR(20),
status VARCHAR(30),
duration INTEGER,
dep_delayed INTEGER,
arr_delayed INTEGER,
dep_estimated TIMESTAMPTZ,
dep_actual TIMESTAMPTZ,
source_file TEXT,
CONSTRAINT airlabs_schedules_unique_index UNIQUE (
airline_icao,
flight_number,
dep_iata,
dep_time,
arr_iata
)
);
