# iNaturalist Images ML

A machine learning project for species classification using iNaturalist data with geospatial analysis.

## What this does

- Downloads images and metadata from iNaturalist for different species
- Analyzes geographic distribution of species observations
- Provides interactive maps showing where species are found
- Prepares data for machine learning models

## Files

- `api.py` - Downloads images and geocoordinate data from iNaturalist
- `map_app.py` - Interactive web app to visualize species on maps
- `simple_charts.py` - Creates comparison charts between species
- `cleanup_images.py` - Removes images without metadata
- `transformer.py` - Prepares data for PyTorch machine learning

## Quick Start

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Download species data:
```bash
python api.py
```

3. View species on interactive maps:
```bash
streamlit run map_app.py
```

4. Create comparison charts:
```bash
python simple_charts.py
```

## Features

- **Smart downloading**: Skips existing files, downloads only new images
- **Rich metadata**: Includes coordinates, uncertainty, location names, taxonomy
- **Interactive maps**: Click on observation points to see photos
- **Geographic analysis**: Shows species distribution and range
- **Data quality**: Validates coordinates and tracks uncertainty

## Data Structure

```
inat_data/
├── Species_name/
│   ├── observation_id.jpg
│   ├── observation_id_metadata.json
│   └── ...
└── Another_species/
    └── ...
```

Each observation includes:
- High-resolution image
- GPS coordinates (if available)
- Location names (country, state, etc.)
- Observation date and quality grade
- Taxonomic information and common names

## Coordinate System

All coordinates are in WGS84 (standard GPS coordinates) suitable for machine learning and mapping applications.
