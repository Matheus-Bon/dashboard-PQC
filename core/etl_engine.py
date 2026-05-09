"""ETL Engine — carrega dados brutos (Excel) no star schema MySQL.

Estratégia: truncate-reload em fact_benchmark (seguro para ~2k linhas).
As dimensões são semeadas pelo dw_schema_star_v2.sql; o ETL só carrega fatos.

Uso:
    from core.etl_engine import run_full_etl
    result = run_full_etl()
    # result = {"status": "ok", "rows_loaded": 2277, "message": "..."}
"""
from __future__ import annotations

import logging
import os
import time
from collections import Counter
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SQL_SCHEMA = _PROJECT_ROOT / "dw_schema_star_v2.sql"

# Localidades conhecidas do arquivo Excel bruto (ordem de preferência)
_RAW_EXCEL_CANDIDATES: list[Path] = [
    _PROJECT_ROOT / "data" / "raw" / "dados bruto.xlsx",
    _PROJECT_ROOT / "dados bruto.xlsx",
]

# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _build_engine():
    """Cria um SQLAlchemy engine lendo credenciais do .env."""
    from sqlalchemy import create_engine

    url = "mysql+pymysql://{user}:{passwd}@{host}:{port}/{db}".format(
        user=os.getenv("DB_USER", "root"),
        passwd=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "3306"),
        db=os.getenv("DB_NAME", "pqc_benchmark_dw"),
    )
    return create_engine(url, pool_pre_ping=True)


def _split_sql_statements(sql_text: str) -> list[str]:
    """Divide um arquivo SQL em statements individuais executáveis."""
    statements: list[str] = []
    for raw in sql_text.split(";"):
        # Remove linhas que são apenas comentários SQL (-- ...)
        lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
        stmt = "\n".join(lines).strip()
        if stmt:
            statements.append(stmt)
    return statements


def _coerce_float(v) -> Optional[float]:
    try:
        f = float(v)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


def _coerce_int(v) -> Optional[int]:
    try:
        f = float(v)
        return None if pd.isna(f) else int(f)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# API pública — passos do ETL
# ---------------------------------------------------------------------------


def find_raw_excel() -> Optional[Path]:
    """Retorna o caminho do Excel bruto verificando locais conhecidos."""
    for candidate in _RAW_EXCEL_CANDIDATES:
        if candidate.exists():
            logger.debug("Excel bruto encontrado: %s", candidate)
            return candidate
    return None


def ensure_schema(engine=None) -> None:
    """Cria o schema e semeia dimensões se ainda não existirem.

    Executa o arquivo dw_schema_star_v2.sql inteiro, ignorando erros
    esperados (tabela já existe, chave duplicada nas dimensões).
    """
    if engine is None:
        engine = _build_engine()

    sql_text = _SQL_SCHEMA.read_text(encoding="utf-8")
    statements = _split_sql_statements(sql_text)

    from sqlalchemy import text

    # Códigos MySQL que indicam estado já correto (não são erros reais)
    _ignorable = {"1007", "1050", "1062", "already exists", "Duplicate entry"}

    with engine.connect() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception as exc:
                err = str(exc)
                if any(code in err for code in _ignorable):
                    pass  # DB/tabela já existe ou dimensão já inserida — OK
                else:
                    logger.debug("Schema stmt aviso: %.80s | %s", stmt, exc)

    logger.info("Schema verificado/criado com sucesso")


def load_raw_excel(path: Optional[Path] = None) -> pd.DataFrame:
    """Lê a aba 'Dados Brutos' do arquivo Excel de benchmark."""
    if path is None:
        path = find_raw_excel()
    if path is None:
        raise FileNotFoundError(
            "Arquivo Excel bruto não encontrado. "
            "Esperado em: data/raw/dados bruto.xlsx ou raiz do projeto."
        )
    logger.info("Lendo dados brutos: %s", path)
    df = pd.read_excel(path, sheet_name="Dados Brutos", engine="openpyxl")
    logger.info("Carregados %d registros brutos", len(df))
    return df


def _build_dim_lookups(engine) -> tuple[dict, dict, dict]:
    """Constrói dicts de lookup: nome→sk para cada dimensão."""
    from sqlalchemy import text

    with engine.connect() as conn:
        alg_rows = conn.execute(
            text("SELECT sk_algorithm, algorithm_name FROM dim_algorithm")
        ).fetchall()
        op_rows = conn.execute(
            text("SELECT sk_operation, operation_name FROM dim_operation")
        ).fetchall()
        hw_rows = conn.execute(
            text("SELECT sk_hardware, provider, cpu_model FROM dim_hardware")
        ).fetchall()

    alg_lookup: dict[str, int] = {str(r[1]).strip(): int(r[0]) for r in alg_rows}
    op_lookup: dict[str, int] = {str(r[1]).strip().lower(): int(r[0]) for r in op_rows}
    hw_lookup: dict[tuple[str, str], int] = {
        (str(r[1]).strip(), str(r[2]).strip()): int(r[0]) for r in hw_rows
    }
    logger.debug(
        "Lookups: %d algoritmos, %d operações, %d hardwares",
        len(alg_lookup),
        len(op_lookup),
        len(hw_lookup),
    )
    return alg_lookup, op_lookup, hw_lookup


