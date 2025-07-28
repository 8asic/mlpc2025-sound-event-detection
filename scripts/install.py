# ./scripts/install.py

#!/usr/bin/env python3
"""
MLPC2025 Installation Script

Automatically detects hardware configuration and installs:
- Core dependencies
- PyTorch (GPU/CPU/M1 optimized)
- Project in development mode
- Optional extras based on hardware
"""

import os
import platform
import subprocess
import sys
import time
from typing import Dict, List, Optional, TypedDict
import importlib

class EnvironmentInfo(TypedDict):
    """Type definition for detected environment information."""
    has_gpu: bool
    is_mac_arm: bool
    is_windows: bool
    is_linux: bool
    python_version: str  # Changed from bool to str

class Installer:
    """Handles system detection and package installation."""
    
    # Core package versions (must match pyproject.toml)
    CORE_PACKAGES = [
        "numpy==1.23.5",
        "pandas==2.0.3",
        "scikit-learn==1.3.0",
        "tqdm==4.66.1",
        "python-dotenv==1.0.0"
    ]
    
    # Platform-specific PyTorch versions
    TORCH_PACKAGES = {
        'cuda': {
            'torch': "2.0.1+cu118",
            'torchaudio': "2.0.2+cu118",
            'torchvision': "0.15.2+cu118",
            'index_url': "https://download.pytorch.org/whl/cu118"
        },
        'cpu': {
            'torch': "2.0.1",
            'torchaudio': "2.0.2",
            'torchvision': "0.15.2",
            'onnxruntime': "1.15.1"
        },
        'm1': {
            'torch': "2.0.1",
            'torchaudio': "2.0.2",
            'torchvision': "0.15.2"
        }
    }

    def __init__(self):
        self.env = self._detect_environment()
        self.start_time = time.time()

    def _detect_environment(self) -> EnvironmentInfo:
        """Comprehensive environment detection."""
        system = platform.system()
        machine = platform.machine()
        
        return EnvironmentInfo(
            has_gpu=self._check_gpu_support(),
            is_mac_arm=(system == 'Darwin') and (machine == 'arm64'),
            is_windows=system == 'Windows',
            is_linux=system == 'Linux',
            python_version=platform.python_version()
        )

    def _check_gpu_support(self) -> bool:
        """Robust GPU detection with fallbacks."""
        # First try nvidia-smi
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=gpu_name", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=gpu_name", "--format=csv,noheader"],
                    capture_output=True,
                    text=True
                )
            return "NVIDIA" in result.stdout.strip()
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
        
        # Fallback to checking for CUDA in PATH
        try:
            if platform.system() == "Windows":
                subprocess.run(
                    ["nvcc", "--version"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                return True
            else:
                subprocess.run(
                    ["nvcc", "--version"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return True
        except (FileNotFoundError, subprocess.SubprocessError):
            return False

    def _run_pip_command(self, args: List[str]) -> bool:
        """Execute pip command with error handling."""
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install"] + args,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Failed to install packages: {e.stderr.decode().strip()}")
            return False

    def install_core(self) -> bool:
        """Install core requirements."""
        print("\n🔧 Installing core requirements...")
        return self._run_pip_command(self.CORE_PACKAGES)

    def install_torch(self) -> bool:
        """Install PyTorch for the detected hardware."""
        print("\n⚡ Installing PyTorch...")
        
        if self.env['is_mac_arm']:
            print("  - Detected Apple Silicon (M1/M2)")
            pkgs = [f"{k}=={v}" for k, v in self.TORCH_PACKAGES['m1'].items()]
        elif self.env['has_gpu']:
            print("  - Detected NVIDIA GPU")
            pkgs = [f"{k}=={v}" for k, v in self.TORCH_PACKAGES['cuda'].items()]
            pkgs.extend(["--extra-index-url", self.TORCH_PACKAGES['cuda']['index_url']])
        else:
            print("  - Using CPU-only installation")
            pkgs = [f"{k}=={v}" for k, v in self.TORCH_PACKAGES['cpu'].items()]
            pkgs.append(f"onnxruntime=={self.TORCH_PACKAGES['cpu']['onnxruntime']}")

        return self._run_pip_command(pkgs)

    def install_project(self) -> bool:
        """Install project in development mode."""
        print("\n📦 Installing project in development mode...")
        return self._run_pip_command(["-e", "."])

    def install_extras(self) -> bool:
        """Install optional extras based on hardware."""
        print("\n✨ Installing additional dependencies...")
        
        extras = ["extras"]
        if self.env['has_gpu']:
            extras.append("gpu")
        elif not self.env['is_mac_arm']:
            extras.append("cpu")
            
        return self._run_pip_command([f".[{','.join(extras)}]"])

    def _verify_package(self, name: str, expected_version: Optional[str] = None) -> bool:
        """Verify a package is installed and correct version."""
        try:
            module = importlib.import_module(name)
            if expected_version and module.__version__ != expected_version:
                print(f"⚠️ Version mismatch: {name} (expected {expected_version}, got {module.__version__})")
                return False
            return True
        except ImportError:
            print(f"❌ Package not found: {name}")
            return False

    def verify_installation(self) -> bool:
        """Validate critical packages are installed correctly."""
        print("\n🔍 Verifying installation...")
        success = True
        
        # Verify PyTorch installation
        if not self._verify_package("torch"):
            success = False
        else:
            import torch
            print(f"  - PyTorch {torch.__version__} installed")
            if self.env['has_gpu']:
                cuda_available = torch.cuda.is_available()
                print(f"  - CUDA available: {cuda_available}")
                if cuda_available:
                    # Safely get CUDA version
                    cuda_version = getattr(torch.version, 'cuda', None)
                    if cuda_version:
                        print(f"  - CUDA version: {cuda_version}")
                    else:
                        print("  - CUDA version: Unknown (torch.version.cuda not available)")
        
        # Verify other core packages
        for pkg in self.CORE_PACKAGES:
            name, version = pkg.split("==")
            if not self._verify_package(name, version):
                success = False

        return success

    def install(self) -> bool:
        """Run complete installation process."""
        print("=== MLPC2025 Installation ===")
        print(f"Detected environment: Python {self.env['python_version']}")
        print(f"  - OS: {'Windows' if self.env['is_windows'] else 'macOS' if self.env['is_mac_arm'] else 'Linux'}")
        print(f"  - GPU: {'Available' if self.env['has_gpu'] else 'Not available'}")

        steps = [
            ("Core Packages", self.install_core),
            ("PyTorch", self.install_torch),
            ("Project", self.install_project),
            ("Extras", self.install_extras),
            ("Verification", self.verify_installation)
        ]

        for name, step in steps:
            print(f"\n🚀 {name}")
            if not step():
                print(f"\n❌ Installation failed during: {name}")
                return False

        elapsed = time.time() - self.start_time
        print(f"\n✅ Installation completed successfully in {elapsed:.1f} seconds!")
        return True

def main():
    installer = Installer()
    if not installer.install():
        sys.exit(1)

if __name__ == "__main__":
    main()