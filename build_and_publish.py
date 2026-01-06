#!/usr/bin/env python3
"""
Build and publish script for Dynamic CBOM.

This script helps with building and publishing the package to PyPI.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {description} failed with code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Error: Command not found. Ensure all dependencies are installed.")
        return False


def main():
    """Main entry point."""
    root = Path(__file__).parent
    
    print("🚀 Dynamic CBOM PyPI Build & Publish Tool\n")
    
    # Check if build tools are installed
    print("Checking dependencies...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list"],
        capture_output=True,
        text=True
    )
    
    required_tools = ["build", "twine"]
    installed = result.stdout
    
    for tool in required_tools:
        if tool not in installed:
            print(f"⚠️  Installing {tool}...")
            run_command([sys.executable, "-m", "pip", "install", tool], f"Install {tool}")
    
    # Clean previous builds
    print("\n🧹 Cleaning previous builds...")
    import shutil
    for path in [root / "build", root / "dist", root / "*.egg-info"]:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
                print(f"   Removed {path}")
    
    # Build the package
    if not run_command(
        [sys.executable, "-m", "build"],
        "Build package"
    ):
        sys.exit(1)
    
    print("\n✅ Build successful!")
    print(f"\n📦 Generated files:")
    for f in sorted((root / "dist").glob("*")):
        print(f"   {f.name}")
    
    # Ask what to do next
    print("\n" + "="*60)
    print("Next steps:")
    print("="*60)
    print("1. Test upload (recommended):")
    print(f"   python -m twine upload --repository testpypi dist/*")
    print("\n2. Production upload:")
    print(f"   python -m twine upload dist/*")
    print("\nMore details: see PUBLISHING.md")


if __name__ == "__main__":
    main()
