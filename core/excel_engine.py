from __future__ import annotations
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent
SPREADSHEET_DIR = _ROOT / "banco-planilha"
DIM_ALGORITHM_COLS = ["sk_algorithm", "algorithm_name", "algorithm_family", "security_level"]
DIM_OPERATION_COLS = ["sk_operation", "operation_name"]
DIM_HARDWARE_COLS = [
    "sk_hardware", "provider", "cpu_model", "vcpu", "ram_gb", "os", "environment_type",
]
FACT_BENCHMARK_COLS = [
    "sk_benchmark", "sk_algorithm", "sk_operation", "sk_hardware",
    "payload_kb", "key_size_bytes", "execution_time_ms",
    "memory_usage_mb", "cpu_usage_percent", "variation_pct", "overhead_pct",
]

SHEET_COLUMNS = {
    "dim_algorithm": DIM_ALGORITHM_COLS,
    "dim_operation": DIM_OPERATION_COLS,
    "dim_hardware": DIM_HARDWARE_COLS,
    "fact_benchmark": FACT_BENCHMARK_COLS,
}

def _latest_xlsx(directory: Path = SPREADSHEET_DIR) -> Optional[Path]:
    if not directory.exists():
        return None
    files = sorted(directory.glob("*.xlsx"), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None

def read_spreadsheet(path: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
    if path is None:
        path = _latest_xlsx()
    if path is None or not path.exists():
        return {}

    logger.info("Lendo planilha: %s", path)
    sheets: Dict[str, pd.DataFrame] = {}
    xls = pd.ExcelFile(path, engine="openpyxl")

    for sheet_name in xls.sheet_names:
        if sheet_name in SHEET_COLUMNS:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            for col in SHEET_COLUMNS[sheet_name]:
                if col not in df.columns:
                    df[col] = None
            sheets[sheet_name] = df
            logger.info("  aba '%s': %d registros", sheet_name, len(df))

    xls.close()
    return sheets

def write_spreadsheet(
    tables: Dict[str, pd.DataFrame],
    filename: Optional[str] = None,
    directory: Path = SPREADSHEET_DIR,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pqc_benchmark_{timestamp}.xlsx"
    filepath = directory / filename
    logger.info("Gravando planilha: %s", filepath)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        order = ["dim_algorithm", "dim_operation", "dim_hardware", "fact_benchmark"]
        for sheet_name in order:
            if sheet_name in tables:
                df = tables[sheet_name]
                expected_cols = SHEET_COLUMNS.get(sheet_name, [])
                if expected_cols:
                    existing = [c for c in expected_cols if c in df.columns]
                    extra = [c for c in df.columns if c not in expected_cols]
                    df = df[existing + extra]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                logger.info("  aba '%s': %d registros", sheet_name, len(df))

        for sheet_name, df in tables.items():
            if sheet_name not in order:
                df.to_excel(writer, sheet_name=sheet_name, index=False)

    logger.info("Planilha gravada com sucesso: %s", filepath)
    return filepath

def build_flat_dataframe(sheets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    fact = sheets.get("fact_benchmark")
    if fact is None or fact.empty:
        return pd.DataFrame()

    dim_alg = sheets.get("dim_algorithm", pd.DataFrame())
    dim_op = sheets.get("dim_operation", pd.DataFrame())
    dim_hw = sheets.get("dim_hardware", pd.DataFrame())

    df = fact.copy()

    if not dim_alg.empty and "sk_algorithm" in dim_alg.columns:
        df = df.merge(dim_alg, on="sk_algorithm", how="left")

    if not dim_op.empty and "sk_operation" in dim_op.columns:
        df = df.merge(dim_op, on="sk_operation", how="left")

    if not dim_hw.empty and "sk_hardware" in dim_hw.columns:
        df = df.merge(dim_hw, on="sk_hardware", how="left")

    rename_map = {
        "algorithm_name": "library",
        "algorithm_family": "crypto_type",
        "operation_name": "operation",
        "provider": "environment",
        "cpu_model": "processor",
        "os": "operating_system",
        "execution_time_ms": "response_ms",
        "overhead_pct": "hybrid_overhead_pct",
        "variation_pct": "vs_classic_pct",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    numeric_cols = ["response_ms", "payload_kb", "key_size_bytes", "ram_gb",
                    "hybrid_overhead_pct", "vs_classic_pct", "vcpu",
                    "memory_usage_mb", "cpu_usage_percent"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "crypto_type" in df.columns:
        df["crypto_type"] = df["crypto_type"].astype(str).str.strip().str.lower()

    return df

def spreadsheet_available() -> bool:
    return _latest_xlsx() is not None

def get_spreadsheet_info() -> Dict:
    path = _latest_xlsx()
    if path is None:
        return {"available": False}
    sheets = read_spreadsheet(path)
    return {
        "available": True,
        "filename": path.name,
        "path": str(path),
        "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        "sheets": {name: len(df) for name, df in sheets.items()},
    }