from src.config import config, DatasetType

def download_and_extract(task_numbers):
    for task in task_numbers:
        if task == 2:
            dataset_type = DatasetType.EXPLORATION
        elif task == 3:
            dataset_type = DatasetType.CLASSIFICATION
        elif task == 4:
            dataset_type = DatasetType.CHALLENGE
            
        target_dir = config.get_path(dataset_type)
        url = config.DATASETS[dataset_type]["download_url"]
        
        print(f"Downloading {dataset_type.name} dataset...")
        # Download and extraction logic here
        # Would use the configured paths automatically