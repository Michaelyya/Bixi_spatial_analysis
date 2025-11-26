import os
import json
import atexit
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

import config
from data_fetch import BIXIDataFetcher

PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
STATIC_DIR = PROJECT_DIR / "static"

STATIC_DIR.mkdir(exist_ok=True)

current_data = None
current_csv_path = None
conversation_history = []

def cleanup():
    global conversation_history
    conversation_history = []
    print("\nCleaning up data files and conversation history...")
    for pattern in ["latest_combined_*.csv", "combined_stations_*.csv", "station_*.json"]:
        for f in DATA_DIR.glob(pattern):
            f.unlink()
            print(f"  Deleted: {f.name}")
    print("  Cleared conversation history")

atexit.register(cleanup)


class BIXIRequestHandler(SimpleHTTPRequestHandler):
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html_path = PROJECT_DIR / "index.html"
            with open(html_path, 'rb') as f:
                self.wfile.write(f.read())
        
        elif parsed.path == "/api/stations":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            if current_data is not None:
                df = current_data[['station_id', 'name', 'lat', 'lon', 'num_bikes_available', 'num_docks_available', 'capacity']].copy()
                df = df.fillna(0)
                df['num_bikes_available'] = df['num_bikes_available'].astype(int)
                df['num_docks_available'] = df['num_docks_available'].astype(int)
                df['lat'] = df['lat'].astype(float)
                df['lon'] = df['lon'].astype(float)
                stations = df.to_dict('records')
                self.wfile.write(json.dumps(stations).encode())
            else:
                self.wfile.write(json.dumps([]).encode())
        
        elif parsed.path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            if current_data is not None:
                df = current_data
                stats = {
                    "total_stations": len(df),
                    "total_bikes": int(df['num_bikes_available'].sum()),
                    "total_docks": int(df['num_docks_available'].sum()),
                    "avg_bikes": round(df['num_bikes_available'].mean(), 1),
                    "empty_stations": int(len(df[df['num_bikes_available'] == 0])),
                    "full_stations": int(len(df[df['num_docks_available'] == 0])),
                    "last_update": datetime.now().strftime("%H:%M:%S")
                }
                self.wfile.write(json.dumps(stats).encode())
            else:
                self.wfile.write(json.dumps({}).encode())
        
        else:
            super().do_GET()
    
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == "/api/chat":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            message = data.get("message", "")
            response = self.handle_chat(message)
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"response": response}).encode())
        
        elif parsed.path == "/api/chat/clear":
            global conversation_history
            conversation_history = []
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode())
        
        elif parsed.path == "/api/refresh":
            global current_data, current_csv_path
            
            fetcher = BIXIDataFetcher()
            current_data = fetcher.get_combined_station_data()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_csv_path = DATA_DIR / f"latest_combined_{timestamp}.csv"
            current_data.to_csv(current_csv_path, index=False)
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "stations": len(current_data)}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def handle_chat(self, message):
        global conversation_history
        
        if not config.OPENAI_API_KEY:
            return "OpenAI API key not configured. Please add OPENAI_API_KEY to your .env file."
        
        if current_data is None:
            return "No station data loaded. Click 'Refresh Data' first."
        
        import openai
        import re
        import math
        
        client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        df = current_data
        
        user_lat, user_lon = None, None
        coord_match = re.search(r'(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)', message)
        if coord_match:
            user_lat = float(coord_match.group(1))
            user_lon = float(coord_match.group(2))
        
        if user_lat is None:
            for prev_msg in reversed(conversation_history):
                if prev_msg['role'] == 'user':
                    coord_match = re.search(r'(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)', prev_msg['content'])
                    if coord_match:
                        lat_val = float(coord_match.group(1))
                        lon_val = float(coord_match.group(2))
                        if 45 < lat_val < 46 and -74 < lon_val < -73:
                            user_lat, user_lon = lat_val, lon_val
                            break
        
        system_context = f"""You are a BIXI Montreal bike-sharing assistant with real-time data.
You remember the conversation history and can reference previous messages.

SYSTEM STATUS:
- Total Stations: {len(df)}
- Total Bikes Available: {df['num_bikes_available'].sum():.0f}
- Total Docks Available: {df['num_docks_available'].sum():.0f}
- Empty Stations: {len(df[df['num_bikes_available'] == 0])}
- Full Stations: {len(df[df['num_docks_available'] == 0])}
"""
        
        if user_lat and user_lon:
            df_copy = df.copy()
            df_copy['distance_m'] = df_copy.apply(
                lambda row: math.sqrt((row['lat'] - user_lat)**2 + (row['lon'] - user_lon)**2) * 111000,
                axis=1
            )
            nearby = df_copy.nsmallest(15, 'distance_m')
            
            system_context += f"\n🎯 USER'S LOCATION: {user_lat:.4f}, {user_lon:.4f}\n"
            system_context += "\n📍 NEAREST 15 STATIONS (sorted by distance):\n"
            for _, row in nearby.iterrows():
                system_context += f"- {row['name']}: {row['num_bikes_available']:.0f}🚲, {row['num_docks_available']:.0f}🅿️, {row['distance_m']:.0f}m away (lat:{row['lat']:.4f}, lon:{row['lon']:.4f})\n"
            
            system_context += "\n⚡ IMPORTANT: Always recommend stations from the NEAREST list above when user asks about nearby stations!"
        else:
            system_context += "\nNote: User location not detected. Ask them for their location or coordinates to find nearby stations.\n"
            
            system_context += "\nTOP 10 STATIONS WITH MOST BIKES (citywide):\n"
            top_bikes = df.nlargest(10, 'num_bikes_available')[['name', 'num_bikes_available', 'num_docks_available']]
            for _, row in top_bikes.iterrows():
                system_context += f"- {row['name']}: {row['num_bikes_available']:.0f}🚲, {row['num_docks_available']:.0f}🅿️\n"
        
        system_context += """
RESPONSE GUIDELINES:
- When user shares location, ONLY recommend from the nearest stations list
- Include distance in meters when recommending stations
- Prioritize stations with 5+ bikes for pickup, 5+ docks for returns
- Give walking directions (north/south/east/west, street names if visible)
- Use emojis: 🚲 bikes, 🅿️ docks, 📍 location, ⚠️ warnings, ✅ good, ❌ avoid
- Be concise but helpful
"""
        
        conversation_history.append({"role": "user", "content": message})
        
        messages = [{"role": "system", "content": system_context}]
        messages.extend(conversation_history[-20:])
        
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=600
        )
        
        assistant_response = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": assistant_response})
        
        return assistant_response


def run_server(port=8080):
    global current_data, current_csv_path
    
    print("=" * 60)
    print("BIXI Web Application")
    print("=" * 60)
    
    print("\nFetching BIXI data...")
    fetcher = BIXIDataFetcher()
    current_data = fetcher.get_combined_station_data()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_csv_path = DATA_DIR / f"latest_combined_{timestamp}.csv"
    current_data.to_csv(current_csv_path, index=False)
    print(f"✓ Loaded {len(current_data)} stations")
    
    os.chdir(PROJECT_DIR)
    
    server = HTTPServer(('localhost', port), BIXIRequestHandler)
    print(f"\n✓ Server running at http://localhost:{port}")
    print("  Open this URL in your browser!")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    server.serve_forever()


if __name__ == "__main__":
    run_server()

