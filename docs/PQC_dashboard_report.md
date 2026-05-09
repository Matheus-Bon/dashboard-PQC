# Relatório Técnico — Dashboard de Criptografia Pós-Quântica

Data: 2026-04-21

Autores: Equipe de Engenharia de Dados / Divulgação Científica

Resumo executivo
-----------------
- Objetivo: Documentar o dashboard de benchmark de algoritmos criptográficos (PQC e clássicos), descrever ETL e modelagem de dados, explicar conceitos de Criptografia Pós-Quântica (PQC) para não-especialistas, sumarizar as principais análises e oferecer recomendações estratégicas para o Banco Inter (foco: transações PIX com baixa latência).

1) Dashboards — seções analíticas
---------------------------------

- KPIs (topo do dashboard):
  - `Algoritmo Mais Rápido`: algoritmo com menor latência média (métrica principal para caminhos críticos de transação).
  - `Overhead Híbrido Médio`: aumento percentual médio de latência quando se usa um esquema híbrido (clássico + PQC).
  - `Latência P50 / P95 / Máx`: medidas resumidas para monitoramento de SLA.
  - `Throughput` e `Utilização de CPU/RAM`: impacto de latência em recursos.

- Ranking de Encapsulamento (KEM): gráfico de barras horizontais com média e IC95 (fig_kem_ranking). Permite identificar o algoritmo com melhor custo temporal por encapsulamento.

- Segurança vs Velocidade: barras por nível de segurança NIST (L1..L5 e Clássico), confrontando latência média com o nível de segurança.

- Comparação de Assinaturas: barras agrupadas (sign/verify) por algoritmo — útil para avaliar SLH-DSA e ML-DSA.

- Latência por Ambiente (Box plot): boxplots horizontais por `environment` e por `library` (local vs cloud). Esses plots evidenciam dispersão, outliers e diferenças entre medianas.

- Comparação direta RSA-2048 vs ML-KEM-512: barras agrupadas por operação funcionalmente equivalente (keygen/encap/decap).

- Análise de Payload: painéis que mostram correlação entre `payload_kb`, `ciphertext_bytes` e `response_ms` (scatter / regressão), além de medidas de throughput por payload.

Observações de UX/UI
- Filtros inteligentes agrupados (Clássico / Híbrido / PQC Puro), colapsáveis e com tooltips explicativos para reduzir a carga cognitiva (Lei de Hick). Filtro de comparação permite selecionar até duas bibliotecas para comparação lado a lado.
- Layout responsivo: KPIs em cards no topo; filtros em painel lateral/drawer em telas pequenas; gráficos adaptáveis por variante (md/lg/xl).

2) ETL e Data Warehouse (arquitetura e fluxo) — Mapeamento para o seu esquema (`dw_schema_star_v2.sql`)
---------------------------------------------------------------------------------------------

Visão geral do pipeline (concreto ao projeto)
- Fonte: arquivos CSV / planilhas Excel (raw) — ingestão via `core/excel_engine.py` e adaptador em `core/data_adapter.py`.
- Staging: os dados brutos são normalizados e validados antes do upsert nas tabelas DW fornecidas (`dim_algorithm`, `dim_operation`, `dim_hardware`, `fact_benchmark`).
- Transformação: a normalização usada no código (`normalize_category`, `extract_family`) permanece válida; campos derivados são carregados em colunas existentes do fato (`vt_classico_pct`, `overhead_hibrido_pct`).
- Orquestração: `run_etl.py` executa o pipeline; pode ser agendado via cron/Task Scheduler, ou orquestrado com Airflow/Prefect.

Observação importante: o seu DW v2 contém 3 dimensões e 1 fato, portanto o relatório original (que propunha mais dimensões) foi adaptado para mapear 1:1 com o esquema real. Não alteramos o esquema — documentamos e fornecemos consultas e views compatíveis.

Mapeamento 1:1 — recomendações do relatório ↔ esquema real
- `dim_algorithm` (existente)
  - chaves: `sk_algorithm` (PK)
  - colunas relevantes: `algorithm_name` ↔ `library`, `algorithm_family` ↔ `family`, `security_level` ↔ `crypto_type`/nível de segurança.

