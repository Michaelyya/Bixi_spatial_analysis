import sys
import os
from pathlib import Path
from datetime import datetime

PROJECT_PATH = r'/Users/yonganyu/Desktop/Bixi_spatial_analysis'

if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)
os.chdir(PROJECT_PATH)

print("🚲 BIXI Quick Analysis")
print("=" * 40)

from qgis_mapping import run_full_analysis
from data_fetch import BIXIDataFetcher

fetcher = BIXIDataFetcher()
data = fetcher.get_combined_station_data()

csv_path = Path(PROJECT_PATH) / "data" / f"bixi_{datetime.now().strftime('%H%M%S')}.csv"
data.to_csv(csv_path, index=False)

run_full_analysis(str(csv_path))
