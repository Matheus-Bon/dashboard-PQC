from __future__ import annotations

HERO_EYEBROW = "Projeto de Extensão PUC Minas"
HERO_TITLE = "Criptografia Pós-Quântica na Prática"
HERO_TEXT = (
    "Dashboard científico com foco em seis análises: ranking de encapsulamento, "
    "segurança versus velocidade, assinatura digital, latência em cloud, latência "
    "em ambiente local e comparação direta entre RSA-2048 e ML-KEM-512."
)
HERO_SCOPE_TAG = "Escopo do Benchmark"
HERO_SCOPE_TEXT = "Base integrada para comparar algoritmos, operações e ambientes sob a mesma modelagem analítica."
HERO_SCOPE_NOTE = "Painel orientado a latência observada e equivalência funcional entre algoritmos clássicos, PQC e híbridos."
FILTERS_TITLE = "Filtros"
CLEAR_FILTERS_LABEL = "Limpar filtros"
CHART_SECTIONS = [
    {
        "id": "chart-kem-ranking",
        "title": "Ranking de Encapsulamento de Chave",
        "sub": "Algoritmo mais rápido para encapsulamento de chave, incluindo KEM puro e KEM híbrido, com média e IC 95%.",
        "variant": "graph-box-lg",
        "field": "kem_ranking",
    },
    {
        "id": "chart-security-speed",
        "title": "Segurança vs Velocidade",
        "sub": "Comparação entre segurança e velocidade usando os níveis NIST e a latência observada nos benchmarks.",
        "variant": "graph-box-lg",
        "field": "security_speed",
    },
    {
        "id": "chart-signature-comparison",
        "title": "Comparação de Algoritmos de Assinatura",
        "sub": "Comparação entre algoritmos de assinatura digital nas operações de sign e verify.",
        "variant": "graph-box-xl",
        "field": "signature_comparison",
    },
    {
        "id": "chart-cloud-latency",
        "title": "Latência em Ambientes Cloud",
        "sub": "Comparação de latência entre os algoritmos executados em ambientes cloud, ordenada pela mediana.",
        "variant": "graph-box-xxl",
        "field": "cloud_latency",
    },
    {
        "id": "chart-local-latency",
        "title": "Latência no Ambiente Local",
        "sub": "Comparação de latência entre os algoritmos executados no ambiente local, ordenada pela mediana.",
        "variant": "graph-box-xxl",
        "field": "local_latency",
    },
    {
        "id": "chart-rsa-vs-mlkem",
        "title": "RSA-2048 vs ML-KEM-512",
        "sub": "Comparação direta entre RSA-2048 e ML-KEM-512 em operações funcionalmente equivalentes.",
        "variant": "graph-box-lg",
        "field": "rsa_vs_mlkem",
    },
]
