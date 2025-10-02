import requests
import os
import json

def extract_and_validate_coordinates(obs):
    """
    Extract and validate geocoordinates from iNaturalist observation.
    Returns (latitude, longitude) or (None, None) if invalid.
    """
    # Try multiple sources for coordinates in order of preference
    latitude = longitude = None
    
    # Method 1: Direct latitude/longitude fields (most reliable)
    if obs.get("latitude") is not None and obs.get("longitude") is not None:
        try:
            latitude = float(obs.get("latitude"))
            longitude = float(obs.get("longitude"))
        except (ValueError, TypeError):
            pass
    
    # Method 2: Parse from location string (backup method)
    if latitude is None and obs.get("location"):
        try:
            coords = obs.get("location").strip().split(",")
            if len(coords) == 2:
                latitude = float(coords[0].strip())
                longitude = float(coords[1].strip())
        except (ValueError, IndexError, AttributeError):
            pass
    
    # Method 3: Extract from geojson if available
    if latitude is None and obs.get("geojson") and obs.get("geojson", {}).get("coordinates"):
        try:
            coords = obs["geojson"]["coordinates"]
            if len(coords) >= 2:
                # GeoJSON uses [longitude, latitude] order
                longitude = float(coords[0])
                latitude = float(coords[1])
        except (ValueError, IndexError, KeyError, TypeError):
            pass
    
    # Validate coordinate ranges
    if latitude is not None and longitude is not None:
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            print(f"⚠️  Invalid coordinates for obs {obs.get('id', 'unknown')}: lat={latitude}, lon={longitude}")
            return None, None
        
        # Check for obviously invalid coordinates (0,0 or other suspicious values)
        if latitude == 0 and longitude == 0:
            print(f"⚠️  Suspicious null coordinates for obs {obs.get('id', 'unknown')}")
            return None, None
    
    return latitude, longitude

def count_existing_images(out_dir):
    """Count total images that already exist in the output directory."""
    count = 0
    for root, dirs, files in os.walk(out_dir):
        for file in files:
            if file.endswith('.jpg'):
                count += 1
    return count

