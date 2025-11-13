"""
Example Usage Scripts
Demonstrates how to use individual components of the BIXI GenAI pipeline
"""
import sys
from pathlib import Path

# Example 1: Fetch BIXI Data Only
def example_fetch_data():
    """Example: Fetch and display BIXI data"""
    print("=" * 60)
    print("Example 1: Fetching BIXI Data")
    print("=" * 60)
    
    from data_fetch import BIXIDataFetcher
    
    fetcher = BIXIDataFetcher()
    data = fetcher.get_combined_station_data()
    
    if not data.empty:
        print(f"\n✓ Fetched {len(data)} stations")
        print("\nSample data:")
        print(data[['station_id', 'name', 'num_bikes_available', 
                   'num_docks_available', 'utilization_rate']].head(10))
    else:
        print("✗ No data fetched")


# Example 2: GenAI Analysis Only
def example_genai_analysis():
    """Example: Analyze data with GenAI"""
    print("\n" + "=" * 60)
    print("Example 2: GenAI Analysis")
    print("=" * 60)
    
    try:
        from openai_client import OpenAIClient
        from data_fetch import BIXIDataFetcher
        
        # Fetch data
        fetcher = BIXIDataFetcher()
        data = fetcher.get_combined_station_data()
        
        if data.empty:
            print("✗ No data to analyze")
            return
        
        # Create summary
        summary = f"""
        Total Stations: {len(data)}
        Average Bikes Available: {data['num_bikes_available'].mean():.2f}
        Average Docks Available: {data['num_docks_available'].mean():.2f}
        Average Utilization: {data['utilization_rate'].mean():.2%}
        """
        
        # Analyze with AI
        client = OpenAIClient()
        result = client.analyze_data(summary)
        
        if result["success"]:
            print("\n✓ Analysis complete:")
            print(result["analysis"])
        else:
            print(f"✗ Analysis failed: {result.get('error')}")
    
    except ValueError as e:
        print(f"⚠ {e}")
        print("  Set OPENAI_API_KEY in .env file to use this feature")


# Example 3: Get Map Design Recommendations
def example_map_design():
    """Example: Get map design recommendations from GenAI"""
    print("\n" + "=" * 60)
    print("Example 3: Map Design Recommendations")
    print("=" * 60)
    
    try:
        from openai_client import OpenAIClient
        from data_fetch import BIXIDataFetcher
        
        fetcher = BIXIDataFetcher()
        data = fetcher.get_combined_station_data()
        
        if data.empty:
            print("✗ No data available")
            return
        
        summary = f"Total Stations: {len(data)}, Utilization Range: {data['utilization_rate'].min():.2%} to {data['utilization_rate'].max():.2%}"
        
        client = OpenAIClient()
        result = client.get_map_design_recommendations(
            "High utilization in downtown, low in suburbs",
            summary
        )
        
        if result["success"]:
            print("\n✓ Recommendations received:")
            print(result["recommendations"])
        else:
            print(f"✗ Failed: {result.get('error')}")
    
    except ValueError as e:
        print(f"⚠ {e}")


# Example 4: Full Pipeline (without ArcGIS Pro)
def example_full_pipeline_no_arcgis():
    """Example: Run full pipeline without ArcGIS Pro"""
    print("\n" + "=" * 60)
    print("Example 4: Full Pipeline (Data + GenAI)")
    print("=" * 60)
    
    from main_workflow import BIXIGenAIPipeline
    
    pipeline = BIXIGenAIPipeline()
    results = pipeline.run_full_pipeline(use_genai=True, create_map=False)
    
    print("\nPipeline Results Summary:")
    print(f"  Data Fetch: {'✓' if results['data_fetch'] and results['data_fetch'].get('success') else '✗'}")
    print(f"  GenAI Analysis: {'✓' if results.get('genai_analysis') and results['genai_analysis'].get('success') else '✗'}")


# Example 5: Interactive Chat with GenAI
def example_interactive_chat():
    """Example: Interactive chat with GenAI about BIXI data"""
    print("\n" + "=" * 60)
    print("Example 5: Interactive GenAI Chat")
    print("=" * 60)
    
    try:
        from openai_client import OpenAIClient
        from data_fetch import BIXIDataFetcher
        
        fetcher = BIXIDataFetcher()
        data = fetcher.get_combined_station_data()
        
        if data.empty:
            print("✗ No data available")
            return
        
        context = f"BIXI has {len(data)} stations with average utilization of {data['utilization_rate'].mean():.2%}"
        
        client = OpenAIClient()
        
        questions = [
            "What factors might affect bike-sharing station utilization?",
            "How can we improve the BIXI system?",
            "What spatial patterns should we look for in the data?"
        ]
        
        for question in questions:
            print(f"\nQ: {question}")
            answer = client.chat(question, context)
            print(f"A: {answer}\n")
    
    except ValueError as e:
        print(f"⚠ {e}")


if __name__ == "__main__":
    print("BIXI GenAI Pipeline - Example Usage")
    print("\nChoose an example to run:")
    print("1. Fetch BIXI Data")
    print("2. GenAI Analysis")
    print("3. Map Design Recommendations")
    print("4. Full Pipeline (Data + GenAI)")
    print("5. Interactive Chat")
    print("6. Run All Examples")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    if choice == "1":
        example_fetch_data()
    elif choice == "2":
        example_genai_analysis()
    elif choice == "3":
        example_map_design()
    elif choice == "4":
        example_full_pipeline_no_arcgis()
    elif choice == "5":
        example_interactive_chat()
    elif choice == "6":
        example_fetch_data()
        example_genai_analysis()
        example_map_design()
        example_full_pipeline_no_arcgis()
    else:
        print("Invalid choice. Running example 1...")
        example_fetch_data()

