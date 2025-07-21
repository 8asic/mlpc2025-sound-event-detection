from pathlib import Path
from enum import Enum, auto
import os

class DatasetType(Enum):
    EXPLORATION = auto()  # Task 2
    CLASSIFICATION = auto()  # Task 3
    CHALLENGE = auto()  # Task 4

class Config:
    # Default directory structure (keep your existing structure)
    BASE_DATA_DIR = Path("data")
    RAW_DIR = BASE_DATA_DIR / "raw"
    
    # Updated DATASETS with checksum support (preserves your custom paths)
    DATASETS = {
        DatasetType.EXPLORATION: {
            "dir_name": "MLPC2025_dataset",
            "zip_name": "MLPC2025_dataset.zip",
            "download_url": "https://cloud.cp.jku.at/index.php/s/YKJqiWjnQQAjiH5?openfile=true",
            "sha256": None  # Optional: Add "a1b2c3..." if you get checksums
        },
        DatasetType.CLASSIFICATION: {
            "dir_name": "MLPC2025_classification", 
            "zip_name": "MLPC2025_classification.zip",
            "download_url": "https://cloud.cp.jku.at/index.php/s/DxtxDck5fSjKAgZ?openfile=true",
            "sha256": None
        },
        DatasetType.CHALLENGE: {
            "dir_name": "MLPC2025_test",
            "zip_name": "MLPC2025_test.zip",
            "download_url": "https://cloud.cp.jku.at/index.php/s/ae3aAEE3gPJwo6f?openfile=true",
            "sha256": None
        }
    }

    def __init__(self):
        self._custom_paths = {}  # Keep your custom path logic

    def get_path(self, dataset_type: DatasetType) -> Path:
        """Resolve path for a specific dataset type"""
        # Preserve your existing priority:
        # 1. Custom paths
        if dataset_type in self._custom_paths:
            return self._custom_paths[dataset_type]
        
        # 2. Environment variables
        env_var = f"MLPC_{dataset_type.name}_PATH"
        if env_var in os.environ:
            return Path(os.environ[env_var])
        
        # 3. Default location
        return self.RAW_DIR / self.DATASETS[dataset_type]["dir_name"]

    def set_path(self, dataset_type: DatasetType, path: Path):
        """Set custom path for a dataset type"""
        self._custom_paths[dataset_type] = Path(path)

# Singleton configuration instance (keep this)
config = Config()