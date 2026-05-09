# Modelo de Dados — PQC Benchmark DW

Banco de dados: **MySQL** | Schema: `pqc_benchmark` | Modelo: **Star Schema v2**

---

## Star Schema v2

3 tabelas de dimensão + 1 tabela de fatos.

```
 ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
 │  dim_algorithm   │   │  dim_operation   │   │  dim_hardware    │
 ├──────────────────┤   ├──────────────────┤   ├──────────────────┤
 │ PK sk_algorithm  │   │ PK sk_operation  │   │ PK sk_hardware   │
 │    algorithm_name│   │    operation_name│   │    provider      │
 │    algorithm_fam.│   │    operation_cat.│   │    instance_type │
 │    crypto_type   │   │    created_at    │   │    cpu_model     │
 │    security_level│   └────────┬─────────┘   │    vcpu          │
 │    nist_approval │            │              │    ram_gb        │
 │    created_at    │            │              │    hypervisor    │
 └────────┬─────────┘            │              │    os            │
          │                      │              │    environment_  │
          │                      │              │      type        │
          │                      │              │    cost_per_     │
          │                      │              │      hour_usd    │
          │                      │              └────────┬─────────┘
          │           ┌──────────┴──────────────┐        │
          └───────────┤     fact_benchmark      ├────────┘
                      ├─────────────────────────┤
                      │ PK sk_benchmark         │
                      │ FK sk_algorithm         │
                      │ FK sk_operation         │
                      │ FK sk_hardware          │
                      │ ── Métricas ──          │
                      │    latencia_ms          │
                      │    payload_kb           │
                      │    key_size_bytes       │
                      │    iterations           │
                      │    hybrid_overhead_pct  │
                      │    vt_classico_pct      │
                      └─────────────────────────┘
```

---

## Tabelas

### `dim_algorithm`

| Coluna | Tipo | Descrição |
|---|---|---|
| `sk_algorithm` | INT PK | Surrogate key |
| `algorithm_name` | VARCHAR | Nome do algoritmo (ex.: `ML-KEM-512`) |
| `algorithm_family` | VARCHAR | Família (ex.: `CRYSTALS-Kyber`) |
| `crypto_type` | VARCHAR | Tipo: `kem`, `signature`, `hybrid` |
| `security_level` | INT | Nível NIST (1–5) |
| `nist_approval` | VARCHAR | Status de aprovação NIST |

### `dim_operation`

| Coluna | Tipo | Descrição |
|---|---|---|
| `sk_operation` | INT PK | Surrogate key |
| `operation_name` | VARCHAR | Nome da operação (ex.: `encapsulate`) |
| `operation_category` | VARCHAR | Categoria: `kem`, `signature`, etc. |

### `dim_hardware`

| Coluna | Tipo | Descrição |
|---|---|---|
| `sk_hardware` | INT PK | Surrogate key |
| `provider` | VARCHAR | Provedor de infraestrutura (ex.: `AWS`, `Local`) |
| `instance_type` | VARCHAR | Tipo de instância |
| `cpu_model` | VARCHAR | Modelo do processador |
| `vcpu` | FLOAT | Número de vCPUs |
| `ram_gb` | FLOAT | Memória RAM em GB |
| `os` | VARCHAR | Sistema operacional |
| `environment_type` | VARCHAR | `cloud` ou `local` |
| `cost_per_hour_usd` | DECIMAL | Custo por hora em USD |

### `fact_benchmark`

| Coluna | Tipo | Descrição |
|---|---|---|
| `sk_benchmark` | INT PK | Surrogate key |
| `sk_algorithm` | INT FK | → `dim_algorithm` |
| `sk_operation` | INT FK | → `dim_operation` |
| `sk_hardware` | INT FK | → `dim_hardware` |
| `latencia_ms` | FLOAT | Latência observada em ms |
| `payload_kb` | FLOAT | Tamanho do payload em KB |
| `key_size_bytes` | INT | Tamanho da chave em bytes |
| `iterations` | INT | Número de iterações no benchmark |
| `hybrid_overhead_pct` | FLOAT | Overhead percentual do modo híbrido |
| `vt_classico_pct` | FLOAT | Comparativo vs algoritmo clássico (%) |

---

## Coluna mapeada pelo dashboard

O `data_adapter` executa um JOIN e retorna um DataFrame "plano" com as seguintes colunas:

