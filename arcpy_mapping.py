"""
ArcPy Mapping Module
Handles automated map creation, layer styling, and layout design
"""
import arcpy
import os
from pathlib import Path
import pandas as pd
import config


class ArcPyMapper:
    """Handles ArcGIS Pro map automation using ArcPy"""
    
    def __init__(self, aprx_path: str = None):
        """
        Initialize ArcPy mapper
        
        Args:
            aprx_path: Path to ArcGIS Pro project (.aprx file)
                      If None, will try to use current project or create new
        """
        self.aprx_path = aprx_path or config.ARCGIS_PRO_PROJECT_PATH
        
        if self.aprx_path and os.path.exists(self.aprx_path):
            self.aprx = arcpy.mp.ArcGISProject(self.aprx_path)
            print(f"✓ Loaded ArcGIS Pro project: {self.aprx_path}")
        else:
            # Try to get current project
            try:
                self.aprx = arcpy.mp.ArcGISProject("CURRENT")
                print("✓ Using current ArcGIS Pro project")
            except:
                raise ValueError("No ArcGIS Pro project available. Please open a project or specify aprx_path.")
        
        self.output_dir = Path(config.OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)
    
    def create_feature_class_from_csv(self, csv_path: str, output_fc: str, 
                                     x_field: str = None, y_field: str = None,
                                     spatial_reference: int = 4326):
        try:
            # Read CSV to detect coordinate fields
            df = pd.read_csv(csv_path)
            
            # Auto-detect coordinate fields
            if x_field is None:
                if 'lon' in df.columns:
                    x_field = 'lon'
                elif 'longitude' in df.columns:
                    x_field = 'longitude'
                else:
                    raise ValueError("Could not find longitude field (lon or longitude)")
            
            if y_field is None:
                if 'lat' in df.columns:
                    y_field = 'lat'
                elif 'latitude' in df.columns:
                    y_field = 'latitude'
                else:
                    raise ValueError("Could not find latitude field (lat or latitude)")
            
            # Create XY event layer
            temp_layer = "temp_xy_layer"
            arcpy.management.XYTableToPoint(
                csv_path,
                temp_layer,
                x_field,
                y_field,
                coordinate_system=arcpy.SpatialReference(spatial_reference)
            )
            
            # Copy to feature class
            arcpy.management.CopyFeatures(temp_layer, output_fc)
            arcpy.management.Delete(temp_layer)
            
            print(f"✓ Created feature class: {output_fc}")
            return output_fc
        
        except Exception as e:
            print(f"✗ Error creating feature class: {e}")
            raise
    
    def add_layer_to_map(self, layer_path: str, map_name: str = None, 
                        symbology_type: str = "GRADUATED_COLORS",
                        field: str = "utilization_rate"):
        """
        Add a layer to a map with styling
        
        Args:
            layer_path: Path to feature class or layer file
            map_name: Name of the map (defaults to first map)
            symbology_type: Type of symbology
            field: Field to symbolize by
        """
        try:
            # Get map
            if map_name:
                map_obj = self.aprx.listMaps(map_name)[0]
            else:
                map_obj = self.aprx.listMaps()[0]
            
            # Add layer
            layer = map_obj.addDataFromPath(layer_path)
            
            # Apply symbology if it's a feature layer
            if hasattr(layer, 'symbology'):
                if symbology_type == "GRADUATED_COLORS":
                    if hasattr(layer.symbology, 'renderer'):
                        layer.symbology.renderer = "GraduatedColorsRenderer"
                        if hasattr(layer.symbology, 'colorizer'):
                            layer.symbology.colorizer.field = field
                            layer.symbology.colorizer.colorRamp = map_obj.listColorRamps("Red-Yellow-Green")[0]
            
            print(f"✓ Added layer to map: {layer.name}")
            return layer
        
        except Exception as e:
            print(f"✗ Error adding layer: {e}")
            raise
    
    def create_layout(self, layout_name: str = None, template: str = "ANSI_A",
                     map_frame_name: str = "Map Frame"):
        """
        Create a new layout
        
        Args:
            layout_name: Name for the layout
            template: Layout template size
            map_frame_name: Name for the map frame
        
        Returns:
            Layout object
        """
        try:
            layout_name = layout_name or config.OUTPUT_LAYOUT_NAME
            
            # Create layout
            layout = self.aprx.createLayout(template, layout_name)
            
            # Get or create map frame
            map_frames = layout.listElements("MAPFRAME_ELEMENT")
            if map_frames:
                mf = map_frames[0]
            else:
                # Create map frame (simplified - may need adjustment)
                mf = layout.createMapFrame(map_frame_name, self.aprx.listMaps()[0])
            
            print(f"✓ Created layout: {layout_name}")
            return layout
        
        except Exception as e:
            print(f"✗ Error creating layout: {e}")
            raise
    
    def add_layout_elements(self, layout, title: str = "BIXI Station Analysis",
                           include_legend: bool = True,
                           include_scale_bar: bool = True,
                           include_north_arrow: bool = True):
        """
        Add standard layout elements
        
        Args:
            layout: Layout object
            title: Map title
            include_legend: Add legend
            include_scale_bar: Add scale bar
            include_north_arrow: Add north arrow
        """
        try:
            # Add title
            title_element = layout.createTextElement(title)
            title_element.elementPositionX = layout.pageWidth / 2
            title_element.elementPositionY = layout.pageHeight - 0.5
            
            # Add legend
            if include_legend:
                map_frames = layout.listElements("MAPFRAME_ELEMENT")
                if map_frames:
                    legend = layout.createLegendElement(map_frames[0])
                    legend.elementPositionX = 0.5
                    legend.elementPositionY = 1.5
            
            # Add scale bar
            if include_scale_bar:
                map_frames = layout.listElements("MAPFRAME_ELEMENT")
                if map_frames:
                    scale_bar = layout.createScaleBarElement(
                        map_frames[0],
                        "Alternating Scale Bar 1"
                    )
                    scale_bar.elementPositionX = 0.5
                    scale_bar.elementPositionY = 0.5
            
            # Add north arrow
            if include_north_arrow:
                north_arrow = layout.createNorthArrowElement("Simple North Arrow")
                north_arrow.elementPositionX = layout.pageWidth - 0.5
                north_arrow.elementPositionY = layout.pageHeight - 0.5
            
            print("✓ Added layout elements")
        
        except Exception as e:
            print(f"⚠ Warning: Could not add all layout elements: {e}")
    
    def export_map(self, layout_name: str = None, output_format: str = "PDF",
                  output_name: str = None):
        """
        Export map to file
        
        Args:
            layout_name: Name of layout to export
            output_format: Export format (PDF, PNG, JPG)
            output_name: Output filename (without extension)
        
        Returns:
            str: Path to exported file
        """
        try:
            layout_name = layout_name or config.OUTPUT_LAYOUT_NAME
            layout = self.aprx.listLayouts(layout_name)[0]
            
            if not output_name:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"BIXI_Map_{timestamp}"
            
            output_path = self.output_dir / f"{output_name}.{output_format.lower()}"
            
            if output_format.upper() == "PDF":
                layout.exportToPDF(str(output_path))
            elif output_format.upper() == "PNG":
                layout.exportToPNG(str(output_path), resolution=300)
            elif output_format.upper() == "JPG":
                layout.exportToJPEG(str(output_path), resolution=300)
            else:
                raise ValueError(f"Unsupported format: {output_format}")
            
            print(f"✓ Exported map to: {output_path}")
            return str(output_path)
        
        except Exception as e:
            print(f"✗ Error exporting map: {e}")
            raise
    
    def style_layer_by_field(self, layer, field: str, color_ramp: str = "Red-Yellow-Green",
                           classification_method: str = "NaturalBreaks",
                           num_classes: int = 5):
        """
        Style a layer using graduated colors
        
        Args:
            layer: Layer object
            field: Field to symbolize by
            color_ramp: Name of color ramp
            classification_method: Classification method
            num_classes: Number of classes
        """
        try:
            if hasattr(layer, 'symbology'):
                if hasattr(layer.symbology, 'renderer'):
                    layer.symbology.renderer = "GraduatedColorsRenderer"
                    if hasattr(layer.symbology, 'colorizer'):
                        layer.symbology.colorizer.field = field
                        layer.symbology.colorizer.colorRamp = self.aprx.listMaps()[0].listColorRamps(color_ramp)[0]
                        layer.symbology.colorizer.classificationMethod = classification_method
                        layer.symbology.colorizer.breakCount = num_classes
            
            print(f"✓ Styled layer by field: {field}")
        
        except Exception as e:
            print(f"⚠ Warning: Could not style layer: {e}")
    
    def save_project(self):
        """Save the ArcGIS Pro project"""
        try:
            self.aprx.save()
            print("✓ Saved ArcGIS Pro project")
        except Exception as e:
            print(f"⚠ Warning: Could not save project: {e}")


def create_bixi_map_workflow(csv_path: str, output_fc_name: str = "BIXI_Stations",
                            map_name: str = None, layout_name: str = None):
    """
    Complete workflow to create a BIXI map
    
    Args:
        csv_path: Path to CSV with BIXI data
        output_fc_name: Name for output feature class
        map_name: Name of map (defaults to first map)
        layout_name: Name of layout
    
    Returns:
        str: Path to exported map
    """
    try:
        mapper = ArcPyMapper()
        
        # Create feature class
        fc = mapper.create_feature_class_from_csv(csv_path, output_fc_name)
        
        # Add to map
        layer = mapper.add_layer_to_map(fc, map_name, field="utilization_rate")
        
        # Style layer
        mapper.style_layer_by_field(layer, "utilization_rate")
        
        # Create layout
        layout = mapper.create_layout(layout_name)
        mapper.add_layout_elements(layout, title="BIXI Station Utilization Analysis")
        
        # Export
        output_path = mapper.export_map(layout_name)
        
        # Save project
        mapper.save_project()
        
        return output_path
    
    except Exception as e:
        print(f"✗ Error in map workflow: {e}")
        raise

