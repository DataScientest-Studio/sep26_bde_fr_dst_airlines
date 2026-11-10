-----------------------------------------
-- Initial Database structure
-----------------------------------------

-- ============================================================
-- Schémas (créés avant les droits qui les référencent)
-- ============================================================
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS ml;
CREATE SCHEMA IF NOT EXISTS temp;

-- ============================================================
-- Droits
-- ============================================================
GRANT ALL PRIVILEGES ON DATABASE airline TO batch, herve, pascal,airline_rw;
GRANT ALL PRIVILEGES ON DATABASE airflow TO herve, pascal;

GRANT ALL PRIVILEGES ON SCHEMA raw TO batch;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO batch, pascal;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw TO herve,airline_rw;

GRANT USAGE ON SCHEMA raw, silver, gold TO airline_rw;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA raw, silver, gold TO airline_rw;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA raw, silver, gold TO airline_rw;

-- Droits par défaut sur les futurs objets
ALTER DEFAULT PRIVILEGES IN SCHEMA raw, silver, gold, ml, marts, temp
  GRANT ALL PRIVILEGES ON TABLES TO airline_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE batch IN SCHEMA raw, silver, gold, ml, marts, temp
  GRANT ALL PRIVILEGES ON TABLES TO airline_rw;
ALTER DEFAULT PRIVILEGES FOR ROLE batch IN SCHEMA raw, silver, gold, ml, marts, temp
  GRANT ALL PRIVILEGES ON SEQUENCES TO airline_rw;

GRANT airline_rw TO airflow, herve, pascal, batch;


--
-- RAW Schema
--

-- raw.airlabs_airlines definition
CREATE TABLE raw.airlabs_airlines (
	"name" text NULL,
	iata_code text NULL,
	icao_code text NULL
);


-- raw.airlabs_airports definition
CREATE TABLE raw.airlabs_airports (
	"name" text NULL,
	iata_code text NULL,
	icao_code text NULL,
	lat text NULL,
	lng text NULL,
	country_code text NULL
);


-- raw.airlabs_schedules definition
CREATE TABLE raw.airlabs_schedules (
	id int8 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE) NOT NULL,
	airline_icao varchar(10) NULL,
	flight_icao varchar(20) NULL,
	flight_number varchar(20) NULL,
	dep_iata varchar(10) NULL,
	dep_time timestamptz NULL,
	arr_iata varchar(10) NULL,
	arr_time timestamptz NULL,
	arr_estimated timestamptz NULL,
	arr_actual timestamptz NULL,
	cs_flight_iata varchar(20) NULL,
	status varchar(30) NULL,
	duration int4 NULL,
	dep_delayed int4 NULL,
	arr_delayed int4 NULL,
	dep_estimated timestamptz NULL,
	dep_actual timestamptz NULL,
	source_file text NULL,
	arr_icao varchar(4) NULL,
	dep_icao varchar(4) NULL,
	dep_time_utc timestamp NULL,
	arr_time_utc timestamp NULL,
	dep_actual_utc timestamp NULL,
	arr_actual_utc timestamp NULL,
	CONSTRAINT airlabs_schedules_id_not_null NOT NULL id,
	CONSTRAINT airlabs_schedules_pkey PRIMARY KEY (id),
	CONSTRAINT airlabs_schedules_unique_index UNIQUE (airline_icao, flight_number, dep_iata, dep_time, arr_iata)
);
CREATE INDEX airlabs_schedules_airline_icao_idx ON raw.airlabs_schedules USING btree (airline_icao);
CREATE INDEX airlabs_schedules_flight_icao_idx ON raw.airlabs_schedules USING btree (flight_icao);


-- raw.airport_corrections definition
CREATE TABLE raw.airport_corrections (
	old_icao text NULL,
	new_icao text NULL,
	reason text NULL
);


