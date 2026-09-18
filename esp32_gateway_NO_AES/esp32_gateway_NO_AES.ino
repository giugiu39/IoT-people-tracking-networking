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

WiFiClientSecure espClient;
PubSubClient mqtt(espClient);

// ============================================================
// BLE CONFIGURATION
// ============================================================

#define DEVICE_NAME "ESP32_Gateway_IoT"

#define SERVICE_UUID \
"12345678-1234-1234-1234-123456789000"

#define CHARACTERISTIC_UUID \
"12345678-1234-1234-1234-123456789001"

bool deviceConnected = false;


// ============================================================
// MQTT REMAINING LENGTH ENCODING
// ============================================================

int encodeRemainingLength(uint32_t length, uint8_t* output) {
    int bytes = 0;
    do {
        uint8_t encodedByte = length % 128;
        length /= 128;
        if (length > 0) {
            encodedByte |= 0x80;
        }
        output[bytes++] = encodedByte;
    } while (length > 0);
    return bytes;
}


// ============================================================
// HEX DUMP
// ============================================================

void printHex(const uint8_t* data, size_t length) {
    for (size_t i = 0; i < length; i++) {
        Serial.printf("%02X ", data[i]);
        if ((i + 1) % 16 == 0) {
            Serial.println();
        }
    }
    if (length % 16 != 0) {
        Serial.println();
    }
}


// ============================================================
// ASCII DUMP
// ============================================================

void printAscii(const uint8_t* data, size_t length) {
    for (size_t i = 0; i < length; i++) {
        uint8_t c = data[i];
        if (c >= 32 && c <= 126) {
            Serial.print((char)c);
        } else {
            Serial.print(".");
        }
    }
    Serial.println();
}


// ============================================================
// MQTT PUBLISH ANALYSIS
// ============================================================

