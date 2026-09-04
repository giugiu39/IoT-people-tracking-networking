#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

// ── 1. CONFIGURAZIONE RETE ──
const char* ssid = "TIM-32257583";
const char* password = "ug5VmZF53TpIk113cktXjmpK";
const char* mqtt_server = "ab23ed51f0614c02b127cb1f32883fbc.s1.eu.hivemq.cloud";
const int mqtt_port = 8883; 
const char* mqtt_topic = "/people/events/gianluca"; 

WiFiClientSecure espClient;
PubSubClient mqtt(espClient);

// ── 2. CONFIGURAZIONE BLE NATIVA ESP32 ──
#define DEVICE_NAME "ESP32_Gateway_IoT"
#define SERVICE_UUID        "12345678-1234-1234-1234-123456789000"
#define CHARACTERISTIC_UUID "12345678-1234-1234-1234-123456789001"

// Callback per gestire la ricezione dei dati via BLE
class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        String rxValue = pCharacteristic->getValue();
        
        if (rxValue.length() > 0) {
            Serial.println("-----------------------------------------");
            Serial.print("[BLE Ricevuto] ");
            Serial.println(rxValue);
            
            if (mqtt.publish(mqtt_topic, rxValue.c_str())) {
                Serial.println("[MQTT] Inoltrato con successo al cloud!");
            } else {
                Serial.println("[MQTT] Errore di inoltro.");
            }
        }
    }
};

// NUOVO: Gestisce la connessione/disconnessione per riavviare l'advertising
class MyServerCallbacks: public BLEServerCallbacks {
    void onDisconnect(BLEServer* pServer) {
        Serial.println("[BLE] Client disconnesso. Riavvio advertising...");
        delay(500); // Breve pausa di sicurezza per lo stack Bluetooth
        pServer->startAdvertising(); // Rende di nuovo visibile l'ESP32
    }
};

void setup_wifi() {
    Serial.print("Connessione al WiFi...");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connesso!");
}

void reconnect_mqtt() {
    while (!mqtt.connected()) {
        Serial.print("Connessione al Broker MQTT...");
        String clientId = "ESP32Gateway-" + String(random(0, 1000));
        
        if (mqtt.connect(clientId.c_str(), "Networking_Project", "sciaobello")) {
            Serial.println("Connesso!");
        } else {
            Serial.print("Fallito, rc=");
            Serial.print(mqtt.state());
            Serial.println(" Riprovo tra 5 secondi");
            delay(5000);
        }
    }
}

void setup() {
    Serial.begin(115200);
    
    setup_wifi();
    espClient.setInsecure();
    mqtt.setServer(mqtt_server, mqtt_port);

    // Inizializza il BLE Nativo
    BLEDevice::init(DEVICE_NAME);
    BLEServer *pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks()); // <-- COLLEGA LE CALLBACK DEL SERVER
    
    // Crea il Servizio
    BLEService *pService = pServer->createService(SERVICE_UUID);
    
    // Crea la Caratteristica
    BLECharacteristic *pCharacteristic = pService->createCharacteristic(
                                         CHARACTERISTIC_UUID,
                                         BLECharacteristic::PROPERTY_WRITE
                                       );

    pCharacteristic->setCallbacks(new MyCallbacks());
    pService->start();
    
    // Avvia l'advertising iniziale
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06);  
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();
    
    Serial.println("BLE Gateway nativo attivo. In attesa di connessione dal Tracker...");
}

void loop() {
    if (!mqtt.connected()) {
        reconnect_mqtt();
    }
    mqtt.loop();
}