import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import openai
import config

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QLabel, QWidget
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFont


class BIXIChatbot:
    
    def __init__(self, data_path=None):
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
        self.data = None
        self.data_summary = None
        self.conversation_history = []
        
        if data_path:
            self.load_data(data_path)
    
    def load_data(self, csv_path):
        self.data = pd.read_csv(csv_path)
        self.data_summary = self._create_data_context()
        print(f"✓ Chatbot loaded {len(self.data)} stations")
    
    def _create_data_context(self):
        if self.data is None:
            return "No data available"
        
        df = self.data
        
        context = f"""
BIXI Montreal Bike-Sharing Real-Time Data:
- Total Stations: {len(df)}
- Total Bikes Available: {df['num_bikes_available'].sum():.0f}
- Total Docks Available: {df['num_docks_available'].sum():.0f}
- Average Bikes per Station: {df['num_bikes_available'].mean():.1f}
- Average Docks per Station: {df['num_docks_available'].mean():.1f}

Station Status Summary:
- Stations with NO bikes: {len(df[df['num_bikes_available'] == 0])}
- Stations with NO docks: {len(df[df['num_docks_available'] == 0])}
- Stations with 5+ bikes: {len(df[df['num_bikes_available'] >= 5])}

Geographic Coverage:
- Latitude Range: {df['lat'].min():.4f} to {df['lat'].max():.4f}
- Longitude Range: {df['lon'].min():.4f} to {df['lon'].max():.4f}

Top 10 Stations with Most Bikes:
"""
        top_bikes = df.nlargest(10, 'num_bikes_available')[['name', 'num_bikes_available', 'num_docks_available', 'lat', 'lon']]
        for _, row in top_bikes.iterrows():
            context += f"- {row['name']}: {row['num_bikes_available']:.0f} bikes, {row['num_docks_available']:.0f} docks (lat: {row['lat']:.4f}, lon: {row['lon']:.4f})\n"
        
        context += "\nTop 10 Stations with Most Docks (for returns):\n"
        top_docks = df.nlargest(10, 'num_docks_available')[['name', 'num_bikes_available', 'num_docks_available', 'lat', 'lon']]
        for _, row in top_docks.iterrows():
            context += f"- {row['name']}: {row['num_docks_available']:.0f} docks, {row['num_bikes_available']:.0f} bikes (lat: {row['lat']:.4f}, lon: {row['lon']:.4f})\n"
        
        context += "\nFull Station Data (JSON format for reference):\n"
        sample_stations = df[['station_id', 'name', 'lat', 'lon', 'num_bikes_available', 'num_docks_available', 'capacity']].head(50).to_dict('records')
        context += json.dumps(sample_stations, indent=2)
        
        return context
    
    def get_system_prompt(self):
        return f"""You are a helpful BIXI Montreal bike-sharing assistant. You have access to real-time station data.

Your capabilities:
1. Help users find the nearest station with available bikes
2. Help users find stations with available docks to return bikes
3. Provide directions and recommendations based on user location
4. Analyze bike availability patterns and predict trends
5. Answer questions about the BIXI system

When user provides their location (address or coordinates):
- Find the nearest stations with bikes if they want to rent
- Find the nearest stations with docks if they want to return
- Consider stations within walking distance (typically 500m)
- Recommend stations with good availability (5+ bikes/docks)

For trend predictions:
- High utilization stations tend to run out of bikes during morning rush (7-9 AM)
- Downtown stations have higher turnover
- Stations near metro stops are busier
- Weekend patterns differ from weekdays

CURRENT REAL-TIME DATA:
{self.data_summary}

Always be helpful, concise, and provide specific station names with their bike/dock counts.
If asked about a location, find the closest stations and their availability."""
    
    def chat(self, user_message):
        self.conversation_history.append({"role": "user", "content": user_message})
        
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        messages.extend(self.conversation_history[-10:])
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        assistant_message = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message
    
    def find_nearest_stations(self, lat, lon, need_bikes=True, limit=5):
        if self.data is None:
            return []
        
        df = self.data.copy()
        df['distance'] = ((df['lat'] - lat)**2 + (df['lon'] - lon)**2)**0.5
        
        if need_bikes:
            df = df[df['num_bikes_available'] > 0]
        else:
            df = df[df['num_docks_available'] > 0]
        
        return df.nsmallest(limit, 'distance')[['name', 'num_bikes_available', 'num_docks_available', 'distance', 'lat', 'lon']].to_dict('records')
    
    def predict_trend(self, station_name):
        if self.data is None:
            return "No data available"
        
        station = self.data[self.data['name'].str.contains(station_name, case=False, na=False)]
        
        if station.empty:
            return f"Station '{station_name}' not found"
        
        row = station.iloc[0]
        utilization = row['num_bikes_available'] / (row['num_bikes_available'] + row['num_docks_available']) if (row['num_bikes_available'] + row['num_docks_available']) > 0 else 0
        
        prediction = f"Station: {row['name']}\n"
        prediction += f"Current: {row['num_bikes_available']:.0f} bikes, {row['num_docks_available']:.0f} docks\n"
        prediction += f"Utilization: {utilization:.1%}\n\n"
        
        if utilization > 0.7:
            prediction += "⚠️ HIGH DEMAND - This station may run out of bikes soon. Consider alternative stations nearby."
        elif utilization < 0.3:
            prediction += "✅ LOW DEMAND - Good availability expected to continue."
        else:
            prediction += "📊 MODERATE DEMAND - Stable availability expected."
        
        return prediction
    
    def clear_history(self):
        self.conversation_history = []


