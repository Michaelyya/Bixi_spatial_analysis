import sys
import os
import atexit
import importlib
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

PROJECT_DIR = Path(r'/Users/yonganyu/Desktop/Bixi_spatial_analysis')

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
os.chdir(PROJECT_DIR)

print("=" * 60)
print("📍 BIXI Montreal - Optimal Source Location Analysis")
print("   Using QGIS Location-Allocation Tool")
print("=" * 60)

from qgis.core import Qgis
print(f"✓ QGIS Version: {Qgis.QGIS_VERSION}")

DATA_DIR = PROJECT_DIR / "data"

NUM_FACILITIES = 3

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

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
    QgsField, QgsFields, QgsMarkerSymbol, QgsSingleSymbolRenderer,
    QgsRasterLayer, QgsCategorizedSymbolRenderer, QgsRendererCategory,
    QgsWkbTypes, QgsCoordinateReferenceSystem, QgsVectorFileWriter
)
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor
from qgis import processing

project = QgsProject.instance()

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    
    a = np.sin(delta_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    
    return R * c

def create_demand_layer(df, output_path):
    print("   Creating demand points layer...")
    
    fields = QgsFields()
    fields.append(QgsField("station_id", QVariant.String))
    fields.append(QgsField("name", QVariant.String))
    fields.append(QgsField("demand", QVariant.Double))
    fields.append(QgsField("utilization", QVariant.Double))
    fields.append(QgsField("capacity", QVariant.Int))
    
    writer = QgsVectorFileWriter(
        str(output_path),
        "UTF-8",
        fields,
        QgsWkbTypes.Point,
        QgsCoordinateReferenceSystem("EPSG:4326"),
        "ESRI Shapefile"
    )
    
    if writer.hasError() != QgsVectorFileWriter.NoError:
        print(f"   ⚠ Error creating demand layer: {writer.errorMessage()}")
        return None
    
    for _, row in df.iterrows():
        feature = QgsFeature(fields)
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(row['lon'], row['lat'])))
        feature.setAttribute("station_id", str(row.get('station_id', '')))
        feature.setAttribute("name", str(row.get('name', '')))
        
        utilization = row.get('utilization_rate', 0)
        capacity = row.get('capacity', 0)
        if capacity == 0:
            capacity = row.get('num_bikes_available', 0) + row.get('num_docks_available', 0)
        
        demand = utilization * capacity
        feature.setAttribute("demand", demand)
        feature.setAttribute("utilization", utilization)
        feature.setAttribute("capacity", capacity)
        
        writer.addFeature(feature)
    
    del writer
    print(f"   ✓ Created demand layer: {output_path.name}")
    return str(output_path)

def create_candidate_facilities_layer(df, output_path, num_candidates=50):
    print(f"   Creating candidate facilities layer ({num_candidates} candidates)...")
    
    lat_min, lat_max = df['lat'].min(), df['lat'].max()
    lon_min, lon_max = df['lon'].min(), df['lon'].max()
    
    lat_range = lat_max - lat_min
    lon_range = lon_max - lon_min
    
    grid_size = int(np.sqrt(num_candidates)) + 1
    lat_step = lat_range / grid_size
    lon_step = lon_range / grid_size
    
    fields = QgsFields()
    fields.append(QgsField("facility_id", QVariant.Int))
    fields.append(QgsField("capacity", QVariant.Int))
    
    writer = QgsVectorFileWriter(
        str(output_path),
        "UTF-8",
        fields,
        QgsWkbTypes.Point,
        QgsCoordinateReferenceSystem("EPSG:4326"),
        "ESRI Shapefile"
    )
    
    if writer.hasError() != QgsVectorFileWriter.NoError:
        print(f"   ⚠ Error creating candidates layer: {writer.errorMessage()}")
        return None
    
    facility_id = 1
    for i in range(grid_size):
        for j in range(grid_size):
            if facility_id > num_candidates:
                break
            
            candidate_lat = lat_min + (i + 0.5) * lat_step
            candidate_lon = lon_min + (j + 0.5) * lon_step
            
            feature = QgsFeature(fields)
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(candidate_lon, candidate_lat)))
            feature.setAttribute("facility_id", facility_id)
            feature.setAttribute("capacity", 1000)
            
            writer.addFeature(feature)
            facility_id += 1
        
        if facility_id > num_candidates:
            break
    
    del writer
    print(f"   ✓ Created candidates layer: {output_path.name}")
    return str(output_path)

def get_road_network():
    print("   Looking for road network layer...")
    
    layers = project.mapLayers().values()
    for layer in layers:
        if 'road' in layer.name().lower() or 'street' in layer.name().lower() or 'network' in layer.name().lower():
            print(f"   ✓ Found network layer: {layer.name()}")
            return layer
    
    print("   ⚠ No road network found. Creating from OpenStreetMap...")
    print("   💡 Please add a road network layer manually, or the analysis will use straight-line distance")
    return None

