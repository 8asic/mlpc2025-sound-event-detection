#!/usr/bin/env python3
"""
Dataset download and setup script for MLPC2025 project.
Handles downloading and extracting the three required datasets.
"""

import os
import zipfile
import hashlib
from pathlib import Path
from typing import Optional, List

import requests
from tqdm import tqdm
from src.config import config, DatasetType

def download_file(url: str, dest: Path, expected_sha256: Optional[str] = None) -> bool:
    """Download file with progress and checksum verification"""
    try:
        print(f"Downloading {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        progress = tqdm(total=total_size, unit='B', unit_scale=True, desc=dest.name)

        sha256 = hashlib.sha256()
        with open(dest, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                sha256.update(chunk)
                progress.update(len(chunk))
        progress.close()

        if expected_sha256 and sha256.hexdigest() != expected_sha256:
            print(f"Checksum mismatch for {dest.name}")
            dest.unlink()
            return False

        return True
    except requests.exceptions.RequestException as e:
        print(f"Download failed: {e}")
        if dest.exists():
            dest.unlink()
        return False

def setup_dataset(dataset_type: DatasetType) -> bool:
    """Download and extract specific dataset"""
    cfg = config.DATASETS[dataset_type]
    target_dir = config.get_path(dataset_type)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = target_dir.parent / cfg["zip_name"]
    
    if not zip_path.exists():
        if not download_file(cfg["download_url"], zip_path, cfg.get("sha256")):
            return False
    
    print(f"Extracting {zip_path.name}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)
    
    zip_path.unlink()
    return True

def main(task_numbers: Optional[List[int]] = None) -> int:
    """Main function for command-line execution"""
    task_map = {
        2: DatasetType.EXPLORATION,
        3: DatasetType.CLASSIFICATION, 
        4: DatasetType.CHALLENGE
    }
    
    for task in task_numbers or [2, 3, 4]:
        if task not in task_map:
            print(f"Error: Unknown task number {task}")
            return 1
            
        print(f"\n{'='*40}")
        print(f"Setting up Task {task} dataset")
        if not setup_dataset(task_map[task]):
            return 1
    
    return 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MLPC2025 dataset setup")
    parser.add_argument('--tasks', nargs='+', type=int, choices=[2, 3, 4])
    args = parser.parse_args()
    exit(main(args.tasks))