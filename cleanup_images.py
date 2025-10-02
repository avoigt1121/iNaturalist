import os

def clean_images_without_metadata(data_dir="inat_data"):
    """
    Delete images that don't have corresponding JSON metadata files
    """
    deleted_count = 0
    total_images = 0
    
    print(f"🧹 Cleaning images without metadata in {data_dir}/")
    print("=" * 50)
    
    for folder_name in os.listdir(data_dir):
        folder_path = os.path.join(data_dir, folder_name)
        
        # Skip if not a directory
        if not os.path.isdir(folder_path):
            continue
        
        print(f"\n📁 Checking folder: {folder_name}")
        
        folder_deleted = 0
        folder_images = 0
        
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            
            # Only process image files (jpg)
            if file_name.endswith('.jpg'):
                folder_images += 1
                total_images += 1
                
                # Get the observation ID from filename (remove .jpg extension)
                obs_id = file_name[:-4]  # Remove '.jpg'
                
                # Check if corresponding metadata JSON exists
                metadata_file = f"{obs_id}_metadata.json"
                metadata_path = os.path.join(folder_path, metadata_file)
                
                if not os.path.exists(metadata_path):
                    print(f"   ❌ Deleting {file_name} (no metadata)")
                    os.remove(file_path)
                    deleted_count += 1
                    folder_deleted += 1
                else:
                    print(f"   ✅ Keeping {file_name}")
        
        print(f"   📊 Folder summary: {folder_deleted} deleted, {folder_images - folder_deleted} kept")
    
    print("\n" + "=" * 50)
    print(f"🏁 Cleanup complete!")
    print(f"📊 Total images processed: {total_images}")
    print(f"🗑️  Images deleted: {deleted_count}")
    print(f"✅ Images kept: {total_images - deleted_count}")
    
    if deleted_count > 0:
        print(f"\n⚠️  Deleted {deleted_count} images without metadata")
    else:
        print(f"\n🎉 All images have corresponding metadata!")

def preview_cleanup(data_dir="inat_data"):
    """
    Preview what would be deleted without actually deleting
    """
    to_delete = []
    total_images = 0
    
    print(f"🔍 Preview: Images that would be deleted in {data_dir}/")
    print("=" * 50)
    
    for folder_name in os.listdir(data_dir):
        folder_path = os.path.join(data_dir, folder_name)
        
        if not os.path.isdir(folder_path):
            continue
        
        folder_to_delete = []
        
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.jpg'):
                total_images += 1
                obs_id = file_name[:-4]
                metadata_file = f"{obs_id}_metadata.json"
                metadata_path = os.path.join(folder_path, metadata_file)
                
                if not os.path.exists(metadata_path):
                    file_path = os.path.join(folder_path, file_name)
                    to_delete.append(file_path)
                    folder_to_delete.append(file_name)
        
        if folder_to_delete:
            print(f"\n📁 {folder_name}:")
            for file_name in folder_to_delete:
                print(f"   ❌ Would delete: {file_name}")
    
    print("\n" + "=" * 50)
    print(f"📊 Total images: {total_images}")
    print(f"🗑️  Would delete: {len(to_delete)} images")
    print(f"✅ Would keep: {total_images - len(to_delete)} images")
    
    return to_delete

def main():
    """
    Main function with safety check
    """
    print("🧹 Image Cleanup Utility")
    print("This will delete images that don't have corresponding JSON metadata files")
    
    # First, show preview
    to_delete = preview_cleanup()
    
    if not to_delete:
        print("\n🎉 No cleanup needed - all images have metadata!")
        return
    
    # Ask for confirmation
    print(f"\n⚠️  WARNING: This will permanently delete {len(to_delete)} files!")
    response = input("Do you want to proceed? (yes/no): ").lower().strip()
    
    if response in ['yes', 'y']:
        clean_images_without_metadata()
    else:
        print("❌ Cleanup cancelled")

if __name__ == "__main__":
    main()
