"""
Script to run BIXI GenAI Pipeline from within ArcGIS Pro
This script is designed to be run from ArcGIS Pro's Python window or as a script tool.

Usage in ArcGIS Pro Python Window:
1. Open ArcGIS Pro
2. View → Python (or Ctrl+Alt+P)
3. Copy and paste this entire script, or run: exec(open(r'U:\GEOG414\GEOG_414_final\Bixi_spatial_analysis\run_in_arcgis_pro.py').read())
"""
import sys
import os
from pathlib import Path

# Get the project directory (adjust this path if needed)
PROJECT_DIR = Path(__file__).parent if '__file__' in globals() else Path(r'U:\GEOG414\GEOG_414_final\Bixi_spatial_analysis')

# Add project directory to Python path
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# Change to project directory
os.chdir(PROJECT_DIR)

print("=" * 60)
print("BIXI GenAI ArcGIS Pro Pipeline")
print("=" * 60)
print(f"Project Directory: {PROJECT_DIR}")
print(f"Python Path: {sys.executable}")
print()

# Check if arcpy is available
try:
    import arcpy
    print("✓ ArcPy is available")
    print(f"  ArcGIS Pro Version: {arcpy.GetInstallInfo()['Version']}")
except ImportError:
    print("✗ ERROR: ArcPy is not available!")
    print("  This script must be run from within ArcGIS Pro.")
    print("  Please open ArcGIS Pro and run this from the Python window.")
    sys.exit(1)

# Import and run the pipeline
try:
    from main_workflow import BIXIGenAIPipeline
    
    print("\nInitializing pipeline...")
    pipeline = BIXIGenAIPipeline()
    
    print("\nRunning full pipeline with map creation...")
    results = pipeline.run_full_pipeline(
        use_genai=True,  # Set to False if you don't have OpenAI API key
        create_map=True
    )
    
    print("\n" + "=" * 60)
    print("Pipeline execution complete!")
    print("=" * 60)
    
    if results.get("map_creation") and results["map_creation"].get("success"):
        print(f"\n✓ Map exported to: {results['map_creation']['output_path']}")
    
    if results.get("genai_analysis") and results["genai_analysis"].get("success"):
        print(f"\n✓ GenAI analysis saved")
        print(f"  File: {results['genai_analysis'].get('file_path', 'N/A')}")
    
except Exception as e:
    import traceback
    print(f"\n✗ Error running pipeline: {e}")
    print("\nFull traceback:")
    print(traceback.format_exc())
    print("\nTroubleshooting:")
    print("1. Make sure you're running from ArcGIS Pro's Python window")
    print("2. Check that all dependencies are installed")
    print("3. Verify the project directory path is correct")
    print("4. Ensure you have an active ArcGIS Pro project open")

