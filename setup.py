from setuptools import setup, find_packages

# Base dependencies (common to all installations)
base_requirements = [
    'numpy==1.23.5',          # Pinned exact version
    'pandas==2.0.3',
    'scikit-learn==1.3.0',
    'scipy==1.10.1',
    'tqdm==4.66.1',
    'python-dotenv==1.0.0',
    'librosa==0.10.0',        # Updated to stable version
    'soundfile==0.12.1',
    'matplotlib==3.7.2',
    'seaborn==0.12.2',
    'huggingface-hub==0.16.0',
    'h5py==3.9.0',
]

# Simplified platform-specific extras
extras_require = {
    'cpu': [
        'torch==2.0.1',
        'torchaudio==2.0.2',
        'torchvision==0.15.2',
        'onnxruntime==1.15.1'
    ],
    'gpu': [
        'torch==2.0.1+cu118',
        'torchaudio==2.0.2+cu118',
        'torchvision==0.15.2+cu118'
    ],
    'extras': [
        'pytorch-lightning==2.0.0',
        'transformers==4.30.0',
        'wandb==0.15.0',
        'flash-attn==2.0.0'   # Added for transformer optimization
    ]
}

setup(
    name="mlpc_project",
    version="0.1",
    packages=find_packages(include=['src*']),
    install_requires=base_requirements,
    extras_require=extras_require,
    python_requires='>=3.9',  # Explicit Python version requirement
    package_data={
        'src': ['*.json', '*.yaml'],
    },
    entry_points={
        'console_scripts': [
            'mlpc-download=scripts.setup_data:main',
            'mlpc-install=scripts.install:main',
        ],
    },
    # New metadata for better PyPI compliance
    author="Team Fumbling",
    description="Sound Event Detection System for MLPC 2025",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/8asic/mlpc2025-sound-event-detection",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)