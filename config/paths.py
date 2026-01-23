# config/paths.py
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DB_PATH = ROOT / "data" / "BD" / "dia_de_sorte.db"
SCHEMA_PATH = ROOT / "data" / "database" / "db_schema.sql"
CSV_PATH = ROOT / "data" / "planilhas" / "DiaDeSorte.csv"

DATA_DIR = ROOT / "data"
BD_DIR = ROOT / "data" / "BD"
