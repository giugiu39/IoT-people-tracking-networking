// esp32_gateway/esp32_gateway.ino
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoBLE.h>

// --- WiFi & MQTT Config ---
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "YOUR_BROKER_IP_OR_HIVEMQ";
const int mqtt_port = 1883; // 8883 for TLS/HiveMQ
const char* mqtt_topic = "/people/events";

WiFiClient espClient;
PubSubClient mqtt(espClient);

// --- BLE Config ---
#define DEVICE_NAME "ESP32_Gateway"
BLEService gatewayService("12345678-1234-1234-1234-123456789000");
// BLEWrite allows the Raspberry Pi to push JSON strings to this characteristic
BLEStringCharacteristic rxChar("12345678-1234-1234-1234-123456789001", BLEWrite, 256); 

void setup_wifi() {
    Serial.print("Connecting to WiFi");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connected.");
}

void reconnect_mqtt() {
    while (!mqtt.connected()) {
        Serial.print("Connecting to MQTT...");
        if (mqtt.connect("ESP32GatewayClient")) {
            Serial.println("connected");
        } else {
            Serial.print("failed, rc=");
            Serial.print(mqtt.state());
            delay(2000);
        }
    }
}

void setup() {
    Serial.begin(115200);
    setup_wifi();
    mqtt.setServer(mqtt_server, mqtt_port);

    if (!BLE.begin()) {
        Serial.println("Starting BLE failed!");
        while (1);
    }

    BLE.setLocalName(DEVICE_NAME);
    BLE.setAdvertisedService(gatewayService);
    gatewayService.addCharacteristic(rxChar);
    BLE.addService(gatewayService);
    BLE.advertise();
    Serial.println("BLE Gateway active, waiting for Raspberry Pi...");
}

void loop() {
    if (!mqtt.connected()) {
        reconnect_mqtt();
    }
    mqtt.loop();
    BLE.poll();

    // If Raspberry Pi wrote a new event to the BLE characteristic
    if (rxChar.written()) {
        String payload = rxChar.value();
        Serial.println("Received via BLE: " + payload);
        
        // Forward to MQTT Broker over Wi-Fi
        mqtt.publish(mqtt_topic, payload.c_str());
        Serial.println("Forwarded to MQTT.");
    }
}