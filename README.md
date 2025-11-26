# BIXI GenAI Spatial Analysis

A comprehensive pipeline that integrates BIXI (Montreal bike-sharing) data with Generative AI (OpenAI GPT models) and GIS (QGIS or ArcGIS Pro) for automated spatial analysis and map creation.

## Workflow

```
BIXI Data → GenAI Analysis → GIS Spatial Analysis → Automated Map Creation
```

## Features

- **Real-time BIXI Data Fetching**: Retrieves live station information and status from BIXI GBFS API
- **GenAI Integration**: Uses OpenAI GPT models for data analysis, insights, and map design recommendations
- **Automated GIS Mapping**: Creates maps, styles layers, and generates layouts using QGIS (PyQGIS) or ArcGIS Pro (ArcPy)
- **Systematic Automation**: Complete end-to-end pipeline with minimal manual intervention

## Project Structure

```
Bixi_spatial_analysis/
├── data_fetch.py          # BIXI data fetching module
├── openai_client.py       # OpenAI API integration
├── prompts.py             # Prompt management for GenAI
├── qgis_mapping.py        # QGIS automation (PyQGIS)
├── arcpy_mapping.py       # ArcGIS Pro automation (ArcPy)
├── main_workflow.py       # Main pipeline orchestrator
├── run_in_qgis.py         # Script to run in QGIS
├── qgis_quick_start.py    # Quick start for QGIS
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (your API keys)
├── README.md              # This file
├── data/                  # Fetched BIXI data (auto-created)
└── output/                # Generated maps and analysis (auto-created)
```

## Setup

### 1. Prerequisites

- Python 3.8+
- ArcGIS Pro (for map creation features)
- OpenAI API key (for GenAI features)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. (Optional) Configure ArcGIS Pro project path in `.env` or `config.py`

### 4. GIS Setup (QGIS or ArcGIS Pro)

**For QGIS (Recommended):**
- Install QGIS from https://qgis.org
- PyQGIS is automatically available in QGIS Python console
- Run scripts from QGIS Python console: `Plugins` → `Python Console`

**For ArcGIS Pro (Alternative):**
- ArcPy is only available within ArcGIS Pro's Python environment
- Run scripts from ArcGIS Pro's Python window or as a script tool

## Usage

### Running Without Maps (Outside ArcGIS Pro)

Run the complete workflow without map creation:

```bash
# Activate virtual environment first
source venv/bin/activate

# Run without map creation
python main_workflow.py --no-map
```

This will:
1. Fetch BIXI data
2. Analyze with GenAI (if API key is set)
3. Skip map creation (ArcPy not available)

### Running With Maps (Inside QGIS) - RECOMMENDED

**Option 1: Quick Start (Easiest)**

1. Open QGIS
2. Open Python console: `Plugins` → `Python Console` (or `Ctrl+Alt+P`)
3. Copy and paste this:

```python
exec(open(r'/Users/yonganyu/Desktop/Bixi_spatial_analysis/qgis_quick_start.py').read())
```

**Option 2: Full Pipeline with GenAI**

1. Open QGIS
2. Open Python console: `Plugins` → `Python Console`
3. Run:
```python
exec(open(r'/Users/yonganyu/Desktop/Bixi_spatial_analysis/run_in_qgis.py').read())
```

**Option 3: Manual Steps**

```python
import sys, os
sys.path.insert(0, r'/Users/yonganyu/Desktop/Bixi_spatial_analysis')
os.chdir(r'/Users/yonganyu/Desktop/Bixi_spatial_analysis')

from qgis_mapping import create_bixi_map_workflow
from data_fetch import BIXIDataFetcher

# Fetch data
fetcher = BIXIDataFetcher()
data = fetcher.get_combined_station_data()
data.to_csv('data/bixi_stations.csv', index=False)

# Create map
create_bixi_map_workflow('data/bixi_stations.csv')
```

### Running With Maps (Inside ArcGIS Pro) - Alternative

If you prefer ArcGIS Pro instead of QGIS:

1. Open ArcGIS Pro and create/open a project
2. Open Python window: `View` → `Python`
3. Run:
```python
exec(open(r'/Users/yonganyu/Desktop/Bixi_spatial_analysis/run_in_arcgis_pro.py').read())
```

### Options

```bash
# Skip GenAI analysis
python main_workflow.py --no-genai

# Skip map creation
python main_workflow.py --no-map

# Both
python main_workflow.py --no-genai --no-map
```

### Individual Modules