- `dim_operation` (existente)
  - chaves: `sk_operation` (PK)
  - coluna: `operation_name` (ex.: `encap`, `decap`, `sign`, `verify`, `keygen`).

- `dim_hardware` (combina ambiente + hardware)
  - chaves: `sk_hardware` (PK)
  - colunas: `provider`, `cpu_model`, `vcpu`, `ram_gb`, `os`, `environment_type` (local/cloud). Este objeto funciona como `dim_environment` + `dim_hardware` das recomendações.

- `fact_benchmark` (existente)
  - chaves estrangeiras: `sk_algorithm`, `sk_operation`, `sk_hardware`.
  - colunas de métricas (mapeamento):
    - `latencia_ms` ↔ `response_ms` (métrica de latência usada pelo dashboard)
    - `payload_kb` (presente)
    - `key_size_bytes` (presente)
    - `vt_classico_pct` ↔ `vs_classic_pct` (variação vs clássico)
    - `overhead_hibrido_pct` ↔ `hybrid_overhead_pct`
    - `iterations` / `n` (experiment metadata — use `iterations` e contar linhas para `n`)

Campos ausentes / observações
- Não existe, no DW v2 fornecido, um `dim_time` explícito nem coluna `ingest_ts` no fato. Para análises temporais é recomendável que o ETL inclua um timestamp de ingestão/execução (campo adicional) — isso é uma melhoria opcional, não obrigatória.
- `ciphertext_bytes` não aparece na `fact_benchmark` atual; se for necessário para análise de overhead de rede, recomenda-se computá-lo no ETL e inserir em nova coluna (opcional).

Exemplos práticos — views e queries prontas para usar no seu schema

1) Algoritmo mais rápido (média da operação `encap`):
```sql
SELECT da.algorithm_name AS algorithm, AVG(fb.latencia_ms) AS mean_ms, COUNT(*) AS n
FROM fact_benchmark fb
JOIN dim_algorithm da ON fb.sk_algorithm = da.sk_algorithm
JOIN dim_operation op ON fb.sk_operation = op.sk_operation
WHERE op.operation_name = 'encap'
GROUP BY da.algorithm_name
ORDER BY mean_ms ASC
LIMIT 1;
```

2) View: média e dispersão por algoritmo / operação (útil para KPIs):
```sql
CREATE OR REPLACE VIEW vw_mean_latency_by_algorithm AS
SELECT da.algorithm_name,
       da.algorithm_family,
       op.operation_name,
       AVG(fb.latencia_ms) AS mean_ms,
       STDDEV_POP(fb.latencia_ms) AS std_ms,
       COUNT(*) AS n
FROM fact_benchmark fb
JOIN dim_algorithm da ON fb.sk_algorithm = da.sk_algorithm
JOIN dim_operation op ON fb.sk_operation = op.sk_operation
GROUP BY da.algorithm_name, da.algorithm_family, op.operation_name;
```

3) View: overhead híbrido por algoritmo (média):
```sql
CREATE OR REPLACE VIEW vw_hybrid_overhead_by_algorithm AS
SELECT da.algorithm_name,
       AVG(fb.overhead_hibrido_pct) AS avg_hybrid_overhead,
       COUNT(*) AS n
FROM fact_benchmark fb
JOIN dim_algorithm da ON fb.sk_algorithm = da.sk_algorithm
WHERE fb.overhead_hibrido_pct IS NOT NULL
GROUP BY da.algorithm_name;
```

4) Mediana por algoritmo usando funções de janela (MySQL 8+):
```sql
CREATE OR REPLACE VIEW vw_latency_median_by_algorithm AS
SELECT algorithm_name,
       MAX(CASE WHEN rn = FLOOR((cnt+1)/2) THEN latencia_ms END) AS median_ms
FROM (
  SELECT da.algorithm_name, fb.latencia_ms,
         ROW_NUMBER() OVER (PARTITION BY da.algorithm_name ORDER BY fb.latencia_ms) AS rn,
         COUNT(*) OVER (PARTITION BY da.algorithm_name) AS cnt
  FROM fact_benchmark fb
  JOIN dim_algorithm da ON fb.sk_algorithm = da.sk_algorithm
) t
GROUP BY algorithm_name;
```

