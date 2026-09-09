#define MQTT_MAX_PACKET_SIZE 512

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <time.h> // Aggiunto per il fix NTP

const char* ssid = "TIM-32257583";
const char* password = "ug5VmZF53TpIk113cktXjmpK";
const char* mqtt_server = "ab23ed51f0614c02b127cb1f32883fbc.s1.eu.hivemq.cloud";
const int mqtt_port = 8883; 
const char* mqtt_topic = "/people/events/gianluca"; 

WiFiClientSecure espClient;
PubSubClient mqtt(espClient);

// CONFIGURAZIONE BLE PER ESP32 CLASSICO
#define DEVICE_NAME "ESP32_Gateway_IoT"
#define SERVICE_UUID        "12345678-1234-1234-1234-123456789000"
#define CHARACTERISTIC_UUID "12345678-1234-1234-1234-123456789001"

bool deviceConnected = false;

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
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        Serial.println("[BLE] Client connesso.");
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
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
        String clientId = "ESP32ClassicGateway-NOAES-" + String(random(0, 1000));
        
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

    espClient.setInsecure(); // Salta la verifica rigida del certificato SSL per HiveMQ Cloud
    mqtt.setServer(mqtt_server, mqtt_port);

    // Inizializzazione BLE per ESP32 classico
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
    BLEDevice::startAdvertising();
    
    Serial.println("BLE Gateway NO_AES (ESP32 Classico) attivo. In attesa del Tracker...");
}

void loop() {
    if (!mqtt.connected()) {
        reconnect_mqtt();
    }
    mqtt.loop();
}