#define MQTT_MAX_PACKET_SIZE 512

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

const char* ssid = "TIM_plus";
const char* password = "ug5VmZF53TpIk113cktXjmpK";
const char* mqtt_server = "ab23ed51f0614c02b127cb1f32883fbc.s1.eu.hivemq.cloud";
const int mqtt_port = 8883; 
const char* mqtt_topic = "/people/events/gianluca"; 

// SETTA IL LIVELLO DI QOS DESIDERATO PER IL BENCHMARK: 0, 1, oppure 2
const int TARGET_MQTT_QOS = 2; 

WiFiClientSecure espClient;
PubSubClient mqtt(espClient);

#define DEVICE_NAME "ESP32_Gateway_IoT"
#define SERVICE_UUID        "12345678-1234-1234-1234-123456789000"
#define CHARACTERISTIC_UUID "12345678-1234-1234-1234-123456789001"

bool deviceConnected = false;

class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        String rxValue = pCharacteristic->getValue();
        
        if (rxValue.length() > 0) {
            Serial.println("-----------------------------------------");
            Serial.print("[BLE Ricevuto] Payload di ");
            Serial.print(rxValue.length());
            Serial.print(" byte. Inoltro con QoS ");
            Serial.println(TARGET_MQTT_QOS);
            
            // Pubblicazione con specificazione del livello di QoS e del flag retain
            bool success = mqtt.publish(mqtt_topic, (const uint8_t*)rxValue.c_str(), rxValue.length(), false);
            
            if (success) {
                Serial.println("[MQTT] Inoltrato al Cloud con successo!");
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
    Serial.print("Connessione WiFi...");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connesso!");
}

void reconnect_mqtt() {
    while (!mqtt.connected()) {
        Serial.print("Connessione Broker MQTT...");
        String clientId = "ESP32QoSGateway-" + String(random(0, 1000));
        
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
    espClient.setInsecure();
    mqtt.setServer(mqtt_server, mqtt_port);

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
    
    Serial.print("BLE Gateway attivo. Configurato per pubblicazione MQTT QoS ");
    Serial.println(TARGET_MQTT_QOS);
}

void loop() {
    if (!mqtt.connected()) {
        reconnect_mqtt();
    }
    mqtt.loop();
}