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
    """
    print(f"[*] Processing and sorting target directory: {target_dir}")
    dup_count = 0
    unique_count = 0
    
    # Ensure both output folders exist
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
                
                # 1. Step: Check if filename and size match any reference
                if key in ref_map:
                    target_hash = calculate_sha256(full_path)
                    if target_hash:
                        # 2. Step: Deep verification using SHA-256
                        for candidate_path in ref_map[key]:
                            source_hash = calculate_sha256(candidate_path)
                            if target_hash == source_hash:
                                is_duplicate = True
                                break
                
                # Route the file based on verification
                if is_duplicate:
                    dup_count += 1
                    dest_name = f"dup_{dup_count}_{file}"
                    dest_path = os.path.join(duplicates_dir, dest_name)
                    shutil.move(full_path, dest_path)
                    print(f"[DUPLICATE #{dup_count}] Isolated: {file}")
                else:
                    # File is completely unique! Move it to the unique staging area
                    unique_count += 1
                    dest_name = f"unique_{unique_count}_{file}"
                    dest_path = os.path.join(uniques_dir, dest_name)
                    shutil.move(full_path, dest_path)
                    print(f"[UNIQUE #{unique_count}] Extracted: {file}")
                        
            except (OSError, PermissionError):
                continue
                
    print("\n" + "="*50)
    print(f"[+] Pipeline finished tracking.")
    print(f"-> Total Duplicates isolated: {dup_count} (Saved to {duplicates_dir})")
    print(f"-> Total Unique files extracted: {unique_count} (Saved to {uniques_dir})")

if __name__ == '__main__':
    # Define your paths
    SOURCE_DIR = r"C:\Path\To\Main_Gallery"
    TARGET_DIR = r"C:\Path\To\Suspected_Duplicates"
    
    # Output destinations
    DUPLICATES_STAGING = r"C:\Path\To\Desktop\Isolated_Duplicates"
    UNIQUES_STAGING = r"C:\Path\To\Desktop\New_Unique_Photos"

    # Start the clean-up engine
    reference_data = build_reference_map(SOURCE_DIR)
    process_and_sort_gallery(TARGET_DIR, reference_data, DUPLICATES_STAGING, UNIQUES_STAGING)
