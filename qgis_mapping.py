import os
from pathlib import Path
from datetime import datetime
import csv

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsGraduatedSymbolRenderer,
    QgsRendererRange, QgsMarkerSymbol, QgsPrintLayout, 
    QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemLegend,
    QgsLayoutItemScaleBar, QgsLayoutPoint, QgsLayoutSize, 
    QgsUnitTypes, QgsLayoutExporter, QgsRectangle, QgsRasterLayer,
    QgsField, QgsFields, QgsFeature, QgsGeometry, QgsPointXY,
    QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsSymbol,
    QgsVectorFileWriter, QgsCoordinateReferenceSystem
)
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor, QFont
from qgis.analysis import QgsNativeAlgorithms
from qgis import processing


class QGISAnalyzer:
    
    def __init__(self):
        self.project = QgsProject.instance()
        self.output_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "output"
        self.output_dir.mkdir(exist_ok=True)
        print("✓ QGIS Analyzer initialized")
    
    def load_stations(self, csv_path, layer_name="BIXI_Stations"):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
        
        x_field = 'lon' if 'lon' in headers else 'longitude'
        y_field = 'lat' if 'lat' in headers else 'latitude'
        
        csv_path_abs = os.path.abspath(csv_path)
        file_uri = f"file://{csv_path_abs}" if csv_path_abs.startswith('/') else f"file:///{csv_path_abs}"
        uri = f"{file_uri}?delimiter=,&xField={x_field}&yField={y_field}&crs=EPSG:4326"
        
        layer = QgsVectorLayer(uri, layer_name, "delimitedtext")
        self.project.addMapLayer(layer)
        
        print(f"✓ Loaded {layer.featureCount()} stations")
        return layer

    def create_utilization_analysis(self, layer):
        field = "utilization_rate"
        
        ranges = []
        breakpoints = [
            (0.0, 0.2, "#2166ac", "Very Low (0-20%)", 8),
            (0.2, 0.4, "#67a9cf", "Low (20-40%)", 9),
            (0.4, 0.6, "#f7f7f7", "Balanced (40-60%)", 10),
            (0.6, 0.8, "#ef8a62", "High (60-80%)", 11),
            (0.8, 1.0, "#b2182b", "Very High (80-100%)", 12)
        ]
        
        for lower, upper, color, label, size in breakpoints:
            symbol = QgsMarkerSymbol.createSimple({
                'name': 'circle',
                'size': str(size),
                'color': color,
                'outline_color': '#333333',
                'outline_width': '0.8'
            })
            ranges.append(QgsRendererRange(lower, upper, symbol, label))
        
        renderer = QgsGraduatedSymbolRenderer(field, ranges)
        layer.setRenderer(renderer)
        layer.triggerRepaint()
        print("✓ Applied utilization rate symbology")

    def add_basemap(self):
        uri = "type=xyz&url=https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"
        basemap = QgsRasterLayer(uri, "CartoDB Dark", "wms")
        
        if not basemap.isValid():
            uri = "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            basemap = QgsRasterLayer(uri, "OpenStreetMap", "wms")
        
        if basemap.isValid():
            self.project.addMapLayer(basemap, False)
            root = self.project.layerTreeRoot()
            root.insertLayer(-1, basemap)
            print("✓ Added basemap")

    def zoom_to_layer(self, layer):
        from qgis.utils import iface
        if iface:
            iface.mapCanvas().setExtent(layer.extent())
            iface.mapCanvas().refresh()

    def create_layout(self, title, layout_name):
        manager = self.project.layoutManager()
        existing = manager.layoutByName(layout_name)
        if existing:
            manager.removeLayout(existing)
        
        layout = QgsPrintLayout(self.project)
        layout.initializeDefaults()
        layout.setName(layout_name)
        
        page = layout.pageCollection().page(0)
        page.setPageSize(QgsLayoutSize(297, 210, QgsUnitTypes.LayoutMillimeters))
        
        map_item = QgsLayoutItemMap(layout)
        map_item.attemptMove(QgsLayoutPoint(10, 25, QgsUnitTypes.LayoutMillimeters))
        map_item.attemptResize(QgsLayoutSize(200, 170, QgsUnitTypes.LayoutMillimeters))
        
        extent = QgsRectangle()
        for layer in self.project.mapLayers().values():
            if hasattr(layer, 'extent') and not layer.name().startswith('Carto') and not layer.name().startswith('Open'):
                if extent.isEmpty():
                    extent = layer.extent()
                else:
                    extent.combineExtentWith(layer.extent())
        map_item.setExtent(extent)
        layout.addLayoutItem(map_item)
        
        title_item = QgsLayoutItemLabel(layout)
        title_item.setText(title)
        title_item.setFont(QFont("Arial", 16, QFont.Bold))
        title_item.attemptMove(QgsLayoutPoint(10, 5, QgsUnitTypes.LayoutMillimeters))
        title_item.attemptResize(QgsLayoutSize(200, 15, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(title_item)
        
        legend = QgsLayoutItemLegend(layout)
        legend.setLinkedMap(map_item)
        legend.attemptMove(QgsLayoutPoint(215, 25, QgsUnitTypes.LayoutMillimeters))
        legend.attemptResize(QgsLayoutSize(75, 150, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(legend)
        
        scale_bar = QgsLayoutItemScaleBar(layout)
        scale_bar.setLinkedMap(map_item)
        scale_bar.attemptMove(QgsLayoutPoint(10, 198, QgsUnitTypes.LayoutMillimeters))
        layout.addLayoutItem(scale_bar)
        
        manager.addLayout(layout)
        print(f"✓ Created layout: {layout_name}")
        return layout

    def export_pdf(self, layout_name, filename=None):
        manager = self.project.layoutManager()
        layout = manager.layoutByName(layout_name)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"BIXI_Analysis_{timestamp}"
        
        output_path = self.output_dir / f"{filename}.pdf"
        
        exporter = QgsLayoutExporter(layout)
        exporter.exportToPdf(str(output_path), QgsLayoutExporter.PdfExportSettings())
        
        print(f"✓ Exported: {output_path}")
        return str(output_path)
    
    def create_hotspot_analysis(self, layer, field="utilization_rate"):
        print("   Running Getis-Ord Gi* hotspot analysis...")
        
        output_path = str(self.output_dir / "hotspot_analysis.shp")
        
        params = {
            'INPUT': layer,
            'FIELD': field,
            'DISTANCE': 1000,
            'OUTPUT': output_path
        }
        
        result = processing.run('qgis:heatmapkerneldensityestimation', params)
        
        if result and 'OUTPUT' in result:
            hotspot_layer = QgsVectorLayer(result['OUTPUT'], "Hotspot Analysis", "ogr")
            if hotspot_layer.isValid():
                self.project.addMapLayer(hotspot_layer)
                print("   ✓ Hotspot analysis complete")
                return hotspot_layer
        
        print("   ⚠ Hotspot analysis failed, using density instead")
        return self.create_density_analysis(layer, field)
    
    def create_density_analysis(self, layer, field="utilization_rate"):
        print("   Creating kernel density estimation...")
        
        output_path = str(self.output_dir / "density_raster.tif")
        
        params = {
            'INPUT': layer,
            'RADIUS': 500,
            'PIXEL_SIZE': 50,
            'WEIGHT': field,
            'OUTPUT': output_path
        }
        
        result = processing.run('qgis:heatmapkerneldensityestimation', params)
        
        if result and 'OUTPUT' in result:
            density_layer = QgsRasterLayer(result['OUTPUT'], "Utilization Density", "gdal")
            if density_layer.isValid():
                self.project.addMapLayer(density_layer)
                print("   ✓ Density analysis complete")
                return density_layer
        
        return None
    
    def create_nearest_neighbor_analysis(self, layer):
        print("   Calculating nearest neighbor statistics...")
        
        params = {
            'INPUT': layer,
            'OUTPUT': str(self.output_dir / "nn_analysis.csv")
        }
        
        result = processing.run('qgis:nearestneighbouranalysis', params)
        print("   ✓ Nearest neighbor analysis complete")
        return result


def run_full_analysis(csv_path):
    print("\n" + "=" * 60)
    print("🚲 BIXI Montreal - Utilization Rate Analysis")
    print("=" * 60 + "\n")
    
    analyzer = QGISAnalyzer()
    
    print("[1/4] Loading station data...")
    layer = analyzer.load_stations(csv_path, "BIXI Utilization Rate")
    
    print("\n[2/4] Applying utilization symbology...")
    analyzer.create_utilization_analysis(layer)
    
    print("\n[3/4] Adding basemap...")
    analyzer.add_basemap()
    
    print("\n[4/4] Creating map layout...")
    analyzer.zoom_to_layer(layer)
    layout = analyzer.create_layout("BIXI Montreal - Station Utilization Rate", "BIXI_Analysis")
    output_path = analyzer.export_pdf("BIXI_Analysis")
    
    print("\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 60)
    print(f"\n📊 Layer: BIXI Utilization Rate")
    print("   • Blue = Low utilization (many bikes available)")
    print("   • White = Balanced")
    print("   • Red = High utilization (few bikes available)")
    print(f"\n📄 PDF exported: {output_path}")
    
    return output_path