void analyzeMqttPublish(
    const char* topic,
    const uint8_t* payload,
    size_t payloadLength
) {
    size_t topicLength = strlen(topic);

    // --------------------------------------------------------
    // MQTT QoS 0 PUBLISH
    //
    // Fixed Header:
    //   1 byte packet type/flags
    //
    // Variable Header:
    //   2 bytes Topic Length
    //   N bytes Topic
    //
    // Payload:
    //   payloadLength bytes
    // --------------------------------------------------------

    const uint8_t packetTypeFlags = 0x30;
    uint32_t remainingLength = 2 + topicLength + payloadLength;
    uint8_t remainingLengthBytes[4];
    int remainingLengthSize = encodeRemainingLength(remainingLength, remainingLengthBytes);
    size_t fixedHeaderSize = 1 + remainingLengthSize;
    size_t variableHeaderSize = 2 + topicLength;
    size_t mqttPacketSize = fixedHeaderSize + variableHeaderSize + payloadLength;
    size_t mqttOverhead = mqttPacketSize - payloadLength;

    // ========================================================
    // HEADER
    // ========================================================
    Serial.println();
    Serial.println();
    Serial.println("============================================================");
    Serial.println("                 MQTT PUBLISH ANALYSIS");
    Serial.println("============================================================");

    // ========================================================
    // BASIC INFORMATION
    // ========================================================
    Serial.println();
    Serial.println("[1] BASIC INFORMATION");
    Serial.println("------------------------------------------------------------");
    Serial.printf("MQTT Broker       : %s\n", mqtt_server);
    Serial.printf("MQTT Port         : %d\n", mqtt_port);
    Serial.printf("Transport         : MQTT over TLS over TCP\n");
    Serial.printf("MQTT Packet Type  : PUBLISH\n");
    Serial.printf("QoS               : 0\n");
    Serial.printf("DUP               : 0\n");
    Serial.printf("RETAIN            : 0\n");

    // ========================================================
    // TOPIC
    // ========================================================
    Serial.println();
    Serial.println("[2] MQTT TOPIC");
    Serial.println("------------------------------------------------------------");
    Serial.printf("Topic             : %s\n", topic);
    Serial.printf("Topic length      : %u bytes\n", (unsigned)topicLength);
    Serial.print("Topic HEX         : ");
    printHex((const uint8_t*)topic, topicLength);

    // ========================================================
    // PAYLOAD
    // ========================================================
    Serial.println();
    Serial.println("[3] MQTT PAYLOAD");
    Serial.println("------------------------------------------------------------");
    Serial.printf("Payload length    : %u bytes\n", (unsigned)payloadLength);
    Serial.println();
    Serial.println("Payload HEX:");
    printHex(payload, payloadLength);
    Serial.println("Payload ASCII representation:");
    printAscii(payload, payloadLength);

    // ========================================================
    // MQTT REMAINING LENGTH
    // ========================================================
    Serial.println();
    Serial.println("[4] MQTT REMAINING LENGTH");
    Serial.println("------------------------------------------------------------");
    Serial.printf("Remaining Length  : %lu bytes\n", (unsigned long)remainingLength);
    Serial.printf("Encoded in        : %d byte(s)\n", remainingLengthSize);
    Serial.print("Remaining Length HEX : ");
    printHex(remainingLengthBytes, remainingLengthSize);

    // ========================================================
    // FIXED HEADER
    // ========================================================
    Serial.println();
    Serial.println("[5] MQTT FIXED HEADER");
    Serial.println("------------------------------------------------------------");
    Serial.printf("Fixed Header size : %u bytes\n", (unsigned)fixedHeaderSize);
    Serial.print("Fixed Header HEX  : ");
    Serial.printf("%02X ", packetTypeFlags);
    for (int i = 0; i < remainingLengthSize; i++) {
        Serial.printf("%02X ", remainingLengthBytes[i]);
    }
    Serial.println();

    // ========================================================
    // VARIABLE HEADER
    // ========================================================
    Serial.println();
    Serial.println("[6] MQTT VARIABLE HEADER");
    Serial.println("------------------------------------------------------------");
    Serial.printf("Variable Header   : %u bytes\n", (unsigned)variableHeaderSize);
    Serial.println("Contents:");
    Serial.println("  - Topic Length   : 2 bytes");
    Serial.printf("  - Topic          : %u bytes\n", (unsigned)topicLength);
    Serial.print("Variable Header HEX: ");
    Serial.printf("%02X ", (uint8_t)(topicLength >> 8));
    Serial.printf("%02X ", (uint8_t)(topicLength & 0xFF));
    for (size_t i = 0; i < topicLength; i++) {
        Serial.printf("%02X ", (uint8_t)topic[i]);
    }
    Serial.println();

    // ========================================================
    // COMPLETE MQTT PUBLISH
    // ========================================================
    Serial.println();
    Serial.println("[7] COMPLETE MQTT PUBLISH PACKET");
    Serial.println("------------------------------------------------------------");
    Serial.printf("Fixed Header     : %u bytes\n", (unsigned)fixedHeaderSize);
    Serial.printf("Variable Header  : %u bytes\n", (unsigned)variableHeaderSize);
    Serial.printf("Payload          : %u bytes\n", (unsigned)payloadLength);
    Serial.printf("TOTAL MQTT       : %u bytes\n", (unsigned)mqttPacketSize);

    // ========================================================
    // OVERHEAD
    // ========================================================
    Serial.println();
    Serial.println("[8] MQTT PROTOCOL OVERHEAD");
    Serial.println("------------------------------------------------------------");
    Serial.printf("Payload          : %u bytes\n", (unsigned)payloadLength);
    Serial.printf("MQTT overhead    : %u bytes\n", (unsigned)mqttOverhead);
    Serial.printf("Total MQTT       : %u bytes\n", (unsigned)mqttPacketSize);
    double overheadPercentage = 100.0 * ((double)mqttOverhead / (double)payloadLength);
    Serial.printf("Overhead ratio    : %.2f %%\n", overheadPercentage);

    // ========================================================
    // PACKET STRUCTURE
    // ========================================================
    Serial.println();
    Serial.println("[9] MQTT PACKET STRUCTURE");
    Serial.println("------------------------------------------------------------");
    Serial.printf("[Fixed Header]       %u bytes\n", (unsigned)fixedHeaderSize);
    Serial.printf("[Variable Header]    %u bytes\n", (unsigned)variableHeaderSize);
    Serial.printf("[Payload]            %u bytes\n", (unsigned)payloadLength);
    Serial.println();
    Serial.printf("TOTAL                %u bytes\n", (unsigned)mqttPacketSize);

    // ========================================================
    // COMPLETE PACKET RECONSTRUCTION
    // ========================================================
    Serial.println();
    Serial.println("[10] COMPLETE MQTT PACKET - HEX");
    Serial.println("------------------------------------------------------------");
    Serial.printf("%02X ", packetTypeFlags);
    for (int i = 0; i < remainingLengthSize; i++) {
        Serial.printf("%02X ", remainingLengthBytes[i]);
    }
    Serial.printf("%02X %02X ", (uint8_t)(topicLength >> 8), (uint8_t)(topicLength & 0xFF));
    for (size_t i = 0; i < topicLength; i++) {
        Serial.printf("%02X ", (uint8_t)topic[i]);
    }
    for (size_t i = 0; i < payloadLength; i++) {
        Serial.printf("%02X ", payload[i]);
    }
    Serial.println();
    Serial.println("============================================================");
    Serial.println("                 END MQTT ANALYSIS");
    Serial.println("============================================================");
    Serial.println();
}


