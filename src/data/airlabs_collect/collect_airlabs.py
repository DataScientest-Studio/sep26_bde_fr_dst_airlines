import csv
import json
import os
from datetime import datetime
import time
import requests
import argparse
from google.cloud import storage
import re
import tempfile

class Airport:
    def __init__(self, item):
        self.desc = item["desc"]
        self.url=item["url"]
        self.params = item["params"]
        self.pattern = item["pattern"]



def get_api_key(api_keys_file)->tuple:
    """ Read Key files and select first which is not expired 
        @param api_keys_file : Path to json file with list of available keys
    """
    with open(api_keys_file, 'r') as fd:
        api_keys = json.load(fd)
        

    for item in api_keys:
        name = item["name"]
        key=item["key"]
        r = requests.get("https://airlabs.co/api/v9/ping",  params={"api_key": key},  timeout=30)
        if r.ok:
            content= r.json()
            if "request" in content:
                restant = content["request"]["key"]["limits_total"]
                return name,key, restant
    return None

def read_airports(api_key:str, airport_file)->list:
    """ Read List of Airport to collect with API information
        @param api_key : API Key to use
        @param airport_file : File containing list of Airports
    """
    with open(airport_file, 'r') as fd:
        airports_json = json.load(fd)
    airports=[]
    for airport_json in airports_json:
        # Get Airport object from json or airport item
        airport = Airport(airport_json)
        # Put API Key
        for p in airport.params:
            if isinstance(airport.params[p], str):
                airport.params[p] = airport.params[p].replace("{API_KEY}", api_key)
        # Add airport
        airports.append(airport)
    return airports



def uploader_gcs(local_path, bucket_name, blob_name, key_file):
    """ Upload a file to GCP Storage Bucket 
        @param local_path : Local File/Temp file
        @param bucket_name : Name of Bucket
        @param blob_name : Name and path of file
        @param key_file : File with Google Credentials
    """
    #client = storage.Client()
    client = storage.Client.from_service_account_json(key_file)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.upload_from_filename(local_path)

    print(f"Upload : gs://{bucket_name}/{blob_name}")



def collect_data(airport:Airport):
    """ Collect data for one airport (Chunk using pagination)
        @param airport : Airport object to collect
        @return All Data collected for the airport 
    """
    all_data = []
    offset = 0
    url=airport.url
    params=airport.params

    while True:
        params_page = params.copy()
        params_page["offset"] = offset

        print(f"  Query offset={offset}")

        # 1 appel initial + 2 retries
        for trycount in range(3):
            try:
                response = requests.get( url,  params=params_page, timeout=120)
                response.raise_for_status()
                data = response.json()
                break
            
            except (requests.RequestException, ValueError) as e:
                if trycount == 2:
                    print(f" Failed after 2 retries : {e}")
                    raise
            
                print(
                f" Error : {e}"
                f" - retry {trycount + 1}/2 in 10 secondes..."
                )
                time.sleep(10)

        # Données de la page courante
        results = data.get("response", [])

        if not isinstance(results, list):
            raise ValueError("'response' is not a Json Array")

        # Keep only landed
        landed = [
            flight for flight in results
            if flight.get("status") == "landed"
            ]

        all_data.extend(landed)

        # pagination
        request_info = data.get("request", {})

        has_more = request_info.get("has_more", False)
        total_items = request_info.get("total_items")

        print(
            f"    {len(results)} flights collected"
            f" | get={len(all_data)}"
            f" | total={total_items}"
            f" | has_more={has_more}"
        )

        if not has_more:
            break

        # Offset is page number so increase of 1
        offset += 1   

        # Security against infinite loop
        if not results:
            print("  ATTENTION: has_more=true but no result.")
            break
        
        time.sleep(10) # sleep 15 secondes between 2 calls

    print(
        f"  Finished : {len(all_data)} flight(s) collected"
    )

    return all_data

def save_csv(rows, filename, local_folder):
    """ Save Data in a CSV 
        @param rows : Rows to write
        @param filename : Path to output file
    """
    if not rows:
        print(f"No data for {filename}")
        return None

    if local_folder:
        os.makedirs(local_folder, exist_ok=True)

        path = os.path.join(local_folder, filename)
        istemp=False
        exists = os.path.exists(path)
    else:
        path = tempfile.NamedTemporaryFile().name
        istemp=True
        exists=False

    # Union all columns
    columns = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)

    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=columns,
            extrasaction="ignore"
        )

        if not exists:
            writer.writeheader()

        for row in rows:
            # Convert nested structures if necesary
            clean_row = {
                key: json.dumps(value, ensure_ascii=False)
                if isinstance(value, (dict, list))
                else value
                for key, value in row.items()
            }
            writer.writerow(clean_row)

    print(f"{len(rows)} row added in {path}")
    return path, istemp

def main():
    date = datetime.now().strftime("%Y-%m-%d")

    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=False, help="Répertoire de sortie - empty if not write in local")
    parser.add_argument("--api-keys-file", dest="api_keys", required=True,  help="Fichier contannt les clés API AirLabs (json)")
    parser.add_argument("--google-credentials",dest="google_cred",  required=False,  help="Chemin vers le fichier JSON Google Cloud")
    parser.add_argument("--airports", required=True, help="List of Airport")
    parser.add_argument("--bucket-path",dest="bucket_path", required=False,  help="bucket/path for Google Cloud Storage")
    args = parser.parse_args()

    # Get Active Key
    key_to_use = get_api_key(args.api_keys)
    
    if key_to_use is None:
        print("All Keys expired or reach limit")
    else:
        print(f"Use Key {key_to_use[0]} : {key_to_use[2]} restant")

    airports = read_airports(key_to_use[1], args.airports)
    if args.bucket_path:
        m= re.match(r"(?P<bucket>[\.\w\-_]+)\/(?P<path>.*)", args.bucket_path)
        if not m:
            raise Exception(f"Bad Bucket path format")
        bucket = m.group("bucket")
        path = m.group("path").rstrip('/')
    else:
        bucket=False
        path=""

    for airport in airports:
        local_path=''
        istemp=False
        try:
            print(f"Collecting {airport.desc}...")
            # Collect data from Airlabs API
            filename = airport.pattern.replace("{TIMESTAMPH}",datetime.now().strftime("%Y%m%d%H") ).replace("{TIMESTAMP}",datetime.now().strftime("%Y%m%d") )
            data = collect_data(airport)
            # Write local/temp file
            local_path, istemp = save_csv(data, filename, args.dir)
            # Upload to Bucket if bucket path defined
            if local_path and bucket:   
                uploader_gcs(local_path,bucket, f"{path}/{filename}", args.google_cred )

        except Exception as exc:
            print(f"Error {airport.desc}: {exc}")
        finally:
            # Remove Temp file if temp...
            if istemp and os.path.isfile(local_path): os.remove(local_path)


if __name__ == "__main__":
    main()