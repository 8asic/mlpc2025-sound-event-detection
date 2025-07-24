import os
import platform
import subprocess
import sys
from typing import List, Dict

def get_gpu_status() -> bool:
    """Check for NVIDIA GPU without torch dependency."""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=gpu_name", "--format=csv"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=gpu_name", "--format=csv"],
                capture_output=True,
                text=True
            )
        return "NVIDIA" in result.stdout
    except (FileNotFoundError, subprocess.SubprocessError):
        return False

def detect_environment() -> Dict[str, bool]:
    """Detect hardware configuration."""
    return {
        'gpu': get_gpu_status(),
        'mac_arm': (platform.system() == 'Darwin') and (platform.machine() == 'arm64')
    }

def install_torch(env: Dict[str, bool]) -> bool:
    """Install PyTorch appropriate for the detected environment."""
    base_url = "https://download.pytorch.org/whl/cu118"
    
    try:
        if env['mac_arm']:
            print("Installing Apple Silicon (MPS) compatible PyTorch")
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "torch==2.0.1",
                "torchaudio==2.0.2",
                "torchvision==0.15.2"
            ], check=True)
        elif env['gpu']:
            print("Installing CUDA 11.8 compatible PyTorch")
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                f"torch==2.0.1+cu118",
                f"torchaudio==2.0.2+cu118",
                f"torchvision==0.15.2+cu118",
                "--extra-index-url", base_url
            ], check=True)
        else:
            print("Installing CPU-only PyTorch")
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "torch==2.0.1",
                "torchaudio==2.0.2",
                "torchvision==0.15.2",
                "onnxruntime==1.15.1"
            ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install PyTorch: {e}")
        return False

def install_packages(packages: List[str]) -> bool:
    """Generic package installation helper."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + packages,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Package installation failed: {e}")
        return False

def main():
    print("=== MLPC2025 Installation ===")
    print("Detecting hardware configuration...")
    
    env = detect_environment()
    print(f"Configuration: GPU={env['gpu']}, Apple Silicon={env['mac_arm']}")
    
    # Step 1: Install base requirements
    print("\n1/4 Installing core requirements...")
    core_packages = [
        "numpy==1.23.5",
        "pandas==2.0.3",
        "scikit-learn==1.3.0",
        "tqdm==4.66.1"
    ]
    if not install_packages(core_packages):
        sys.exit(1)
    
    # Step 2: Install PyTorch
    print("\n2/4 Installing PyTorch...")
    if not install_torch(env):
        sys.exit(1)
    
    # Step 3: Install project in dev mode
    print("\n3/4 Installing project in development mode...")
    if not install_packages(["-e", "."]):
        sys.exit(1)
    
    # Step 4: Install extras
    print("\n4/4 Installing additional dependencies...")
    extras = ["extras"]
    if env['gpu']:
        extras.append("gpu")
    elif not env['mac_arm']:
        extras.append("cpu")
    
    if not install_packages([f".[{','.join(extras)}]"]):
        sys.exit(1)
    
    # Verification
    print("\nVerifying installation...")
    try:
        import torch
        print(f"PyTorch {torch.__version__} installed")
        if env['gpu']:
            print(f"CUDA available: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                print(f"CUDA version: {torch.version.cuda}")
        
        import sklearn
        print(f"Scikit-learn {sklearn.__version__} installed")
        
        print("\nInstallation completed successfully!")
    except ImportError as e:
        print(f"Verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()