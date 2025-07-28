# ./scripts/setup_data.py
"""
Dataset download and setup script for MLPC2025 project.
Handles downloading and extracting the three required datasets with:
- Automatic retries for failed downloads
- Checksum verification
- Progress tracking
- Proper cleanup on failure
"""

import os
import zipfile
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import shutil

import requests
from tqdm import tqdm
from src.config import config, DatasetType

class DataDownloader:
    """Handles all dataset download and extraction operations."""
    
    CHUNK_SIZE = 8192  # For download streaming and checksum calculation
    MAX_RETRIES = 3    # Maximum download attempts per file
    MIN_SPACE_GB = 10  # Minimum required disk space in GB

    def __init__(self):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'MLPC2025-DataDownloader/1.0'})

    def _check_disk_space(self, required_bytes: int) -> bool:
        """Verify sufficient disk space is available (cross-platform)."""
        try:
            import shutil
            usage = shutil.disk_usage(self.config.data_path)
            return usage.free >= required_bytes
        except Exception as e:
            print(f"Warning: Could not check disk space: {e}")
            return True  # Continue if we can't check

    def _verify_checksum(self, file_path: Path, expected_sha256: str) -> bool:
        """Verify file integrity using SHA256 checksum."""
        if not expected_sha256:
            return True  # Skip verification if no checksum provided
            
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(self.CHUNK_SIZE), b''):
                    sha256.update(chunk)
            return sha256.hexdigest() == expected_sha256
        except IOError as e:
            print(f"Checksum verification failed: {e}")
            return False

    def _download_file(self, url: str, dest: Path, expected_sha256: Optional[str] = None) -> bool:
        """
        Download a single file with progress bar and checksum verification.
        
        Args:
            url: Source URL to download from
            dest: Destination path to save to
            expected_sha256: Optional SHA256 checksum for verification
            
        Returns:
            bool: True if download succeeded and checksum matched
        """
        try:
            print(f"Downloading {url} to {dest}")
            with self.session.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                
                total_size = int(r.headers.get('content-length', 0))
                if not self._check_disk_space(total_size):
                    raise IOError("Insufficient disk space for download")

                with open(dest, 'wb') as f, tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=dest.name
                ) as progress:
                    for chunk in r.iter_content(chunk_size=self.CHUNK_SIZE):
                        if chunk:  # Filter out keep-alive chunks
                            f.write(chunk)
                            progress.update(len(chunk))

            if expected_sha256 and not self._verify_checksum(dest, expected_sha256):
                print(f"Checksum mismatch for {dest.name}")
                dest.unlink()
                return False
                
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Download failed: {e}")
            if dest.exists():
                dest.unlink()
            return False

    def download_with_retry(self, url: str, dest: Path, expected_sha256: Optional[str] = None) -> bool:
        """Attempt download with multiple retries."""
        for attempt in range(1, self.MAX_RETRIES + 1):
            print(f"Attempt {attempt}/{self.MAX_RETRIES}")
            if self._download_file(url, dest, expected_sha256):
                return True
            if attempt < self.MAX_RETRIES:
                print("Waiting 5 seconds before retry...")
                time.sleep(5)
        return False

    def _extract_zip(self, zip_path: Path, extract_to: Path) -> bool:
        """Safely extract a zip file with progress tracking."""
        try:
            print(f"Extracting {zip_path.name} to {extract_to}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                total_files = len(zip_ref.infolist())
                
                with tqdm(total=total_files, unit='file', desc="Extracting") as progress:
                    for file in zip_ref.infolist():
                        zip_ref.extract(file, extract_to)
                        progress.update(1)
            return True
        except (zipfile.BadZipFile, IOError) as e:
            print(f"Extraction failed: {e}")
            # Clean up partially extracted files
            if extract_to.exists():
                shutil.rmtree(extract_to)
            return False

    def setup_dataset(self, dataset_type: DatasetType) -> Tuple[bool, str]:
        """
        Complete dataset setup process:
        1. Check if already exists and is valid
        2. Download zip file
        3. Extract contents
        4. Verify extracted files
        5. Clean up zip file
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        dataset_cfg = self.config.DATASETS[dataset_type]
        target_dir = self.config.get_path(dataset_type)
        zip_path = target_dir.parent / dataset_cfg["zip_name"]
        
        # Skip if dataset already exists and is valid
        if target_dir.exists() and self.config.verify_dataset(dataset_type):
            return True, f"Dataset {dataset_type.name} already exists and is valid"
            
        # Ensure parent directory exists
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        
        # Download the dataset if zip doesn't exist
        if not zip_path.exists():
            if not self.download_with_retry(
                dataset_cfg["download_url"],
                zip_path,
                dataset_cfg.get("sha256")
            ):
                return False, f"Failed to download {dataset_type.name} dataset"
        
        # Extract the dataset
        if not self._extract_zip(zip_path, target_dir):
            return False, f"Failed to extract {dataset_type.name} dataset"
        
        # Verify extracted contents
        if not self.config.verify_dataset(dataset_type):
            return False, f"Extracted {dataset_type.name} dataset is incomplete"
        
        # Clean up zip file
        try:
            zip_path.unlink()
        except OSError as e:
            print(f"Warning: Could not delete zip file: {e}")
        
        return True, f"Successfully set up {dataset_type.name} dataset"

def main(task_numbers: Optional[List[int]] = None) -> int:
    """
    Main entry point for dataset setup.
    
    Args:
        task_numbers: List of task numbers (2, 3, 4) to setup
        
    Returns:
        int: 0 on success, 1 on failure
    """
    task_map = {
        2: DatasetType.EXPLORATION,
        3: DatasetType.CLASSIFICATION, 
        4: DatasetType.CHALLENGE
    }
    
    downloader = DataDownloader()
    exit_code = 0
    
    for task in task_numbers or [2, 3, 4]:
        if task not in task_map:
            print(f"Error: Unknown task number {task}")
            exit_code = 1
            continue
            
        dataset_type = task_map[task]
        print(f"\n{'='*40}")
        print(f"Setting up Task {task} dataset ({dataset_type.name})")
        print('-'*40)
        
        success, message = downloader.setup_dataset(dataset_type)
        print(message)
        
        if not success:
            exit_code = 1
    
    if exit_code == 0:
        print("\nAll datasets successfully set up!")
    else:
        print("\nSome datasets failed to set up properly")
    
    return exit_code

if __name__ == "__main__":
    import argparse
    import time
    
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
    
    print(f"\nCompleted in {elapsed:.2f} seconds")
    exit(exit_code)