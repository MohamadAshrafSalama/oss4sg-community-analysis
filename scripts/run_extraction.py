"""Entry point: clone repositories and extract commit data."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def main():
    print("Running extraction pipeline...")
    scripts = [
        ROOT / "src" / "extraction" / "full_clone_all.py",
        ROOT / "src" / "extraction" / "batch_extract_all.py",
        ROOT / "src" / "extraction" / "build_master_commits_fullfat.py",
    ]
    for script in scripts:
        if script.exists():
            print(f"Running {script.name}")
            subprocess.run([sys.executable, str(script)], check=True)


if __name__ == "__main__":
    main()
