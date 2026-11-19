import argparse
from datetime import date
from .generate import seed_database, default_ref

ap = argparse.ArgumentParser(description="Recria o banco e carrega os dados de DEMONSTRACAO (ficticios)")
ap.add_argument("--ref", help="mes de referencia YYYY-MM (padrao: ultimo mes fechado)")
ap.add_argument("--seed", type=int, default=42)
a = ap.parse_args()
ref = default_ref()
if a.ref:
    y, m = a.ref.split("-")
    ref = date(int(y), int(m), 1)
seed_database(ref, a.seed)
