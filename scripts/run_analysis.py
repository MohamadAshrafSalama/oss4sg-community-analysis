"""Entry point: run correlation and core contributor analysis."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def main():
    print("Running analysis pipeline...")
    scripts = [
        ROOT / "src" / "analysis" / "join_leave_rates.py",
        ROOT / "src" / "analysis" / "build_corr.py",
        ROOT / "src" / "analysis" / "recreate_experiment.py",
    ]
    for script in scripts:
        if script.exists():
            print(f"Running {script.name}")
            subprocess.run([sys.executable, str(script)], check=True)


if __name__ == "__main__":
    main()