def run_alternative_location_allocation(demand_layer, candidates_layer, num_facilities, output_path):
    print("   Using distance-based optimization...")
    
    demand_points = []
    for feature in demand_layer.getFeatures():
        geom = feature.geometry()
        if geom:
            point = geom.asPoint()
            demand = feature.attribute('demand') or 0
            demand_points.append({
                'lon': point.x(),
                'lat': point.y(),
                'demand': demand
            })
    
    candidate_points = []
    for feature in candidates_layer.getFeatures():
        geom = feature.geometry()
        if geom:
            point = geom.asPoint()
            candidate_points.append({
                'lon': point.x(),
                'lat': point.y()
            })
    
    if len(candidate_points) == 0 or len(demand_points) == 0:
        return None
    
    optimal_facilities = []
    
    for facility_num in range(num_facilities):
        best_candidate = None
        best_score = float('inf')
        
        for candidate in candidate_points:
            too_close = False
            for existing in optimal_facilities:
                dist = haversine_distance(
                    candidate['lat'], candidate['lon'],
                    existing['lat'], existing['lon']
                )
                if dist < 3000:
                    too_close = True
                    break
            
            if too_close:
                continue
            
            total_score = 0
            for demand_point in demand_points:
                dist_km = haversine_distance(
                    demand_point['lat'], demand_point['lon'],
                    candidate['lat'], candidate['lon']
                ) / 1000
                total_score += demand_point['demand'] * dist_km
            
            if total_score < best_score:
                best_score = total_score
                best_candidate = candidate
        
        if best_candidate:
            optimal_facilities.append(best_candidate)
    
    fields = QgsFields()
    fields.append(QgsField("facility_id", QVariant.Int))
    
    writer = QgsVectorFileWriter(
        str(output_path),
        "UTF-8",
        fields,
        QgsWkbTypes.Point,
        QgsCoordinateReferenceSystem("EPSG:4326"),
        "ESRI Shapefile"
    )
    
    if writer.hasError() != QgsVectorFileWriter.NoError:
        return None
    
    for idx, facility in enumerate(optimal_facilities):
        feature = QgsFeature(fields)
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(facility['lon'], facility['lat'])))
        feature.setAttribute("facility_id", idx + 1)
        writer.addFeature(feature)
    
    del writer
    
    return {'OUTPUT': str(output_path)}

print("\n[Step 1] Fetching current BIXI data...")
fetcher = BIXIDataFetcher()
data = fetcher.get_combined_station_data()

if 'capacity' not in data.columns:
    data['capacity'] = data.get('num_bikes_available', 0) + data.get('num_docks_available', 0)

print(f"✓ Loaded {len(data)} stations")

print("\n   Filtering for Montreal area only (excluding Sherbrooke)...")
initial_count = len(data)
data = data[
    (data['lat'] >= 45.4) & (data['lat'] <= 45.6) &
    (data['lon'] >= -73.8) & (data['lon'] <= -73.4)
]
print(f"   ✓ Filtered from {initial_count} to {len(data)} Montreal stations")

print("\n[Step 2] Creating input layers for Location-Allocation...")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

demand_shp = DATA_DIR / f"demand_points_{timestamp}.shp"
candidates_shp = DATA_DIR / f"candidate_facilities_{timestamp}.shp"

demand_path = create_demand_layer(data, demand_shp)
candidates_path = create_candidate_facilities_layer(data, candidates_shp, num_candidates=100)

if not demand_path or not candidates_path:
    print("   ❌ Failed to create input layers")
    exit(1)

demand_layer = QgsVectorLayer(demand_path, "Demand Points", "ogr")
candidates_layer = QgsVectorLayer(candidates_path, "Candidate Facilities", "ogr")

if not demand_layer.isValid() or not candidates_layer.isValid():
    print("   ❌ Failed to load layers")
    exit(1)

project.addMapLayer(demand_layer, False)
project.addMapLayer(candidates_layer, False)

print("\n[Step 3] Running Location-Allocation optimization...")
print("   Using distance-based optimization algorithm...")

output_path = str(DATA_DIR / f"location_allocation_result_{timestamp}.shp")

result = run_alternative_location_allocation(demand_layer, candidates_layer, NUM_FACILITIES, output_path)

if result and 'OUTPUT' in result:
    optimal_layer = QgsVectorLayer(result['OUTPUT'], "Optimal Facilities", "ogr")
    if optimal_layer.isValid():
        symbol = QgsMarkerSymbol.createSimple({
            'name': 'star',
            'size': '20',
            'color': '#ff0000',
            'outline_color': '#ffffff',
            'outline_width': '2'
        })
        renderer = QgsSingleSymbolRenderer(symbol)
        optimal_layer.setRenderer(renderer)
        optimal_layer.triggerRepaint()
        project.addMapLayer(optimal_layer)
        print("   ✓ Optimal facilities layer created")
    else:
        print("   ⚠ Failed to load optimal facilities")
else:
    print("   ⚠ Location-Allocation analysis failed")

print("\n[Step 4] Loading results...")
optimal_layer = QgsVectorLayer(result['OUTPUT'], "Optimal Facilities", "ogr")
if optimal_layer.isValid():
    print(f"   ✓ Found {optimal_layer.featureCount()} optimal facilities")
    
    for feature in optimal_layer.getFeatures():
        geom = feature.geometry()
        if geom:
            point = geom.asPoint()
            print(f"   • Facility at: ({point.y():.4f}, {point.x():.4f})")

print("\n[Step 6] Adding basemap...")
basemap_uri = "type=xyz&url=https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"
basemap = QgsRasterLayer(basemap_uri, "CartoDB Dark", "wms")
if basemap.isValid():
    project.addMapLayer(basemap, False)
    root = project.layerTreeRoot()
    root.insertLayer(-1, basemap)
    print("   ✓ Basemap added")