def download_inat_images(taxon_name="Aves", target_new_images=100, per_page=30, out_dir="inat_data"):
    """
    Download a target number of NEW images from iNaturalist for a given taxon.
    Will skip existing files and continue until target_new_images is reached.
    """
    os.makedirs(out_dir, exist_ok=True)
    base_url = "https://api.inaturalist.org/v1/observations"

    # Count existing images at start
    initial_img_count = count_existing_images(out_dir)
    new_img_count = 0
    skipped_count = 0
    page = 1
    
    print(f"📊 Starting with {initial_img_count} existing images")
    print(f"🎯 Target: {target_new_images} new images for {taxon_name}")
    
    while new_img_count < target_new_images:
        params = {
            "taxon_name": taxon_name,     # scientific name (e.g., "Aves" for birds, "Plantae" for plants)
            "quality_grade": "research",  # only verified observations
            "has":"photos",
            "per_page": per_page,
            "page": page
        }
        
        print(f"📄 Fetching page {page}... (downloaded {new_img_count}/{target_new_images} new images)")
        r = requests.get(base_url, params=params)
        data = r.json()
        
        # Check if we got any results
        if not data.get("results"):
            print(f"⚠️  No more results found at page {page}. Stopping.")
            break
        
        results_on_page = len(data["results"])
        new_on_page = 0

        for obs in data["results"]:
            taxon = obs.get("taxon", {})
            species = taxon.get("name", "unknown_species").replace(" ", "_")

            if "photos" in obs and obs["photos"]:
                # Extract and validate geocoordinate data
                latitude, longitude = extract_and_validate_coordinates(obs)
                place_guess = obs.get("place_guess", "")
                
                # Get additional location metadata
                geojson = obs.get("geojson")
                positional_accuracy = obs.get("positional_accuracy")
                geoprivacy = obs.get("geoprivacy")
                coordinate_uncertainty = obs.get("coordinate_uncertainty_in_meters")

                # Create comprehensive metadata dictionary with georeference validation
                metadata = {
                    "observation_id": obs.get("id"),
                    "species": species,
                    "taxonomy": {
                        "taxon_id": taxon.get("id"),
                        "common_name": taxon.get("preferred_common_name"),
                        "rank": taxon.get("rank"),
                        "kingdom": taxon.get("kingdom", {}).get("name") if taxon.get("kingdom") else None
                    },
                    "coordinates": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "has_coordinates": latitude is not None and longitude is not None,
                        "coordinate_uncertainty_meters": coordinate_uncertainty,
                        "positional_accuracy": positional_accuracy,
                        "geoprivacy": geoprivacy,
                        "coordinate_source": "iNaturalist_API"
                    },
                    "location": {
                        "place_guess": place_guess,
                        "country": obs.get("place_country_name"),
                        "state_province": obs.get("place_state_name"),
                        "county": obs.get("place_county_name")
                    },
                    "observation_metadata": {
                        "observed_on": obs.get("observed_on"),
                        "time_observed_at": obs.get("time_observed_at"),
                        "quality_grade": obs.get("quality_grade"),
                        "captive": obs.get("captive"),
                        "user_id": obs.get("user", {}).get("id") if obs.get("user") else None,
                        "license": obs.get("license_code")
                    },
                    "image_metadata": {
                        "image_url": obs["photos"][0]["url"].replace("square", "medium"),
                        "photo_id": obs["photos"][0].get("id"),
                        "attribution": obs["photos"][0].get("attribution"),
                        "license": obs["photos"][0].get("license_code")
                    }
                }

                # Check if this observation already exists
                species_dir = os.path.join(out_dir, species)
                filename = os.path.join(species_dir, f"{obs['id']}.jpg")
                metadata_filename = os.path.join(species_dir, f"{obs['id']}_metadata.json")
                
                if os.path.exists(filename) and os.path.exists(metadata_filename):
                    skipped_count += 1
                    continue

                # Check if we've reached our target
                if new_img_count >= target_new_images:
                    print(f"🎯 Target reached! Downloaded {target_new_images} new images.")
                    break

                img_url = obs["photos"][0]["url"].replace("square", "medium")
                img_data = requests.get(img_url).content

                os.makedirs(species_dir, exist_ok=True)

                # Save image
                filename = os.path.join(species_dir, f"{obs['id']}.jpg")
                with open(filename, "wb") as f:
                    f.write(img_data)

                # Save metadata as JSON
                metadata_filename = os.path.join(species_dir, f"{obs['id']}_metadata.json")
                with open(metadata_filename, "w") as f:
                    json.dump(metadata, f, indent=2)

                new_img_count += 1
                new_on_page += 1
                
                # Enhanced logging with coordinate quality info
                if latitude and longitude:
                    uncertainty_info = ""
                    if coordinate_uncertainty:
                        uncertainty_info = f", ±{coordinate_uncertainty}m"
                    elif positional_accuracy:
                        uncertainty_info = f", accuracy: {positional_accuracy}"
                    
                    coord_info = f" (lat: {latitude:.6f}, lon: {longitude:.6f}{uncertainty_info})"
                    if geoprivacy:
                        coord_info += f" [privacy: {geoprivacy}]"
                else:
                    coord_info = " (no coordinates)"
                
                print(f"Saved {filename}{coord_info}")
        
        # Check if we've reached target within the inner loop
        if new_img_count >= target_new_images:
            break
            
        page += 1

    # Calculate total images now in folder
    total_img_count = count_existing_images(out_dir)
    
    print(f"\n✅ Downloaded {new_img_count} new images into {out_dir}/")
    if skipped_count > 0:
        print(f"⏭️  Skipped {skipped_count} existing images")
    print(f"📊 Total images in folder: {total_img_count}")
    print(f"📊 Total processed this session: {new_img_count + skipped_count}")
    
    # Count and report coordinate statistics
    coord_count = 0
    uncertain_count = 0
    
    for root, dirs, files in os.walk(out_dir):
        for file in files:
            if file.endswith('_metadata.json'):
                try:
                    with open(os.path.join(root, file), 'r') as f:
                        meta = json.load(f)
                        if meta.get('coordinates', {}).get('has_coordinates'):
                            coord_count += 1
                            uncertainty = meta.get('coordinates', {}).get('coordinate_uncertainty_meters')
                            if uncertainty and uncertainty > 1000:  # More than 1km uncertainty
                                uncertain_count += 1
                except (json.JSONDecodeError, KeyError):
                    continue
    
    if total_img_count > 0:
        print(f"📍 Georeferenced: {coord_count}/{total_img_count} ({coord_count/total_img_count*100:.1f}%)")
        if uncertain_count > 0:
            print(f"⚠️  High uncertainty (>1km): {uncertain_count} observations")

download_inat_images(target_new_images=100)
#download_inat_images(taxon_name="Aves", target_new_images=50)
#download_inat_images(taxon_name="Plantae", target_new_images=200)

