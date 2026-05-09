from __future__ import annotations
import logging
import os
import threading
import time
from enum import Enum
from typing import Optional
import pandas as pd
from dotenv import load_dotenv
from core.schema import (
    COL_CRYPTO_TYPE,
    NUMERIC_COLUMNS,
    REQUIRED_COLUMNS,
)

load_dotenv()
logger = logging.getLogger(__name__)

_CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "1800"))
_QUERY_ROW_LIMIT = int(os.getenv("QUERY_ROW_LIMIT", "10000"))

class DataSource(Enum):
    MYSQL = "mysql"
    EXCEL = "excel"
    NONE = "none"

def _build_mysql_url() -> str:
    return "mysql+pymysql://{user}:{passwd}@{host}:{port}/{db}".format(
        user=os.getenv("DB_USER", "root"),
        passwd=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "3306"),
        db=os.getenv("DB_NAME", "pqc_benchmark"),
    )

class DataStore:

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._df: Optional[pd.DataFrame] = None
        self._version: Optional[str] = None
        self._loaded_at: float = 0.0
        self._source: Optional[DataSource] = None
        self._engine = None 

    def get_dataframe(self) -> pd.DataFrame:
        with self._lock:
            if self._is_stale():
                self._reload()
            return self._df 

    def get_dataset_version(self) -> str:
        with self._lock:
            if self._is_stale():
                self._reload()
            return self._version or "unknown"

    def invalidate(self) -> None:
        with self._lock:
            self._loaded_at = 0.0

    def _is_stale(self) -> bool:
        if self._df is None:
            return True
        return (time.monotonic() - self._loaded_at) > _CACHE_TTL

    def _reload(self) -> None:
        source = self._detect_source()

        if source == DataSource.MYSQL:
            self._auto_etl_if_needed()
            df = self._load_from_mysql()
        elif source == DataSource.EXCEL:
            df = self._load_from_excel()
        else:
            logger.error("Nenhuma fonte de dados disponível.")
            df = pd.DataFrame()

        _normalize_df(df)

        if not df.empty:
            cols = [c for c in ("library", "operation", "response_ms") if c in df.columns]
            sig = pd.util.hash_pandas_object(df[cols], index=False).sum()
            self._version = f"{len(df)}:{int(sig)}"
        else:
            self._version = "empty:0"

        logger.info("Dataset carregado: %d registros (fonte: %s)", len(df), source.value)
        self._df = df
        self._loaded_at = time.monotonic()

    def _detect_source(self) -> DataSource:
        if self._source is not None:
            return self._source

        if self._try_mysql():
            self._source = DataSource.MYSQL
            logger.info("Fonte de dados: MySQL")
        elif self._try_excel():
            self._source = DataSource.EXCEL
            logger.info("Fonte de dados: Planilha Excel (banco-planilha/)")
        else:
            self._source = DataSource.NONE
            logger.warning("Nenhuma fonte de dados encontrada")

        return self._source

    def _try_mysql(self) -> bool:
        try:
            from sqlalchemy import create_engine, text
            if self._engine is None:
                self._engine = create_engine(_build_mysql_url(), pool_pre_ping=True)
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1")) 
            return True
        except Exception as exc:
            logger.info("MySQL indisponível: %s", exc)
            self._engine = None
            return False

    def _auto_etl_if_needed(self) -> None:
        from sqlalchemy import text

        needs_etl = False
        try:
            with self._engine.connect() as conn:
                count = conn.execute(text("SELECT COUNT(*) FROM fact_benchmark")).scalar()
            needs_etl = not (count and count > 0)
        except Exception:
            needs_etl = True 

        if not needs_etl:
            return

        try:
            from core.etl_engine import find_raw_excel, run_full_etl

            if find_raw_excel() is None:
                logger.warning("Nenhuma planilha bruta encontrada para ETL.")
                return

            logger.info("fact_benchmark vazia — executando ETL automático...")
            result = run_full_etl()
            logger.info("ETL automático: %s", result["message"])
        except Exception as etl_exc:
            logger.warning("ETL automático falhou: %s", etl_exc)

    def _try_excel(self) -> bool:
        try:
            from core.excel_engine import spreadsheet_available
            return spreadsheet_available()
        except Exception as exc:
            logger.info("Planilha indisponível: %s", exc)
            return False

    def _load_from_mysql(self) -> pd.DataFrame:
        from sqlalchemy import create_engine, text
        if self._engine is None:
            self._engine = create_engine(_build_mysql_url(), pool_pre_ping=True)

        query = text(f"""
            SELECT
                da.algorithm_name                               AS library,
                da.algorithm_family                             AS crypto_type,
                da.security_level,
                do2.operation_name                              AS operation,
                dh.provider                                     AS environment,
                dh.environment_type,
                dh.cpu_model                                    AS processor,
                dh.ram_gb,
                dh.os                                           AS operating_system,
                dh.vcpu,
                fb.latencia_ms                                  AS response_ms,
                fb.payload_kb,
                fb.key_size_bytes,
                fb.iterations,
                COALESCE(fb.vt_classico_pct, 0)                 AS vs_classic_pct,
                COALESCE(fb.overhead_hibrido_pct, 0)            AS hybrid_overhead_pct
            FROM fact_benchmark fb
            JOIN dim_algorithm  da  ON fb.sk_algorithm = da.sk_algorithm
            JOIN dim_operation  do2 ON fb.sk_operation = do2.sk_operation
            JOIN dim_hardware   dh  ON fb.sk_hardware  = dh.sk_hardware
            ORDER BY fb.sk_benchmark DESC
            LIMIT {_QUERY_ROW_LIMIT}
        """) 

        with self._engine.connect() as conn:
            result = conn.execute(query)
            keys = list(result.keys())
            rows = result.fetchall()
        return pd.DataFrame(rows, columns=keys) if rows else pd.DataFrame(columns=keys)

    def _load_from_excel(self) -> pd.DataFrame:
        from core.excel_engine import build_flat_dataframe, read_spreadsheet
        sheets = read_spreadsheet()
        if not sheets:
            return pd.DataFrame()
        return build_flat_dataframe(sheets)

def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if COL_CRYPTO_TYPE in df.columns:
        df[COL_CRYPTO_TYPE] = df[COL_CRYPTO_TYPE].astype(str).str.strip().str.lower()

    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            df.dropna(subset=[col], inplace=True)

    return df

_store = DataStore()

def get_dataframe() -> pd.DataFrame:
    return _store.get_dataframe()

def get_dataset_version() -> str:
    return _store.get_dataset_version()


def invalidate_cache() -> None:
    _store.invalidate()

def detect_source() -> DataSource:
    return _store._detect_source()
