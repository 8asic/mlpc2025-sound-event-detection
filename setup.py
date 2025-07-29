#!/usr/bin/env python3
# ./setup.py
import sys
import io
import os
from setuptools import setup, find_packages

# Force UTF-8 encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def read_file(filename):
    """Read UTF-8 encoded text files safely."""
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

# Base dependencies (MUST include all essential packages)
base_requirements = [
    # Core Scientific Stack
    'numpy==1.23.5',
    'pandas==2.0.3',
    'scikit-learn==1.3.0',
    'scipy==1.10.1',
    'tqdm==4.66.1',
    
    # Environment/Config
    'python-dotenv==1.0.0',
    
    # Audio Processing
    'librosa==0.10.0',
    'soundfile==0.12.1',
    
    # Visualization
    'matplotlib==3.7.2',
    'seaborn==0.12.2',
    
    # Data Management
    'huggingface-hub==0.15.1',  # Changed from 0.16.0
    'h5py==3.9.0'
]

# Platform-specific extras
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
        'torchvision==0.15.2+cu118',
        'flash-attn==2.0.0; platform_system!="Windows"'
    ],
    'extras': [
        'pytorch-lightning==2.0.0',
        'transformers==4.30.0',
        'wandb==0.15.0'
    ]
}

# Windows-specific adjustments
if sys.platform == 'win32':
    extras_require['cpu'].append('torch==2.0.1+cpu')
    extras_require['gpu'].append('torch==2.0.1+cu118')

setup(
    name="mlpc_project",
    version="0.1",
    packages=find_packages(include=['src*']),
    install_requires=base_requirements,
    extras_require=extras_require,
    python_requires='>=3.9,<3.10',
    package_data={
        'src': ['*.json', '*.yaml', '*.md'],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'mlpc-download=scripts.setup_data:main',
            'mlpc-install=scripts.install:main',
            'mlpc-verify=scripts.verify_installation:main'
        ],
    },
    author="Team Fumbling",
    description="Sound Event Detection System for MLPC 2025",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/8asic/mlpc2025-sound-event-detection",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
    ],
    options={
        'build_scripts': {
            'executable': '/usr/bin/env python3',
        },
    },
    zip_safe=False,
)