import sys
import os
import atexit
import importlib
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(r'/Users/yonganyu/Desktop/Bixi_spatial_analysis')

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
os.chdir(PROJECT_DIR)

print("=" * 60)
print("🚲 BIXI Montreal Spatial Analysis for QGIS")
print("=" * 60)

from qgis.core import Qgis
print(f"✓ QGIS Version: {Qgis.QGIS_VERSION}")

DATA_DIR = PROJECT_DIR / "data"

def cleanup():
    print("\n🧹 Cleaning up temporary files...")
    for pattern in ["latest_combined_*.csv", "combined_stations_*.csv", "station_*.json"]:
        for f in DATA_DIR.glob(pattern):
            f.unlink()
            print(f"   Deleted: {f.name}")
    print("✓ Cleanup complete")

atexit.register(cleanup)

import config
importlib.reload(config)

import data_fetch
importlib.reload(data_fetch)
from data_fetch import BIXIDataFetcher

import qgis_mapping
importlib.reload(qgis_mapping)
from qgis_mapping import run_full_analysis

print("\n[Step 1] Fetching live BIXI data...")
fetcher = BIXIDataFetcher()
data = fetcher.get_combined_station_data()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_path = DATA_DIR / f"latest_combined_{timestamp}.csv"
data.to_csv(csv_path, index=False)
print(f"✓ Saved {len(data)} stations to: {csv_path.name}")

print("\n[Step 2] Running spatial analysis...")
output_path = run_full_analysis(str(csv_path))

print("\n" + "=" * 60)
print("🎉 Ready! Toggle layers in the Layers panel to explore.")
print("=" * 60)
print("\n💡 Tips:")
print("   • Turn layers on/off to compare different analyses")
print("   • Click stations to see attribute popup")
print("   • Use Print Layout for publication-ready maps")
print("\n⚠️ Data will auto-delete when QGIS closes")
