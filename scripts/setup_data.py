#!/usr/bin/env python3
"""
Improved automated download script with better messaging and file handling
"""

import os
import time
import zipfile
from pathlib import Path
from typing import Optional, List, Dict, Tuple
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
    """Improved download handler with better file management"""
    
    CHUNK_SIZE = 8192
    MAX_RETRIES = 3
    MIN_SPACE_GB = 10
    DOWNLOAD_FOLDER = str(Path.home() / "Downloads")
    DOWNLOAD_TIMEOUT = 900  # 15 minutes

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

    def _find_downloaded_file(self, base_name: str) -> Optional[Path]:
        """Find the most recently downloaded matching file."""
        pattern = re.compile(rf"^{re.escape(base_name)}( \(\d+\))?\.zip$", re.IGNORECASE)
        candidates = []
        
        for file in Path(self.DOWNLOAD_FOLDER).glob("*.zip"):
            if pattern.match(file.name):
                candidates.append(file)
        
        if not candidates:
            return None
            
        return max(candidates, key=lambda f: f.stat().st_mtime)

    def _wait_for_download_completion(self, file_path: Path) -> bool:
        """Wait for file to stop growing in size."""
        print(f"{Color.BLUE}Waiting for download to complete...{Color.RESET}")
        last_size = -1
        stable_count = 0
        
        for _ in range(30):  # Max 30 checks (about 1 minute)
            try:
                current_size = file_path.stat().st_size
                if current_size == last_size:
                    stable_count += 1
                    if stable_count >= 3:
                        return True
                else:
                    stable_count = 0
                    last_size = current_size
            except FileNotFoundError:
                pass
            
            time.sleep(2)
        
        return False

    def _cleanup_downloads(self, base_name: str):
        """Remove any leftover files from Downloads folder."""
        pattern = re.compile(rf"^{re.escape(base_name)}( \(\d+\))?\.zip$", re.IGNORECASE)
        for file in Path(self.DOWNLOAD_FOLDER).glob("*.zip"):
            if pattern.match(file.name):
                try:
                    file.unlink()
                    print(f"{Color.YELLOW}Cleaned up: {file}{Color.RESET}")
                except Exception as e:
                    print(f"{Color.YELLOW}Couldn't clean up {file}: {e}{Color.RESET}")

    def _show_spinner(self, message: str):
        """Display a spinning wheel animation."""
        spinner = ['-', '\\', '|', '/']
        for i in range(4):
            sys.stdout.write(f"\r{message} {spinner[i % 4]}")
            sys.stdout.flush()
            time.sleep(0.1)

    def process_dataset(self, dataset_type: DatasetType) -> Tuple[bool, str]:
        """Complete dataset processing workflow."""
        dataset_cfg = self.config.DATASETS[dataset_type]
        target_dir = self.config.get_path(dataset_type)
        correct_zip_name = dataset_cfg["zip_name"]
        correct_zip_path = target_dir.parent / correct_zip_name
        base_name = correct_zip_name.split('.')[0]
        
        # Skip if already exists and valid
        if target_dir.exists() and self._verify_dataset_contents(dataset_type):
            return True, f"{Color.GREEN}Dataset already exists and is valid{Color.RESET}"
            
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        
        # Check for existing file in target location
        if correct_zip_path.exists():
            print(f"{Color.YELLOW}Found existing zip file at target location{Color.RESET}")
            if not self._verify_zip(correct_zip_path):
                correct_zip_path.unlink()
            else:
                if self._extract_zip(correct_zip_path, target_dir):
                    if self._verify_dataset_contents(dataset_type):
                        return True, f"{Color.GREEN}Successfully processed existing file{Color.RESET}"
        
        # Check Downloads folder for matching file
        print(f"\n{Color.BOLD}Checking for existing download in Downloads folder...{Color.RESET}")
        downloaded_file = self._find_downloaded_file(base_name)
        
        if downloaded_file:
            print(f"{Color.GREEN}✓ Found matching file: {downloaded_file}{Color.RESET}")
            if not self._wait_for_download_completion(downloaded_file):
                print(f"{Color.YELLOW}⚠ Download may still be in progress{Color.RESET}")
                return False, f"{Color.RED}Download incomplete{Color.RESET}"
            
            # Move and process the file
            try:
                if correct_zip_path.exists():
                    correct_zip_path.unlink()
                shutil.move(str(downloaded_file), str(correct_zip_path))
                print(f"{Color.GREEN}✓ Moved to: {correct_zip_path}{Color.RESET}")
                
                if self._process_zip(correct_zip_path, target_dir, dataset_type):
                    self._cleanup_downloads(base_name)
                    return True, f"{Color.GREEN}✓ Processing successful{Color.RESET}"
            except Exception as e:
                print(f"{Color.RED}✗ Error moving file: {e}{Color.RESET}")
                return False, f"{Color.RED}File processing failed{Color.RESET}"
        else:
            print(f"{Color.YELLOW}ⓘ No matching file found in Downloads folder{Color.RESET}")
        
        # Automatic download flow
        print(f"\n{Color.BOLD}Automatic Download:{Color.RESET}")
        print(f"1. Your browser will open to: {Color.CYAN}{dataset_cfg['download_url']}{Color.RESET}")
        print(f"2. Save the file to your default Downloads folder")
        print(f"3. The script will automatically detect when download completes")
        
        try:
            webbrowser.open(dataset_cfg['download_url'])
        except Exception as e:
            print(f"{Color.YELLOW}⚠ Couldn't open browser automatically: {e}{Color.RESET}")
        
        print(f"\n{Color.BLUE}⏳ Monitoring Downloads folder for {correct_zip_name}...{Color.RESET}")
        
        start_time = time.time()
        spinner_pos = 0
        spinner_chars = ['-', '\\', '|', '/']
        
        while time.time() - start_time < self.DOWNLOAD_TIMEOUT:
            downloaded_file = self._find_downloaded_file(base_name)
            if downloaded_file and self._wait_for_download_completion(downloaded_file):
                print(f"\r{Color.GREEN}✓ Download complete: {downloaded_file}{Color.RESET}")
                
                try:
                    if correct_zip_path.exists():
                        correct_zip_path.unlink()
                    shutil.move(str(downloaded_file), str(correct_zip_path))
                    print(f"{Color.GREEN}✓ Moved to: {correct_zip_path}{Color.RESET}")
                    
                    if self._process_zip(correct_zip_path, target_dir, dataset_type):
                        self._cleanup_downloads(base_name)
                        return True, f"{Color.GREEN}✓ Processing successful{Color.RESET}"
                except Exception as e:
                    print(f"{Color.RED}✗ Error processing file: {e}{Color.RESET}")
                    return False, f"{Color.RED}Processing failed{Color.RESET}"
            
            # Display spinning wheel
            sys.stdout.write(f"\r{Color.BLUE}⏳ Monitoring {spinner_chars[spinner_pos % 4]} {Color.RESET}")
            sys.stdout.flush()
            spinner_pos += 1
            time.sleep(0.2)
        
        print(f"\n{Color.RED}✗ Timeout waiting for download.{Color.RESET}")
        return False, f"{Color.RED}Download timeout{Color.RESET}"
    
    def _process_zip(self, zip_path: Path, target_dir: Path, dataset_type: DatasetType) -> bool:
        """Handle the complete processing of a zip file."""
        if not self._verify_zip(zip_path):
            return False
        
        if not self._extract_zip(zip_path, target_dir):
            return False
        
        if not self._verify_dataset_contents(dataset_type):
            shutil.rmtree(target_dir)
            return False
        
        try:
            zip_path.unlink()
        except OSError as e:
            print(f"{Color.YELLOW}Warning: {e}{Color.RESET}")
        
        return True

    def _verify_dataset_contents(self, dataset_type: DatasetType) -> bool:
        """Verify the extracted dataset contents."""
        path = self.config.get_path(dataset_type)
        dataset_cfg = self.config.DATASETS[dataset_type]
        
        if not path.exists():
            return False

        required_items = set(dataset_cfg.get("required_files", set()))
        required_folders = set(dataset_cfg.get("required_folders", set()))
        
        # Extract folders from required_files (those ending with /)
        folders_from_files = {item[:-1] for item in required_items if item.endswith('/')}
        all_required_folders = required_folders.union(folders_from_files)
        required_files = {item for item in required_items if not item.endswith('/')}

        found_files = set()
        found_folders = set()
        
        for root, dirs, files in os.walk(path):
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

        missing_files = required_files - found_files
        missing_folders = all_required_folders - found_folders

        if missing_files or missing_folders:
            print(f"{Color.YELLOW}Verification failed for {dataset_type.name}:{Color.RESET}")
            if missing_files:
                print(f"{Color.RED}Missing files:{Color.RESET}")
                for f in sorted(missing_files):
                    print(f" - {f}")
            if missing_folders:
                print(f"{Color.RED}Missing folders:{Color.RESET}")
                for d in sorted(missing_folders):
                    print(f" - {d}/")
            return False
        
        return True

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
        processed_count = 0
        total_tasks = len(task_numbers) if task_numbers else 3
        
        for task in task_numbers or [2, 3, 4]:
            if task not in task_map:
                print(f"{Color.RED}Invalid task number: {task}{Color.RESET}")
                exit_code = 1
                continue
                
            dataset_type = task_map[task]
            print(f"\n{Color.BOLD}Processing Task {task} ({dataset_type.name}){Color.RESET}")
            print(f"{Color.BLUE}{'-'*40}{Color.RESET}")
            
            success, message = downloader.process_dataset(dataset_type)
            print(message)
            
            if success:
                processed_count += 1
            else:
                exit_code = 1
        
        if processed_count > 0:
            if processed_count == total_tasks:
                print(f"\n{Color.GREEN}All requested datasets processed successfully!{Color.RESET}")
            else:
                print(f"\n{Color.YELLOW}Processed {processed_count} of {total_tasks} datasets{Color.RESET}")
        else:
            print(f"\n{Color.RED}No datasets were processed successfully{Color.RESET}")
        
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
        description="MLPC2025 Dataset Setup",
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
    
    print(f"\n{Color.BLUE}Operation completed in {elapsed:.1f}s{Color.RESET}")
    sys.exit(exit_code)