"""Run this in the Codespace terminal to confirm your workspace is ready:

    python check_setup.py
"""
import sys
from pathlib import Path

problems = []

if sys.version_info < (3, 10):
    problems.append(f"Python 3.10+ needed, found {sys.version.split()[0]}")

for lib in ["duckdb", "pandas", "requests", "streamlit"]:
    try:
        mod = __import__(lib)
        print(f"  ok  {lib} {getattr(mod, '__version__', '')}")
    except ImportError:
        problems.append(f"{lib} is not installed")

data = Path(__file__).parent / "data" / "penguins.csv"
if not data.exists():
    problems.append("data/penguins.csv is missing")
else:
    try:
        import duckdb
        rows = duckdb.sql(f"SELECT count(*) FROM '{data}'").fetchone()[0]
        print(f"  ok  DuckDB read {rows} rows from data/penguins.csv")
    except Exception as e:  # noqa: BLE001
        problems.append(f"DuckDB could not read the sample data: {e}")

if problems:
    print("\nNot ready yet:")
    for p in problems:
        print("  -", p)
    print("\nFix: run  pip install --user -r requirements.txt  then try again.")
    sys.exit(1)

print("\nYour workspace is ready.")