#### Fetch BIXI Data Only

```python
from data_fetch import BIXIDataFetcher

fetcher = BIXIDataFetcher()
data = fetcher.get_combined_station_data()
print(data.head())
```

#### GenAI Analysis Only

```python
from openai_client import OpenAIClient
from data_fetch import BIXIDataFetcher

# Fetch data
fetcher = BIXIDataFetcher()
data = fetcher.get_combined_station_data()

# Analyze with AI
client = OpenAIClient()
summary = "Total stations: 500, Average bikes: 10..."
result = client.analyze_data(summary)
print(result["analysis"])
```

#### QGIS Mapping (from within QGIS Python Console)

```python
from qgis_mapping import create_bixi_map_workflow

# Create map from CSV
output_path = create_bixi_map_workflow(
    csv_path="data/combined_stations_20240101_120000.csv",
    layer_name="BIXI_Stations"
)
print(f"Map exported to: {output_path}")
```

#### ArcGIS Pro Mapping (from within ArcGIS Pro)

```python
from arcpy_mapping import create_bixi_map_workflow

# Create map from CSV
output_path = create_bixi_map_workflow(
    csv_path="data/combined_stations_20240101_120000.csv",
    output_fc_name="BIXI_Stations"
)
print(f"Map exported to: {output_path}")
```

## BIXI Data Sources

The project uses the BIXI GBFS (General Bikeshare Feed Specification) API:

- **Station Information**: Static station data (location, capacity, etc.)
- **Station Status**: Real-time availability (bikes, docks)
- **System Information**: System metadata
- **System Alerts**: Service alerts and notifications

API Base URL: `https://gbfs.velobixi.com/gbfs/2.2`

## GenAI Features

### Data Analysis
- Pattern recognition in station utilization
- Geographic clustering analysis
- Recommendations for system improvements

### Map Design
- Symbology recommendations
- Color scheme suggestions
- Layout design guidance

### Code Generation
- ArcPy code generation for custom workflows
- Automated script creation based on requirements

## GIS Automation

### QGIS (qgis_mapping.py)

The `qgis_mapping.py` module provides:

- **Layer Creation**: Create point layers from CSV with coordinates
- **Graduated Symbology**: Color-coded visualization by utilization rate
- **Print Layouts**: Automated layouts with title, legend, scale bar
- **Map Export**: Export to PDF or PNG formats
- **Interactive Mapping**: View and interact with data in QGIS canvas

### ArcGIS Pro (arcpy_mapping.py)

The `arcpy_mapping.py` module provides:

- **Feature Class Creation**: Convert CSV to feature classes
- **Layer Styling**: Automated symbology based on data attributes
- **Layout Creation**: Automated map layouts with legends, scale bars, north arrows
- **Map Export**: Export to PDF, PNG, or JPEG formats

## Output Files

The pipeline generates:

- `data/`: Raw JSON and processed CSV files
- `output/`: 
  - GenAI analysis reports (`.txt`)
  - Map design recommendations (`.txt`)
  - Exported maps (`.pdf`, `.png`)
  - Pipeline results summary (`.json`)

## Configuration

Edit `config.py` to customize:

- BIXI API endpoints
- OpenAI model selection
- ArcGIS Pro project paths
- Output directories
- Map and layout names

## Troubleshooting

### PyQGIS Not Available
- PyQGIS only works within QGIS's Python console
- Open QGIS → Plugins → Python Console
- Data fetching and GenAI features work independently outside QGIS

### ArcPy Not Available
- ArcPy only works within ArcGIS Pro's Python environment
- Run scripts from ArcGIS Pro's Python window
- Consider using QGIS instead (free and open source)

### OpenAI API Errors
- Verify your API key in `.env`
- Check your OpenAI account has credits
- Ensure internet connection

### BIXI API Errors
- Check internet connection
- Verify BIXI API is accessible
- API may have rate limits

## Example Workflow

1. **Data Collection**: Fetch real-time BIXI data
2. **AI Analysis**: Get insights on utilization patterns
3. **Design Guidance**: Receive map design recommendations
4. **Map Creation**: Automatically generate styled map in ArcGIS Pro
5. **Export**: Save map as PDF for sharing

## Future Enhancements

- Historical data analysis
- Predictive modeling with GenAI
- Automated report generation
- Integration with other bike-sharing systems
- Real-time dashboard creation

## License

This project is for educational and research purposes.

## Contact

For questions or issues, please refer to the project documentation or contact the development team.

