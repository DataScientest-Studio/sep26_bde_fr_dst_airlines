import os

import functions_framework
from airlabs import run

BUCKET_PATH = os.environ.get("BUCKET_PATH", "liora-airline-project/raw/airlabs")
AIRPORTS_FILE = "airports.json"  


@functions_framework.http
def run_http(request):
    """Point d'entrée HTTP appelé par Cloud Scheduler."""
    api_keys = os.environ["AIRLABS_API_KEYS"]
    run(api_keys, AIRPORTS_FILE, BUCKET_PATH)
    return "OK", 200