5) Exemplo de query para rendimento por hardware / ambiente:
```sql
SELECT dh.provider, dh.environment_type, AVG(fb.latencia_ms) AS mean_ms, COUNT(*) AS n
FROM fact_benchmark fb
JOIN dim_hardware dh ON fb.sk_hardware = dh.sk_hardware
GROUP BY dh.provider, dh.environment_type
ORDER BY mean_ms;
```

ETL prático mapeado ao seu projeto (pseudocódigo)
```py
# Extrair
df_raw = excel_engine.read(workbook_path)

# Normalizar e mapear colunas para o fato
df = validate_types(df_raw)
df['latencia_ms'] = df['response_ms']  # mapear nome de coluna
df['vt_classico_pct'] = compute_vs_classic(df)
df['overhead_hibrido_pct'] = compute_hybrid_overhead(df)

# Upsert dims: dim_algorithm, dim_operation, dim_hardware
upsert_dim_algorithm(df[['algorithm_name','algorithm_family','security_level']])
upsert_dim_operation(df['operation'])
upsert_dim_hardware(df[['provider','cpu_model','vcpu','ram_gb','os','environment_type']])

# Inserir fatos — resolver SKs via joins lookup
facts = resolve_sks_and_build_facts(df)
insert_into_fact_benchmark(facts)
```

Boas práticas aplicadas ao esquema atual
- Use upserts (INSERT ... ON DUPLICATE KEY UPDATE) para dimensões com chaves naturais (`algorithm_name`).
- Validar e rejeitar registros com `latencia_ms` nula ou negativa.
- Criar views materializadas ou agregações se for necessário acelerar KPIs em produção.

3) PQC para leigos (linguagem acessível)
-------------------------------------

- O que é PQC?
  A Criptografia Pós-Quântica (PQC) agrupa algoritmos projetados para permanecer seguros mesmo na presença de computadores quânticos capazes de quebrar os algoritmos clássicos mais usados hoje.

- Por que RSA e ECDSA estão em risco?
  RSA e ECDSA (assinado por curvas elípticas) dependem de problemas matemáticos (fatoração ou logaritmo discreto) que podem ser resolvidos eficientemente por algoritmos quânticos (ex.: algoritmo de Shor). Um computador quântico suficientemente grande tornaria essas proteções inseguras.

- O que são ML-KEM, ML-DSA, SLH-DSA (no contexto deste estudo)?
  - `ML-KEM`: família de Key-Encapsulation Mechanisms (métodos para trocar/encapsular chaves) orientados a resistência pós-quântica; projetados para operações de estabelecimento de chave (encap/decap) e, neste benchmark, apresentam baixa latência média.
  - `ML-DSA` e `SLH-DSA`: famílias de esquemas de assinatura digital pós-quântica; tendem a oferecer fortes garantias de segurança, mas com custo computacional maior (assinatura/verificação mais lentas ou com maiores tamanhos de chave/assinatura).

Analogia simples: imagine dois tipos de cadeado — um que é rápido de abrir (boa escolha para entrada rápida) e outro que é mais robusto mas demora mais para abrir (útil quando a segurança máxima é necessária). ML-KEM fornece 'troca de chaves' rápida; SLH-DSA tende a ser o 'cadeado robusto' que exige mais tempo para calcular/validar.

4) Análises principais (resumo dos achados do benchmark)
------------------------------------------------------
- ML-KEM como o mais rápido: nos dados de benchmark, as operações de encapsulamento (`encap`) associadas a ML-KEM apresentam as menores medianas e médias de latência, consistente tanto em ambiente local quanto em cloud. Isso torna ML-KEM um forte candidato para caminhos críticos de latência.
- Custo elevado do SLH-DSA: as operações de assinatura e verificação associadas a SLH-DSA mostram latências significativamente maiores — impacto direto em operações que exigem assinaturas síncronas.
- Híbridos: soluções híbridas (clássico + PQC) introduzem overhead mensurável; a métrica `hybrid_overhead_pct` captura esse custo e deve ser monitorada quando for exigida compatibilidade retroativa.
- Sensibilidade ao payload: existe correlação entre `payload_kb` / `ciphertext_bytes` e latência para alguns algoritmos — importante otimizar tamanho de payloads para transações onde latência é crítica.

