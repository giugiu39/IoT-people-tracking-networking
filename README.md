Networking Performance Analysis of an Edge-Based People Tracking IoT System
===========================================================================

📌 Overview
-----------

This repository contains the software components, embedded firmware, benchmarking tools, and experimental utilities developed for the performance evaluation of an **edge-based IoT system for people tracking**.

The project investigates two heterogeneous communication paths for transmitting compact, event-based information generated at the edge:

*   **Path A — BLE + MQTT/TLS**Raspberry Pi → BLE → ESP32 Gateway → Wi-Fi → MQTT/TLS → Cloud Broker → Subscriber
    
*   **Path B — CoAP/UDP**Raspberry Pi → CoAP over UDP → Local Server
    

The two architectures are evaluated under controlled experimental conditions, with a focus on:

*   end-to-end latency;
    
*   reliability;
    
*   protocol behavior;
    
*   security overhead;
    
*   scalability under increasing event rates.
    

The system follows an **edge-computing approach**: video analysis and people tracking are performed locally on the Raspberry Pi, while only the resulting semantic movement events are transmitted through the IoT communication infrastructure.

🎯 Objectives
=============

The main objectives of the project are:

*   Evaluate end-to-end communication latency.
    
*   Measure Packet Delivery Ratio (PDR) and message losses.
    
*   Compare a local edge/LAN architecture with a gateway-based cloud architecture.
    
*   Investigate the impact of MQTT Quality of Service (QoS) levels.
    
*   Evaluate communication behavior under increasing Events Per Second (EPS).
    
*   Analyze the effects of BLE, Wi-Fi, UDP, MQTT, CoAP, and cloud connectivity.
    
*   Evaluate the overhead associated with AES-GCM authenticated encryption.
    
*   Measure CoAP Round-Trip Time (RTT).
    
*   Provide reproducible experiments through dedicated stress-testing and logging scripts.
    

🏗️ System Architecture
=======================

The experimental testbed consists of three main nodes:

NodeRoleMain Technologies**Raspberry Pi**Edge tracker and event producerPython, YOLO, ByteTrack, BLE, CoAP**ESP32 / Arduino Nano ESP32**BLE-to-IP gatewayBLE, Wi-Fi, MQTT/TLS**MacBook Pro**Aggregation and measurement nodeCoAP server, MQTT subscriber, metric collection

High-Level Architecture
-----------------------

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML                              `┌─────────────────────────┐                                │      Raspberry Pi       │                                │       Edge Node         │                                │                         │                                │ YOLO + ByteTrack        │                                │ Zone Detection          │                                │ Event Generation       │                                └────────────┬────────────┘                                             │                           ┌─────────────────┴─────────────────┐                           │                                   │                        PATH A                              PATH B                           │                                   │                           ▼                                   ▼                    ┌─────────────┐                     ┌─────────────┐                    │     BLE     │                     │ CoAP / UDP  │                    └──────┬──────┘                     └──────┬──────┘                           │                                   │                           ▼                                   │                    ┌─────────────┐                            │                    │    ESP32    │                            │                    │   Gateway   │                            │                    └──────┬──────┘                            │                           │ Wi-Fi                             │                           ▼                                   ▼                    ┌─────────────┐                     ┌─────────────┐                    │ MQTT / TLS  │                     │    CoAP     │                    │ Cloud Broker│                     │   Server    │                    └──────┬──────┘                     │   MacBook   │                           │                            └─────────────┘                           │ WAN                           ▼                    ┌─────────────┐                    │   MQTT      │                    │  Subscriber │                    │   MacBook   │                    └─────────────┘`

🔀 Communication Paths
======================

Path A — BLE + MQTT/TLS
-----------------------

Path A implements an **edge-to-cloud communication architecture**:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Raspberry Pi       │       │ Bluetooth Low Energy       ▼  ESP32 Gateway       │       │ Wi-Fi       ▼  MQTT over TLS       │       ▼  Cloud MQTT Broker       │       │ Internet / WAN       ▼  MacBook MQTT Subscriber   `

The Raspberry Pi generates movement events and sends them to the ESP32 gateway through **Bluetooth Low Energy (BLE)**.

The ESP32 receives the BLE payload and forwards the event through Wi-Fi using **MQTT over TLS**. A cloud MQTT broker handles message distribution to the MacBook subscriber.

This path combines multiple communication technologies and network segments, making it suitable for studying a heterogeneous **edge-to-cloud IoT pipeline**.

### MQTT Quality of Service

Dedicated firmware and subscriber scripts support MQTT QoS experiments:

QoSDelivery Semantics**QoS 0**At most once**QoS 1**At least once**QoS 2**Exactly once

The experiments investigate the relationship between:

*   MQTT delivery semantics;
    
*   communication overhead;
    
*   measured end-to-end latency.
    

Path B — CoAP over UDP
----------------------

Path B implements a **direct edge-to-LAN communication architecture**:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Raspberry Pi       │       │ CoAP / UDP       ▼  MacBook Pro  CoAP Server   `