-- raw.airports definition
CREATE TABLE raw.airports (
	id int4 NULL,
	ident text NULL,
	"type" text NULL,
	"name" text NULL,
	latitude_deg float8 NULL,
	longitude_deg float8 NULL,
	elevation_ft int4 NULL,
	continent text NULL,
	iso_country text NULL,
	iso_region text NULL,
	municipality text NULL,
	scheduled_service text NULL,
	icao_code text NULL,
	iata_code text NULL,
	gps_code text NULL,
	local_code text NULL,
	home_link text NULL,
	wikipedia_link text NULL,
	keywords text NULL
);


-- raw.excluded_dates definition
CREATE TABLE raw.excluded_dates (
	excluded_date date NOT NULL PRIMARY KEY
);


-- raw.icao_corrections definition
CREATE TABLE raw.icao_corrections (
	old_icao text NULL,
	new_icao text NULL,
	CONSTRAINT icao_corrections_pkey PRIMARY KEY (old_icao, new_icao)
);


-- raw.meteo_hourly definition
CREATE TABLE raw.meteo_hourly (
	"time" timestamptz NULL,
	temperature_2m float8 NULL,
	dew_point_2m float8 NULL,
	relative_humidity_2m int8 NULL,
	pressure_msl float8 NULL,
	cloud_cover int8 NULL,
	cloud_cover_low int8 NULL,
	cloud_cover_mid int8 NULL,
	cloud_cover_high int8 NULL,
	wind_speed_10m float8 NULL,
	wind_direction_10m int8 NULL,
	wind_gusts_10m float8 NULL,
	precipitation float8 NULL,
	rain float8 NULL,
	snowfall float8 NULL,
	weather_code int8 NULL,
	icao text NULL
);
CREATE UNIQUE INDEX ux_meteo_hourly_icao_time ON raw.meteo_hourly USING btree (icao, "time");


-- raw.weather_codes definition
CREATE TABLE raw.weather_codes (
	code int4 NULL,
	wmo4677 text NULL
);


-- raw.wiki_airline_types definition
CREATE TABLE raw.wiki_airline_types (
	airline_name text NULL,
	icao text NULL,
	wikidata_type text NULL
);

