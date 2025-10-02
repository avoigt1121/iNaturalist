import json
import os
import matplotlib.pyplot as plt

def load_species_counts(data_dir="inat_data"):
    """Load observation counts for each species"""
    species_counts = {}
    
    for species_folder in os.listdir(data_dir):
        species_path = os.path.join(data_dir, species_folder)
        if not os.path.isdir(species_path):
            continue
        
        # Count JSON metadata files (these represent observations with coordinates)
        json_count = len([f for f in os.listdir(species_path) if f.endswith('_metadata.json')])
        
        if json_count > 0:
            species_counts[species_folder.replace('_', ' ')] = json_count
    
    return species_counts

def calculate_species_ranges(data_dir="inat_data"):
    """Calculate geographic range for each species (simplified)"""
    species_ranges = {}
    
    for species_folder in os.listdir(data_dir):
        species_path = os.path.join(data_dir, species_folder)
        if not os.path.isdir(species_path):
            continue
        
        lats = []
        lons = []
        
        # Read all JSON files to get coordinates
        for file in os.listdir(species_path):
            if file.endswith('_metadata.json'):
                try:
                    with open(os.path.join(species_path, file), 'r') as f:
                        metadata = json.load(f)
                    
                    coords = metadata.get('coordinates', {})
                    if coords.get('has_coordinates'):
                        lats.append(coords['latitude'])
                        lons.append(coords['longitude'])
                        
                except (json.JSONDecodeError, KeyError):
                    continue
        
        # Calculate simple range (lat/lon span in degrees)
        if len(lats) >= 2:
            lat_range = max(lats) - min(lats)
            lon_range = max(lons) - min(lons)
            # Simple approximation: convert to rough km estimate
            range_km = max(lat_range, lon_range) * 111  # 1 degree ≈ 111 km
            species_ranges[species_folder.replace('_', ' ')] = range_km
    
    return species_ranges

def create_charts():
    """Create the two top charts"""
    # Load data
    species_counts = load_species_counts()
    species_ranges = calculate_species_ranges()
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Chart 1: Observation counts
    species_names = list(species_counts.keys())
    counts = list(species_counts.values())
    
    ax1.barh(species_names, counts, color='skyblue')
    ax1.set_xlabel('Number of Observations')
    ax1.set_title('Observations per Species')
    ax1.tick_params(axis='y', labelsize=8)
    
    # Chart 2: Geographic ranges (only for species that have range data)
    range_species = []
    ranges = []
    for species in species_names:
        if species in species_ranges:
            range_species.append(species)
            ranges.append(species_ranges[species])
    
    ax2.barh(range_species, ranges, color='lightcoral')
    ax2.set_xlabel('Geographic Range (km)')
    ax2.set_title('Geographic Range per Species')
    ax2.tick_params(axis='y', labelsize=8)
    
    plt.tight_layout()
    plt.savefig('species_charts.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"📊 Charts saved as 'species_charts.png'")
    print(f"📈 {len(species_counts)} species with observations")
    print(f"🌍 {len(species_ranges)} species with geographic range data")

if __name__ == "__main__":
    create_charts()
