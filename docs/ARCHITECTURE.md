# Arquitetura — PQC Benchmark Dashboard

## Estrutura de Diretórios

```
dashboard/
├── app.py                     # Entry point: inicializa Dash, carrega dados, expõe `server`
├── requirements.txt           # Dependências Python
├── docker-compose.yml         # MySQL 8 para desenvolvimento local
├── dw_schema_star_v2.sql      # DDL do Star Schema v2
├── .env                       # Variáveis de ambiente (não versionado)
│
├── core/                      # Pacote principal do dashboard
│   ├── callbacks.py           # Todos os callbacks Dash registrados
│   ├── chart_core.py          # Helpers de layout e estilos de gráficos
│   ├── chart_figures.py       # Funções que constroem cada figura Plotly
│   ├── colors.py              # Paleta de cores e mapeamentos
│   ├── config.py              # Constantes de configuração (títulos, cache TTL, etc.)
│   ├── dashboard_payload.py   # Dataclass DashboardPayload + build_dashboard_payload()
│   ├── data.py                # Fachada pública: get_dataframe(), get_dataset_version(),
│   │                          #   invalidate_cache() — delega para data_adapter
│   ├── data_adapter.py        # DataStore: cache TTL thread-safe, auto-detect MySQL/Excel
│   ├── excel_engine.py        # Leitura e normalização de planilha Excel (fallback)
│   ├── filter_config.py       # Definição declarativa dos filtros (ID, label, coluna)
│   ├── filters.py             # apply_filters(df, envs, libs, …) → DataFrame filtrado
│   ├── layout.py              # build_layout(): monta o layout completo + dcc.Store
│   ├── layout_sections.py     # Hero, painel de filtros, grid de gráficos
│   ├── layout_shared.py       # Componentes Bootstrap reutilizáveis (badges, KPI cards)
│   └── ui_text.py             # Strings de interface + CHART_SECTIONS registry
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_dashboard_callbacks.py
│   │   ├── test_dashboard_layout.py
│   │   ├── test_data_store.py
│   │   ├── test_transformer.py
│   │   └── test_validator.py
│   └── integration/
│
├── assets/
│   └── dashboard.css          # CSS customizado do dashboard
│
├── banco-planilha/            # Planilhas Excel de benchmark (fonte alternativa)
│
├── data/
│   ├── raw/                   # Dados brutos de entrada
│   ├── processed/             # Dados processados intermediários
│   └── logs/                  # Logs gerados
│
└── docs/
    ├── ARCHITECTURE.md        # Este arquivo
    ├── DATABASE.md            # Schema do banco e DER
    ├── ETL.md                 # Pipeline de carga de dados
    └── QUICKSTART.md          # Instalação e execução
```

---

## Fluxo de Dados (Runtime)

```
app.py
  │
  ├── get_dataframe()              # core/data.py → core/data_adapter.py (DataStore)
  │     ├── [MySQL disponível]  → query JOIN fact_benchmark + 3 dimensões
  │     └── [fallback]          → core/excel_engine.py → planilha Excel
  │           └── DataFrame normalizado (colunas padronizadas)
  │
  ├── build_layout(app, df)        # core/layout.py → core/layout_sections.py
  │     └── Componentes Dash/Bootstrap + dcc.Store(id="etl-refresh-ts")
  │
  └── register_callbacks(app)      # core/callbacks.py
        │
        ├── etl_refresh()
        │     └── botão "Atualizar Dados" → invalidate_cache() + cache_clear()
        │           → get_dataframe() (recarrega) → seta etl-refresh-ts
        │
        ├── _cached_dashboard_payload(dataset_version, filtros…)   [LRU maxsize=64]
        │     └── build_dashboard_payload(df_filtrado)   # core/dashboard_payload.py
        │           └── chart_figures.py → 6 figuras Plotly
        │
        └── update_dashboard(filtros…, etl_refresh_ts)
              └── payload.as_callback_tuple() → 7 outputs
```

---

## Módulos — core/