// ============================================================
// BLE CALLBACK
// ============================================================

class MyCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        String rxValue = pCharacteristic->getValue();

        if (rxValue.length() > 0) {
            const uint8_t* payload = (const uint8_t*)rxValue.c_str();
            size_t payloadLength = rxValue.length();

            Serial.println();
            Serial.println("############################################################");
            Serial.println("                 BLE EVENT RECEIVED (NO_AES)");
            Serial.println("############################################################");
            Serial.printf("BLE payload length: %u bytes\n", (unsigned)payloadLength);

            // ------------------------------------------------
            // PRINT RAW BLE PAYLOAD
            // ------------------------------------------------
            Serial.println();
            Serial.println("Raw BLE payload HEX:");
            printHex(payload, payloadLength);
            
            Serial.println("Raw BLE payload ASCII (JSON in chiaro):");
            printAscii(payload, payloadLength);

            // ------------------------------------------------
            // MQTT ANALYSIS
            // ------------------------------------------------
            analyzeMqttPublish(mqtt_topic, payload, payloadLength);

            // ------------------------------------------------
            // ACTUAL MQTT PUBLISH
            // ------------------------------------------------
            Serial.println();
            Serial.println("[11] SENDING MQTT PUBLISH (NO_AES)...");

            bool success = mqtt.publish(mqtt_topic, payload, payloadLength);

            if (success) {
                Serial.println("[MQTT] Publish accepted by client.");
            } else {
                Serial.println("[MQTT] ERROR: publish failed.");
            }

            Serial.println();
            Serial.println("############################################################");
            Serial.println();
        }
    }
};


// ============================================================
// BLE SERVER CALLBACKS
// ============================================================

class MyServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        Serial.println("[BLE] Client connesso.");
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        Serial.println("[BLE] Client disconnesso.");
        Serial.println("[BLE] Riavvio advertising...");
        delay(500);
        pServer->startAdvertising();
    }
};


// ============================================================
// WIFI
// ============================================================

void setup_wifi() {
    Serial.print("Connessione al WiFi...");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println();
    Serial.println("WiFi connesso!");
    Serial.print("ESP32 IP address: ");
    Serial.println(WiFi.localIP());
}


// ============================================================
// MQTT CONNECTION
// ============================================================

void reconnect_mqtt() {
    while (!mqtt.connected()) {
        Serial.print("Connessione al Broker MQTT...");
        String clientId = "ESP32ClassicGateway-" + String(random(0, 1000));

        if (mqtt.connect(clientId.c_str(), "Networking_Project", "sciaobello")) {
            Serial.println("Connesso!");
            Serial.println();
            Serial.println("MQTT connection parameters:");
            Serial.printf("  Broker : %s\n", mqtt_server);
            Serial.printf("  Port   : %d\n", mqtt_port);
            Serial.printf("  TLS    : ENABLED\n");
            Serial.printf("  QoS    : 0\n");
        } else {
            Serial.print("Fallito, rc=");
            Serial.print(mqtt.state());
            Serial.println();
            Serial.println("Riprovo tra 5 secondi...");
            delay(5000);
        }
    }
}


// ============================================================
// SETUP
// ============================================================

void setup() {
    Serial.begin(115200);
    delay(1000);

    // --------------------------------------------------------
    // WIFI
    // --------------------------------------------------------
    setup_wifi();

    // --------------------------------------------------------
    // TLS
    // --------------------------------------------------------
    espClient.setInsecure();

    // --------------------------------------------------------
    // MQTT
    // --------------------------------------------------------
    mqtt.setServer(mqtt_server, mqtt_port);

    // --------------------------------------------------------
    // BLE
    // --------------------------------------------------------
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

    Serial.println();
    Serial.println("============================================================");
    Serial.println("BLE Gateway IoT ATTIVO [MODALITÀ NO_AES]");
    Serial.println("============================================================");
    Serial.println("In attesa del Tracker...");
}


// ============================================================
// LOOP
// ============================================================

void loop() {
    if (!mqtt.connected()) {
        reconnect_mqtt();
    }
    mqtt.loop();
}