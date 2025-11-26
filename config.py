import os
from pathlib import Path

def load_env_file():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

load_env_file()

BIXI_GBFS_BASE_URL = "https://gbfs.velobixi.com/gbfs"
BIXI_FEEDS = {
    "station_information": "/en/station_information.json",
    "station_status": "/en/station_status.json",
    "system_information": "/en/system_information.json",
    "system_alerts": "/en/system_alerts.json",
    "vehicle_types": "/en/vehicle_types.json"
}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

OUTPUT_LAYOUT_NAME = os.getenv("OUTPUT_LAYOUT_NAME", "BIXI_Layout")

DATA_DIR = "data"
OUTPUT_DIR = "output"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