-- Insert Weather codes
INSERT INTO raw.weather_codes (code,wmo4677) VALUES
	 (0,'Cloud development not observed or not observable'),
	 (1,'Clouds generally dissolving or becoming less developed'),
	 (2,'State of sky on the whole unchanged'),
	 (3,'Clouds generally forming or developing'),
	 (4,'Visibility reduced by smoke, e.g. veldt or forest fires, industrial smoke or volcanic ashes'),
	 (5,'Haze'),
	 (6,'Widespread dust in suspension in the air, not raised by wind at or near the station at the time of observation'),
	 (7,'Dust or sand raised by wind at or near the station at the time of observation, but no well developed dust whirl(s) or sand whirl(s), and no duststorm or sandstorm seen'),
	 (8,'Well developed dust whirl(s) or sand whirl(s) seen at or near the station during the preceding hour or at the time of observation, but no duststorm or sandstorm'),
	 (9,'Duststorm or sandstorm within sight at the time of observation, or at the station during the preceding hour'),
	 (10,'Mist'),
	 (11,'Patches - shallow fog or ice fog at the station, not deeper than about 2 metres on land or 10 metres at sea'),
	 (12,'More or less continuous - shallow fog or ice fog at the station'),
	 (13,'Lightning visible, no thunder heard'),
	 (14,'Precipitation within sight, not reaching the ground or the surface of the sea'),
	 (15,'Precipitation within sight, reaching the ground or the surface of the sea, but distant (more than 5 km from the station)'),
	 (16,'Precipitation within sight, reaching the ground or the surface of the sea, near to, but not at the station'),
	 (17,'Thunderstorm, but no precipitation at the time of observation'),
	 (18,'Squalls - at or within sight of the station during the preceding hour or at the time of observation'),
	 (19,'Funnel cloud(s)'),
	 (20,'Drizzle (not freezing) or snow grains - not falling as shower(s) - preceding hour'),
	 (21,'Rain (not freezing) - preceding hour'),
	 (22,'Snow - preceding hour'),
	 (23,'Rain and snow or ice pellets - preceding hour'),
	 (24,'Freezing drizzle or freezing rain - preceding hour'),
	 (25,'Shower(s) of rain - preceding hour'),
	 (26,'Shower(s) of snow, or of rain and snow - preceding hour'),
	 (27,'Shower(s) of hail, or of rain and hail - preceding hour'),
	 (28,'Fog or ice fog - preceding hour'),
	 (29,'Thunderstorm (with or without precipitation) - preceding hour'),
	 (30,'Slight or moderate duststorm or sandstorm - has decreased during the preceding hour'),
	 (31,'Slight or moderate duststorm or sandstorm - no appreciable change during the preceding hour'),
	 (32,'Slight or moderate duststorm or sandstorm - has begun or has increased during the preceding hour'),
	 (33,'Severe duststorm or sandstorm - has decreased during the preceding hour'),
	 (34,'Severe duststorm or sandstorm - no appreciable change during the preceding hour'),
	 (35,'Severe duststorm or sandstorm - has begun or has increased during the preceding hour'),
	 (36,'Slight or moderate blowing snow - generally low (below eye level)'),
	 (37,'Heavy drifting snow - generally low (below eye level)'),
	 (38,'Slight or moderate blowing snow - generally high (above eye level)'),
	 (39,'Heavy drifting snow - generally high (above eye level)'),
	 (40,'Fog or ice fog at a distance at the time of observation, but not at the station during the preceding hour'),
	 (41,'Fog or ice fog in patches'),
	 (42,'Fog or ice fog, sky visible - has become thinner during the preceding hour'),
	 (43,'Fog or ice fog, sky invisible - has become thinner during the preceding hour'),
	 (44,'Fog or ice fog, sky visible - no appreciable change during the preceding hour'),
	 (45,'Fog or ice fog, sky invisible - no appreciable change during the preceding hour'),
	 (46,'Fog or ice fog, sky visible - has begun or has become thicker during the preceding hour'),
	 (47,'Fog or ice fog, sky invisible - has begun or has become thicker during the preceding hour'),
	 (48,'Fog, depositing rime, sky visible'),
	 (49,'Fog, depositing rime, sky invisible');
