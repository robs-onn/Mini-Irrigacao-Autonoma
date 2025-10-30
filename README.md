# Projeto: Irrigação Autônoma

Resumo
------
Aplicação web leve para monitoramento e controle de um sistema de irrigação em pequena escala. O backend é feito com Flask e armazena leituras em SQLite; existe um frontend mínimo para visualização e controle.

## Implementação atual

- Backend: Flask
- Banco de dados: SQLite (arquivo em `IrrigacaoAutonoma/db/`)
- ORM: Flask-SQLAlchemy
- Rotas principais:
  - `/` — dashboard (renderiza `templates/index.html`)
  - `/grupo/` — página do grupo (`templates/grupo.html`)
  - `/api/dados` (POST) — endpoint para o ESP8266 ou outro microcontrolador enviar leituras (JSON)
  - `/api/config` (POST) — endpoint para atualizar a configuração a partir do frontend

Modelos principais (em `IrrigacaoAutonoma/__init__.py`):

- `LeiturasSensores`: umidade do solo, luminosidade, estado da bomba, timestamp.
- `Configuracao`: modo (`AUTOMATICO` / `MANUAL`), setpoint de umidade e comando manual da bomba.

## Inicialização

O `app.py` usa a factory `create_app()` (em `IrrigacaoAutonoma/__init__.py`). Ao iniciar, o banco e as tabelas são criados automaticamente (se necessário) e uma configuração inicial é inserida.

## Pré-requisitos

- Python 3.8+
- Recomenda-se criar um ambiente virtual (venv).

## Instalação e execução (rápido)

```bash
python -m venv .venv
source .venv/bin/activate
pip install Flask Flask-SQLAlchemy
python app.py
# ou: FLASK_APP=app.py flask run --host=0.0.0.0 --port=5000
```

Abra `http://localhost:5000/` no navegador.

## API: envio de dados (ESP8266 / microcontrolador)

- Endpoint: `POST /api/dados`
- Exemplo de payload JSON:

```json
{
  "umidade": 45.3,
  "luz": 300.0,
  "bomba_ligada": 0
}
```

- O backend persiste a leitura em `leituras_sensores` e responde com a configuração atual, exemplo:
  `{ "modo": "AUTOMATICO", "setpoint": 60.0, "comando_manual": 0 }`

## API: atualização via frontend

- Endpoint: `POST /api/config`
- Exemplo de payload JSON:

```json
{ "chave": "setpoint", "valor": "55.0" }
```

- Chaves válidas: `modo` (`AUTOMATICO` | `MANUAL`), `setpoint`, `comando_manual` (0 | 1).

## Estrutura do projeto

- `app.py` — entrypoint
- `IrrigacaoAutonoma/` — pacote principal
  - `__init__.py` — factory, modelos e inicialização do DB
  - `routes.py` — rotas e APIs
  - `db/` — banco SQLite
  - `static/` — JS/CSS
  - `templates/` — páginas HTML

## Objetivos futuros

1) Integração com hardware (microcontrolador WiFi)
   - Adotar Arduino com ESP8266 (módulo WiFi) como plataforma primária para leitura dos sensores e comunicação com o servidor.
     - O ESP8266 atuará como nó de sensores: lê sensores (umidade, luminosidade, etc.) e envia leituras via HTTP POST para `/api/dados` ou via MQTT quando habilitado.
     - Fornecer um firmware de exemplo (ex.: Arduino/PlatformIO) que envie JSON compatível com o backend.
   - Implementar camada de abstração de hardware no backend para permitir múltiplos backends (GPIO local, Serial, I2C, SPI) e canais de comunicação (HTTP/MQTT/Modbus).
   - Adaptadores sugeridos: `ValveGPIO`, `ValveSerial`, `ValveSimulator`.

2) Comunicação em rede e telemetria
   - Suporte a MQTT (paho-mqtt) para telemetria e comandos remotos.
   - Integração com Modbus TCP/RTU quando necessário.

3) Modo simulação e testes
   - Implementar modo `simulation` para emular sensores/atuadores e facilitar CI.
   - Criar testes unitários para regras de decisão e mocks para drivers e para o canal de comunicação (simular ESP8266).

4) Regras de automação
   - Implementar algoritmos de decisão (thresholds, agendamento, PID simples) e um histórico de ações. Garantir testabilidade com entradas simuladas.

5) Segurança e robustez
   - Watchdog, limites de atuação, E-Stop, validação de comandos e tratamento de falhas elétricas. Quando aplicado, adicionar autenticação/autorização para comandos remotos.

6) Documentação e DevOps
   - Adicionar `requirements.txt` e `docs/hardware.md` (com exemplos de firmware ESP8266).
   - Criar pipelines de CI para testes automatizados e escolher licença (ex.: MIT).

## Contribuição

- Abra issues para bugs e funcionalidades.
- Envie PRs pequenas e focadas.
- Documente novos drivers e mudanças significativas em `docs/`.

## Contato

- Robson William Teixeira Junior — [github.com/robs-onn] (https://github.com/robs-onn) — robsonwtj@gmail.com
- Pedro Henrique Teixeira Crispim — [github.com/PedroCrispim11] (https://github.com/PedroCrispim11) — pedrocrispim020@gmail.com

## Observação final

Priorize a camada de abstração de hardware para permitir desenvolvimento e testes sem o hardware físico. Isso facilita integração com múltiplos protocolos e acelera o desenvolvimento da lógica autônoma.
