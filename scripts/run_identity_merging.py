"""Entry point: run identity resolution pipeline."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def main():
    print("Running identity merging pipeline...")
    scripts = [
        ROOT / "src" / "identity" / "run_all_projects.py",
        ROOT / "src" / "identity" / "combine_global.py",
    ]
    for script in scripts:
        if script.exists():
            print(f"Running {script.name}")
            subprocess.run([sys.executable, str(script)], check=True)


if __name__ == "__main__":
    main()