| DataFrame col | Fonte |
|---|---|
| `library` | `dim_algorithm.algorithm_name` |
| `crypto_type` | `dim_algorithm.algorithm_family` |
| `security_level` | `dim_algorithm.security_level` |
| `operation` | `dim_operation.operation_name` |
| `environment` | `dim_hardware.provider` |
| `environment_type` | `dim_hardware.environment_type` |
| `processor` | `dim_hardware.cpu_model` |
| `ram_gb` | `dim_hardware.ram_gb` |
| `operating_system` | `dim_hardware.os` |
| `vcpu` | `dim_hardware.vcpu` |
| `response_ms` | `fact_benchmark.latencia_ms` |
| `payload_kb` | `fact_benchmark.payload_kb` |
| `key_size_bytes` | `fact_benchmark.key_size_bytes` |
| `iterations` | `fact_benchmark.iterations` |
| `vs_classic_pct` | `fact_benchmark.vt_classico_pct` |
| `hybrid_overhead_pct` | `fact_benchmark.hybrid_overhead_pct` |

---

## Configuração MySQL

Defina as variáveis de ambiente em `.env`:

```
DB_USER=root
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=3306
DB_NAME=pqc_benchmark
```

Script DDL: [`dw_schema_star_v2.sql`](../dw_schema_star_v2.sql)


---

## Query Principal do Dashboard

A view consolidada utilizada pelo dashboard é gerada por:

```sql
SELECT
    da.algorithm_name                               AS library,
    LOWER(COALESCE(da.crypto_type, 'unknown'))      AS crypto_type,
    da.security_level,
    do.operation_name                               AS operation,
    dh.provider                                     AS environment,
    dh.environment_type,
    dh.cpu_model                                    AS processor,
    dh.ram_gb,
    dh.os                                           AS operating_system,
    dh.vcpu,
    dh.hypervisor,
    COALESCE(dem.method_name, 'SEQUENTIAL')         AS execution_method,
    fb.execution_time_ms                            AS response_ms,
    COALESCE(dm.payload_kb, 0)                      AS payload_kb,
    COALESCE(dm.key_size_bytes, 0)                  AS key_size_bytes,
    COALESCE(dm.iterations, 1)                      AS iterations,
    0                                               AS hybrid_overhead_pct,
    0                                               AS vs_classic_pct
FROM fact_benchmark fb
JOIN  dim_algorithm        da  ON fb.sk_algorithm        = da.sk_algorithm
JOIN  dim_operation        do  ON fb.sk_operation        = do.sk_operation
JOIN  dim_hardware         dh  ON fb.sk_hardware         = dh.sk_hardware
JOIN  dim_measurement      dm  ON fb.sk_measurement      = dm.sk_measurement
LEFT JOIN dim_execution_method dem ON fb.sk_execution_method = dem.sk_execution_method
ORDER BY fb.sk_benchmark DESC
LIMIT 10000;
```

---

## Reconstrução do Banco

Para recriar o banco do zero:

```bash
# 1. Criar o schema MySQL
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS pqc_benchmark CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 2. Criar as tabelas via SQLAlchemy (modelos em src/dw/models/)
python -c "
from src.dw.database import db
from src.dw.models.base import Base
from src.dw.models.dimensions import *
from src.dw.models.facts import *
from src.dw.models.logs import *
Base.metadata.create_all(db.engine)
print('Tabelas criadas com sucesso.')
"

# 3. Migrar as dimensões a partir dos dados de origem
python migrate_dimensions.py

# 4. Executar o pipeline ETL completo
python run_etl.py
```

Veja [ETL.md](ETL.md) para detalhes completos do pipeline.

---

## Ambientes Registrados

| Provider              | Tipo    | Billing           | Config             |
|-----------------------|---------|-------------------|--------------------|
| Google Cloud Platform | cloud   | CPU (vCPU-s)      | `$0.000011/vCPU-s` |
| Azure                 | cloud   | VPS + Free Tier   | `$0.012/h`, 730h/mes grátis |
| AWS EC2               | cloud   | VPS               | `$0.0864/h`, 2 vCPUs |
| Local                 | local   | N/A               | Sem custo          |
| Hostinger VPS         | vps     | VPS               | Sem custo configurado |

Configuração de preços: [`cloud_pricing.json`](../cloud_pricing.json)
