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

# Shared base requirements (sync with Installer.CORE_PACKAGES in install.py)
BASE_REQUIRES = [
    'numpy==1.23.5',
    'pandas==2.0.3',
    'scikit-learn==1.3.0',
    'scipy==1.10.1',
    'tqdm==4.66.1',
    'python-dotenv==1.0.0',
    'librosa==0.10.0',
    'soundfile==0.12.1',
    'matplotlib==3.7.2',
    'seaborn==0.12.2',
    'huggingface-hub==0.15.1',
    'h5py==3.9.0'
]

# Platform-specific extras
EXTRAS_REQUIRE = {
    'cpu': [
        # PyTorch CPU with index URL (Windows/Linux x86)
        'torch==2.0.1; platform_system!="Darwin" and platform_machine!="arm64" '
        '--index-url https://download.pytorch.org/whl/cpu',
        'torchaudio==2.0.2; platform_system!="Darwin" and platform_machine!="arm64" '
        '--index-url https://download.pytorch.org/whl/cpu',
        'torchvision==0.15.2; platform_system!="Darwin" and platform_machine!="arm64" '
        '--index-url https://download.pytorch.org/whl/cpu',
        
        # Mac Silicon (M1/M2) - no index URL needed
        'torch==2.0.1; platform_system=="Darwin" and platform_machine=="arm64"',
        'torchaudio==2.0.2; platform_system=="Darwin" and platform_machine=="arm64"',
        'torchvision==0.15.2; platform_system=="Darwin" and platform_machine=="arm64"',
        
        'onnxruntime==1.15.1'
    ],
    'gpu': [
        # PyTorch CUDA with index URL
        'torch==2.0.1+cu118; platform_system!="Darwin" '
        '--index-url https://download.pytorch.org/whl/cu118',
        'torchaudio==2.0.2+cu118; platform_system!="Darwin" '
        '--index-url https://download.pytorch.org/whl/cu118',
        'torchvision==0.15.2+cu118; platform_system!="Darwin" '
        '--index-url https://download.pytorch.org/whl/cu118',
        
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
    EXTRAS_REQUIRE['cpu'].extend([
        'torch==2.0.1+cpu; platform_system=="Windows" '
        '--index-url https://download.pytorch.org/whl/cpu',
        'torchaudio==2.0.2+cpu; platform_system=="Windows" '
        '--index-url https://download.pytorch.org/whl/cpu',
        'torchvision==0.15.2+cpu; platform_system=="Windows" '
        '--index-url https://download.pytorch.org/whl/cpu'
    ])
    EXTRAS_REQUIRE['gpu'].extend([
        'torch==2.0.1+cu118; platform_system=="Windows" '
        '--index-url https://download.pytorch.org/whl/cu118',
        'torchaudio==2.0.2+cu118; platform_system=="Windows" '
        '--index-url https://download.pytorch.org/whl/cu118',
        'torchvision==0.15.2+cu118; platform_system=="Windows" '
        '--index-url https://download.pytorch.org/whl/cu118'
    ])

setup(
    name="mlpc_project",
    version="0.1",
    packages=find_packages(include=['src*']),
    install_requires=BASE_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
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