"""
RAMGuard Setup Script
Creates required directories on first run.
"""

import os
from pathlib import Path

ROOT = Path(__file__).parent

DIRECTORIES = [
    ROOT / "data",
    ROOT / "logs",
    ROOT / "config",
]

def setup():
    for d in DIRECTORIES:
        d.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {d}")
    print("\nRAMGuard directories are ready.")
    print("Run:  python main.py")

if __name__ == "__main__":
    setup()