INSERT INTO raw.weather_codes (code,wmo4677) VALUES
	 (50,'Drizzle, not freezing, intermittent - slight at time of observation'),
	 (51,'Drizzle, not freezing, continuous - slight at time of observation'),
	 (52,'Drizzle, not freezing, intermittent - moderate at time of observation'),
	 (53,'Drizzle, not freezing, continuous - moderate at time of observation'),
	 (54,'Drizzle, not freezing, intermittent - heavy (dense) at time of observation'),
	 (55,'Drizzle, not freezing, continuous - heavy (dense) at time of observation'),
	 (56,'Drizzle, freezing, slight'),
	 (57,'Drizzle, freezing, moderate or heavy (dense)'),
	 (58,'Drizzle and rain, slight'),
	 (59,'Drizzle and rain, moderate or heavy'),
	 (60,'Rain, not freezing, intermittent - slight at time of observation'),
	 (61,'Rain, not freezing, continuous - slight at time of observation'),
	 (62,'Rain, not freezing, intermittent - moderate at time of observation'),
	 (63,'Rain, not freezing, continuous - moderate at time of observation'),
	 (64,'Rain, not freezing, intermittent - heavy at time of observation'),
	 (65,'Rain, not freezing, continuous - heavy at time of observation'),
	 (66,'Rain, freezing, slight'),
	 (67,'Rain, freezing, moderate or heavy (dense)'),
	 (68,'Rain or drizzle and snow, slight'),
	 (69,'Rain or drizzle and snow, moderate or heavy'),
	 (70,'Intermittent fall of snowflakes - slight at time of observation'),
	 (71,'Continuous fall of snowflakes - slight at time of observation'),
	 (72,'Intermittent fall of snowflakes - moderate at time of observation'),
	 (73,'Continuous fall of snowflakes - moderate at time of observation'),
	 (74,'Intermittent fall of snowflakes - heavy at time of observation'),
	 (75,'Continuous fall of snowflakes - heavy at time of observation'),
	 (76,'Diamond dust (with or without fog)'),
	 (77,'Snow grains (with or without fog)'),
	 (78,'Isolated star-like snow crystals (with or without fog)'),
	 (79,'Ice pellets'),
	 (80,'Rain shower(s), slight'),
	 (81,'Rain shower(s), moderate or heavy'),
	 (82,'Rain shower(s), violent'),
	 (83,'Shower(s) of rain and snow mixed, slight'),
	 (84,'Shower(s) of rain and snow mixed, moderate or heavy'),
	 (85,'Snow shower(s), slight'),
	 (86,'Snow shower(s), moderate or heavy'),
	 (87,'Shower(s) of snow pellets or small hail, with or without rain or rain and snow mixed - slight'),
	 (88,'Shower(s) of snow pellets or small hail, with or without rain or rain and snow mixed - moderate or heavy'),
	 (89,'Shower(s) of hail, with or without rain or rain and snow mixed, not associated with thunder - slight'),
	 (90,'Shower(s) of hail, with or without rain or rain and snow mixed, not associated with thunder - moderate or heavy'),
	 (91,'Slight rain at time of observation - thunderstorm during the preceding hour but not at time of observation'),
	 (92,'Moderate or heavy rain at time of observation - thunderstorm during the preceding hour but not at time of observation'),
	 (93,'Slight snow, or rain and snow mixed or hail at time of observation - thunderstorm during the preceding hour but not at time of observation'),
	 (94,'Moderate or heavy snow, or rain and snow mixed or hail at time of observation - thunderstorm during the preceding hour but not at time of observation'),
	 (95,'Thunderstorm, slight or moderate, without hail but with rain and/or snow at time of observation'),
	 (96,'Thunderstorm, slight or moderate, with hail at time of observation'),
	 (97,'Thunderstorm, heavy, without hail but with rain and/or snow at time of observation'),
	 (98,'Thunderstorm combined with duststorm or sandstorm at time of observation'),
	 (99,'Thunderstorm, heavy, with hail at time of observation');

--
-- Silver
--

-- Toutes les table sont gérées par DBT à partir de Raw


--
-- Gold
--

-- Toutes les table sont gérées par DBT à partir de Silver

--
-- Silver
--

-- Toutes les table sont gérées par DBT à partir de Raw


--
-- Marts : Utilisé pour l'entrainement des modèles
--

-- Toutes les table sont gérées par DBT à partir de Gold


--
-- ML : Information sur les modèles
--

-- ml.model_runs definition
-- ml.model_runs definition

-- Drop table

-- DROP TABLE ml.model_runs;

CREATE TABLE ml.model_runs (
	model_name varchar NOT NULL,
	model_type varchar NOT NULL,
	trained_at timestamptz NOT NULL,
	train_rows int4 NULL,
	test_rows int4 NULL,
	train_days int4 NULL,
	test_days int4 NULL,
	train_delay_rate float8 NULL,
	test_delay_rate float8 NULL,
	tp int4 NULL,
	fp int4 NULL,
	tn int4 NULL,
	fn int4 NULL,
	"precision" float8 NULL,
	recall float8 NULL,
	f1 float8 NULL,
	roc_auc float8 NULL,
	training_seconds float8 NULL,
	model_path varchar NULL,
	deployed_at timestamptz NULL,
	online bool DEFAULT false NOT NULL,
	CONSTRAINT model_runs_model_name_not_null NOT NULL model_name,
	CONSTRAINT model_runs_model_type_not_null NOT NULL model_type,
	CONSTRAINT model_runs_online_not_null NOT NULL online,
	CONSTRAINT model_runs_pkey PRIMARY KEY (model_name),
	CONSTRAINT model_runs_trained_at_not_null NOT NULL trained_at
);

--
-- Temp : Schema pour recevoir les tables temporaires
--