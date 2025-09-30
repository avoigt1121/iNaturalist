import requests
import os

def download_inat_images(taxon_name="Aves", per_page=30, max_pages=3, out_dir="inat_data"):
    """
    Download images from iNaturalist for a given taxon.
    """
    os.makedirs(out_dir, exist_ok=True)
    base_url = "https://api.inaturalist.org/v1/observations"

    img_count = 0
    for page in range(1, max_pages+1):
        params = {
            "taxon_name": taxon_name,     # scientific name (e.g., "Aves" for birds, "Plantae" for plants)
            "quality_grade": "research",  # only verified observations
            "has":"photos",
            "per_page": per_page,
            "page": page
        }
        r = requests.get(base_url, params=params)
        data = r.json()

        for obs in data["results"]:
            taxon = obs.get("taxon", {})
            species = taxon.get("name", "unknown_species").replace(" ", "_")

            if "photos" in obs and obs["photos"]:
                img_url = obs["photos"][0]["url"].replace("square", "medium")
                img_data = requests.get(img_url).content

                species_dir = os.path.join(out_dir, species)
                os.makedirs(species_dir, exist_ok=True)

                filename = os.path.join(species_dir, f"{obs['id']}.jpg")
                with open(filename, "wb") as f:
                    f.write(img_data)

                img_count += 1
                print(f"Saved {filename}")

    print(f"\n✅ Downloaded {img_count} images into {out_dir}/")

download_inat_images()
#download_inat_images(taxon_name="Aves", per_page=20, max_pages=2)

