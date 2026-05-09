# Acesso a Dados — PQC Benchmark

O dashboard **não tem pipeline ETL próprio**. O acesso a dados é gerenciado por `core/data_adapter.py`, que detecta automaticamente a fonte disponível.

---

## Fluxo de detecção de fonte

```
DataStore.get_dataframe()
      │
      ├─ TTL não expirado? ──► retorna cache
      │
      └─ _detect_source()
            ├─ MySQL acessível e com dados? ──► carrega via JOIN (SQLAlchemy)
            ├─ Planilha em banco-planilha/?   ──► carrega via excel_engine
            └─ Nenhuma fonte?                ──► DataFrame vazio
```

---

## `core/data_adapter.py`

Ponto central de acesso a dados. Expõe:

| Função pública | Descrição |
|---|---|
| `get_dataframe()` | Retorna o DataFrame com cache TTL |
| `get_dataset_version()` | Hash compacto dos dados carregados |
| `detect_source()` | Retorna `"mysql"`, `"excel"` ou `"none"` |

Classe interna: `DataStore` — thread-safe, singleton, TTL configurável.

**Variáveis de ambiente:**

| Variável | Padrão | Descrição |
|---|---|---|
| `CACHE_TTL_SECONDS` | `1800` | Segundos até expirar o cache |
| `QUERY_ROW_LIMIT` | `10000` | Limite de linhas na query MySQL |

---

## `core/excel_engine.py`

Fallback quando MySQL não está disponível. Lê arquivos `.xlsx` / `.xls` de `banco-planilha/`.

Funções relevantes:

| Função | Descrição |
|---|---|
| `spreadsheet_available()` | Verifica se há planilha na pasta |
| `load_spreadsheet()` | Carrega e normaliza a planilha |

---

## Normalização (`_normalize_df`)

Aplicada sobre qualquer DataFrame antes de ser cacheado:

1. Colunas numéricas definidas em `core/schema.py → NUMERIC_COLUMNS` são convertidas com `pd.to_numeric(..., errors="coerce")` — valores inválidos viram `NaN` (não `0`).
2. Linhas com `library` ou `operation` nulos são descartadas.
3. `crypto_type` é normalizado para minúsculas.

---

## Carga inicial do banco MySQL

O schema DDL está em [`dw_schema_star_v2.sql`](../dw_schema_star_v2.sql). Para criar o banco:

```bash
mysql -u root -p < dw_schema_star_v2.sql
```

A carga de dados fica a critério do time de engenharia de dados (fora do escopo do dashboard).


---

## Visão Geral

O pipeline ETL é **independente do dashboard**. Os dois scripts utilitários populam e reconstroem o banco `pqc_benchmark` sem nenhuma dependência da camada de visualização.

```
Dados de origem
      │
      ├──► migrate_dimensions.py   ──► dim_algorithm, dim_operation,
      │                                dim_hardware, dim_date, dim_time,
      │                                dim_execution_method, dim_measurement
      │
      └──► run_etl.py              ──► fact_benchmark
                                       (executa o pipeline completo)
```

---

## Scripts

### `run_etl.py` — Pipeline Completo

**Quando usar:** carga inicial ou recarga total da tabela de fatos.

**O que faz:**
1. Inicializa o engine SQLAlchemy via `src.dw.database.db`
2. Carrega as configurações de conexão a partir de `src.config.settings`
3. Instancia `DataWarehouseETL` (orquestrador em `src/dw/etl/pipeline.py`)
4. Executa as etapas: Extract → Transform → Load
5. Registra cada etapa na tabela `etl_execution_log`
6. Registra métricas de qualidade em `data_quality_metrics`

**Execução:**

```bash
python run_etl.py
```

**Logs:** gravados em `data/logs/` (caminho configurado em `src/config/settings.py`).

---

### `migrate_dimensions.py` — Migração de Dimensões

**Quando usar:** criação inicial das dimensões a partir dos dados de origem, ou repovoamento de dimensões após alteração de schema.

**O que faz:**
1. Conecta ao banco via `src.dw.database.DatabaseManager`
2. Para cada dimensão, verifica se o dado já existe (evita duplicatas por `nk_id_*`):
   - `dim_algorithm` — algoritmos com metadados NIST
   - `dim_operation` — operações (keygen, sign, verify, etc.)
   - `dim_hardware` — ambientes de hardware/cloud
   - `dim_date` — dimensão de data (calendário completo)
   - `dim_time` — dimensão de hora (granularidade por segundo)
   - `dim_execution_method` — métodos de execução (Sequential, Parallel, etc.)
   - `dim_measurement` — parâmetros de medição (payload, keysize, iterations)

**Execução:**

```bash
python migrate_dimensions.py
```

**Idempotência:** seguro para reexecutar; registros existentes são ignorados com base na natural key (`nk_id_*`).

---

## Ordem de Execução Recomendada

Para reconstrução completa do banco:

```bash
# 1. Garantir que o schema MySQL existe
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS pqc_benchmark CHARACTER SET utf8mb4;"

# 2. Criar as tabelas (DDL via SQLAlchemy)
python -c "
from src.dw.database import db
from src.dw.models.base import Base
from src.dw.models.dimensions import *
from src.dw.models.facts import *
from src.dw.models.logs import *
Base.metadata.create_all(db.engine)
"

# 3. Popular dimensões
python migrate_dimensions.py

# 4. Executar ETL (popula fact_benchmark)
python run_etl.py
```

---

## Monitoramento

Após execução, consulte os logs diretamente no banco:

```sql
-- Verificar execuções ETL
SELECT session_id, stage_name, status, records_processed, duration_seconds, started_at
FROM etl_execution_log
ORDER BY started_at DESC
LIMIT 20;

-- Verificar métricas de qualidade
SELECT session_id, metric_name, metric_value, status, threshold, recorded_at
FROM data_quality_metrics
ORDER BY recorded_at DESC
LIMIT 20;

-- Contagem atual da tabela de fatos
SELECT COUNT(*) AS total_registros FROM fact_benchmark;
```

---

## Configuração de Ambiente

Ambos os scripts leem as variáveis de ambiente do arquivo `.env` na raiz do projeto:

```env
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=3306
DB_NAME=pqc_benchmark
```

Veja [QUICKSTART.md](QUICKSTART.md) para configuração completa do ambiente.

---

## Módulos Internos (src/dw/)

| Módulo                    | Responsabilidade                                    |
|---------------------------|-----------------------------------------------------|
| `src/dw/database.py`      | Engine SQLAlchemy, `DatabaseManager`, `db` singleton |
| `src/dw/etl/pipeline.py`  | Orquestrador `DataWarehouseETL`                     |
| `src/dw/etl/transformer.py` | Transformações e normalização de tipos            |
| `src/dw/etl/loader.py`    | Carga incremental / upsert                          |
| `src/dw/models/dimensions.py` | ORM: 7 tabelas de dimensão                     |
| `src/dw/models/facts.py`  | ORM: `FactBenchmark`                                |
| `src/dw/models/logs.py`   | ORM: `ETLExecutionLog`, `DataQualityMetrics`        |
| `src/config/settings.py`  | Dataclass de configurações (lê `.env`)              |
