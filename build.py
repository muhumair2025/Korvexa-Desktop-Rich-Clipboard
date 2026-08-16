"""
Build automation script for ClipVault.
Runs PyInstaller using ClipVault.spec to produce a standalone Windows binary.
"""

import os
import shutil
import subprocess
import sys


def build_executable():
    print("=" * 60)
    print("Building ClipVault Standalone Windows Executable")
    print("=" * 60)

    # 1. Clean previous build artifacts
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            print(f"Cleaning existing '{folder}' directory...")
            shutil.rmtree(folder, ignore_errors=True)

    # 2. Run PyInstaller
    cmd = [sys.executable, "-m", "PyInstaller", "ClipVault.spec", "--noconfirm", "--clean"]
    print(f"Running command: {' '.join(cmd)}")

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("\n[ERROR] PyInstaller build failed!")
        sys.exit(result.returncode)

    exe_path = os.path.abspath("dist/ClipVault.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print("\n" + "=" * 60)
        print(f"[SUCCESS] Standalone Executable created:")
        print(f"Path: {exe_path}")
        print(f"Size: {size_mb:.2f} MB")
        print("=" * 60)
    else:
        print("\n[ERROR] Output executable not found in dist/")


if __name__ == "__main__":
    build_executable()
