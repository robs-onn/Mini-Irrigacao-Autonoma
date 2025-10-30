#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

// --- Definições de Pinos (Baseado no seu código) ---
const int PINO_SENSOR_UMIDADE_SOLO = A0; // Pino Analógico
const int PINO_LDR_DIGITAL = D2;        // <-- NOVO: Pino DIGITAL para o módulo LDR
const int PINO_RELE_BOMBA = D7;         // <-- ATUALIZADO: Pino Digital para o relé

// --- Lógica Invertida do Relé (Baseado no seu código) ---
const int LIGAR_BOMBA = LOW;
const int DESLIGAR_BOMBA = HIGH;

// --- Configuração de Rede ---
const char* SSID_REDE = "RobPhone"; // <-- AJUSTAR!
const char* SENHA_REDE = "umdoistres"; // <-- AJUSTAR!
String ENDERECO_SERVIDOR = "http://172.20.10.2:5000"; // <-- AJUSTAR!

// --- Configuração da Comunicação ---
const long INTERVALO_ENVIO_DADOS = 2000; // 2 segundos
unsigned long tempoUltimoEnvio = 0;

// --- Variáveis Globais de Estado ---
float umidadeAtualPercentual = 0.0; // Nome mais claro
int   luzEstadoDigital = 1;       // 1 para LOW (Escuro), 0 para HIGH (Claro) - Ajuste conforme seu módulo
bool  estadoBombaAtual = false;

String modoOperacao = "MANUAL";
float setpointUmidade = 60.0;
bool comandoManualBomba = false;

// --- Protótipos ---
void conectarWiFi();
void lerSensores();
void enviarDadosReceberConfig();
void controlarBomba();

// =============================================================
// SETUP
// =============================================================
void setup() {
  Serial.begin(115200); // Usar 115200 é geralmente melhor com ESP8266
  Serial.println("\nIniciando Sistema de Irrigação Automática (ESP8266)...");

  pinMode(PINO_LDR_DIGITAL, INPUT); // Configura pino do LDR digital como entrada
  pinMode(PINO_RELE_BOMBA, OUTPUT);
  digitalWrite(PINO_RELE_BOMBA, DESLIGAR_BOMBA); // Garante bomba desligada no início

  conectarWiFi();

  Serial.println("Setup concluído.");
}

// =============================================================
// LOOP
// =============================================================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi desconectado. Tentando reconectar...");
    conectarWiFi();
    if (WiFi.status() != WL_CONNECTED) {
        delay(5000);
        return;
    }
  }

  lerSensores();
  controlarBomba();

  unsigned long tempoAtual = millis();
  if (tempoAtual - tempoUltimoEnvio >= INTERVALO_ENVIO_DADOS) {
    tempoUltimoEnvio = tempoAtual;
    enviarDadosReceberConfig();
  }

  delay(500); // Mantido o delay do seu snippet original por enquanto
}

// =============================================================
// conectarWiFi (Sem alterações)
// =============================================================
void conectarWiFi() {
  Serial.print("Conectando a ");
  Serial.println(SSID_REDE);
  WiFi.begin(SSID_REDE, SENHA_REDE);
  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 20) {
    delay(500);
    Serial.print(".");
    tentativas++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi conectado!");
    Serial.print("Endereço IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFalha ao conectar ao WiFi.");
  }
}

