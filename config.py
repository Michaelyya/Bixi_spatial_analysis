"""
Configuration module for BIXI GenAI ArcGIS Pro Integration
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# BIXI GBFS API Configuration
# Note: BIXI uses the standard GBFS format without version in path
BIXI_GBFS_BASE_URL = "https://gbfs.velobixi.com/gbfs"
BIXI_FEEDS = {
    "station_information": "/en/station_information.json",
    "station_status": "/en/station_status.json",
    "system_information": "/en/system_information.json",
    "system_alerts": "/en/system_alerts.json",
    "vehicle_types": "/en/vehicle_types.json"
}

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Use gpt-4o-mini for cost efficiency

# ArcGIS Pro Configuration
ARCGIS_PRO_PROJECT_PATH = os.getenv("ARCGIS_PRO_PROJECT_PATH", "")
OUTPUT_MAP_NAME = os.getenv("OUTPUT_MAP_NAME", "BIXI_Analysis_Map")
OUTPUT_LAYOUT_NAME = os.getenv("OUTPUT_LAYOUT_NAME", "BIXI_Layout")

# Data Storage
DATA_DIR = "data"
OUTPUT_DIR = "output"

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

