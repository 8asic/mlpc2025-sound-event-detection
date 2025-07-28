# ./src/data/loaders.py

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Union
import warnings
from numpy.typing import NDArray

def load_annotations(data_path: Union[str, Path]) -> Tuple[pd.DataFrame, NDArray[np.float64]]:
    """Load annotations with text embeddings.
    
    Args:
        data_path: Path to directory containing annotations.csv and embeddings
        
    Returns:
        Tuple of (annotations_df, embeddings_array)
        
    Raises:
        FileNotFoundError: If required files are missing
        ValueError: If annotation file is malformed
    """
    data_path = Path(data_path)
    annot_path = data_path / "annotations.csv"
    embed_path = data_path / "annotations_text_embeddings.npz"
    
    if not annot_path.exists():
        raise FileNotFoundError(f"Annotation file not found at {annot_path}")
    if not embed_path.exists():
        raise FileNotFoundError(f"Embedding file not found at {embed_path}")

    # Load and validate annotations
    annot_df = pd.read_csv(annot_path)
    required_cols = {'filename', 'onset', 'offset', 'text', 'annotator'}
    if not required_cols.issubset(annot_df.columns):
        missing = required_cols - set(annot_df.columns)
        raise ValueError(f"Annotation file missing required columns: {missing}")
    
    # Calculate durations
    annot_df['duration'] = annot_df['offset'] - annot_df['onset']
    
    # Load embeddings
    with np.load(embed_path) as data:
        embeddings = data["embeddings"]
    
    # Validate alignment
    if len(annot_df) != len(embeddings):
        warnings.warn(
            f"Annotation count ({len(annot_df)}) doesn't match "
            f"embedding count ({len(embeddings)})",
            RuntimeWarning
        )
    
    return annot_df, embeddings

def load_audio_features(
    feature_dir: Union[str, Path],
    file_list: Union[None, list[str]] = None,
    feature_keys: Union[str, list[str]] = 'embeddings'
) -> Dict[str, Dict[str, NDArray[np.float64]]]:
    """Load audio features from multiple NPZ files.
    
    Args:
        feature_dir: Directory containing NPZ feature files
        file_list: Optional list of specific files to load (without .npz)
        feature_keys: Feature(s) to extract from each file
        
    Returns:
        Nested dictionary: {filename: {feature_key: feature_array}}
        
    Raises:
        FileNotFoundError: If feature directory doesn't exist
        ValueError: If requested features are missing
    """
    feature_dir = Path(feature_dir)
    if not feature_dir.exists():
        raise FileNotFoundError(f"Feature directory not found at {feature_dir}")
    
    if isinstance(feature_keys, str):
        feature_keys = [feature_keys]
    
    features = {}
    loaded_files = 0
    
    for npz_path in feature_dir.glob('*.npz'):
        filename = npz_path.stem
        if file_list is not None and filename not in file_list:
            continue
            
        try:
            with np.load(npz_path) as data:
                file_features = {}
                for key in feature_keys:
                    if key in data:
                        file_features[key] = data[key]
                    else:
                        warnings.warn(
                            f"Feature '{key}' not found in {filename}.npz",
                            RuntimeWarning
                        )
                
                if file_features:  # Only add if we found requested features
                    features[filename] = file_features
                    loaded_files += 1
        except Exception as e:
            warnings.warn(
                f"Error loading {filename}.npz: {str(e)}",
                RuntimeWarning
            )
    
    if not features:
        raise ValueError(f"No valid feature files found in {feature_dir}")
    
    print(f"Successfully loaded features from {loaded_files} files")
    return features

def load_metadata(data_path: Union[str, Path]) -> Tuple[pd.DataFrame, NDArray[np.float64], NDArray[np.float64]]:
    """Load metadata with title and keyword embeddings.
    
    Args:
        data_path: Path to directory containing metadata files
        
    Returns:
        Tuple of (metadata_df, title_embeddings, keyword_embeddings)
        
    Raises:
        FileNotFoundError: If required files are missing
    """
    data_path = Path(data_path)
    meta_path = data_path / "metadata.csv"
    title_path = data_path / "metadata_title_embeddings.npz"
    keyword_path = data_path / "metadata_keywords_embeddings.npz"
    
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found at {meta_path}")
    if not title_path.exists():
        raise FileNotFoundError(f"Title embeddings not found at {title_path}")
    if not keyword_path.exists():
        raise FileNotFoundError(f"Keyword embeddings not found at {keyword_path}")
    
    # Load metadata
    metadata_df = pd.read_csv(meta_path)
    
    # Load embeddings
    with np.load(title_path) as data:
        title_emb = data["embeddings"]
    with np.load(keyword_path) as data:
        keyword_emb = data["embeddings"]
    
    # Validate alignment
    if len(metadata_df) != len(title_emb) or len(metadata_df) != len(keyword_emb):
        warnings.warn(
            "Metadata row count doesn't match embedding counts: "
            f"metadata={len(metadata_df)}, "
            f"titles={len(title_emb)}, "
            f"keywords={len(keyword_emb)}",
            RuntimeWarning
        )
    
    return metadata_df, title_emb, keyword_emb