// =============================================================
// lerSensores - Com LDR Digital e Calibração de Umidade
// =============================================================
void lerSensores() {
  // --- Leitura da Umidade do Solo (A0) ---
  int leituraAnalogicaUmidade = analogRead(A0); // Range 0-1023

  // CALIBRAÇÃO: Ajuste estes valores com testes reais!
  int umidadeMinLeitura = 300;  // <-- AJUSTAR! Leitura A0 com sensor na água (deve ser o valor MENOR se a lógica for invertida)
  int umidadeMaxLeitura = 1023; // <-- AJUSTAR! Leitura A0 com sensor seco no ar (deve ser o valor MAIOR)

  // Mapeia assumindo que MAIOR leitura = SECO (0%) e MENOR leitura = MOLHADO (100%)
  umidadeAtualPercentual = map(leituraAnalogicaUmidade, umidadeMaxLeitura, umidadeMinLeitura, 0, 100);
  umidadeAtualPercentual = constrain(umidadeAtualPercentual, 0, 100); // Garante 0 a 100

  // --- Leitura do LDR Digital ---
  int estadoLDR = digitalRead(PINO_LDR_DIGITAL); // Lê HIGH ou LOW

  // Você precisa verificar o que HIGH/LOW significa no SEU módulo LDR
  // Exemplo: Se HIGH significa que está claro:
  if (estadoLDR == HIGH) {
      luzEstadoDigital = 0; // Representa "Claro" ou "Acima do threshold"
      Serial.print("Luz: ALTO (HIGH)");
  } else {
      luzEstadoDigital = 1; // Representa "Escuro" ou "Abaixo do threshold"
      Serial.print("Luz: BAIXO (LOW)");
  }

  // Debug:
  Serial.print(" | Leitura Umid Ana (A0): "); Serial.print(leituraAnalogicaUmidade);
  Serial.print(" -> Umid Calc: "); Serial.print(umidadeAtualPercentual); Serial.println("%");
}

// =============================================================
// controlarBomba - Com lógica de relé invertida
// =============================================================
void controlarBomba() {
  bool ligarBomba = false;

  if (modoOperacao == "AUTOMATICO") {
    if (umidadeAtualPercentual < setpointUmidade) {
      ligarBomba = true;
    } else {
      ligarBomba = false;
    }
    Serial.print("[AUTO] ");
  } else { // Modo MANUAL
    ligarBomba = comandoManualBomba;
    Serial.print("[MANUAL] ");
  }

  if (ligarBomba && !estadoBombaAtual) {
    digitalWrite(PINO_RELE_BOMBA, LIGAR_BOMBA); // Usa a constante (LOW)
    estadoBombaAtual = true;
    Serial.println("-> Bomba LIGADA");
  } else if (!ligarBomba && estadoBombaAtual) {
    digitalWrite(PINO_RELE_BOMBA, DESLIGAR_BOMBA); // Usa a constante (HIGH)
    estadoBombaAtual = false;
    Serial.println("-> Bomba DESLIGADA");
  }
}

// =============================================================
// enviarDadosReceberConfig - Envia estado LDR digital
// =============================================================
void enviarDadosReceberConfig() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Erro: Sem WiFi para enviar dados.");
    return;
  }

  WiFiClient client;
  HTTPClient http;
  String urlCompleta = ENDERECO_SERVIDOR + "/api/dados";
  Serial.print("Comunicando com servidor: "); Serial.println(urlCompleta);

  if (http.begin(client, urlCompleta)) {
    http.addHeader("Content-Type", "application/json");

    // Monta JSON para enviar
    StaticJsonDocument<200> docEnvio;
    docEnvio["umidade"] = umidadeAtualPercentual;
    docEnvio["luz"] = luzEstadoDigital; // <-- Envia 0 ou 1
    docEnvio["bomba_ligada"] = estadoBombaAtual;
    String jsonEnvio;
    serializeJson(docEnvio, jsonEnvio);
    Serial.print("JSON Enviado: "); Serial.println(jsonEnvio); // Debug JSON

    int httpCode = http.POST(jsonEnvio);

    if (httpCode > 0) {
      String payload = http.getString();
      Serial.print("HTTP "); Serial.print(httpCode); Serial.print(": "); Serial.println(payload);
      if (httpCode == HTTP_CODE_OK) {
        StaticJsonDocument<200> docRecebido;
        DeserializationError error = deserializeJson(docRecebido, payload);
        if (error) {
          Serial.print("Falha ao interpretar JSON: "); Serial.println(error.c_str());
        } else {
          if (docRecebido.containsKey("modo")) modoOperacao = docRecebido["modo"].as<String>();
          if (docRecebido.containsKey("setpoint")) setpointUmidade = docRecebido["setpoint"].as<float>();
          if (docRecebido.containsKey("comando_manual")) comandoManualBomba = docRecebido["comando_manual"].as<bool>();
          Serial.println("Config recebida OK.");
        }
      }
    } else {
      Serial.printf("[HTTP] POST falhou, erro: %s\n", http.errorToString(httpCode).c_str());
    }
    http.end();
  } else {
    Serial.printf("[HTTP] Não foi possível conectar a: %s\n", urlCompleta.c_str());
  }
}