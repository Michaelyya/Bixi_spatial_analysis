"""
Quick Start Script for ArcGIS Pro
Copy and paste this into ArcGIS Pro's Python window
"""
import sys
import os

# ===== CONFIGURE THIS PATH =====
PROJECT_PATH = r'U:\GEOG414\GEOG_414_final\Bixi_spatial_analysis'
# ================================

# Setup
sys.path.insert(0, PROJECT_PATH)
os.chdir(PROJECT_PATH)

# Import and run
from main_workflow import BIXIGenAIPipeline

pipeline = BIXIGenAIPipeline()
results = pipeline.run_full_pipeline(use_genai=True, create_map=True)

print("\n✓ Done! Check the output/ directory for results.")