The Raspberry Pi sends CoAP requests directly to the local server.

The CoAP server:

1.  Receives the request.
    
2.  Decrypts the payload when AES-GCM is enabled.
    
3.  Extracts the sender timestamp.
    
4.  Calculates the end-to-end latency.
    
5.  Stores the event and associated metrics.
    
6.  Returns a CoAP response.
    

The Raspberry Pi also measures the **Round-Trip Time (RTT)** associated with the CoAP request/response exchange.

🧠 Edge AI and Event Generation
===============================

The Raspberry Pi performs **people detection and tracking locally**, avoiding the need to continuously transmit raw video to the cloud.

Processing Pipeline
-------------------

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   RTSP Video Stream          │          ▼  Frame Acquisition          │          ▼  YOLO Object Detection          │          ▼  ByteTrack          │          ▼  Person Tracking          │          ▼  Zone Classification          │          ▼  Zone Transition Event          │          ▼  BLE / CoAP Transmission   `

The generated events describe semantic movements such as:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Person 1053: Zone_A → Zone_D   `

Only the resulting event is transmitted through the IoT communication paths.

This design separates the **edge intelligence layer** from the **network communication layer**, allowing network performance to be investigated without continuously transmitting video streams.

🔐 Security
===========

The encrypted versions of the system use **AES-GCM (Advanced Encryption Standard – Galois/Counter Mode)** for authenticated encryption.

AES-GCM provides:

*   confidentiality;
    
*   integrity;
    
*   authentication of the encrypted payload.
    

The encrypted message contains the required nonce together with the authenticated ciphertext.

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Plaintext Event        │        ▼     AES-GCM        │        ▼  Encrypted Payload        │        ├── Nonce        └── Ciphertext + Authentication Tag   `

For controlled comparison experiments, the repository also contains NO\_AES implementations.

These variants allow the impact of:

*   cryptographic processing;
    
*   payload overhead;
    

to be evaluated separately.

> **Security Note**
> 
> Credentials, broker passwords, shared keys, and other secrets must **not** be committed to Git.
> 
> Use environment variables or local configuration files excluded through .gitignore.

⏱️ Time Synchronization
=======================

Accurate one-way latency measurements require synchronized clocks on the participating nodes.

The experimental setup uses:

*   **chrony** on the Raspberry Pi;
    
*   **sntp** / network time synchronization on the MacBook;
    
*   the Raspberry Pi as a local time reference for the experimental LAN.
    

Before a measurement session, the MacBook can be synchronized with:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`sudo sntp -sS` 

The resulting clock offset should be sufficiently small compared with the latency being measured.

No fixed artificial latency correction is applied to the final measurements.

📏 Performance Metrics
======================

End-to-End Latency
------------------

The communication latency is calculated from the sender-side transmission timestamp to the receiver-side reception timestamp:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Latency = Receive Timestamp − Send Timestamp   `

Implementation:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   latency_ms = (receive_time_ns - send_time_ns) / 1_000_000.0   `

The timestamp is assigned immediately before serialization and transmission of the event.

Therefore, the measured quantity represents an **application-level end-to-end communication latency**, rather than a pure physical-layer propagation delay.

Packet Delivery Ratio
---------------------

The Packet Delivery Ratio is calculated as:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   PDR = Received Messages / Sent Messages × 100   `

PDR is used to evaluate message delivery reliability under different communication conditions and traffic loads.

CoAP Round-Trip Time
--------------------

