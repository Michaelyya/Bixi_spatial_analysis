import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

import config
from data_fetch import BIXIDataFetcher
from openai_client import OpenAIClient

QGIS_AVAILABLE = False
GIS_ENGINE = None

import importlib.util
if importlib.util.find_spec("qgis"):
    from qgis_mapping import run_full_analysis
    QGIS_AVAILABLE = True
    GIS_ENGINE = "QGIS"


class BIXIGenAIPipeline:
    
    def __init__(self):
        self.data_fetcher = BIXIDataFetcher()
        self.openai_client = None
        
        if config.OPENAI_API_KEY:
            self.openai_client = OpenAIClient()
            print("✓ OpenAI client initialized")
    
    def run_full_pipeline(self, use_genai=True, create_map=True):
        results = {
            "timestamp": datetime.now().isoformat(),
            "data_fetch": None,
            "genai_analysis": None,
            "map_creation": None
        }
        
        print("=" * 60)
        print(f"BIXI GenAI Pipeline ({GIS_ENGINE or 'No GIS'} Mode)")
        print("=" * 60)
        
        print("\n[Step 1] Fetching BIXI Data...")
        combined_data = self.data_fetcher.get_combined_station_data()
        
        if combined_data.empty:
            print("✗ Failed to fetch data. Exiting.")
            return results
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        latest_csv = Path(config.DATA_DIR) / f"latest_combined_{timestamp}.csv"
        combined_data.to_csv(latest_csv, index=False)
        
        results["data_fetch"] = {
            "success": True,
            "num_stations": len(combined_data),
            "columns": list(combined_data.columns),
            "csv_path": str(latest_csv)
        }
        
        print(f"✓ Fetched {len(combined_data)} stations")
        
        if use_genai and self.openai_client:
            print("\n[Step 2] Running GenAI Analysis...")
            data_summary = self._create_data_summary(combined_data)
            
            analysis_result = self.openai_client.analyze_data(data_summary)
            
            if analysis_result["success"]:
                results["genai_analysis"] = {
                    "success": True,
                    "analysis": analysis_result["analysis"],
                    "model": analysis_result["model"]
                }
                
                analysis_path = Path(config.OUTPUT_DIR) / f"genai_analysis_{timestamp}.txt"
                with open(analysis_path, 'w') as f:
                    f.write(analysis_result["analysis"])
                results["genai_analysis"]["file_path"] = str(analysis_path)
                
                print("✓ GenAI analysis complete")
                
                print("\n[Step 2b] Getting Map Design Recommendations...")
                design_result = self.openai_client.get_map_design_recommendations(
                    analysis_result["analysis"],
                    data_summary
                )
                
                if design_result["success"]:
                    design_path = Path(config.OUTPUT_DIR) / f"map_design_recommendations_{timestamp}.txt"
                    with open(design_path, 'w') as f:
                        f.write(design_result["recommendations"])
                    results["genai_analysis"]["design_recommendations"] = design_result["recommendations"]
                    print("✓ Map design recommendations received")
        else:
            print("\n[Step 2] Skipping GenAI Analysis (not configured or disabled)")
        
        if create_map:
            print(f"\n[Step 3] Creating Map ({GIS_ENGINE or 'N/A'})...")
            
            if not QGIS_AVAILABLE:
                print("⚠ QGIS not available. Skipping map creation.")
                results["map_creation"] = {"success": False, "error": "QGIS not available"}
                return results
            
            print(f"✓ {GIS_ENGINE} available")
            
            csv_path = results["data_fetch"]["csv_path"]
            output_path = run_full_analysis(csv_path)
            
            results["map_creation"] = {"success": True, "output_path": output_path, "gis_engine": GIS_ENGINE}
            print(f"✓ Map created: {output_path}")
        else:
            print("\n[Step 3] Skipping Map Creation")
        
        results_path = Path(config.OUTPUT_DIR) / f"pipeline_results_{timestamp}.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "=" * 60)
        print("Pipeline Complete!")
        print(f"Results saved to: {results_path}")
        print("=" * 60)
        
        return results
    
    def _create_data_summary(self, df):
        summary_parts = [f"Total Stations: {len(df)}"]
        
        if 'num_bikes_available' in df.columns:
            summary_parts.append(f"Average Bikes Available: {df['num_bikes_available'].mean():.2f}")
            summary_parts.append(f"Total Bikes Available: {df['num_bikes_available'].sum()}")
        
        if 'num_docks_available' in df.columns:
            summary_parts.append(f"Average Docks Available: {df['num_docks_available'].mean():.2f}")
            summary_parts.append(f"Total Docks Available: {df['num_docks_available'].sum()}")
        
        if 'utilization_rate' in df.columns:
            summary_parts.append(f"Average Utilization Rate: {df['utilization_rate'].mean():.2%}")
            summary_parts.append(f"Max Utilization Rate: {df['utilization_rate'].max():.2%}")
            summary_parts.append(f"Min Utilization Rate: {df['utilization_rate'].min():.2%}")
        
        if 'lon' in df.columns and 'lat' in df.columns:
            summary_parts.append(f"Geographic Extent:")
            summary_parts.append(f"  Longitude: {df['lon'].min():.4f} to {df['lon'].max():.4f}")
            summary_parts.append(f"  Latitude: {df['lat'].min():.4f} to {df['lat'].max():.4f}")
        
        if 'utilization_rate' in df.columns and 'name' in df.columns:
            top_stations = df.nlargest(5, 'utilization_rate')[['name', 'utilization_rate']]
            summary_parts.append("\nTop 5 Stations by Utilization:")
            for idx, row in top_stations.iterrows():
                summary_parts.append(f"  {row['name']}: {row['utilization_rate']:.2%}")
        
        return "\n".join(summary_parts)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="BIXI GenAI Pipeline")
    parser.add_argument("--no-genai", action="store_true", help="Skip GenAI analysis")
    parser.add_argument("--no-map", action="store_true", help="Skip map creation")
    
    args = parser.parse_args()
    
    pipeline = BIXIGenAIPipeline()
    results = pipeline.run_full_pipeline(use_genai=not args.no_genai, create_map=not args.no_map)
    
    return results


if __name__ == "__main__":
    main()
