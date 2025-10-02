import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import os
from math import radians, cos, sin, asin, sqrt

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points on Earth
    Returns distance in kilometers
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Earth's radius in km
    return 6371 * c

def load_species_coordinates(species_folder):
    """
    Load all coordinates for a single species
    Returns list of (lat, lon, observation_info) and common_name
    """
    coords = []
    common_name = None
    species_path = os.path.join("inat_data", species_folder)
    
    for file in os.listdir(species_path):
        if file.endswith('_metadata.json'):
            try:
                with open(os.path.join(species_path, file), 'r') as f:
                    data = json.load(f)
                
                if data.get('coordinates', {}).get('has_coordinates'):
                    lat = data['coordinates']['latitude']
                    lon = data['coordinates']['longitude']
                    obs_id = data['observation_id']
                    image_url = data.get('image_metadata', {}).get('image_url', '')
                    coords.append((lat, lon, obs_id, image_url))
                    
                    # Get common name from first file (they should all be the same)
                    if not common_name:
                        common_name = data.get('taxonomy', {}).get('common_name')
                    
            except (json.JSONDecodeError, KeyError):
                continue
    
    return coords, common_name

def calculate_centroid_and_max_span(coords):
    """
    Calculate the center point and find the two furthest points from each other
    """
    if not coords:
        return None, 0, None, None
    
    # Calculate centroid (average lat/lon)
    lats = [coord[0] for coord in coords]
    lons = [coord[1] for coord in coords]
    
    centroid_lat = sum(lats) / len(lats)
    centroid_lon = sum(lons) / len(lons)
    
    # Find the two points that are furthest apart
    max_distance = 0
    furthest_point1 = None
    furthest_point2 = None
    
    for i, (lat1, lon1, obs1, image_url) in enumerate(coords):
        for lat2, lon2, obs2, image_url in coords[i+1:]:
            distance = haversine_distance(lat1, lon1, lat2, lon2)
            if distance > max_distance:
                max_distance = distance
                furthest_point1 = (lat1, lon1, obs1)
                furthest_point2 = (lat2, lon2, obs2)
    
    return (centroid_lat, centroid_lon), max_distance, furthest_point1, furthest_point2

def create_species_map(species_name, coords):
    """
    Create a folium map for a species
    """
    if not coords:
        return None
    
    # Calculate center and find furthest points
    centroid, max_distance, point1, point2 = calculate_centroid_and_max_span(coords)
    
    # Create map centered on centroid
    m = folium.Map(
        location=[centroid[0], centroid[1]], 
        zoom_start=6,
        tiles='OpenStreetMap'
    )
    
    # Add centroid marker (red)
    folium.Marker(
        [centroid[0], centroid[1]],
        popup=f"Centroid of {species_name}",
        icon=folium.Icon(color='red', icon='star')
    ).add_to(m)
    
    # If we found the two furthest points, add special markers and circle
    if point1 and point2:
        # Add markers for the two furthest points (green)
        folium.Marker(
            [point1[0], point1[1]],
            popup=f"Furthest Point 1<br>Obs: {point1[2]}<br>Distance: {max_distance:.1f} km apart",
            icon=folium.Icon(color='green', icon='screenshot')
        ).add_to(m)
        
        folium.Marker(
            [point2[0], point2[1]],
            popup=f"Furthest Point 2<br>Obs: {point2[2]}<br>Distance: {max_distance:.1f} km apart",
            icon=folium.Icon(color='green', icon='screenshot')
        ).add_to(m)
        
        # Calculate midpoint between the two furthest points
        mid_lat = (point1[0] + point2[0]) / 2
        mid_lon = (point1[1] + point2[1]) / 2
        
        # Add circle centered on midpoint with radius = half the distance
        folium.Circle(
            location=[mid_lat, mid_lon],
            radius=(max_distance / 2) * 1000,  # Convert km to meters, radius = half distance
            popup=f"Species span: {max_distance:.1f} km diameter",
            color='green',
            fill=False,
            weight=3
        ).add_to(m)
    
    # Add all observation points (blue)
    for lat, lon, obs_id, image_url in coords:
        folium.Marker(
            [lat, lon],
            popup=f"""
            <div>
                <img src="{image_url}" width="200" height="150">
                <br><b>Observation:</b> {obs_id}
            </div>
            """,
            icon=folium.Icon(color='blue', icon='info-sign', size=(20, 20))
        ).add_to(m)
    
    return m

def main():
    """
    Main Streamlit app
    """
    st.title("🗺️ Species Geographic Distribution")
    st.write("Interactive maps showing where each species was observed")
    
    # Get list of species folders
    if not os.path.exists("inat_data"):
        st.error("No inat_data folder found. Run api.py first!")
        return
    
    species_folders = [f for f in os.listdir("inat_data") 
                      if os.path.isdir(os.path.join("inat_data", f))]
    
    if not species_folders:
        st.error("No species folders found!")
        return
    
    # Create display names with both scientific and common names
    species_display_names = {}
    for folder in species_folders:
        scientific_name = folder.replace('_', ' ')
        # Just use scientific name for now, we'll get common name when selected
        species_display_names[scientific_name] = folder
    
    # Species selection dropdown
    selected_display_name = st.selectbox(
        "Choose a species to map:",
        list(species_display_names.keys())
    )
    
    selected_species = species_display_names[selected_display_name]
    
    # Load coordinates for selected species (now also gets common name)
    coords, common_name = load_species_coordinates(selected_species)
    
    if not coords:
        st.warning(f"No coordinate data found for {selected_species}")
        return
    
    # Show basic stats
    scientific_name = selected_species.replace('_', ' ')
    
    if common_name:
        st.write(f"**Species:** {scientific_name} ({common_name})")
    else:
        st.write(f"**Species:** {scientific_name}")
        
    st.write(f"**Observations with coordinates:** {len(coords)}")
    
    # Calculate and show range info
    centroid, max_distance, point1, point2 = calculate_centroid_and_max_span(coords)
    st.write(f"**Geographic span:** {max_distance:.1f} km (furthest points apart)")
    st.write(f"**Centroid:** {centroid[0]:.4f}°, {centroid[1]:.4f}°")
    
    if point1 and point2:
        st.write(f"**Furthest points:** Obs {point1[2]} to Obs {point2[2]}")
    
    # Create and display map
    species_map = create_species_map(selected_species, coords)
    
    if species_map:
        st.write("### Map")
        st.write("🔴 Red star = centroid, 🔵 Blue markers = observations, 🟢 Green markers = furthest points, Green circle = species span")
        
        # Display the map
        st_folium(species_map, width=700, height=500)
    
    # Show coordinate list (optional)
    if st.checkbox("Show all coordinates"):
        st.write("### All Observations")
        for i, (lat, lon, obs_id) in enumerate(coords, 1):
            st.write(f"{i}. Observation {obs_id}: {lat:.4f}°, {lon:.4f}°")

if __name__ == "__main__":
    main()