For CoAP, the Raspberry Pi measures the request/response RTT:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Raspberry Pi       │       │ CoAP Request       ▼  MacBook       │       │ CoAP Response       ▼  Raspberry Pi   `

RTT is distinct from one-way end-to-end event latency and is therefore reported as a separate metric.

MQTT QoS
--------

The MQTT experiments evaluate:

*   QoS 0;
    
*   QoS 1;
    
*   QoS 2.
    

QoS 1 introduces the MQTT acknowledgment mechanism between publisher and broker.

However, the end-to-end latency reported by the subscriber is measured from the sender-side timestamp to subscriber reception.

Therefore, the reported value represents the latency of the **complete BLE + MQTT communication path**, rather than the MQTT PUBACK time itself.

🧪 Stress Testing
=================

The repository includes dedicated scripts for evaluating system behavior under increasing event-generation rates.

The incremental stress-test methodology progressively increases the offered load in **Events Per Second (EPS)**:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML `5 EPS     │     ▼  10 EPS     │     ▼  15 EPS     │     ▼  20 EPS     │    ...     │     ▼  50 EPS`

For each operating point, the system can be evaluated in terms of:

*   transmitted events;
    
*   received events;
    
*   packet losses;
    
*   PDR;
    
*   latency distribution;
    
*   CoAP RTT;
    
*   protocol behavior under increasing load.
    

This methodology is intended to identify:

*   performance degradation;
    
*   increased latency;
    
*   packet losses;
    
*   potential saturation conditions.
    

The stress-test scripts are designed to identify these behaviors **experimentally rather than assuming a theoretical saturation point**.

📁 Repository Structure
=======================

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   .  ├── arduinoNanoESP32_gateway/  │   └── arduinonanoesp32_gateway.ino  │  ├── arduinoNanoESP32_gateway_NO_AES/  │   └── arduinonanoesp32_gateway_NO_AES.ino  │  ├── edge_ai/  │   ├── output/  │   ├── videos/  │   └── zone_picker.py  │  ├── esp32_gateway/  │   └── esp32_gateway.ino  │  ├── esp32_gateway_NO_AES/  │   └── esp32_gateway_NO_AES.ino  │  ├── esp32_qos_gateway/  │   └── esp32_qos_gateway.ino  │  ├── path_a_mqtt/  │   ├── mqtt_subscriber.py  │   ├── mqtt_subscriber_NO_AES.py  │   └── mqtt_subscriber_qos.py  │  ├── path_b_coap/  │   ├── coap_server.py  │   ├── coap_server_NO_AES.py  │   └── coap_server_stress_test.py  │  ├── Raspberry_deploy/  │   ├── requirements.txt  │   ├── stress_test.py  │   ├── stress_test_intervalli_graduali.py  │   ├── tracker.py  │   ├── tracker_NO_AES.py  │   └── yolo11s.pt  │  ├── .gitignore  ├── Proposta di Progetto.docx  └── README.md   `

📦 Component Overview
=====================

ComponentPurposearduinoNanoESP32\_gateway/Arduino Nano ESP32 BLE-to-MQTT gateway implementationarduinoNanoESP32\_gateway\_NO\_AES/Arduino Nano ESP32 gateway without AES-GCMesp32\_gateway/Standard ESP32 BLE-to-MQTT gatewayesp32\_gateway\_NO\_AES/ESP32 gateway without AES-GCMesp32\_qos\_gateway/ESP32 gateway used for MQTT QoS experimentsedge\_ai/Edge-AI utilities, videos, and experimental outputspath\_a\_mqtt/MQTT subscribers and QoS evaluation scriptspath\_b\_coap/CoAP servers and CoAP stress-testing implementationRaspberry\_deploy/Raspberry Pi deployment, tracking, and stress-testing scriptsyolo11s.ptYOLO model used by the edge tracking pipelineProposta di Progetto.docxOriginal project proposal

⚙️ Requirements
===============

The main software components are based on **Python 3.9+**.

The Python environment requires libraries including:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   aiocoap  bleak  paho-mqtt  cryptography  opencv-python  numpy  ultralytics   `

The exact Raspberry Pi environment is documented in:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Raspberry_deploy/requirements.txt   `

A Python virtual environment is recommended.

🚀 Installation
===============

1\. Clone the Repository
------------------------

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`git clone   cd` 

2\. Create and Activate a Virtual Environment
---------------------------------------------

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python3 -m venv venv  source venv/bin/activate   `

3\. Install Dependencies
------------------------

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   pip install -r Raspberry_deploy/requirements.txt   `

▶️ Running the System
=====================

1\. Synchronize the Clocks
--------------------------

On the MacBook:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`sudo sntp -sS` 

Verify that the clock offset is sufficiently small before collecting measurements.

2\. Start the CoAP Server
-------------------------

On the MacBook:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python path_b_coap/coap_server.py   `

For the stress-test configuration:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python path_b_coap/coap_server_stress_test.py   `

3\. Start the MQTT Subscriber
-----------------------------

On the MacBook:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python path_a_mqtt/mqtt_subscriber.py   `

For QoS experiments:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python path_a_mqtt/mqtt_subscriber_qos.py --qos 0   `

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python path_a_mqtt/mqtt_subscriber_qos.py --qos 1   `

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python path_a_mqtt/mqtt_subscriber_qos.py --qos 2   `

4\. Start the Edge Tracker
--------------------------

On the Raspberry Pi:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   cd Raspberry_deploy  python tracker.py --source "rtsp://:8554/live" --no-show   `

The tracker performs:

1.  Local people detection.
    
2.  Object tracking.
    
3.  Zone classification.
    
4.  Zone-transition event generation.
    

5\. Run the Stress Tests
------------------------

### Standard Stress Test

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   cd Raspberry_deploy  python stress_test.py   `

