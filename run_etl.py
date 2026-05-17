"""CLI: executa o pipeline ETL completo (Excel → MySQL star schema).

Uso:
    python run_etl.py
"""
from __future__ import annotations

import logging
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

from core.etl_engine import run_full_etl  # noqa: E402 — deve vir após load_dotenv


def main() -> None:
    print("=" * 60)
    print("PQC Benchmark  —  ETL Runner")
    print("=" * 60)
    result = run_full_etl()
    print()
    if result["status"] == "ok":
        print(f"  [OK] {result['message']}")
        sys.exit(0)
    else:
        print(f"  [ERRO] {result['message']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
