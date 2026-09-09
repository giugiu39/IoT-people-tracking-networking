#define MQTT_MAX_PACKET_SIZE 512 // Espande il buffer per i payload

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <time.h> // Aggiunto per il fix NTP

const char* ssid = "Iphone di Gianluca";
const char* password = "giuland39";
const char* mqtt_server = "ab23ed51f0614c02b127cb1f32883fbc.s1.eu.hivemq.cloud";
const int mqtt_port = 8883; 
const char* mqtt_topic = "/people/events/gianluca"; 

WiFiClientSecure espClient;
PubSubClient mqtt(espClient);

// CONFIGURAZIONE BLE NATIVA ESP32
#define DEVICE_NAME "ESP32_Gateway_IoT"
#define SERVICE_UUID        "12345678-1234-1234-1234-123456789000"
#define CHARACTERISTIC_UUID "12345678-1234-1234-1234-123456789001"

class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        String rxValue = pCharacteristic->getValue();
        
        if (rxValue.length() > 0) {
            Serial.println("-----------------------------------------");
            Serial.print("[BLE Ricevuto] Payload IN CHIARO di ");
            Serial.print(rxValue.length());
            Serial.println(" byte.");
            
            if (mqtt.publish(mqtt_topic, (const uint8_t*)rxValue.c_str(), rxValue.length())) {
                Serial.println("[MQTT] Inoltrato con successo al cloud!");
            } else {
                Serial.println("[MQTT] Errore di inoltro.");
            }
        }
    }
};

class MyServerCallbacks: public BLEServerCallbacks {
    void onDisconnect(BLEServer* pServer) {
        Serial.println("[BLE] Client disconnesso. Riavvio advertising...");
        delay(500); 
        pServer->startAdvertising(); 
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
        String clientId = "ESP32NanoGateway-NOAES-" + String(random(0, 1000));
        
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
    delay(1000);
    
    setup_wifi();

    // Sincronizzazione dell'orario via NTP (indispensabile per TLS su porta 8883)
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    Serial.print("Sincronizzazione orario NTP");
    time_t nowSecs = time(nullptr);
    while (nowSecs < 8 * 3600 * 24) {
        delay(500);
        Serial.print(".");
        nowSecs = time(nullptr);
    }
    Serial.println("\nOrario sincronizzato!");

    espClient.setInsecure(); // Salta la verifica rigida del certificato SSL per HiveMQ Cloud nei test
    mqtt.setServer(mqtt_server, mqtt_port);

    // Inizializza il BLE Nativo sull'ESP32-S3 interno al Nano
    BLEDevice::init(DEVICE_NAME);
    BLEServer *pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());
    
    BLEService *pService = pServer->createService(SERVICE_UUID);
    
    BLECharacteristic *pCharacteristic = pService->createCharacteristic(
                                         CHARACTERISTIC_UUID,
                                         BLECharacteristic::PROPERTY_WRITE |
                                         BLECharacteristic::PROPERTY_WRITE_NR
                                       );

    pCharacteristic->setCallbacks(new MyCallbacks());
    pService->start();
    
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06);  
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();
    
    Serial.println("BLE Gateway nativo NO_AES (Nano ESP32) attivo. In attesa del Tracker...");
}

void loop() {
    if (!mqtt.connected()) {
        reconnect_mqtt();
    }
    mqtt.loop();
}