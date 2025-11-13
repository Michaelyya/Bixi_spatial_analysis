"""
Main Workflow Script
Orchestrates the entire pipeline: BIXI Data → GenAI Analysis → ArcGIS Pro → Automated Map
"""
import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# Import custom modules
import config
from data_fetch import BIXIDataFetcher
from openai_client import OpenAIClient

# ArcPy imports are conditional (only available in ArcGIS Pro)
try:
    from arcpy_mapping import ArcPyMapper, create_bixi_map_workflow
    ARCPY_AVAILABLE = True
except ImportError:
    ARCPY_AVAILABLE = False
    ArcPyMapper = None
    create_bixi_map_workflow = None


class BIXIGenAIPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self):
        self.data_fetcher = BIXIDataFetcher()
        self.openai_client = None
        self.mapper = None
        
        # Initialize OpenAI if API key is available
        try:
            self.openai_client = OpenAIClient()
            print("✓ OpenAI client initialized")
        except ValueError as e:
            print(f"⚠ Warning: {e}")
            print("  Continuing without GenAI features...")
    
    def run_full_pipeline(self, use_genai: bool = True, create_map: bool = True):
        """
        Run the complete pipeline
        
        Args:
            use_genai: Whether to use GenAI analysis
            create_map: Whether to create ArcGIS Pro map
        
        Returns:
            dict: Results from each step
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "data_fetch": None,
            "genai_analysis": None,
            "map_creation": None
        }
        
        print("=" * 60)
        print("BIXI GenAI ArcGIS Pro Pipeline")
        print("=" * 60)
        
        # Step 1: Fetch BIXI Data
        print("\n[Step 1] Fetching BIXI Data...")
        try:
            combined_data = self.data_fetcher.get_combined_station_data()
            
            if combined_data.empty:
                print("✗ Failed to fetch data. Exiting.")
                return results
            
            results["data_fetch"] = {
                "success": True,
                "num_stations": len(combined_data),
                "columns": list(combined_data.columns)
            }
            
            # Save latest data path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            latest_csv = Path(config.DATA_DIR) / f"latest_combined_{timestamp}.csv"
            combined_data.to_csv(latest_csv, index=False)
            results["data_fetch"]["csv_path"] = str(latest_csv)
            
            print(f"✓ Fetched {len(combined_data)} stations")
        
        except Exception as e:
            import traceback
            print(f"✗ Error fetching data: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            results["data_fetch"] = {"success": False, "error": str(e)}
            return results
        
        # Step 2: GenAI Analysis
        if use_genai and self.openai_client:
            print("\n[Step 2] Running GenAI Analysis...")
            try:
                # Create data summary
                data_summary = self._create_data_summary(combined_data)
                
                # Get AI analysis
                analysis_result = self.openai_client.analyze_data(data_summary)
                
                if analysis_result["success"]:
                    results["genai_analysis"] = {
                        "success": True,
                        "analysis": analysis_result["analysis"],
                        "model": analysis_result["model"]
                    }
                    
                    # Save analysis
                    analysis_path = config.OUTPUT_DIR / f"genai_analysis_{timestamp}.txt"
                    with open(analysis_path, 'w') as f:
                        f.write(analysis_result["analysis"])
                    results["genai_analysis"]["file_path"] = str(analysis_path)
                    
                    print("✓ GenAI analysis complete")
                    
                    # Get map design recommendations
                    print("\n[Step 2b] Getting Map Design Recommendations...")
                    design_result = self.openai_client.get_map_design_recommendations(
                        analysis_result["analysis"],
                        data_summary
                    )
                    
                    if design_result["success"]:
                        design_path = config.OUTPUT_DIR / f"map_design_recommendations_{timestamp}.txt"
                        with open(design_path, 'w') as f:
                            f.write(design_result["recommendations"])
                        results["genai_analysis"]["design_recommendations"] = design_result["recommendations"]
                        print("✓ Map design recommendations received")
                
                else:
                    results["genai_analysis"] = {
                        "success": False,
                        "error": analysis_result.get("error", "Unknown error")
                    }
                    print(f"⚠ GenAI analysis failed: {analysis_result.get('error')}")
            
            except Exception as e:
                print(f"✗ Error in GenAI analysis: {e}")
                results["genai_analysis"] = {"success": False, "error": str(e)}
        else:
            print("\n[Step 2] Skipping GenAI Analysis (not configured or disabled)")
        
        # Step 3: Create ArcGIS Pro Map
        if create_map:
            print("\n[Step 3] Creating ArcGIS Pro Map...")
            try:
                # Check if ArcGIS Pro is available
                if not ARCPY_AVAILABLE:
                    print("⚠ ArcPy not available. Skipping map creation.")
                    print("  Note: ArcPy is only available within ArcGIS Pro.")
                    print("  To create maps, run this script from ArcGIS Pro's Python window.")
                    results["map_creation"] = {
                        "success": False,
                        "error": "ArcPy not available outside ArcGIS Pro"
                    }
                    return results
                
                print("✓ ArcPy available")
                
                # Create map workflow
                csv_path = results["data_fetch"]["csv_path"]
                output_path = create_bixi_map_workflow(
                    csv_path,
                    output_fc_name="BIXI_Stations",
                    map_name=config.OUTPUT_MAP_NAME,
                    layout_name=config.OUTPUT_LAYOUT_NAME
                )
                
                results["map_creation"] = {
                    "success": True,
                    "output_path": output_path
                }
                
                print(f"✓ Map created: {output_path}")
            
            except Exception as e:
                print(f"✗ Error creating map: {e}")
                results["map_creation"] = {"success": False, "error": str(e)}
        else:
            print("\n[Step 3] Skipping Map Creation")
        
        # Save results summary
        results_path = Path(config.OUTPUT_DIR) / f"pipeline_results_{timestamp}.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "=" * 60)
        print("Pipeline Complete!")
        print(f"Results saved to: {results_path}")
        print("=" * 60)
        
        return results
    
    def _create_data_summary(self, df: pd.DataFrame) -> str:
        """Create a summary of the dataframe for AI analysis"""
        summary_parts = []
        
        summary_parts.append(f"Total Stations: {len(df)}")
        
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
        
        # Add top stations by utilization
        if 'utilization_rate' in df.columns and 'name' in df.columns:
            top_stations = df.nlargest(5, 'utilization_rate')[['name', 'utilization_rate']]
            summary_parts.append("\nTop 5 Stations by Utilization:")
            for idx, row in top_stations.iterrows():
                summary_parts.append(f"  {row['name']}: {row['utilization_rate']:.2%}")
        
        return "\n".join(summary_parts)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BIXI GenAI ArcGIS Pro Pipeline")
    parser.add_argument("--no-genai", action="store_true", help="Skip GenAI analysis")
    parser.add_argument("--no-map", action="store_true", help="Skip map creation")
    
    args = parser.parse_args()
    
    pipeline = BIXIGenAIPipeline()
    results = pipeline.run_full_pipeline(
        use_genai=not args.no_genai,
        create_map=not args.no_map
    )
    
    return results


if __name__ == "__main__":
    main()

