# src/data/loaders.py
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Union, Optional, List
import warnings
from numpy.typing import NDArray

class DataLoader:
    """Centralized data loading for MLPC2025 project."""
    
    def __init__(self, data_root: Union[str, Path] = "../data/raw"):
        """
        Initialize data loader with root directory.
        
        Args:
            data_root: Path to directory containing raw dataset files
        """
        self.data_root = Path(data_root)
        self._validate_data_paths()
        
    def _validate_data_paths(self) -> None:
        """Check if required data files exist."""
        required_files = [
            "annotations.csv",
            "annotations_text_embeddings.npz",
            "metadata.csv",
            "metadata_title_embeddings.npz",
            "metadata_keywords_embeddings.npz"
        ]
        
        for file in required_files:
            if not (self.data_root / file).exists():
                raise FileNotFoundError(f"Required file not found: {file}")
    
    def load_annotations(self) -> Tuple[pd.DataFrame, NDArray]:
        """
        Load annotations with text embeddings.
        
        Returns:
            Tuple of (annotations DataFrame, text embeddings array)
        """
        annot_df = pd.read_csv(self.data_root / "annotations.csv")
        embeddings = np.load(self.data_root / "annotations_text_embeddings.npz")["embeddings"]
        
        # Basic validation
        if len(annot_df) != len(embeddings):
            warnings.warn(
                f"Annotation count ({len(annot_df)}) doesn't match "
                f"embedding count ({len(embeddings)})",
                RuntimeWarning
            )
        
        # Add duration column
        annot_df['duration'] = annot_df['offset'] - annot_df['onset']
        
        return annot_df, embeddings
    
    def load_metadata(self) -> Tuple[pd.DataFrame, NDArray, NDArray]:
        """
        Load metadata with title and keyword embeddings.
        
        Returns:
            Tuple of (metadata DataFrame, title embeddings, keyword embeddings)
        """
        meta_df = pd.read_csv(self.data_root / "metadata.csv")
        title_emb = np.load(self.data_root / "metadata_title_embeddings.npz")["embeddings"]
        kw_emb = np.load(self.data_root / "metadata_keywords_embeddings.npz")["embeddings"]
        
        return meta_df, title_emb, kw_emb
    
    def load_audio_features(
        self,
        feature_keys: Union[str, List[str]] = 'mfcc',
        file_list: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, NDArray]]:
        """
        Load audio features from NPZ files.
        
        Args:
            feature_keys: Feature(s) to load (default: 'mfcc')
            file_list: Optional list of specific files to load
            
        Returns:
            Nested dictionary: {filename: {feature_key: feature_array}}
        """
        if isinstance(feature_keys, str):
            feature_keys = [feature_keys]
            
        features = {}
        audio_feat_dir = self.data_root / "audio_features"
        
        for npz_path in audio_feat_dir.glob('*.npz'):
            filename = npz_path.stem
            if file_list is not None and filename not in file_list:
                continue
                
            try:
                with np.load(npz_path) as data:
                    file_features = {}
                    for key in feature_keys:
                        if key in data:
                            file_features[key] = data[key]
                    
                    if file_features:
                        features[filename] = file_features
            except Exception as e:
                warnings.warn(f"Error loading {filename}: {str(e)}", RuntimeWarning)
        
        if not features:
            raise ValueError("No audio features loaded - check feature_keys and file_list")
            
        return features