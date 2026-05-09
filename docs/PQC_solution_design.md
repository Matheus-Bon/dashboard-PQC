# PQC Solution Design — ETL, DW, Dashboard & Operational Guidance

Resumo curto
- Propósito: documentar o mapeamento ETL → DW, decisões de visualização e recomendações operacionais para adoção de algoritmos pós-quânticos (PQC) no dashboard.
- Escopo: extração/transformação do Excel → carregamento em `fact_benchmark` (MySQL), visualizações em Dash/Plotly, presets de baixa-latência (PIX), e recomendações de segurança e hardware.

1) Mapeamento ETL ↔ Data Warehouse (resumo)
- Fonte autoritativa: [dw_schema_star_v2.sql](dw_schema_star_v2.sql)
- View/Rede de colunas usadas pelo dashboard (já implementado em `core/data_adapter._load_from_mysql`):

```sql
SELECT
  da.algorithm_name AS library,
  da.algorithm_family AS crypto_type,
  da.security_level,
  do2.operation_name AS operation,
  dh.provider AS environment,
  dh.environment_type,
  dh.cpu_model AS processor,
  dh.os AS operating_system,
  fb.latencia_ms AS response_ms,
  fb.payload_kb,
  fb.key_size_bytes,
  fb.iterations,
  COALESCE(fb.vt_classico_pct,0) AS vs_classic_pct,
  COALESCE(fb.overhead_hibrido_pct,0) AS hybrid_overhead_pct
FROM fact_benchmark fb
JOIN dim_algorithm da ON fb.sk_algorithm = da.sk_algorithm
JOIN dim_operation do2 ON fb.sk_operation = do2.sk_operation
JOIN dim_hardware dh ON fb.sk_hardware = dh.sk_hardware;
```

- Observação: o campo `latencia_ms` do DW é exposto como `response_ms` pelo adaptador para compatibilidade com o código de visualização.

2) ETL — passos e boas práticas
- Extração: ler planilha bruta (se presente) ou consultar MySQL direto se já populado.
- Transformação mínima obrigatória:
  - Normalizar nomes de algoritmo (`algorithm_name`) para casar com `core/chart_figures.py` (ex.: `ML-KEM-512`, `RSA-2048`, `SLH-DSA-*`).
  - Converter unidades numéricas e coalescer nulls (`latencia_ms` → numérico, `key_size_bytes` → int).
  - Popular `security_level` (Classico/L1/L2/L3/L5) conforme `dim_algorithm`.
- Carregamento: inserir em `fact_benchmark` com FK para dimensões; manter `sk_benchmark` sequencial.
- Recomendações ETL:
  - Validar cardinalidade por algoritmo/hardware antes de substituir dados de produção.
  - Atuar com `soft-delete` ou staging table para deploys de ETL e rollback seguro.

3) Visualizações (decisões implementadas)
- `fig_kem_ranking`: ranking horizontal de KEMs por latência média com IC95. Cores por categoria: PQC (laranja), Híbrido (grafite), Clássico (cinza). Anotação visível para `ML-KEM-512`.
- `fig_security_vs_speed`: scatter/bubbles mapeando nível NIST (x) × latência (y); tamanho de bolha = key size (bytes). Ajuda a escolher trade-offs segurança ↔ atraso.
- `fig_signature_comparison`: comparação ML-DSA vs SLH-DSA; destaca assinaturas com latências >2000 ms como “não adequadas para tempo real”.
- `fig_rsa_vs_mlkem`: foco em `keygen` com escala log para evidenciar ordens de grandeza e razão RSA/ML-KEM.

4) UX: filtros e presets operacionais
- Agrupamento de filtros por Lei de Hick: `lib-classic-filter`, `lib-hybrid-filter`, `lib-pqc-filter` + `tipo-algoritmo-filter`.
- Preset `Configuração PIX`: seleciona automaticamente os algoritmos de menor latência observada (top N) — ideal para sessões de avaliação de performance de pagamentos instantâneos.

5) PQC: recomendações de família e políticas
- Algoritmos recomendados (modelo de produção piloto):
  - KEM: Kyber (familia ML-KEM) — bom trade-off throughput/latency para key-establishment.
  - Signatures: Dilithium (rápido), SPHINCS+ (resistente, porém mais pesado) — usar SPHINCS+ apenas onde assinatura offline é aceitável.
- Estratégia de transição: "Harvest Now, Decrypt Later" — armazenar tráfego cifrado hoje e manter dados para decryption futuro com chaves post-quantum à medida que a interoperabilidade for estabelecida. Planejar retenção e chave/segredos em HSM/KeyVault.
- Conformidade e padrões: recomenda-se avaliar requisitos (FIPS 203/204/205) e implementar controles de KMS/HSM; adaptar políticas internas para rotação e proteção de chaves.

6) Hardware & implantação (resumo)
- Medir em duas classes: local bare-metal (Ryzen desktop / Apple M2) e cloud (Intel/AMD/ARM). Observações gerais:
  - CPUs com instruções vetoriais maiores (AVX2/AVX-512) aceleram operações de grande bloco e criptografia simétrica; muitas implementações PQC ainda se beneficiam de otimizações específicas de plataforma.
  - Apple M2 (ARM) tende a ter ótimo desempenho por Watt; medir especificamente versões de bibliotecas PQC compiladas para ARM.
  - Em cloud, escolha instâncias com instrução vetorial adequada e compare latências por vCPU; colocar testes de benchmark automatizados no pipeline.

7) Métricas operacionais e SLAs
- Métricas principais: median/mean `response_ms` por operação, p95/p99, throughput ops/s, tamanho de payload, `hybrid_overhead_pct`.
- Alertas: p99 > SLA_threshold (ex.: 500 ms) para operações de pagamento.

8) Integração com o código atual
- `core/data_adapter._load_from_mysql` já expõe `latencia_ms AS response_ms` — portanto as visualizações são compatíveis sem alterações adicionais.
- Se desejar renomear consistentemente no ETL, incluir etapa `df.rename(columns={'latencia_ms':'response_ms'}, inplace=True)` no `build_flat_dataframe`/`etl_engine`.

9) Próximos passos técnicos (curto prazo)
- Finalizar este documento (adicionar resultados de benchmarks reais). 
- Executar o suite de testes automático (`pytest`) e validar dashboards manuais.
- Preparar playbook de rollout: ETL stage → validação → deploy do dashboard em container.

---
Referências rápidas
- Arquivo de esquema DW: `dw_schema_star_v2.sql` (raiz do repositório).
- Código do dashboard: `core/chart_figures.py`, `core/layout_sections.py`, `core/callbacks.py`.

Documento gerado automaticamente pelo assistente de desenvolvimento; ajustar conforme revisões internas.
