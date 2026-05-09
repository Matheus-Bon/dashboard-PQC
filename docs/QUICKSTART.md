# Guia de Início Rápido — PQC Benchmark Dashboard

## Pré-requisitos

| Ferramenta | Versão mínima | Observação |
|------------|---------------|------------|
| Python | 3.12 | `python --version` |
| Docker + Docker Compose | 24+ | para o banco MySQL local |
| MySQL Client (opcional) | 8.x | para carregar o schema manualmente |

> **Alternativa sem Docker**: o dashboard aceita planilha Excel como fallback. Coloque o arquivo em `banco-planilha/` e pule as etapas de banco.

---

## 1 — Clonar e instalar dependências

```bash
# 1. Clonar o repositório
git clone <URL_DO_REPO>
cd dashboard

# 2. Criar e ativar o ambiente virtual
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt
```

---

## 2 — Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=pqc_benchmark
DB_USER=root
DB_PASSWORD=root_password_aqui

# Opcional: ajuste de cache e limites
CACHE_TTL_SECONDS=1800
QUERY_ROW_LIMIT=10000
```

---

## 3 — Subir o banco MySQL com Docker

```bash
# Iniciar o serviço MySQL em background
docker compose up -d db

# Verificar se o container está saudável
docker compose ps

# Aguardar o healthcheck ficar "healthy" (~15 s)
docker compose logs -f db
```

### Carregar o schema Star Schema v2

```bash
# Opção A: via docker exec (sem MySQL client local)
docker compose exec -T db mysql -u root -proot_password_aqui pqc_benchmark \
  < dw_schema_star_v2.sql

# Opção B: com MySQL client instalado localmente
mysql -h 127.0.0.1 -P 3306 -u root -p pqc_benchmark < dw_schema_star_v2.sql
```

### Acessar o shell MySQL (opcional)

```bash
docker compose exec db mysql -u root -proot_password_aqui pqc_benchmark
```

---

## 4 — Executar o dashboard

```bash
# Modo desenvolvimento (auto-reload)
python app.py
```

Acesse: **http://localhost:8050**

```bash
# Modo produção com Gunicorn (Linux / macOS)
gunicorn app:server --bind 0.0.0.0:8050 --workers 2
```

### Botão "Atualizar Dados"

O painel de filtros contém o botão **Atualizar Dados** (laranja). Clique nele para:
1. Invalidar o cache TTL do `DataStore`
2. Limpar o cache LRU dos callbacks
3. Recarregar os dados diretamente do MySQL
4. Redesenhar todos os gráficos com os dados mais recentes

---

## 5 — Executar os testes

```bash
# Todos os testes
pytest tests/ -v

# Somente testes unitários
pytest tests/unit/ -v

# Com relatório de cobertura
pytest tests/ -v --cov=core --cov-report=term-missing
```

Resultado esperado: **70 passed** (sem warnings de erro).

---

## 6 — Estrutura do projeto

Consulte [ARCHITECTURE.md](ARCHITECTURE.md) para a descrição completa dos módulos.

---

## Comandos úteis

```bash
# Parar e remover os containers Docker
docker compose down

# Parar e remover containers + volume do banco (dados perdidos)
docker compose down -v

# Inspecionar logs do dashboard (se rodando em Docker)
docker compose logs -f app

# Recriar o banco do zero
docker compose down -v
docker compose up -d db
# aguardar healthcheck, depois carregar o schema novamente
```

---

## Solução de Problemas

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| `Access denied for user 'root'` | Senha no `.env` diferente da usada no `docker compose` | Verificar `DB_PASSWORD` e `MYSQL_ROOT_PASSWORD` |
| Dashboard abre sem dados | MySQL indisponível, cai para Excel | Verificar `docker compose ps`; ou adicionar planilha em `banco-planilha/` |
| Gráficos não atualizam após carga ETL | Cache TTL ainda válido | Clicar em **Atualizar Dados** no painel de filtros |
| `ModuleNotFoundError: dash` | Dependências não instaladas | Rodar `pip install -r requirements.txt` no venv ativo |
| Porta 3306 já em uso | MySQL local rodando | Alterar `DB_PORT` no `.env` e `docker-compose.yml` |
