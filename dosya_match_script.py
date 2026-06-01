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
        # Skip broken symlinks or unreadable files
        return None

def build_reference_map(source_dir):
    """
    Scans the main reference directory and maps files by (filename, size).
    This acts as a fast lookup filter before we do heavy hash checks.
    """
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
                
    print(f"[+] Mapping complete. Found {len(ref_map)} unique (name+size) groups.\n")
    return ref_map

def isolate_duplicates(target_dir, ref_map, safe_zone_dir):
    """
    Compares target directory against the reference map.
    Verifies matches using SHA-256 and safely moves duplicates to a staging area.
    """
    print(f"[*] Analyzing target directory for duplicates: {target_dir}")
    match_count = 0
    
    if not os.path.exists(safe_zone_dir):
        os.makedirs(safe_zone_dir)

    for root, _, files in os.walk(target_dir):
        for file in files:
            full_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(full_path)
                key = (file, file_size)
                
                # Fast track: check if filename and size match anything in the source
                if key in ref_map:
                    target_hash = calculate_sha256(full_path)
                    if not target_hash:
                        continue
                        
                    is_duplicate = False
                    # Deep validation: compare actual hashes
                    for candidate_path in ref_map[key]:
                        source_hash = calculate_sha256(candidate_path)
                        if target_hash == source_hash:
                            is_duplicate = True
                            break
                    
                    if is_duplicate:
                        match_count += 1
                        # Rename slightly to avoid filename collisions in the staging folder
                        staged_filename = f"dup_{match_count}_{file}"
                        destination_path = os.path.join(safe_zone_dir, staged_filename)
                        
                        shutil.move(full_path, destination_path)
                        print(f"[MATCH #{match_count}] Isolated: {file}")
                        
            except (OSError, PermissionError):
                continue
                
    print("\n" + "="*50)
    print(f"[+] Process finished. {match_count} duplicates moved to: {safe_zone_dir}")

if __name__ == '__main__':
    # Define your local paths here
    SOURCE_DIR = r"C:\Path\To\Main_Gallery"
    TARGET_DIR = r"C:\Path\To\Suspected_Duplicates"
    STAGING_DIR = r"C:\Path\To\Desktop\Isolated_Duplicates"

    # Run the pipeline
    reference_data = build_reference_map(SOURCE_DIR)
    isolate_duplicates(TARGET_DIR, reference_data, STAGING_DIR)