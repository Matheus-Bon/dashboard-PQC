# Criptografia Pós-Quântica na Prática - Dashboard

![Dashboard PQC](assets/logo-puc.png)

Este projeto apresenta um **Dashboard Científico e Executivo** para análise de benchmarks de algoritmos de Criptografia Pós-Quântica (PQC), comparando-os com algoritmos Clássicos e Híbridos em diversos ambientes (Cloud e Local). O sistema foi desenvolvido em Python utilizando **Dash (Plotly)** e segue princípios de **Business Intelligence (BI)** sobre um modelo de dados em **Star Schema (Kimball)**.

## 🚀 Funcionalidades e Escopo Analítico

O dashboard é orientado a dados observados de latência, fornecendo as seguintes análises:
- **Ranking de Encapsulamento de Chave**: Identifica o KEM (Key Encapsulation Mechanism) mais performático.
- **Segurança vs Velocidade**: Avalia o trade-off entre o nível de segurança NIST e o custo computacional.
- **Comparação de Assinaturas**: Confronta o desempenho operacional de `sign` e `verify` de algoritmos de assinatura (ML-DSA, SLH-DSA, RSA, ECDSA).
- **Latência Cloud e Local**: Distribuição estatística de execução por ambiente.
- **Comparativo Direto**: RSA-2048 vs ML-KEM-512.

### Filtros Inteligentes (Presets)
O painel agora conta com presets que otimizam as visualizações ocultando gráficos irrelevantes para o caso de uso:
1. **Otimização para PIX**: Foca em *Key Encapsulation* e esconde assinaturas digitais, pré-filtrando ML-KEM-512 e limitando operações (encap, decap).
2. **Assinatura de Contratos**: Foca em algoritmos de assinatura (ML-DSA) e esconde análises de encapsulamento.

## 🛠️ Stack Tecnológica

- **Frontend/UI**: Dash, Plotly, Dash Bootstrap Components.
- **Backend/Data Manipulation**: Python 3.10+, Pandas, Numpy, SciPy.
- **Banco de Dados/ETL**: MySQL, Excel Adaptor.
- **Arquitetura de Dados**: Data Warehouse com schema estrela (fatos e dimensões).

## ⚙️ Instalação e Execução

### Pré-requisitos
- Python 3.10+
- Ambiente virtual configurado (`.venv`)

### Passos

1. **Clone o repositório e acesse a pasta:**
   ```bash
   git clone <repo_url>
   cd dashboard
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Inicie o servidor local:**
   ```bash
   python app.py
   ```

4. **Acesse no navegador:**
   Abra `http://localhost:8050`

## 📊 Estrutura de ETL e Dados
O sistema abstrai as origens de dados usando um padrão *Adapter*. 
Ele tenta conectar a um banco **MySQL** contendo o Star Schema e, caso não esteja disponível, usa planilhas Excel da pasta `banco-planilha/` como fallback, permitindo flexibilidade na atualização de dados. O processamento (ETL) converte esses dados brutos em um Pandas DataFrame desnormalizado em cache, otimizado para os filtros de dashboard.

Leia o [PONTOS_ATENCAO_DW_BI_ETL.md](PONTOS_ATENCAO_DW_BI_ETL.md) para detalhes da implementação do DW e as decisões de modelagem dimensional.

## ✨ UX e Design
A interface utiliza elementos como *glassmorphism* e temas premium para a exibição de métricas. O design é 100% responsivo e garante clareza técnica tanto para engenheiros quanto para executivos avaliando transições criptográficas.
