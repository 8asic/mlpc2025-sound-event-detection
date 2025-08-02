#./src/config.py

from pathlib import Path
from enum import Enum, auto
import os
from typing import Dict, Any, Optional, Set
import hashlib
import warnings

class DatasetType(Enum):
    """Enum representing different dataset types in the project."""
    EXPLORATION = auto()    # Task 2: Initial exploration dataset
    CLASSIFICATION = auto() # Task 3: Classification dataset
    CHALLENGE = auto()     # Task 4: Final challenge dataset

class Config:
    """
    Central configuration management for the MLPC2025 project.
    Handles paths, dataset verification, and environment settings.
    """
    
    # Base directory is two levels up from this file (src/config.py -> src/ -> project root)
    BASE_DIR = Path(__file__).parent.parent
    ENV_PREFIX = "MLPC_"  # Prefix for all environment variables
    
    # Default directory structure following repository conventions
    DEFAULT_PATHS = {
        "data": BASE_DIR / "data",
        "artifacts": BASE_DIR / "artifacts",
        "models": BASE_DIR / "models",
        "notebooks": BASE_DIR / "notebooks",
        "reports": BASE_DIR / "artifacts" / "reports"
    }
    
    # Dataset configurations with checksum support
    DATASETS = {
        DatasetType.EXPLORATION: {
            "dir_name": "MLPC2025_dataset",
            "zip_name": "MLPC2025_dataset.zip",
            "download_url": "https://cloud.cp.jku.at/public.php/dav/files/YKJqiWjnQQAjiH5/?accept=zip",
            "sha256": None,  # TODO: Add actual checksum when available
            "required_files": {
                "audio/",                      # Required folder (note trailing slash)
                "audio_features/",                      # Required folder (note trailing slash)
                "annotations.csv",      # Required file
                "annotations_text_embeddings.npz",          # Required file
                "metadata.csv",          # Required file
                "metadata_keywords_embeddings.npz",          # Required file
                "metadata_title_embeddings.npz",          # Required file
                "README.md",          # Required file
            },
            "required_folders": {             # Alternative approach
                "audio",                        # Folder name without slash
                "audio_features",                   # Another required folder
            }
        },
        DatasetType.CLASSIFICATION: {
            "dir_name": "MLPC2025_classification", 
            "zip_name": "MLPC2025_classification.zip",
            "download_url": "https://cloud.cp.jku.at/public.php/dav/files/DxtxDck5fSjKAgZ/?accept=zip",
            "sha256": None,
            "required_files": {
                "audio/",                      # Required folder (note trailing slash)
                "audio_features/",                      # Required folder (note trailing slash)
                "labels/",                        # Folder name without slash
                "annotations.csv",      # Required file
                "metadata.csv",          # Required file
            },
            "required_folders": {             # Alternative approach
                "audio",                        # Folder name without slash
                "audio_features",                   # Another required folder
                "labels",                        # Folder name without slash
            }
        },
        DatasetType.CHALLENGE: {
            "dir_name": "MLPC2025_test",
            "zip_name": "MLPC2025_test.zip",
            "download_url": "https://cloud.cp.jku.at/public.php/dav/files/ae3aAEE3gPJwo6f/?accept=zip",
            "sha256": None,
            "required_files": {
                "audio/",                      # Required folder (note trailing slash)
                "audio_features/",                      # Required folder (note trailing slash)
                "ground_truth.csv",      # Required file
                "metadata.csv",          # Required file
            },
            "required_folders": {             # Alternative approach
                "audio",                     # Folder name without slash
                "audio_features",                   # Another required folder
            }
        }
    }

    def __init__(self):
        """Initialize configuration with environment-aware paths."""
        self._paths = self._init_paths()
        self._custom_dataset_paths: Dict[DatasetType, Path] = {}
        
    def _init_paths(self) -> Dict[str, Path]:
        """Initialize all paths with environment variable overrides."""
        paths = {}
        for key, default in self.DEFAULT_PATHS.items():
            env_var = f"{self.ENV_PREFIX}{key.upper()}_PATH"
            path_str = os.getenv(env_var, str(default))
            paths[key] = Path(path_str).absolute()
            
            # Create directory if it doesn't exist
            if key in ["data", "artifacts", "models"]:
                paths[key].mkdir(parents=True, exist_ok=True)
        return paths

    def get_path(self, dataset_type: DatasetType) -> Path:
        """
        Get the filesystem path for a specific dataset type.
        
        Args:
            dataset_type: The type of dataset to get the path for
            
        Returns:
            Path object pointing to the dataset directory
            
        Raises:
            ValueError: If the dataset type is invalid
        """
        if not isinstance(dataset_type, DatasetType):
            raise ValueError(f"Invalid dataset type: {dataset_type}")
        
        # 1. Check custom path set via set_path()
        if dataset_type in self._custom_dataset_paths:
            return self._custom_dataset_paths[dataset_type]
            
        # 2. Check environment variable override
        env_var = f"{self.ENV_PREFIX}{dataset_type.name}_PATH"
        if env_path := os.getenv(env_var):
            return Path(env_path).absolute()
            
        # 3. Use default location
        dataset_cfg = self.DATASETS[dataset_type]
        return (self._paths["data"] / "raw" / dataset_cfg["dir_name"]).absolute()

    def set_path(self, dataset_type: DatasetType, path: Path) -> None:
        """
        Set a custom path for a specific dataset type.
        
        Args:
            dataset_type: The dataset type to configure
            path: The filesystem path to use
        """
        self._custom_dataset_paths[dataset_type] = Path(path).absolute()

    def verify_dataset(self, dataset_type: DatasetType) -> bool:
        """
        Verify that a dataset is properly installed and complete.
        
        Args:
            dataset_type: The dataset type to verify
            
        Returns:
            bool: True if dataset is complete and valid
        """
        path = self.get_path(dataset_type)
        required_files = self.DATASETS[dataset_type]["required_files"]
        
        missing_files = []
        for file in required_files:
            if not (path / file).exists():
                missing_files.append(file)
                
        if missing_files:
            warnings.warn(
                f"Dataset {dataset_type.name} missing files: {missing_files}",
                RuntimeWarning
            )
            return False
        return True

    def get_sha256(self, dataset_type: DatasetType) -> Optional[str]:
        """Get the expected SHA256 checksum for a dataset if available."""
        return self.DATASETS[dataset_type].get("sha256")

    @property
    def data_path(self) -> Path:
        """Get the base data directory path."""
        return self._paths["data"]
        
    @property
    def artifacts_path(self) -> Path:
        """Get the artifacts directory path."""
        return self._paths["artifacts"]
        
    @property
    def models_path(self) -> Path:
        """Get the models directory path."""
        return self._paths["models"]

# Singleton configuration instance
config = Config()