5) Conclusão estratégica e recomendações (Banco Inter — PIX)
-----------------------------------------------------------

Recomendação de alto nível (prioridade por caso de uso):

- Para caminhos de baixa latência (transações PIX, estabelecimento rápido de sessão): priorizar `ML-KEM` para operações de estabelecimento de chave/encapsulamento. Justificativa: menor latência média observada nos benchmarks.
- Para autenticações/assinaturas síncronas: evitar, na fase inicial, o uso de `SLH-DSA` em caminhos sensíveis à latência; avaliar `ML-DSA` ou outras assinaturas de baixa-latência pós-quânticas, ou executar assinaturas assincronamente quando possível.
- Estratégia de migração (fases):
  1. Pilot (0–6 semanas): rodar ML-KEM em ambiente de homologação/end-to-end para medir impacto real na cadeia de transações (incluindo HSM, middleware e latência de rede).
  2. Canary/hybrid (6–16 semanas): deploy controlado em tráfego real com feature flag; usar modo híbrido para retrocompatibilidade; monitorar `P50/P95/P99` e `success_rate`.
  3. Adoção progressiva (3–9 meses): expandir uso a mais endpoints de baixa latência após validações e ajustes operacionais.

Recomendações operacionais e riscos
- Integração com HSM/infra existente: validar suporte a PQC nas HSMs (ou uso de wrappers). Se hardware não suportar, medir overhead em software.
- Medir e observar efeitos colaterais: consumo CPU/RAM, tamanhos de chave/assinatura (impacto em rede), compatibilidade com protocolos (TLS, JWT) e interação com bibliotecas de terceiros.
- Verificar maturidade das bibliotecas: dar preferência a implementações padronizadas e testadas (NIST PQC candidates e bibliotecas mantidas pela comunidade/fornecedores confiáveis).
- Manter compatibilidade: usar estratégia híbrida enquanto clientes e parceiros não migram.

Checklist operacional mínimo para iniciar o piloto
- Definir endpoints de teste (PIX testnet / sandbox) e métricas de sucesso (P95<target, error<target).
- Preparar ambiente: HSM, certificados, logs e automações de rollback.
- Executar testes de carga e latência end-to-end (incluindo cenário de peak) e comparar com baseline atual (RSA/ECDSA).
- Implementar monitoramento no dashboard (adicionar métricas: P99, erro por algoritmo, overhead híbrido por operação).

Apêndice A — Pseudocódigo ETL (alto nível)
```py
# Extrair
df_raw = excel_engine.read(workbook_path)

# Validar e limpar
df = validate_types(df_raw)
df['crypto_type'] = df['crypto_type'].map(normalize_category)
df['family'] = df['library'].map(extract_family)

# Enriquecer
df['hybrid_overhead_pct'] = compute_hybrid_overhead(df)

# Carregar staging, deduplicar e then upsert into dims and fact
load_to_staging(df)
upsert_dimensions()
insert_into_fact()
```

Apêndice B — Métricas chave do dashboard (sugestão)
- P50 / P95 / P99 de `response_ms` por algoritmo
- `hybrid_overhead_pct` por par algoritmo-operacao
- `vs_classic_pct` para medir perda/ganho relativo a clássicos
- CPU/RAM por execução (detecta candidatos a offload/hardware acceleration)

Conclusão
----------
Este relatório integra o trabalho de engenharia de dados (ETL/DW) e análises experimentais presentes no dashboard. As evidências do benchmark apontam `ML-KEM` como candidato primário para caminhos críticos de baixa latência (PIX), enquanto `SLH-DSA` exige cautela por seu custo temporal. Recomenda-se iniciar um piloto controlado com monitoramento robusto e avaliar integração com HSM e impacto operacional antes de um rollout amplo.

---
Arquivo gerado: `docs/PQC_dashboard_report.md`
