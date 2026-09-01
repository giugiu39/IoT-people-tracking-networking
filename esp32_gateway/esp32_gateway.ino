#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

// ── 1. CONFIGURAZIONE RETE (Modifica con i tuoi dati) ──
const char* ssid = "TIM_plus";
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

// Questa classe gestisce automaticamente l'arrivo di nuovi dati via Bluetooth
class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        // CORREZIONE: Usiamo la String nativa di Arduino per la versione 3.x del core ESP32
        String rxValue = pCharacteristic->getValue();
        
        if (rxValue.length() > 0) {
            Serial.println("-----------------------------------------");
            Serial.print("[BLE Ricevuto] ");
            Serial.println(rxValue);
            
            // Inoltra il payload a MQTT
            if (mqtt.publish(mqtt_topic, rxValue.c_str())) {
                Serial.println("[MQTT] Inoltrato con successo al cloud!");
            } else {
                Serial.println("[MQTT] Errore di inoltro.");
            }
        }
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
    
    // Crea il Servizio
    BLEService *pService = pServer->createService(SERVICE_UUID);
    
    // Crea la Caratteristica (con permessi di scrittura)
    BLECharacteristic *pCharacteristic = pService->createCharacteristic(
                                         CHARACTERISTIC_UUID,
                                         BLECharacteristic::PROPERTY_WRITE
                                       );

    // Assegna la callback per intercettare i dati scritti dal Mac/Raspberry
    pCharacteristic->setCallbacks(new MyCallbacks());
    
    pService->start();
    
    // Inizia l'advertising per farsi trovare
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06);  
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();
    
    Serial.println("BLE Gateway nativo attivo. In attesa di connessione dal Tracker...");
}

void loop() {
    // Mantieni viva la connessione MQTT
    if (!mqtt.connected()) {
        reconnect_mqtt();
    }
    mqtt.loop();
    
}