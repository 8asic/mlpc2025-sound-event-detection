#!/usr/bin/env python3
"""
Complete automated manual download script with enhanced folder verification
"""

import os
import time
import zipfile
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Set
import shutil
import sys
import webbrowser
import re
import requests
from tqdm import tqdm
from src.config import config, DatasetType

class Color:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class DataDownloader:
    """Handles dataset operations with smart manual download support"""
    
    CHUNK_SIZE = 8192
    MAX_RETRIES = 3
    MIN_SPACE_GB = 10
    DOWNLOAD_FOLDER = str(Path.home() / "Downloads")  # Default download location

    def __init__(self):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'MLPC2025-DataDownloader/1.0'})

    def _verify_zip(self, file_path: Path) -> bool:
        """Verify the file is a valid ZIP archive."""
        try:
            with zipfile.ZipFile(file_path, 'r') as test_zip:
                if not test_zip.filelist:
                    raise zipfile.BadZipFile("Empty ZIP file")
                return True
        except zipfile.BadZipFile as e:
            print(f"{Color.RED}Invalid ZIP file:{Color.RESET} {e}")
            return False

    def _extract_zip(self, zip_path: Path, extract_to: Path) -> bool:
        """Safely extract a zip file with progress tracking."""
        try:
            print(f"{Color.BLUE}Extracting {zip_path.name}{Color.RESET}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                total_files = len(zip_ref.infolist())
                
                with tqdm(total=total_files, unit='file', desc=f"{Color.CYAN}Extracting{Color.RESET}") as progress:
                    for file in zip_ref.infolist():
                        zip_ref.extract(file, extract_to)
                        progress.update(1)
            return True
        except (zipfile.BadZipFile, IOError) as e:
            print(f"{Color.RED}Extraction failed:{Color.RESET} {e}")
            if extract_to.exists():
                shutil.rmtree(extract_to)
            return False

    def _find_downloaded_file(self, base_name: str, download_folder: str) -> Optional[Path]:
        """Find the most recently downloaded file matching the base name."""
        pattern = re.compile(rf"^{re.escape(base_name)}( \(\d+\))?\.zip$", re.IGNORECASE)
        candidates = []
        
        for file in Path(download_folder).glob("*.zip"):
            if pattern.match(file.name):
                candidates.append(file)
        
        if not candidates:
            return None
            
        # Return the most recently modified file
        return max(candidates, key=lambda f: f.stat().st_mtime)

    def _verify_dataset_contents(self, dataset_type: DatasetType) -> bool:
        """Enhanced verification that checks both files and folders."""
        path = self.config.get_path(dataset_type)
        dataset_cfg = self.config.DATASETS[dataset_type]
        
        if not path.exists():
            print(f"{Color.RED}Dataset directory not found: {path}{Color.RESET}")
            return False

        # Get all required items
        required_files = set()
        required_folders = set()
        
        for item in dataset_cfg["required_files"]:
            if item.endswith('/'):
                required_folders.add(item[:-1])
            else:
                required_files.add(item)
        
        # Also check required_folders if specified
        if "required_folders" in dataset_cfg:
            required_folders.update(dataset_cfg["required_folders"])

        # Scan the directory
        found_files = set()
        found_folders = set()
        
        for root, dirs, files in os.walk(path):
            # Record relative paths
            rel_root = os.path.relpath(root, path)
            
            for file in files:
                if rel_root == '.':
                    found_files.add(file)
                else:
                    found_files.add(f"{rel_root}/{file}")
            
            for dir in dirs:
                if rel_root == '.':
                    found_folders.add(dir)
                else:
                    found_folders.add(f"{rel_root}/{dir}")

        # Check for missing items
        missing_files = required_files - found_files
        missing_folders = required_folders - found_folders

        if missing_files or missing_folders:
            print(f"{Color.YELLOW}Found in {path}:{Color.RESET}")
            print("Files:")
            for f in sorted(found_files):
                print(f" - {f}")
            print("Folders:")
            for d in sorted(found_folders):
                print(f" - {d}/")
            
            print(f"{Color.RED}Missing:{Color.RESET}")
            for f in sorted(missing_files):
                print(f" - File: {f}")
            for d in sorted(missing_folders):
                print(f" - Folder: {d}/")
            
            return False
        
        return True

    def manual_download(self, dataset_type: DatasetType) -> Tuple[bool, str]:
        """Handle manual download with automatic file finding and renaming"""
        dataset_cfg = self.config.DATASETS[dataset_type]
        target_dir = self.config.get_path(dataset_type)
        correct_zip_name = dataset_cfg["zip_name"]
        correct_zip_path = target_dir.parent / correct_zip_name
        
        # Skip if dataset already exists and is valid
        if target_dir.exists() and self._verify_dataset_contents(dataset_type):
            return True, f"{Color.GREEN}Dataset exists{Color.RESET}"
            
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        
        # Display download instructions
        print(f"\n{Color.BOLD}Manual Download Instructions:{Color.RESET}")
        print(f"1. Click this link to download: {Color.CYAN}{dataset_cfg['download_url']}{Color.RESET}")
        print(f"2. Save the file with default name (any added numbers will be handled automatically)")
        print(f"3. The script will automatically find and move it to: {Color.YELLOW}{correct_zip_path}{Color.RESET}")
        
        # Try to open browser automatically
        try:
            webbrowser.open(dataset_cfg['download_url'])
        except Exception as e:
            print(f"{Color.YELLOW}Couldn't open browser automatically: {e}{Color.RESET}")
        
        # Wait for file to appear in Downloads folder
        print(f"\n{Color.BLUE}Waiting for file matching '{correct_zip_name}' in Downloads folder...{Color.RESET}")
        print("(Will automatically detect files with added numbers like '(1)')")
        
        downloaded_file = None
        start_time = time.time()
        timeout = 900  # 15 minute timeout
        
        while time.time() - start_time < timeout:
            downloaded_file = self._find_downloaded_file(correct_zip_name.split('.')[0], self.DOWNLOAD_FOLDER)
            if downloaded_file:
                break
            time.sleep(2)
            print(".", end="", flush=True)
        
        print()  # New line after progress dots
        
        if not downloaded_file:
            print(f"{Color.RED}Timeout waiting for file. Please try again.{Color.RESET}")
            return False, f"{Color.RED}Download timeout{Color.RESET}"
        
        print(f"{Color.GREEN}Found downloaded file: {downloaded_file}{Color.RESET}")
        
        # Rename and move to correct location
        try:
            if downloaded_file != correct_zip_path:
                if correct_zip_path.exists():
                    correct_zip_path.unlink()
                shutil.move(str(downloaded_file), str(correct_zip_path))
                print(f"{Color.GREEN}Moved to: {correct_zip_path}{Color.RESET}")
        except Exception as e:
            print(f"{Color.RED}Error moving file: {e}{Color.RESET}")
            return False, f"{Color.RED}File move failed{Color.RESET}"
        
        # Verify the downloaded file
        if not self._verify_zip(correct_zip_path):
            return False, f"{Color.RED}Invalid ZIP file{Color.RESET}"
        
        # Extract the dataset
        if not self._extract_zip(correct_zip_path, target_dir):
            return False, f"{Color.RED}Extraction failed{Color.RESET}"
        
        # Verify extracted contents
        if not self._verify_dataset_contents(dataset_type):
            return False, f"{Color.RED}Dataset incomplete{Color.RESET}"
        
        # Clean up
        try:
            correct_zip_path.unlink()
        except OSError as e:
            print(f"{Color.YELLOW}Warning: {e}{Color.RESET}")
        
        return True, f"{Color.GREEN}Success{Color.RESET}"

def main(task_numbers: Optional[List[int]] = None) -> int:
    """Main entry point for dataset setup."""
    task_map = {
        2: DatasetType.EXPLORATION,
        3: DatasetType.CLASSIFICATION, 
        4: DatasetType.CHALLENGE
    }
    
    try:
        downloader = DataDownloader()
        exit_code = 0
        
        for task in task_numbers or [2, 3, 4]:
            if task not in task_map:
                print(f"{Color.RED}Invalid task number: {task}{Color.RESET}")
                exit_code = 1
                continue
                
            dataset_type = task_map[task]
            print(f"\n{Color.BOLD}Task {task} ({dataset_type.name}){Color.RESET}")
            print(f"{Color.BLUE}{'-'*40}{Color.RESET}")
            
            success, message = downloader.manual_download(dataset_type)
            print(message)
            
            if not success:
                exit_code = 1
        
        if exit_code == 0:
            print(f"\n{Color.GREEN}All datasets ready!{Color.RESET}")
        else:
            print(f"\n{Color.YELLOW}Some datasets failed{Color.RESET}")
        
        return exit_code
    
    except KeyboardInterrupt:
        print(f"\n{Color.RED}Operation cancelled{Color.RESET}")
        return 1
    except Exception as e:
        print(f"\n{Color.RED}Error:{Color.RESET} {e}")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MLPC2025 Dataset Setup - Manual Download Helper",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--tasks',
        nargs='+',
        type=int,
        choices=[2, 3, 4],
        help='Task numbers to setup (default: all)'
    )
    args = parser.parse_args()
    
    start_time = time.time()
    exit_code = main(args.tasks)
    elapsed = time.time() - start_time
    
    print(f"\n{Color.BLUE}Completed in {elapsed:.1f}s{Color.RESET}")
    sys.exit(exit_code)