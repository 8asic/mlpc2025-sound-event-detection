# root/scripts/install.py
import os
import platform
import subprocess
import sys

def detect_environment():
    """Detect if GPU is available and OS type"""
    is_cuda_available = False
    try:
        import torch
        is_cuda_available = torch.cuda.is_available()
    except ImportError:
        pass
    
    is_mac_arm = (platform.system() == 'Darwin') and (platform.machine() == 'arm64')
    
    return {
        'gpu': is_cuda_available,
        'mac_arm': is_mac_arm
    }

def main():
    env = detect_environment()
    extras = ['extras']  # Always install extras
    
    if env['gpu']:
        print("GPU detected - installing GPU-accelerated packages")
        extras.append('gpu')
    elif env['mac_arm']:
        print("Apple Silicon detected - installing MPS-accelerated packages")
    else:
        print("Using CPU-only configuration")
        extras.append('cpu')
    
    pip_command = [
        sys.executable, '-m', 'pip', 'install', '-e', '.',
    ] + [f'.[{extra}]' for extra in extras]
    
    subprocess.run(pip_command, check=True)

if __name__ == "__main__":
    main()