# Pontos de Atenção — DW, BI e ETL

Documento de referência para entendimento dos conceitos aplicados neste projeto.

---

## 1. Data Warehouse (DW)

### O que é
Um Data Warehouse é um repositório centralizado de dados integrados e historicizados, otimizado para consultas analíticas (OLAP) em vez de transações (OLTP).

### Metodologia aplicada: Star Schema (Kimball)
Neste projeto utilizamos o **esquema estrela** (Star Schema) de Ralph Kimball:

| Componente | Papel | Exemplo no projeto |
|---|---|---|
| **Tabela Fato** | Armazena métricas/medidas quantitativas | `fact_benchmark` (execution_time_ms, payload_kb, etc.) |
| **Tabelas Dimensão** | Descrevem o contexto das medidas | `dim_algorithm`, `dim_operation`, `dim_hardware` |
| **Surrogate Keys** | Chaves inteiras artificiais (sk_*) substituem chaves naturais | sk_algorithm, sk_operation, sk_hardware |

### Pontos de atenção
- **Granularidade**: Cada linha da `fact_benchmark` representa uma execução individual de benchmark — esta é a menor unidade de análise.
- **Desnormalização controlada**: As dimensões são intencionalmente desnormalizadas (ex.: `dim_hardware` contém provider + cpu + vcpu + ram + os numa só tabela) para simplificar JOINs e acelerar consultas.
- **Redução de 7 → 3 dimensões**: As dimensões `dim_measurement`, `dim_execution_method`, `dim_date` e `dim_time` foram eliminadas por redundância ou dados fabricados.
- **Surrogate vs Natural keys**: Usamos surrogate keys (sk_*) para isolar o DW de mudanças nas chaves das fontes originais.

---

## 2. Business Intelligence (BI)

### O que é
BI é o processo de coleta, integração, análise e apresentação de dados para apoiar decisões. O dashboard é a camada de apresentação do BI.

### Princípios aplicados
1. **Filtros dinâmicos**: Permitem análise exploratória (slice & dice) por qualquer combinação de dimensões.
2. **KPIs diretos**: Latência média, contagem de registros, overhead híbrido — métricas derivadas diretamente da tabela fato.
3. **Visualizações comparativas**: Gráficos posicionam classic vs PQC vs hybrid para evidenciar trade-offs.
4. **Renderização Condicional**: O dashboard oculta automaticamente gráficos vazios ou irrelevantes para o preset selecionado (ex: oculta assinaturas no preset PIX), otimizando o espaço e o foco analítico.
5. **Drill-down**: A aba "Base de Dados" permite explorar tabelas individuais do esquema estrela.

### Pontos de atenção
- **Dados nulos eliminados**: 8 colunas da fact original (cpu_usage_percent, memory_usage_mb, etc.) eram 100% NULL e foram removidas do schema v5 para não poluir análises.
- **Métricas derivadas**: `variation_pct` e `overhead_pct` são calculados em relação a um baseline clássico — o significado depende do contexto da operação.
- **Categorias (crypto_type)**: Os valores "classic", "pqc" e "hybrid" vêm do campo `algorithm_family` da `dim_algorithm`. Originalmente eram mapeados do campo `t` nos JSONs fonte.

---

## 3. ETL (Extract, Transform, Load)

### O que é
ETL é o processo de **Extrair** dados das fontes, **Transformar** (limpar, padronizar, enriquecer) e **Carregar** no destino (DW ou planilha).

### Fluxo implementado neste projeto

```
┌──────────────┐     ┌───────────────┐     ┌──────────────────┐
│  FONTES      │     │  TRANSFORMAR  │     │  DESTINO         │
│              │     │               │     │                  │
│ • MySQL DB   │────▶│ • Joins dims  │────▶│ • DataFrame flat │
│ • Excel .xlsx│     │ • Rename cols │     │ • Dashboard BI   │
│ (banco-plan.)│     │ • Tipos dados │     │ • Excel export   │
└──────────────┘     │ • Strip spaces│     └──────────────────┘
                     └───────────────┘
```

