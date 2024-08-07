"""Entry point: run statistical tests."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def main():
    print("Running statistical tests...")
    scripts = [
        ROOT / "src" / "statistics" / "kruskal_wallis_three_methods.py",
        ROOT / "src" / "statistics" / "pairwise_comparisons.py",
        ROOT / "src" / "statistics" / "verify_contributor_counts.py",
    ]
    for script in scripts:
        if script.exists():
            print(f"Running {script.name}")
            subprocess.run([sys.executable, str(script)], check=True)


if __name__ == "__main__":
    main()