def map_to_fact(raw_df: pd.DataFrame, engine) -> pd.DataFrame:
    """Mapeia linhas brutas para fact_benchmark usando surrogate keys."""
    alg_lookup, op_lookup, hw_lookup = _build_dim_lookups(engine)

    rows: list[dict] = []
    skipped: list[tuple] = []

    for _, row in raw_df.iterrows():
        algoritmo = str(row.get("algoritmo", "")).strip()
        operacao = str(row.get("operacao", "")).strip().lower()
        provedor = str(row.get("Provedor", "")).strip()
        processador = str(row.get("processador", "")).strip()

        sk_algorithm = alg_lookup.get(algoritmo)
        sk_operation = op_lookup.get(operacao)
        sk_hardware = hw_lookup.get((provedor, processador))

        if sk_algorithm is None or sk_operation is None or sk_hardware is None:
            skipped.append((algoritmo, operacao, provedor, processador))
            continue

        rows.append(
            {
                "sk_algorithm": sk_algorithm,
                "sk_operation": sk_operation,
                "sk_hardware": sk_hardware,
                "payload_kb": _coerce_float(row.get("payload_kb")),
                "key_size_bytes": _coerce_int(row.get("tamanho_chave_bytes")),
                "latencia_ms": _coerce_float(row.get("latencia_ms")),
                "iterations": _coerce_int(row.get("iteracoes")),
                "vt_classico_pct": _coerce_float(row.get("vs_classico_pct")),
                "overhead_hibrido_pct": _coerce_float(row.get("overhead_hibrido_pct")),
            }
        )

    if skipped:
        by_provider = Counter(f"{p}/{c}" for _, _, p, c in skipped)
        logger.warning(
            "%d registros ignorados (dimensão não resolvida). "
            "Combinações Provedor/CPU sem correspondência: %s",
            len(skipped),
            dict(by_provider.most_common(10)),
        )

    logger.info("Mapeados %d registros para fact_benchmark", len(rows))
    return pd.DataFrame(rows)


def load_facts(fact_df: pd.DataFrame, engine) -> int:
    """Trunca fact_benchmark e insere os novos fatos. Retorna nº de linhas."""
    if fact_df.empty:
        logger.warning("Nenhum registro de fato para inserir")
        return 0

    from sqlalchemy import text

    cols = list(fact_df.columns)
    col_names = ", ".join(f"`{c}`" for c in cols)
    placeholders = ", ".join(f":{c}" for c in cols)
    insert_sql = text(f"INSERT INTO fact_benchmark ({col_names}) VALUES ({placeholders})")

    records = fact_df.to_dict(orient="records")
    chunk_size = 500

    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        conn.execute(text("TRUNCATE TABLE fact_benchmark"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        logger.info("fact_benchmark truncada")

        for i in range(0, len(records), chunk_size):
            chunk = records[i : i + chunk_size]
            conn.execute(insert_sql, chunk)

        conn.commit()

    logger.info("Inseridos %d registros em fact_benchmark", len(fact_df))
    return len(fact_df)


# ---------------------------------------------------------------------------
# Orquestrador principal
# ---------------------------------------------------------------------------


def run_full_etl(raw_excel_path: Optional[Path] = None) -> dict:
    """Executa o pipeline ETL completo: Excel → MySQL star schema.

    Returns:
        dict com chaves: status ("ok"|"error"), rows_loaded (int), message (str)
    """
    t0 = time.monotonic()
    try:
        engine = _build_engine()

        # 1. Garantir schema e dimensões
        ensure_schema(engine)

        # 2. Carregar dados brutos
        raw_df = load_raw_excel(raw_excel_path)

        # 3. Mapear para star schema
        fact_df = map_to_fact(raw_df, engine)

        # 4. Persistir fatos
        n_rows = load_facts(fact_df, engine)

        elapsed = time.monotonic() - t0
        msg = f"ETL concluído: {n_rows:,} registros carregados em {elapsed:.1f}s"
        logger.info(msg)
        return {"status": "ok", "rows_loaded": n_rows, "message": msg}

    except Exception as exc:
        msg = f"ETL falhou: {exc}"
        logger.error(msg, exc_info=True)
        return {"status": "error", "rows_loaded": 0, "message": msg}