class ChatbotDialog(QDialog):
    
    def __init__(self, chatbot, parent=None):
        super().__init__(parent)
        self.chatbot = chatbot
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("BIXI Assistant")
        self.setMinimumSize(500, 600)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; }
            QTextEdit { 
                background-color: #2d2d3d; 
                color: #cdd6f4; 
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit { 
                background-color: #2d2d3d; 
                color: #cdd6f4; 
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton { 
                background-color: #89b4fa; 
                color: #1e1e2e; 
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #b4befe; }
            QLabel { color: #cdd6f4; font-size: 16px; font-weight: bold; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title = QLabel("🚲 BIXI Montreal Assistant")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Arial", 12))
        layout.addWidget(self.chat_display)
        
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask about bike stations, your location, or predictions...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        btn_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear Chat")
        clear_btn.clicked.connect(self.clear_chat)
        clear_btn.setStyleSheet("background-color: #f38ba8;")
        btn_layout.addWidget(clear_btn)
        
        bikes_btn = QPushButton("Find Bikes Near Me")
        bikes_btn.clicked.connect(lambda: self.quick_action("I need to find bikes near downtown Montreal"))
        btn_layout.addWidget(bikes_btn)
        
        docks_btn = QPushButton("Find Docks Near Me")
        docks_btn.clicked.connect(lambda: self.quick_action("I need to return my bike, find docks near downtown"))
        btn_layout.addWidget(docks_btn)
        
        layout.addLayout(btn_layout)
        
        self.add_message("assistant", "Hello! I'm your BIXI Montreal assistant. 🚲\n\nI can help you:\n• Find nearby stations with available bikes\n• Find stations with docks to return bikes\n• Predict bike availability trends\n• Answer questions about the BIXI system\n\nTell me your location or ask any question!")
    
    def add_message(self, role, content):
        if role == "user":
            self.chat_display.append(f"<p style='color: #a6e3a1; margin: 5px 0;'><b>You:</b> {content}</p>")
        else:
            self.chat_display.append(f"<p style='color: #89b4fa; margin: 5px 0;'><b>BIXI Assistant:</b></p><p style='color: #cdd6f4; margin: 5px 0 15px 0;'>{content}</p>")
    
    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return
        
        self.input_field.clear()
        self.add_message("user", message)
        
        response = self.chatbot.chat(message)
        self.add_message("assistant", response)
    
    def quick_action(self, message):
        self.input_field.setText(message)
        self.send_message()
    
    def clear_chat(self):
        self.chat_display.clear()
        self.chatbot.clear_history()
        self.add_message("assistant", "Chat cleared! How can I help you?")


def create_chatbot_dialog(data_path):
    chatbot = BIXIChatbot(data_path)
    dialog = ChatbotDialog(chatbot)
    return dialog

