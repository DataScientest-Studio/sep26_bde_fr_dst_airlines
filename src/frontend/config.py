import os
from dotenv import load_dotenv
from pathlib import Path
env_file = Path(__file__).parent / ".env"
load_dotenv()

API_URL: str = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY: str = os.getenv("API_KEY", "dev-secret-api-key")
ALLOW_DEV_BYPASS_GOOGLE_AUTH: bool = os.getenv("ALLOW_DEV_BYPASS_GOOGLE_AUTH", "true").lower() == "true"
print(API_URL)