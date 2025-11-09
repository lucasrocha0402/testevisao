# API Mock de IOT - Guia para o Candidato

## 1. Visão Geral

Olá, candidato(a)!

Esta aplicação é um **simulador de IOT** criado para o seu desafio técnico. O objetivo dela é atuar como um sistema externo que envia dados em tempo real para a API que você irá construir.

Ela gerencia um registro de dispositivos "virtuais" e envia eventos de telemetria (como temperatura e umidade) para os endpoints que sua aplicação expor.

## 2. Pré-requisitos

Esta aplicação foi empacotada como um **executável autocontido para Windows (win-x64)**.

* ✅ **Sistema Operacional:** Windows 10 ou superior (64-bit).
* ❌ **Não é necessário instalar o .NET SDK ou Runtime.** Todo o necessário já está incluído no pacote.

## 3. Como Executar

Siga estes passos simples para iniciar o simulador:

1.  **Extraia** o conteúdo do arquivo `.zip` para uma pasta de sua preferência (ex: `C:\Desafio\IotApiMock\`).
2.  **Dê dois cliques no executável** `Imagenseguranca.Test.IOT.exe` para iniciar o servidor.
5.  Pronto! O terminal exibirá logs indicando que o servidor foi iniciado e está escutando na porta **`http://localhost:5000`**. Mantenha este terminal aberto durante todo o seu teste.

## 4. Explorando a API com Swagger

Para facilitar a interação e os testes, a API Mock possui uma documentação interativa com Swagger UI.

* **Acesse no seu navegador:** [**http://localhost:5000/swagger**](http://localhost:5000/swagger)

Através do Swagger, você pode visualizar todos os endpoints disponíveis, seus parâmetros e até mesmo executá-los diretamente do navegador, o que é ótimo para testes iniciais.

## 5. Fluxo de Interação com a Sua Aplicação

Sua aplicação deverá interagir com esta API Mock para gerenciar o ciclo de vida dos dispositivos.

### Passo 1: Registro do Dispositivo (`POST /register`)

Quando um novo dispositivo é criado na sua plataforma, sua API deve registrá-lo no simulador para que ele comece a enviar eventos.

* **Endpoint:** `POST http://localhost:5000/register`
* **Corpo da Requisição (JSON):**

```json
{
  "deviceName": "Sensor da Sala de Servidores",
  "location": "Rack 03, Prateleira 01",
  "callbackUrl": "https://localhost:7001/api/events" // URL COMPLETA do endpoint da SUA API que receberá os eventos.
}
```

## 6. Relatório de Alertas (Fluxo Bônus)

Este repositório já inclui os arquivos necessários para suportar o desafio bônus no n8n.

1. **Volumes do n8n** – `docker-compose.yml` monta `./scripts` e `./output` em `/workspace/scripts` e `/workspace/output`. No nó *Execute Command*, utilize:
   ```
   python /workspace/scripts/gerar_relatorio.py
   ```

2. **Dependências Python** – instale-as no container, se necessário:
   ```
   pip install psycopg2-binary reportlab
   ```

3. **Script `gerar_relatorio.py`** – conecta-se ao Postgres, coleta até 100 registros da tabela `events` e gera `/workspace/output/relatorio_alertas.pdf`.

4. **Workflow `GET /webhook/report`** – crie um fluxo com:
   - Webhook (GET)
   - Execute Command (executa o script)
   - Read Binary File (lê o PDF)
   - Respond to Webhook (retorna o binário para download)

Assim, acessar `http://localhost:5678/webhook/report` executa o script e devolve o PDF imediatamente.