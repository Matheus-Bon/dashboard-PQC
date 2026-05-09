from __future__ import annotations

HERO_EYEBROW = "Projeto de Extensao PUC Minas"
HERO_TITLE = "Criptografia Pos-Quantica na Pratica"
HERO_TEXT = (
    "Dashboard cientifico com foco em seis analises: ranking de encapsulamento, "
    "seguranca versus velocidade, assinatura digital, latencia em cloud, latencia "
    "em ambiente local e comparacao direta entre RSA-2048 e ML-KEM-512."
)
HERO_SCOPE_TAG = "Escopo do Benchmark"
HERO_SCOPE_TEXT = "Base integrada para comparar algoritmos, operacoes e ambientes sob a mesma modelagem analitica."
HERO_SCOPE_NOTE = "Painel orientado a latencia observada e equivalencia funcional entre algoritmos classicos, PQC e hibridos."
FILTERS_TITLE = "Filtros"
CLEAR_FILTERS_LABEL = "Limpar filtros"
CHART_SECTIONS = [
    {
        "id": "chart-kem-ranking",
        "title": "Ranking de Encapsulamento de Chave",
        "sub": "Algoritmo mais rapido para encapsulamento de chave, incluindo KEM puro e KEM hibrido, com media e IC 95%.",
        "variant": "graph-box-lg",
        "field": "kem_ranking",
    },
    {
        "id": "chart-security-speed",
        "title": "Seguranca vs Velocidade",
        "sub": "Comparacao entre seguranca e velocidade usando os niveis NIST e a latencia observada nos benchmarks.",
        "variant": "graph-box-lg",
        "field": "security_speed",
    },
    {
        "id": "chart-signature-comparison",
        "title": "Comparacao de Algoritmos de Assinatura",
        "sub": "Comparacao entre algoritmos de assinatura digital nas operacoes de sign e verify.",
        "variant": "graph-box-xl",
        "field": "signature_comparison",
    },
    {
        "id": "chart-cloud-latency",
        "title": "Latencia em Ambientes Cloud",
        "sub": "Comparacao de latencia entre os algoritmos executados em ambientes cloud, ordenada pela mediana.",
        "variant": "graph-box-xxl",
        "field": "cloud_latency",
    },
    {
        "id": "chart-local-latency",
        "title": "Latencia no Ambiente Local",
        "sub": "Comparacao de latencia entre os algoritmos executados no ambiente local, ordenada pela mediana.",
        "variant": "graph-box-xxl",
        "field": "local_latency",
    },
    {
        "id": "chart-rsa-vs-mlkem",
        "title": "RSA-2048 vs ML-KEM-512",
        "sub": "Comparacao direta entre RSA-2048 e ML-KEM-512 em operacoes funcionalmente equivalentes.",
        "variant": "graph-box-lg",
        "field": "rsa_vs_mlkem",
    },
]
