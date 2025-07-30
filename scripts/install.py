#!/usr/bin/env python3
"""
MLPC2025 Installation Script - Professional Version
Integrated with setup.py dependencies
"""
import os
import platform
import subprocess
import sys
import time
from typing import List, Dict, Tuple
import importlib
from enum import Enum, auto
from importlib.metadata import version

class LogLevel(Enum):
    INFO = auto()
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()

class Color:
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Installer:
    """Professional installation handler with GitHub-style output formatting."""
    
    def __init__(self):
        self.env = self._detect_environment()
        self.start_time = time.time()
        self.total_steps = 4
        self.current_step = 0
        
        # Dynamically load requirements from setup.py
        try:
            from setup import BASE_REQUIRES, EXTRAS_REQUIRE
            self.base_packages = [
                (pkg.split('==')[0], pkg.split('==')[1] if '==' in pkg else None)
                for pkg in BASE_REQUIRES
            ]
            self.extras_require = EXTRAS_REQUIRE
        except ImportError:
            self._log("Failed to load setup.py dependencies", LogLevel.ERROR)
            sys.exit(1)

        # Core packages that must be verifiable
        self.verifiable_packages = [
            ('numpy', '1.23.5'),
            ('pandas', '2.0.3'),
            ('scikit-learn', '1.3.0'),
            ('librosa', '0.10.0'),
            ('torch', '2.0.1')  # Will be replaced by correct version later
        ]

    def _log(self, message: str, level: LogLevel = LogLevel.INFO, indent: int = 0):
        """GitHub-style logging with colors."""
        prefix = "  " * indent
        if level == LogLevel.INFO:
            print(f"{prefix}{Color.BLUE}ℹ{Color.END} {message}")
        elif level == LogLevel.SUCCESS:
            print(f"{prefix}{Color.GREEN}✓{Color.END} {message}")
        elif level == LogLevel.WARNING:
            print(f"{prefix}{Color.YELLOW}⚠{Color.END} {message}")
        elif level == LogLevel.ERROR:
            print(f"{prefix}{Color.RED}✗{Color.END} {message}")

    def _print_section(self, title: str):
        """GitHub-style section headers."""
        print(f"\n{Color.BOLD}{Color.CYAN}### {title}{Color.END}")

    def _print_environment_summary(self):
        """Professional environment summary with GitHub-style formatting."""
        print(f"\n{Color.BOLD}Environment Summary:{Color.END}")
        print(f"  {Color.BLUE}∙{Color.END} OS: {platform.system()}")
        print(f"  {Color.BLUE}∙{Color.END} Python: {platform.python_version()}")
        print(f"  {Color.BLUE}∙{Color.END} Architecture: {platform.machine()}")
        print(f"  {Color.BLUE}∙{Color.END} GPU: {'Available' if self.env['has_gpu'] else 'Not available'}")
        
        if self.env['has_gpu']:
            try:
                gpu_info = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    capture_output=True, text=True
                )
                print(f"  {Color.BLUE}∙{Color.END} GPU Model: {gpu_info.stdout.strip()}")
            except:
                pass

    def _print_progress(self, step_name: str):
        """GitHub Actions-style progress tracking."""
        self.current_step += 1
        self._log(f"Step {self.current_step}/{self.total_steps}: {step_name}")

    def _detect_environment(self) -> Dict[str, bool]:
        """Detect hardware configuration with silent logging."""
        has_gpu = self._check_gpu_support()
        return {
            'has_gpu': has_gpu,
            'is_mac_arm': (platform.system() == 'Darwin') and (platform.machine() == 'arm64'),
            'is_windows': platform.system() == 'Windows'
        }

    def _check_gpu_support(self) -> bool:
        """Check for NVIDIA GPU."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=gpu_name", "--format=csv,noheader"],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            return "NVIDIA" in result.stdout.strip()
        except:
            return False

    def _run_pip_install(self, packages: List[str]) -> bool:
        """Run pip install with professional output."""
        self._log(f"Installing: {', '.join(packages)}", LogLevel.INFO, 1)
        
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--no-cache-dir"] + packages,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except subprocess.CalledProcessError as e:
            self._log(f"Failed to install packages", LogLevel.ERROR, 1)
            self._log(e.stderr.decode().strip(), LogLevel.ERROR, 2)
            return False

    def install_base(self) -> bool:
        """Install core requirements."""
        self._print_progress("Installing base requirements")
        return self._run_pip_install([pkg for pkg, _ in self.base_packages])

    def install_project(self) -> bool:
        """Install project in development mode."""
        self._print_progress("Installing project package")
        return self._run_pip_install(["-e", "."])

    def install_hardware_extras(self) -> bool:
        """Install hardware-specific packages with clear output."""
        self._print_progress("Installing hardware-optimized packages")
        
        if self.env['is_mac_arm']:
            self._log("Detected Apple Silicon - installing extras", LogLevel.INFO, 1)
            extras = ".[extras]"
        elif self.env['has_gpu']:
            self._log("Detected NVIDIA GPU - installing GPU extras", LogLevel.INFO, 1)
            extras = ".[gpu,extras]"
        else:
            self._log("Using CPU-only packages", LogLevel.INFO, 1)
            extras = ".[cpu,extras]"
            
        return self._run_pip_install([extras])

    def verify_installation(self) -> bool:
        """Professional package verification with GitHub-style output."""
        self._print_progress("Verifying installation")
        self._log("Checking critical package versions...", LogLevel.INFO, 1)
        
        results = []
        critical_failure = False
        
        for pkg, expected_ver in self.verifiable_packages:
            try:
                installed_ver = version(pkg)
                if expected_ver and installed_ver != expected_ver:
                    status = f"{Color.YELLOW}⚠ MISMATCH{Color.END}"
                    note = f"expected {expected_ver}, got {installed_ver}"
                    results.append((pkg, status, note))
                else:
                    status = f"{Color.GREEN}✓ {installed_ver}{Color.END}"
                    results.append((pkg, status, ""))
            except ImportError:
                status = f"{Color.RED}✗ MISSING{Color.END}"
                results.append((pkg, status, ""))
                critical_failure = True
        
        # Print verification table
        max_pkg_len = max(len(pkg) for pkg, _, _ in results)
        max_status_len = max(len(status) for _, status, _ in results)
        
        print(f"\n{'Package':<{max_pkg_len}}  {'Status':<{max_status_len}}  Notes")
        print("-" * (max_pkg_len + max_status_len + 20))
        for pkg, status, note in results:
            print(f"  {pkg:<{max_pkg_len}}  {status:<{max_status_len}}  {note}")
        
        # Final summary
        if critical_failure:
            self._log("Critical packages missing - installation may not work", LogLevel.ERROR)
            return False
        else:
            self._log("Core packages verified (warnings may exist)", LogLevel.SUCCESS)
            return True
    
    def install(self) -> bool:
        """Run complete professional installation process."""
        print(f"\n{Color.BOLD}🚀 MLPC2025 Sound Event Detection Setup{Color.END}")
        self._print_environment_summary()
        
        steps = [
            ("Base Packages", self.install_base),
            ("Project", self.install_project),
            ("Hardware Extras", self.install_hardware_extras),
            ("Verification", self.verify_installation)
        ]

        for name, step in steps:
            self._print_section(name)
            if not step():
                self._log(f"Installation failed during: {name}", LogLevel.ERROR)
                return False

        elapsed = time.time() - self.start_time
        print(f"\n{Color.BOLD}{Color.GREEN}✅ Installation completed in {elapsed:.1f} seconds{Color.END}")
        print(f"{Color.BOLD}Next steps:{Color.END} Run the application using the project's entry points")
        return True

if __name__ == "__main__":
    installer = Installer()
    sys.exit(0 if installer.install() else 1)