### Incremental Stress Test

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python stress_test_intervalli_graduali.py   `

📊 Experimental Evaluation
==========================

The experimental campaign evaluates the two communication architectures under controlled conditions.

Path B — CoAP / LAN
-------------------

The direct CoAP/LAN path avoids the BLE gateway and cloud/WAN segment.

In the tested local-network configuration, this architecture generally produced lower communication latency and high delivery reliability.

These observations are specific to the implemented experimental testbed and should not be interpreted as universal protocol benchmarks.

Path A — BLE + MQTT / Cloud
---------------------------

The BLE + MQTT architecture introduces additional communication stages:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   BLE   ↓  ESP32 Gateway   ↓  Wi-Fi   ↓  TLS   ↓  Cloud Broker   ↓  WAN   ↓  Subscriber   `

Consequently, measured end-to-end latency is affected by the combined behavior of:

*   BLE communication;
    
*   gateway processing;
    
*   Wi-Fi connectivity;
    
*   TLS processing;
    
*   MQTT communication;
    
*   cloud-broker routing;
    
*   Internet/WAN conditions.
    

Load Dependence
---------------

Under increasing event rates, the system can experience:

*   increased queueing;
    
*   wireless-interface contention;
    
*   buffer pressure;
    
*   increased latency;
    
*   packet losses;
    
*   reduced effective delivery performance.
    

The stress-test scripts are intended to identify these behaviors experimentally rather than assuming a theoretical saturation point.

> **Experimental Note**
> 
> Measured performance values depend on the specific hardware, firmware, software versions, wireless environment, broker configuration, geographic location, network conditions, and workload used during the experiments.
> 
> They should therefore be interpreted as results of the implemented testbed rather than universal benchmarks of the underlying protocols.

📂 Experimental Outputs
=======================

Communication events and measurements are stored in **JSONL** format under:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   edge_ai/output/   `

A typical event record can contain information such as:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   {    "event_id": 1,    "person_id": 123,    "from_zone": "Zone_A",    "to_zone": "Zone_D",    "event": "zone_transition",    "path": "CoAP",    "latency_ms": 12.345  }   `

The output files can subsequently be processed to obtain statistical indicators such as:

*   minimum latency;
    
*   maximum latency;
    
*   mean latency;
    
*   median latency;
    
*   standard deviation;
    
*   P95;
    
*   P99;
    
*   Packet Delivery Ratio;
    
*   RTT.
    

🔬 Reproducibility
==================

For meaningful comparisons, experimental runs should maintain consistent:

*   hardware configuration;
    
*   firmware version;
    
*   Python environment;
    
*   wireless network;
    
*   MQTT broker and region;
    
*   MQTT QoS level;
    
*   CoAP configuration;
    
*   encryption configuration;
    
*   event-generation rate;
    
*   video/RTSP source;
    
*   clock synchronization procedure;
    
*   experiment duration.
    

When comparing communication paths, the same workload and comparable experimental conditions should be used whenever possible.

🛠️ Technologies
================

The project integrates the following technologies:

CategoryTechnologies**Programming**Python, C++ / Arduino**Edge Computing**Raspberry Pi**Embedded Systems**ESP32, Arduino Nano ESP32**Computer Vision**YOLO, ByteTrack, OpenCV**Wireless Communication**BLE, Wi-Fi**IoT Protocols**MQTT, MQTT/TLS, CoAP, UDP**Security**AES-GCM, TLS**Cloud**HiveMQ Cloud**Streaming**RTSP**Network Analysis**Wireshark, TShark**Time Synchronization**chrony, sntp

🎓 Academic Context
===================

This project was developed within the academic activities of the **Networking and IoT Systems** course.

The project integrates concepts from:

*   Internet of Things;
    
*   edge computing;
    
*   wireless and IP networking;
    
*   application-layer communication protocols;
    
*   distributed systems;
    
*   network performance evaluation;
    
*   network security;
    
*   real-time event communication;
    
*   edge-based artificial intelligence.
    

The experimental methodology provides a practical comparison between a **direct local edge communication architecture** and a **gateway-based edge-to-cloud architecture**, with emphasis on:

*   latency;
    
*   reliability;
    
*   scalability;
    
*   communication overhead.
    

👥 Authors
==========

**Gianluca Perrotta****Marco Macrì****Orazio Ruberto****Asrar**

**University of Calabria — DIMES**Department of Computer, Modeling, Electronics, and Systems Engineering

📄 License
==========

This repository was developed for **academic and research purposes**.

Unless otherwise specified, the source code is intended for:

*   educational use;
    
*   experimentation;
    
*   research;
    
*   reproducibility of the presented testbed.