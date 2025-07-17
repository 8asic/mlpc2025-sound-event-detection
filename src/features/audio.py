import math
from typing import Optional, Tuple, Dict, List
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from numpy.typing import NDArray

RESOLUTION = 0.12  # 120ms per feature frame

def extract_region_features(
    onset: float,
    offset: float,
    audio_features: NDArray[np.float64],
    scaler: Optional[StandardScaler] = None
) -> Optional[NDArray[np.float64]]:
    """Extract fixed-length features for a time region.
    
    Args:
        onset: Start time in seconds
        offset: End time in seconds  
        audio_features: Full audio feature array (time, features)
        scaler: Optional StandardScaler instance
        
    Returns:
        Mean features for the region or None if empty segment
    """
    start_idx = math.floor(onset / RESOLUTION)
    end_idx = math.ceil(offset / RESOLUTION)
    
    # Handle case where region is outside audio bounds
    if start_idx >= audio_features.shape[0] or end_idx <= 0:
        return None
        
    # Clip indices to valid range
    start_idx = max(0, start_idx)
    end_idx = min(audio_features.shape[0], end_idx)
    
    segment = audio_features[start_idx:end_idx]
    if segment.shape[0] == 0:
        return None
    
    if scaler is not None:
        segment = scaler.transform(segment)
    
    return segment.mean(axis=0)

def process_all_regions(
    annotations: pd.DataFrame,
    audio_features: Dict[str, Dict[str, NDArray[np.float64]]],
    feature_key: str = "mfcc"
) -> Tuple[NDArray[np.float64], NDArray[np.str_]]:
    """Process all annotated and silent regions.
    
    Args:
        annotations: DataFrame with columns ['filename', 'onset', 'offset']
        audio_features: Dict mapping filenames to feature dicts
        feature_key: Key to extract from audio_features dict
        
    Returns:
        Tuple of (feature_matrix, region_labels) where:
        - feature_matrix: (n_samples, n_features) array
        - region_labels: (n_samples,) array of 'annotated'|'silent'
    """
    # Collect all features for standardization
    all_feature_arrays = []
    for feat_dict in audio_features.values():
        if feature_key in feat_dict:
            all_feature_arrays.append(feat_dict[feature_key])
    
    if not all_feature_arrays:
        raise ValueError(f"No '{feature_key}' features found in audio_features")
    
    scaler = StandardScaler().fit(np.concatenate(all_feature_arrays))
    
    X: List[NDArray[np.float64]] = []
    labels: List[str] = []
    
    for filename, feat_dict in audio_features.items():
        if feature_key not in feat_dict:
            continue
            
        features = feat_dict[feature_key]
        total_frames = features.shape[0]
        total_duration = total_frames * RESOLUTION
        
        # Get annotations for this file
        file_annots = annotations[annotations['filename'] == filename]
        file_annots = file_annots.sort_values('onset')
        
        # Process annotated regions
        annotated_regions = []
        for _, row in file_annots.iterrows():
            feat = extract_region_features(
                row['onset'],
                row['offset'],
                features,
                scaler
            )
            if feat is not None:
                X.append(feat)
                labels.append('annotated')
                annotated_regions.append((row['onset'], row['offset']))
        
        # Process silent regions (gaps between annotations)
        prev_end = 0.0
        for onset, offset in annotated_regions:
            if onset > prev_end:
                silent_feat = extract_region_features(
                    prev_end,
                    onset,
                    features,
                    scaler
                )
                if silent_feat is not None:
                    X.append(silent_feat)
                    labels.append('silent')
            prev_end = max(prev_end, offset)
        
        # Final silent region after last annotation
        if prev_end < total_duration:
            silent_feat = extract_region_features(
                prev_end,
                total_duration,
                features,
                scaler
            )
            if silent_feat is not None:
                X.append(silent_feat)
                labels.append('silent')
    
    if not X:
        raise ValueError("No valid regions found in any audio files")
    
    return np.stack(X), np.array(labels, dtype=np.str_)

def get_region_durations(
    annotations: pd.DataFrame
) -> Dict[str, List[Tuple[float, float]]]:
    """Get time regions grouped by filename.
    
    Returns:
        Dict mapping filenames to list of (onset, offset) tuples
    """
    regions = {}
    for filename, group in annotations.groupby('filename'):
        regions[filename] = list(zip(group['onset'], group['offset']))
    return regions