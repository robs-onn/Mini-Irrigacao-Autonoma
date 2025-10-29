# Projeto Irrigação Autônoma

Este repositório contém uma aplicação web para monitoramento e controle de um sistema de irrigação miniaturizado.

Implementação atual
-------------------
- Backend: Flask
- Banco de dados: SQLite
- ORM: Flask-SQLAlchemy
- Rotas principais disponíveis:
  - `/` : dashboard (renderiza `templates/index.html`)
  - `/grupo/` : página de informações do grupo (`templates/grupo.html`)
  - `/api/dados` (POST) : endpoint para o ESP32 enviar leituras (JSON)
  - `/api/config` (POST) : endpoint para atualizar a configuração a partir do frontend

O projeto já define os modelos SQLAlchemy em `IrrigacaoAutonoma/__init__.py`:
- `LeiturasSensores`: armazena leituras (umidade do solo, luminosidade, estado da bomba, timestamp).
- `Configuracao`: guarda o modo (`AUTOMATICO` ou `MANUAL`), setpoint de umidade e comando manual da bomba.

Como a aplicação é inicializada
------------------------------
O arquivo `app.py` usa a factory `create_app()` definida em `IrrigacaoAutonoma/__init__.py`. Ao iniciar, as tabelas são criadas automaticamente (se necessário) e uma configuração inicial é inserida (id=1).

Pré-requisitos (rápido)
----------------------
- Python 3.8+
- Recomendo criar um ambiente virtual (venv) antes de instalar dependências.

Instalação e execução local (exemplo)
-----------------------------------
1) Criar e ativar venv:

```bash
python -m venv .venv
source .venv/bin/activate
```

2) Instalar dependências mínimas:

```bash
pip install Flask Flask-SQLAlchemy
```

3) Iniciar a aplicação:

```bash
python app.py
# ou:
FLASK_APP=app.py flask run --host=0.0.0.0 --port=5000
```

4) Acesse o dashboard em `http://localhost:5000/`.

API para envio de dados (ESP32 ou outro microcontrolador)
-------------------------------------------------------
- Endpoint: `POST /api/dados`
- Payload JSON esperado (exemplo):

```json
{
  "umidade": 45.3,
  "luz": 300.0,
  "bomba_ligada": 0
}
```

- O servidor persiste a leitura em `leituras_sensores` e responde com a configuração atual:
  `{ "modo": "AUTOMATICO", "setpoint": 60.0, "comando_manual": 0 }`

API para atualização via frontend
---------------------------------
- Endpoint: `POST /api/config`
- Payload JSON esperado (exemplo):

```json
{ "chave": "setpoint", "valor": "55.0" }
```

- Chaves válidas: `modo` (`AUTOMATICO` ou `MANUAL`), `setpoint`, `comando_manual` (0 ou 1).

Estrutura atual do projeto
--------------------------------
- `app.py` - entrypoint que chama `create_app()`
- `IrrigacaoAutonoma/` - pacote principal
  - `__init__.py` - factory de app, modelos e inicialização do DB
  - `routes.py` - rotas e APIs
  - `db/` - pasta onde o SQLite é criado
  - `static/` - arquivos JS/CSS (`index.js`, `css/`)
  - `templates/` - `index.html`, `grupo.html`

Objetivos futuros
----------------------------------------
1) Integração com hardware (microcontrolador WiFi)
   - Adotar Arduino com módulo WiFi (ESP8266 integrado) como a plataforma primária para leitura dos sensores e comunicação com o servidor web.
     - O ESP8266 atuará como nó de sensores: lê sensores (umidade do solo, luminosidade, etc.) e envia leituras ao servidor via HTTP POST para `/api/dados` ou via MQTT quando for habilitado.
     - Implementar um firmware de exemplo (Arduino/PlatformIO) que envie JSON compatível com o backend.
   - Implementar camada de abstração de hardware no backend para permitir múltiplos backends (GPIO local, Serial, I2C, SPI) e para suportar adaptadores de rede (HTTP/MQTT/Modbus).
   - Adicionar adaptadores sugeridos: `ValveGPIO`, `ValveSerial`, `ValveSimulator`.

2) Comunicação em rede e telemetria
   - Suporte a MQTT (paho-mqtt) para telemetria e comandos remotos, caso precise-se transmitir dados a uma broker local/remote.
   - Possibilidade de integração com Modbus TCP / RTU quando necessário.

3) Modo simulação e testes
   - Criar um modo `simulation` que emule sensores e atuadores para testes locais e CI.
   - Implementar testes unitários para regras de decisão e mocks para drivers e para o canal de comunicação (simular ESP8266).

4) Regras de automação
   - Implementar algoritmos de decisão (thresholds, agendamento, PID simples) e um histórico de ações. Garantir que as regras possam ser testadas com entradas simuladas.

5) Segurança e robustez
   - Implementar watchdogs, limites de atuação, E-Stop, validação de comandos e tratamento de falhas elétricas. Garantir que comandos por rede sejam autenticados/validados quando aplicável.

6) Documentação e DevOps
   - Adicionar `requirements.txt`, documentação de hardware em `docs/hardware.md` com exemplos de firmware para ESP8266 e pipelines de CI para testes automatizados.
   - Escolher e adicionar licença (por exemplo MIT).

Contribuição
------------
- Abra issues para bugs/funcionalidades.
- Envie PRs pequenas e focadas.
- Documente novos drivers e alterações significativas em `docs/`.

Contato
-------
- (Robson William Teixeira Junior)[https://github.com/robs-onn] - robsonwtj@gmail.com
- (Pedro Henrique Teixeira Crispim)[https://github.com/PedroCrispim11] - pedrocrispim020@gmail.com

Observação final
----------------
Priorize a criação de uma camada de abstração de hardware para permitir desenvolvimento e testes sem a necessidade do hardware físico. Isso facilita integração com diferentes protocolos e acelera o desenvolvimento da lógica autônoma.
