import os
import shutil
import hashlib
import json
from pathlib import Path
from datetime import datetime

CONFIG_FILE = "D:/Games/config.json"

def get_dir_hash(directory):
    """Calculates a hash based on file contents to detect changes."""
    hasher = hashlib.md5()
    for path in sorted(Path(directory).rglob('*')):
        if path.is_file():
            try:
                with open(path, 'rb') as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)
            except OSError:
                continue 
    return hasher.hexdigest()

def run_backup():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found.")
        return

    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    backup_base = Path(config.get("backup_destination", "D:/Games"))
    backup_base.mkdir(parents=True, exist_ok=True)
    
    config_changed = False

    for game in config.get("games", []):
        name = game['name']
        source = Path(game['path'])
        
        if not source.exists():
            print(f"Skipping {name}: Path not found.")
            continue

        target = backup_base / name
        current_hash = get_dir_hash(source)
        last_hash = game.get("last_hash", "")

        if current_hash != last_hash:
            print(f"Update detected for {name}. Syncing...")
            
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
            
            # Generate timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create path.txt with metadata
            info_text = (
                f"Game Name: {name}\n"
                f"Original Path: {source.absolute()}\n"
                f"Backup Date: {timestamp}\n"
                f"File Hash: {current_hash}"
            )
            (target / "path.txt").write_text(info_text)
            
            # Update config object
            game["last_hash"] = current_hash
            game["last_backup"] = timestamp # Also tracking time in JSON
            config_changed = True
            print(f"Successfully backed up {name} at {timestamp}.")
        else:
            print(f"No changes for {name}. Skipping.")

    if config_changed:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print("\nConfig file updated with new hashes and timestamps.")

if __name__ == "__main__":
    run_backup()

