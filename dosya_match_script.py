import os
import shutil
import hashlib

def calculate_sha256(file_path):
    """Generates SHA-256 hash for a file. Uses chunks to keep memory usage low."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (OSError, PermissionError):
        return None

def get_safe_path(target_folder, original_filename):
    """
    Ensures that moving a file won't overwrite an existing file.
    If 'IMG_1234.jpg' exists, it returns 'IMG_1234 (1).jpg' without touching the root name.
    """
    base_name, extension = os.path.splitext(original_filename)
    counter = 1
    new_path = os.path.join(target_folder, original_filename)
    
    # If file already exists in the destination, append (1), (2), etc.
    while os.path.exists(new_path):
        new_filename = f"{base_name} ({counter}){extension}"
        new_path = os.path.join(target_folder, new_filename)
        counter += 1
        
    return new_path

def build_reference_map(source_dir):
    """Scans the main reference directory and maps files by (filename, size)."""
    ref_map = {}
    print(f"[*] Scanning reference directory: {source_dir}")
    
    for root, _, files in os.walk(source_dir):
        for file in files:
            full_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(full_path)
                key = (file, file_size)
                
                if key not in ref_map:
                    ref_map[key] = []
                ref_map[key].append(full_path)
            except (OSError, PermissionError):
                continue
                
    print(f"[+] Mapping complete. Found {len(ref_map)} unique groups.\n")
    return ref_map

def process_and_sort_gallery(target_dir, ref_map, duplicates_dir, uniques_dir):
    """
    Scans the target directory. 
    Moves actual duplicates to 'duplicates_dir' and completely unique files to 'uniques_dir'.
    Preserves original filenames unless a naming collision occurs.
    """
    print(f"[*] Processing and sorting target directory: {target_dir}")
    dup_count = 0
    unique_count = 0
    
    for folder in [duplicates_dir, uniques_dir]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    for root, _, files in os.walk(target_dir):
        for file in files:
            full_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(full_path)
                key = (file, file_size)
                
                is_duplicate = False
                
                # Step 1: Pre-filter check
                if key in ref_map:
                    target_hash = calculate_sha256(full_path)
                    if target_hash:
                        # Step 2: SHA-256 verification
                        for candidate_path in ref_map[key]:
                            source_hash = calculate_sha256(candidate_path)
                            if target_hash == source_hash:
                                is_duplicate = True
                                break
                
                # Step 3: Route files with safe naming check
                if is_duplicate:
                    dup_count += 1
                    # Finds a safe path like C:\...\Desktop\Duplicates\IMG_1234.jpg
                    destination_path = get_safe_path(duplicates_dir, file)
                    shutil.move(full_path, destination_path)
                    print(f"[DUPLICATE #{dup_count}] Isolated: {os.path.basename(destination_path)}")
                else:
                    unique_count += 1
                    # Finds a safe path like C:\...\Desktop\Uniques\IMG_1234.jpg
                    destination_path = get_safe_path(uniques_dir, file)
                    shutil.move(full_path, destination_path)
                    print(f"[UNIQUE #{unique_count}] Extracted: {os.path.basename(destination_path)}")
                        
            except (OSError, PermissionError):
                continue
                
    print("\n" + "="*50)
    print(f"[+] Pipeline finished tracking.")
    print(f"-> Total Duplicates isolated: {dup_count} (Saved to {duplicates_dir})")
    print(f"-> Total Unique files extracted: {unique_count} (Saved to {uniques_dir})")

if __name__ == '__main__':
    SOURCE_DIR = r"C:\Path\To\Main_Gallery"
    TARGET_DIR = r"C:\Path\To\Suspected_Duplicates"
    
    DUPLICATES_STAGING = r"C:\Path\To\Desktop\Isolated_Duplicates"
    UNIQUES_STAGING = r"C:\Path\To\Desktop\New_Unique_Photos"

    reference_data = build_reference_map(SOURCE_DIR)
    process_and_sort_gallery(TARGET_DIR, reference_data, DUPLICATES_STAGING, UNIQUES_STAGING)