| Módulo               | Responsabilidade                                                              |
|----------------------|-------------------------------------------------------------------------------|
| `callbacks.py`       | Callbacks Dash: `etl_refresh`, `clear_filters`, `update_dashboard`            |
| `chart_core.py`      | Helpers de traço Plotly (cores, eixos, hover, layout base)                    |
| `chart_figures.py`   | Uma função por figura: latência, throughput, radar, heatmap, scatter          |
| `colors.py`          | Paleta e mapeamentos por `crypto_type`, operação, algoritmo                   |
| `config.py`          | Constantes: título, versão, `CACHE_TTL_SECONDS`, `QUERY_ROW_LIMIT`            |
| `dashboard_payload.py` | `DashboardPayload` dataclass + `build_dashboard_payload()` + `as_callback_tuple()` |
| `data.py`            | Fachada: re-exporta `get_dataframe`, `get_dataset_version`, `invalidate_cache` |
| `data_adapter.py`    | `DataStore` (TTL cache, lock, auto-detect), `DataSource` enum                 |
| `excel_engine.py`    | Leitura e normalização de planilhas Excel (fonte alternativa ao MySQL)        |
| `filter_config.py`   | Lista declarativa de filtros (ID, label, coluna, opções)                      |
| `filters.py`         | `apply_filters(df, …)` → DataFrame filtrado                                   |
| `layout.py`          | `build_layout()`: monta o layout Dash + `dcc.Store` para coordenação de refresh |
| `layout_sections.py` | `build_hero_section`, `build_filter_panel`, `build_analysis_children`         |
| `layout_shared.py`   | Componentes Bootstrap reutilizáveis (badges, cards de KPI)                    |
| `ui_text.py`         | Strings de interface + `CHART_SECTIONS` (registry das 6 seções de gráficos)  |

---

## Decisões de Design

### Cache LRU com Invalidação Sob Demanda

`_cached_dashboard_payload` usa `@lru_cache(maxsize=64)`. A chave inclui `dataset_version` (hash SHA do DataFrame) mais todos os valores dos filtros ativos. Isso evita recálculos quando o usuário alterna filtros sem alterar os dados.

Quando o botão **"Atualizar Dados"** é clicado:
1. `invalidate_cache()` zera `DataStore._loaded_at = 0.0` → o próximo acesso força reload do MySQL
2. `_cached_dashboard_payload.cache_clear()` descarta todas as entradas LRU
3. `get_dataframe()` é chamado imediatamente para pré-aquecer o cache
4. `dcc.Store(id="etl-refresh-ts")` recebe um timestamp → dispara `update_dashboard`

### Padrão dcc.Store como Intermediário

O botão ETL não dispara `update_dashboard` diretamente. A cadeia é:

```
etl-refresh-btn (click) → etl_refresh() → etl-refresh-ts (Store) → update_dashboard()
```

Isso garante que `invalidate_cache()` executa **antes** de `get_dataset_version()` dentro de `update_dashboard`, evitando cache stale.

### DataStore — Auto-detect de Fonte

`DataStore._detect_source()` testa conexão MySQL. Se falhar, cai para Excel. A ordem de prioridade é:
1. MySQL (`DB_HOST`, `DB_NAME`, etc. no `.env`)
2. Planilha Excel em `banco-planilha/`
3. DataFrame vazio (dashboard renderiza com aviso)

### Star Schema v2 — Separação DW / Dashboard

O DDL (`dw_schema_star_v2.sql`) define o schema Star Schema v2 com 3 dimensões (`dim_algorithm`, `dim_operation`, `dim_hardware`) e 1 tabela fato (`fact_benchmark`). O dashboard acessa o banco apenas via `DataStore` com uma query JOIN direta — sem ORM, sem modelos SQLAlchemy no runtime do dashboard.

---

## Stack

| Componente                | Versão  |
|---------------------------|---------|
| Python                    | 3.12    |
| Dash                      | 2.18.2  |
| dash-bootstrap-components | 1.6.0   |
| Plotly                    | 5.24.1  |
| Pandas                    | 2.2.3   |
| SQLAlchemy                | 2.0.36  |
| PyMySQL                   | 1.1.1   |
| python-dotenv             | 1.0.1   |
| pytest                    | 8.3.4   |

---

## Documentação Relacionada

- [DATABASE.md](DATABASE.md) — Schema completo, DER e DDL
- [ETL.md](ETL.md) — Pipeline de carga e DataStore
- [QUICKSTART.md](QUICKSTART.md) — Instalação, Docker e execução
