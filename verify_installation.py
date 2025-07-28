#!/usr/bin/env python3
"""
Installation verification script for MLPC2025 project.
Checks package versions and dataset integrity.
"""

import sys
from importlib.metadata import version, PackageNotFoundError
from typing import Dict, List
from src.config import config, DatasetType

# Core package versions (must match pyproject.toml/requirements)
REQUIRED_PACKAGES = {
    'torch': '2.0.1',
    'torchaudio': '2.0.2',
    'torchvision': '0.15.2',
    'numpy': '1.23.5',
    'pandas': '2.0.3',
    'scikit-learn': '1.3.0',
    'tqdm': '4.66.1',
    'python-dotenv': '1.0.0',
    'librosa': '0.10.0',
    'soundfile': '0.12.1'
}

# Optional packages that may be installed based on hardware
OPTIONAL_PACKAGES = {
    'gpu': {
        'flash-attn': '2.0.0'
    },
    'cpu': {
        'onnxruntime': '1.15.1'
    }
}

def check_package(pkg_name: str, expected_version: str) -> bool:
    """Verify a single package is installed with correct version."""
    try:
        installed_version = version(pkg_name)
        if installed_version != expected_version:
            print(f"⚠️  {pkg_name} version mismatch "
                  f"(installed: {installed_version}, required: {expected_version})")
            return False
        return True
    except PackageNotFoundError:
        print(f"❌ {pkg_name} not installed")
        return False

def check_optional_packages(env_type: str) -> int:
    """Check optional packages based on environment type."""
    failures = 0
    if env_type in OPTIONAL_PACKAGES:
        for pkg, ver in OPTIONAL_PACKAGES[env_type].items():
            if not check_package(pkg, ver):
                failures += 1
    return failures

def detect_environment() -> str:
    """Determine environment type for optional packages."""
    try:
        import torch
        if torch.cuda.is_available():
            return 'gpu'
    except ImportError:
        pass
    
    if platform.system() == 'Darwin' and platform.machine() == 'arm64':
        return 'm1'  # Apple Silicon has different requirements
    
    return 'cpu'

def check_datasets() -> int:
    """Verify all required datasets are properly installed."""
    failures = 0
    for dataset_type in DatasetType:
        if not config.verify_dataset(dataset_type):
            print(f"❌ Dataset {dataset_type.name} missing or incomplete")
            failures += 1
    return failures

def verify() -> bool:
    """Run complete verification process."""
    print("🔍 Verifying MLPC2025 installation...\n")
    
    # Check core packages
    print("=== Core Packages ===")
    core_failures = 0
    for pkg, ver in REQUIRED_PACKAGES.items():
        if not check_package(pkg, ver):
            core_failures += 1
    
    # Check environment-specific packages
    print("\n=== Environment Packages ===")
    env_type = detect_environment()
    print(f"Detected environment: {env_type.upper()}")
    optional_failures = check_optional_packages(env_type)
    
    # Check datasets
    print("\n=== Datasets ===")
    dataset_failures = check_datasets()
    
    # Summary
    total_failures = core_failures + optional_failures + dataset_failures
    print("\n=== Verification Summary ===")
    print(f"Core packages: {len(REQUIRED_PACKAGES) - core_failures}/{len(REQUIRED_PACKAGES)} OK")
    print(f"Environment packages: {len(OPTIONAL_PACKAGES.get(env_type, {})) - optional_failures}/"
          f"{len(OPTIONAL_PACKAGES.get(env_type, {}))} OK")
    print(f"Datasets: {len(DatasetType) - dataset_failures}/{len(DatasetType)} OK")
    
    if total_failures == 0:
        print("\n✅ All checks passed!")
        return True
    else:
        print(f"\n❌ Found {total_failures} problems")
        return False

if __name__ == "__main__":
    import platform
    
    if not verify():
        sys.exit(1)