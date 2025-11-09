# Guia de Configuração e Execução

## Visão Geral

Este repositório reúne os artefatos necessários para rodar um cenário de integração IOT + automações low-code:

- `Imagenseguranca.Test.IOT.exe` – simulador de dispositivos IOT que envia eventos para a sua API.
- `docker-compose.yml` – orquestra Postgres, n8n e Flowise.
- `sql/create_tables.sql` – definição de tabelas utilizadas pelo fluxo.
- `scripts/gerar_relatorio.py` – gera um relatório PDF de alertas críticos a partir do Postgres.
- `flowise.json` e `n8n.json` – exports de workflows prontos.
- `output/relatorio_alertas.pdf` – exemplo de saída gerada.

Use este guia para preparar o ambiente, popular o banco, rodar os serviços e gerar o relatório.

## Requisitos

- Windows 10 x64 ou superior.
- Docker Desktop com suporte a `docker compose`.
- Python 3.10+ (apenas se for executar os scripts localmente; o container n8n já possui Python).
- Acesso à internet para baixar dependências (psycopg2-binary, reportlab).

## Estrutura do Projeto

```
.
├── docker-compose.yml
├── sql/
│   └── create_tables.sql
├── scripts/
│   └── gerar_relatorio.py
├── flowise.json
├── n8n.json
├── output/
│   └── relatorio_alertas.pdf
└── README.md
```

## Passo a Passo

### 1. Start do simulador IOT

1. Extraia o pacote do repositório para uma pasta local.
2. Execute `Imagenseguranca.Test.IOT.exe`.
3. Mantenha o terminal aberto; o simulador estará disponível em `http://localhost:5000` com Swagger em `/swagger`.

### 2. Subir infraestrutura (Postgres, n8n, Flowise)

```powershell
docker compose up -d
```

Serviços expostos:

- Postgres: `localhost:5433` (mapeado para `postgres:5432` no container)
- n8n: `http://localhost:5678`
- Flowise: `http://localhost:3000`

As credenciais padrão estão definidas em `docker-compose.yml`.

### 3. Criar tabelas no Postgres

1. Conecte-se ao banco usando as credenciais do compose (`sma_user` / `senhaforte123` no database `sma_db`).
2. Rode o script SQL:

```sql
\i sql/create_tables.sql
```

As tabelas criadas (`register` e `events`) são consumidas tanto pelo simulador quanto pelos automations.

### 4. Importar workflows (opcional, mas recomendado)

- **n8n**: Acesse `http://localhost:5678`, importe `n8n.json` e ajuste as credenciais/variáveis conforme necessário.
- **Flowise**: Em `http://localhost:3000`, importe `flowise.json` para carregar o fluxo de IA.

### 5. Gerar relatório de alertas

#### Via n8n (recomendado)

1. No workflow importado, localize o nó *Execute Command*.
2. O docker compose monta `./scripts` em `/workspace/scripts` e `./output` em `/workspace/output`.
3. Com o Postgres populado, acione o webhook `GET http://localhost:5678/webhook/report` (ou endpoint configurado).
4. O fluxo executa `python /workspace/scripts/gerar_relatorio.py` e devolve o PDF gerado.

#### Via linha de comando

1. Opcional: crie um `.env` (exemplo abaixo) para sobrescrever parâmetros de conexão.

   ```env
   REPORT_DB_HOST=localhost
   REPORT_DB_PORT=5433
   REPORT_DB_NAME=sma_db
   REPORT_DB_USER=sma_user
   REPORT_DB_PASSWORD=senhaforte123
   REPORT_OUTPUT_DIR=./output
   ```

2. Instale dependências e execute:

   ```powershell
   pip install -r requirements.txt  # ou pip install psycopg2-binary reportlab
   python scripts/gerar_relatorio.py
   ```

3. O PDF é salvo em `output/relatorio_alertas.pdf`.

## Dependências Python

O script `gerar_relatorio.py` requer:

- `psycopg2-binary` – conexão com Postgres.
- `reportlab` – geração de PDF.

Ao rodar dentro do container n8n:

```bash
pip install psycopg2-binary reportlab
```

## Troubleshooting

- **Erro de conexão com Postgres**: verifique se os containers estão de pé (`docker compose ps`) e se as variáveis `REPORT_DB_*` apontam para `postgres`.
- **psycopg2/reportlab não encontrados**: instale-os no ambiente onde o script está sendo executado.
- **Sem registros no PDF**: confira se a tabela `events` possui registros com `is_alarm = true` e status `processado` ou `completo`.

## Referências Rápidas

- Swagger do simulador: `http://localhost:5000/swagger`
- SQL inicial: `sql/create_tables.sql`
- Script de relatório: `scripts/gerar_relatorio.py`
- Workflow n8n: `n8n.json`
- Workflow Flowise: `flowise.json`