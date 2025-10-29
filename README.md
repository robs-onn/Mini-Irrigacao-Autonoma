# Projeto Irrigação Autônoma

Descrição breve
- Repositório para controlar um sistema de irrigação com modos manual e autônomo. Próximos passos: integrar comunicação via hardware (GPIO, UART/Serial, I2C, SPI, MQTT/Modbus) para controlar sensores e atuadores.

Funcionalidades esperadas
- Leitura de sensores (umidade do solo, temperatura, nível de água).
- Controle de atuadores (válvulas, bombas).
- Modo autônomo: regras/algoritmos de decisão (thresholds, agendamento, PID simples).
- Modo manual: interface para acionamento direto.
- Logs e telemetria para auditoria e análise.

Requisitos
- Python 3.8+ (ou outra linguagem escolhida)
- Dependências de comunicação (pyserial, paho-mqtt, RPi.GPIO ou gpiozero para Raspberry Pi, libmodbus, etc.)
- Ambiente com acesso ao hardware (GPIO/Serial) ou simulador para desenvolvimento sem hardware.

Estrutura sugerida
- README.md
- docs/
- src/
    - controllers/       # lógica de autonomia e manual
    - hw/                # abstrações de hardware (drivers)
    - services/          # comunicação (MQTT, REST), logger
    - config/            # arquivos de configuração
    - tests/
- scripts/             # utilitários de deploy e simulação

Instalação (exemplo Python)
- Criar venv:
    python -m venv .venv
    source .venv/bin/activate
- Instalar dependências:
    pip install -r requirements.txt

Configuração (exemplo YAML)
- config/system.yml
```yaml
mode: autonomous          # manual | autonomous | simulation
soil_moisture_threshold: 40
water_pulse_seconds: 30
mqtt:
    host: 192.168.1.10
    topic: irrigacao/telemetry
serial:
    port: /dev/ttyUSB0
    baudrate: 9600
```

Uso (exemplos)
- Rodar em modo simulação:
    MODE=simulation python -m src.main
- Rodar em modo manual:
    MODE=manual python -m src.main --open-valve zone1
- Rodar em modo autônomo:
    MODE=autonomous python -m src.main

Boas práticas para integração de hardware (próximos passos)
- Definir uma camada de abstração de hardware (interface comum para sensores/atuadores) para permitir testes sem hardware.
- Escolher protocolo(s):
    - Local: GPIO, PWM (Raspberry Pi/Arduino), I2C, SPI
    - Rede: MQTT, Modbus TCP, REST
    - Serial: UART/RS-485 para microcontroladores
- Implementar modo de simulação que emule sensores e atuadores.
- Projetar mensagens/command set claros para comunicação (ex.: JSON com comandos e respostas).
- Validar segurança: watchdogs, tempos máximos de atuação, confirmações de estado, tratamento de falhas.
- Testes e CI: incluir unit tests para regras e mocks para drivers de hardware.
- Logging e telemetria: registrar ações críticas, falhas e leituras periódicas.

Exemplo minimal de interface de driver (pseudocódigo)
```python
class ValveInterface:
        def open(self): ...
        def close(self): ...
        def status(self) -> dict: ...
```
- Implementar adaptadores: ValveGPIO, ValveSerial, ValveSimulator.

Checklist rápido antes de conectar hardware real
- Testes unitários passando com drivers simulados.
- Proteção elétrica e isolamento apropriado.
- Planos de rollback e parada de emergência (E-Stop).
- Monitoramento inicial em ambiente controlado.

Contribuição
- Abrir issues para funcionalidades e bugs.
- Usar PRs pequenas e descritivas.
- Documentar novos drivers em docs/hardware.md.

Licença
- Escolha uma licença (ex.: MIT) e adicione LICENSE no repositório.

Contato
- Incluir mantenedor/contato no arquivo de configuração do projeto.

Observação final
- Organize o desenvolvimento priorizando uma camada de abstração de hardware — isso facilitará integrar diferentes protocolos e testar a lógica autonoma sem depender do hardware físico imediatamente.