### Padrão Data Adapter
O sistema implementa um **Data Adapter** que abstrai a fonte:
1. **Detecta** se MySQL está disponível (tenta conexão)
2. Se sim → executa query SQL com JOINs do star schema
3. Se não → procura `banco-planilha/*.xlsx` e lê as abas como tabelas
4. Em ambos os casos → retorna um DataFrame unificado para o dashboard

### Pontos de atenção
- **Prioridade MySQL > Excel**: Quando ambos existem, MySQL é preferido. A planilha serve como fallback.
- **Consistência de nomes**: O adapter renomeia colunas (ex.: `algorithm_name` → `library`, `execution_time_ms` → `response_ms`) para manter backward compatibility com o dashboard.
- **Planilha como Star Schema**: O Excel em `banco-planilha/` segue o mesmo modelo estrela com 4 abas: `dim_algorithm`, `dim_operation`, `dim_hardware`, `fact_benchmark`.
- **Validação na importação**: Ao importar uma planilha, o sistema valida se as abas e colunas esperadas existem antes de carregar.
- **Cache**: O DataFrame é cacheado em memória para evitar releituras. Use `reload_data()` para forçar atualização após importação.

---

## 4. Estrutura do Star Schema

```
dim_algorithm ──────┐
  sk_algorithm (PK)  │
  algorithm_name     │
  algorithm_family   │     fact_benchmark
  security_level     │       sk_benchmark (PK)
                     ├──── sk_algorithm (FK)
dim_operation ──────┤       sk_operation (FK)
  sk_operation (PK)  ├──── sk_hardware  (FK)
  operation_name     │       payload_kb
                     │       key_size_bytes
dim_hardware ───────┘       execution_time_ms
  sk_hardware (PK)          memory_usage_mb
  provider                   cpu_usage_percent
  cpu_model                  variation_pct
  vcpu                       overhead_pct
  ram_gb
  os
  environment_type
```

### Contagem atual de registros
| Tabela | Registros |
|---|---|
| dim_algorithm | 23 |
| dim_operation | 7 |
| dim_hardware | 11 |
| fact_benchmark | 2.277 |

---

## 5. Decisões Importantes Documentadas

| Decisão | Motivo |
|---|---|
| Remover `dim_execution_method` | Dados fabricados (Sequential/Parallel não existiam na fonte) |
| Remover `dim_measurement` | Uma única unidade (ms) — dimensão degenerada |
| Remover `dim_date` e `dim_time` | Timestamps não existiam nos dados fonte |
| Remover `hypervisor` | Valor fixo "docker" para 100% dos registros |
| Remover `iterations` | Sempre 1 em todos os registros |
| Remover 8 colunas NULL da fact | cpu_usage_percent, memory_usage_mb etc. — 100% NULL |
| Manter `variation_pct` e `overhead_pct` | Métricas derivadas com valor analítico real |

---

## 6. Glossário

| Termo | Significado |
|---|---|
| **PQC** | Post-Quantum Cryptography — algoritmos resistentes a computação quântica |
| **Hybrid** | Combinação de algoritmo clássico + PQC |
| **Classic** | Algoritmos criptográficos tradicionais (RSA, ECDSA, etc.) |
| **Overhead** | Custo adicional de performance ao usar PQC/hybrid vs classic |
| **Surrogate Key** | Chave artificial (inteiro auto-incremento) que substitui a chave natural |
| **Star Schema** | Modelo dimensional com fato central e dimensões ao redor |
| **Granularidade** | Nível de detalhe de cada registro na tabela fato |
| **OLAP** | Online Analytical Processing — otimizado para consultas analíticas |
| **Slice & Dice** | Técnica de filtrar dados por diferentes combinações de dimensões |
