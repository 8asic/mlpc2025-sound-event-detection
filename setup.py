# root/setup.py
from setuptools import setup, find_packages
import platform

# Base dependencies (common to both CPU and GPU)
base_requirements = [
    'numpy>=1.21.0',
    'pandas>=1.3.0',
    'scikit-learn>=1.0.0',
    'scipy>=1.7.0',
    'tqdm>=4.0.0',
    'python-dotenv>=1.0.0',
    'librosa>=0.9.0',
    'soundfile>=0.12.0',
    'matplotlib>=3.5.0',
    'seaborn>=0.11.0',
    'huggingface-hub>=0.16.0',
    'h5py>=3.9.0',
]

# Platform-specific extras
extras_require = {
    'cpu': [
        'torch>=2.0.1 ; sys_platform != "darwin" and platform_machine != "arm64"',
        'torchaudio>=2.0.2 ; sys_platform != "darwin" and platform_machine != "arm64"',
        'torchvision>=0.15.2 ; sys_platform != "darwin" and platform_machine != "arm64"',
        'onnxruntime>=1.15.1',
        # Mac M1/M2 specific
        'torch>=2.0.1 ; sys_platform == "darwin" and platform_machine == "arm64"',
        'torchaudio>=2.0.2 ; sys_platform == "darwin" and platform_machine == "arm64"',
        'torchvision>=0.15.2 ; sys_platform == "darwin" and platform_machine == "arm64"',
    ],
    'gpu': [
        'torch>=2.0.1+cu118 --index-url https://download.pytorch.org/whl/cu118',
        'torchaudio>=2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118',
        'torchvision>=0.15.2+cu118 --index-url https://download.pytorch.org/whl/cu118',
    ],
    'extras': [
        'pytorch-lightning>=2.0.0',
        'transformers>=4.30.0',
        'wandb>=0.15.0',
    ]
}

setup(
    name="mlpc_project",
    version="0.1",
    packages=find_packages(include=['src*']),
    install_requires=base_requirements,
    extras_require=extras_require,
    package_data={
        'src': ['*.json', '*.yaml'],
    },
    entry_points={
        'console_scripts': [
            'mlpc-download=scripts.setup_data:main',
            'mlpc-install=scripts.install:main',  # New installation helper
        ],
    },
)