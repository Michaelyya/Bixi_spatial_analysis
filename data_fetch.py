import requests
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import config


class BIXIDataFetcher:
    
    def __init__(self):
        self.base_url = config.BIXI_GBFS_BASE_URL
        self.data_dir = Path(config.DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
    
    def fetch_feed(self, feed_name):
        url = self.base_url + config.BIXI_FEEDS[feed_name]
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.data_dir / f"{feed_name}_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Fetched {feed_name} - {len(data.get('data', {}).get('stations', []))} stations")
        return data
    
    def get_station_information(self):
        data = self.fetch_feed("station_information")
        if data and 'data' in data and 'stations' in data['data']:
            return pd.DataFrame(data['data']['stations'])
        return pd.DataFrame()
    
    def get_station_status(self):
        data = self.fetch_feed("station_status")
        if data and 'data' in data and 'stations' in data['data']:
            return pd.DataFrame(data['data']['stations'])
        return pd.DataFrame()
    
    def get_combined_station_data(self):
        info_df = self.get_station_information()
        status_df = self.get_station_status()
        
        combined = info_df.merge(status_df, on='station_id', how='inner', suffixes=('_info', '_status'))
        
        if 'lon' not in combined.columns and 'longitude' in combined.columns:
            combined['lon'] = combined['longitude']
        if 'lat' not in combined.columns and 'latitude' in combined.columns:
            combined['lat'] = combined['latitude']
        
        if 'num_bikes_available' in combined.columns and 'num_docks_available' in combined.columns:
            combined['num_bikes_available'] = pd.to_numeric(combined['num_bikes_available'], errors='coerce').fillna(0)
            combined['num_docks_available'] = pd.to_numeric(combined['num_docks_available'], errors='coerce').fillna(0)
            combined['total_capacity'] = combined['num_bikes_available'] + combined['num_docks_available']
            combined['utilization_rate'] = combined.apply(
                lambda row: row['num_bikes_available'] / row['total_capacity'] if row['total_capacity'] > 0 else 0.0,
                axis=1
            )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = self.data_dir / f"combined_stations_{timestamp}.csv"
        combined.to_csv(csv_path, index=False)
        print(f"✓ Saved combined data to {csv_path}")
        
        return combined
    
    def get_system_alerts(self):
        return self.fetch_feed("system_alerts")
    
    def get_system_information(self):
        return self.fetch_feed("system_information")


if __name__ == "__main__":
    fetcher = BIXIDataFetcher()
    print("Fetching BIXI data...")
    combined_data = fetcher.get_combined_station_data()
    
    if not combined_data.empty:
        print(f"\n✓ Successfully fetched {len(combined_data)} stations")
        print(f"\nSample data:")
        print(combined_data[['station_id', 'name', 'num_bikes_available', 'num_docks_available', 'utilization_rate']].head())
