# Networking Performance Analysis of an Edge-Based People Tracking IoT System

<p align="center">
  <strong>Edge AI · IoT Networking · BLE · MQTT · CoAP · Performance Evaluation</strong>
</p>

<p align="center">
  A distributed edge-based IoT system for people tracking and comparative performance analysis of heterogeneous communication architectures.
</p>

---

## 📌 Overview

This repository contains the software components, embedded firmware, benchmarking tools, and experimental utilities developed for the performance evaluation of an **edge-based IoT system for people tracking**.

The project investigates two heterogeneous communication paths for transmitting compact, event-based information generated at the edge:

- **Path A — BLE + MQTT/TLS**
  `Raspberry Pi → BLE → ESP32 Gateway → Wi-Fi → MQTT/TLS → Cloud Broker → Subscriber`

- **Path B — CoAP/UDP**
  `Raspberry Pi → CoAP over UDP → Local Server`

The two architectures are evaluated under controlled experimental conditions, with a focus on:

- end-to-end latency
- reliability
- protocol behavior
- security overhead
- scalability under increasing event rates

The system follows an **edge-computing approach**: video analysis and people tracking are performed locally on the Raspberry Pi, while only the resulting semantic movement events are transmitted through the IoT communication infrastructure.

---

## 🎯 Objectives

- Evaluate end-to-end communication latency.
- Measure Packet Delivery Ratio (PDR) and message losses.
- Compare a local edge/LAN architecture with a gateway-based cloud architecture.
- Investigate the impact of MQTT Quality of Service (QoS) levels.
- Evaluate communication behavior under increasing Events Per Second (EPS).
- Analyze the effects of BLE, Wi-Fi, UDP, MQTT, CoAP, and cloud connectivity.
- Evaluate the overhead associated with AES-GCM authenticated encryption.
- Measure CoAP Round-Trip Time (RTT).
- Provide reproducible experiments through dedicated stress-testing and logging scripts.

---

## 🏗️ System Architecture

The experimental testbed consists of three main nodes:

| Node | Role | Main Technologies |
|---|---|---|
| **Raspberry Pi** | Edge tracker and event producer | Python, YOLO, ByteTrack, BLE, CoAP |
| **ESP32 / Arduino Nano ESP32** | BLE-to-IP gateway | BLE, Wi-Fi, MQTT/TLS |
| **MacBook Pro** | Aggregation and measurement node | CoAP server, MQTT subscriber, metric collection |

### High-Level Architecture

```text
                    ┌─────────────────────────┐
                    │      Raspberry Pi       │
                    │       Edge Node         │
                    │  YOLO + ByteTrack       │
                    │  Zone Detection         │
                    │  Event Generation       │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
             PATH A                           PATH B
          (BLE + MQTT/TLS)                 (CoAP/UDP)
                │                                 │
                ▼                                 ▼
         ┌─────────────┐                   ┌─────────────┐
         │     BLE     │                   │  CoAP/UDP   │
         └──────┬──────┘                   └──────┬──────┘
                │                                 │
                ▼                                 │
         ┌─────────────┐                          │
         │    ESP32    │                          │
         │   Gateway   │                          │
         └──────┬──────┘                          │
                │ Wi-Fi                           │
                ▼                                 ▼
         ┌─────────────┐                   ┌─────────────┐
         │  MQTT/TLS   │                   │    CoAP     │
         │ Cloud Broker│                   │   Server    │
         └──────┬──────┘                   │  (MacBook)  │
                │ WAN                      └─────────────┘
                ▼
         ┌─────────────┐
         │    MQTT     │
         │  Subscriber │
         │  (MacBook)  │
         └─────────────┘
```

---

## 🔀 Communication Paths

### Path A — BLE + MQTT/TLS

Path A implements an **edge-to-cloud communication architecture**:

```text
Raspberry Pi
     │
     │ Bluetooth Low Energy
     ▼
ESP32 Gateway
     │
     │ Wi-Fi
     ▼
MQTT over TLS
     │
     ▼
Cloud MQTT Broker
     │
     │ Internet / WAN
     ▼
MacBook MQTT Subscriber
```

The Raspberry Pi generates movement events and sends them to the ESP32 gateway through **Bluetooth Low Energy (BLE)**. The ESP32 forwards the event via Wi-Fi using **MQTT over TLS**. A cloud MQTT broker handles message distribution to the MacBook subscriber.

#### MQTT Quality of Service

| QoS | Delivery Semantics |
|---|---|
| **QoS 0** | At most once |
| **QoS 1** | At least once |
| **QoS 2** | Exactly once |

The experiments investigate the relationship between MQTT delivery semantics, communication overhead, and measured end-to-end latency.

---

### Path B — CoAP over UDP

Path B implements a **direct edge-to-LAN communication architecture**:

```text
Raspberry Pi
     │
     │ CoAP / UDP
     ▼
MacBook Pro
CoAP Server
```

The CoAP server:

1. Receives the request.
2. Decrypts the payload (when AES-GCM is enabled).
3. Extracts the sender timestamp.
4. Calculates the end-to-end latency.
5. Stores the event and associated metrics.
6. Returns a CoAP response.

The Raspberry Pi also measures the **Round-Trip Time (RTT)** of the CoAP request/response exchange.

---

## 🧠 Edge AI and Event Generation

The Raspberry Pi performs **people detection and tracking locally**, avoiding the need to transmit raw video to the cloud.

### Processing Pipeline

```text
RTSP Video Stream
        │
        ▼
Frame Acquisition
        │
        ▼
YOLO Object Detection
        │
        ▼
ByteTrack
        │
        ▼
Person Tracking
        │
        ▼
Zone Classification
        │
        ▼
Zone Transition Event
        │
        ▼
BLE / CoAP Transmission
```

Generated events describe semantic movements such as:

```text
Person 1053: Zone_A → Zone_D
```

Only the resulting event is transmitted — no video stream is ever sent over the network.

---

## 🔐 Security

The encrypted versions of the system use **AES-GCM (Advanced Encryption Standard – Galois/Counter Mode)** for authenticated encryption, providing:

- Confidentiality
- Integrity
- Authentication of the encrypted payload

```text
Plaintext Event
      │
      ▼
   AES-GCM
      │
      ▼
Encrypted Payload
      ├── Nonce (12 B)
      └── Ciphertext + Authentication Tag
```

The repository also includes **NO_AES** variants to evaluate the impact of cryptographic processing and payload overhead separately.

> **⚠️ Security Note**
> Credentials, broker passwords, shared keys, and other secrets must **not** be committed to Git.
> Use environment variables or local configuration files excluded via `.gitignore`.

---

## ⏱️ Time Synchronization

Accurate one-way latency measurements require synchronized clocks on all participating nodes.

The experimental setup uses:

- **chrony** on the Raspberry Pi
- **sntp** on the MacBook
- Public NTP servers (`pool.ntp.org`)

Before each measurement session, synchronize the MacBook:

```bash
sudo sntp -sS <raspberry-pi-ip>
```

Verify that the resulting clock offset is small relative to the latency being measured. No fixed artificial latency correction is applied to the final measurements.

---

## 📏 Performance Metrics

### End-to-End Latency

```text
Latency = Receive Timestamp − Send Timestamp
```

```python
latency_ms = (receive_time_ns - send_time_ns) / 1_000_000.0
```

The timestamp is assigned immediately before serialization and transmission, so the measured value represents **application-level end-to-end latency**.

### Packet Delivery Ratio (PDR)

```text
PDR = (Received Messages / Sent Messages) × 100
```

### CoAP Round-Trip Time (RTT)

```text
Raspberry Pi  →  CoAP Request  →  MacBook
Raspberry Pi  ←  CoAP Response ←  MacBook
```

RTT is reported as a separate metric, distinct from one-way end-to-end latency.

### MQTT QoS Latency

The end-to-end latency for Path A is measured from the sender-side timestamp (Raspberry Pi) to subscriber reception (MacBook), representing the latency of the **complete BLE + MQTT communication path**.

---

## 🧪 Stress Testing

The stress test progressively increases the offered load in **Events Per Second (EPS)**:

```text
5 EPS → 10 EPS → 15 EPS → 20 EPS → ... → 50 EPS
```

For each operating point the system is evaluated in terms of:

- transmitted and received events
- packet losses and PDR
- latency distribution (min, avg, p50, p95, p99)
- CoAP RTT
- protocol behavior under increasing load

The methodology identifies performance degradation, saturation conditions, and packet loss **experimentally**, without assuming a theoretical saturation point.

---

## 📁 Repository Structure

```text
.
├── arduinoNanoESP32_gateway/
│   └── arduinonanoesp32_gateway.ino
│
├── arduinoNanoESP32_gateway_NO_AES/
│   └── arduinonanoesp32_gateway_NO_AES.ino
│
├── edge_ai/
│   ├── output/
│   ├── videos/
│   └── zone_picker.py
│
├── esp32_gateway/
│   └── esp32_gateway.ino
│
├── esp32_gateway_NO_AES/
│   └── esp32_gateway_NO_AES.ino
│
├── esp32_qos_gateway/
│   └── esp32_qos_gateway.ino
│
├── path_a_mqtt/
│   ├── mqtt_subscriber.py
│   ├── mqtt_subscriber_NO_AES.py
│   └── mqtt_subscriber_qos.py
│
├── path_b_coap/
│   ├── coap_server.py
│   ├── coap_server_NO_AES.py
│   └── coap_server_stress_test.py
│
├── Raspberry_deploy/
│   ├── requirements.txt
│   ├── stress_test.py
│   ├── stress_test_intervalli_graduali.py
│   ├── tracker.py
│   ├── tracker_NO_AES.py
│   └── yolo11s.pt
│
├── .env.example
├── .gitignore
├── Proposta di Progetto.docx
└── README.md
```

---

## 📦 Component Overview

| Component | Purpose |
|---|---|
| `arduinoNanoESP32_gateway/` | Arduino Nano ESP32 BLE-to-MQTT gateway |
| `arduinoNanoESP32_gateway_NO_AES/` | Arduino Nano ESP32 gateway without AES-GCM |
| `esp32_gateway/` | Standard ESP32 BLE-to-MQTT gateway |
| `esp32_gateway_NO_AES/` | ESP32 gateway without AES-GCM |
| `esp32_qos_gateway/` | ESP32 gateway for MQTT QoS experiments |
| `edge_ai/` | Edge-AI utilities, videos, and experimental outputs |
| `path_a_mqtt/` | MQTT subscribers and QoS evaluation scripts |
| `path_b_coap/` | CoAP servers and stress-testing scripts |
| `Raspberry_deploy/` | Raspberry Pi deployment, tracking, and stress-testing |
| `yolo11s.pt` | YOLO model used by the edge tracking pipeline |
| `Proposta di Progetto.docx` | Original project proposal |

---

## ⚙️ Requirements

**Python 3.9+** is required. Main dependencies:

```text
aiocoap
bleak
paho-mqtt
cryptography
opencv-python
numpy
ultralytics
```

The full Raspberry Pi environment is documented in `Raspberry_deploy/requirements.txt`.

---

## 🚀 Installation

**1. Clone the repository**

```bash
git clone https://github.com/giugiu39/Networking-Aspects-of-IoT-MQTT-QoS-Analysis-in-an-Edge-AI-Surveillance-System.git
cd Networking-Aspects-of-IoT-MQTT-QoS-Analysis-in-an-Edge-AI-Surveillance-System
```

**2. Create and activate a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

**3. Install dependencies**

```bash
pip install -r Raspberry_deploy/requirements.txt
```

**4. Configure credentials**

```bash
cp .env.example .env
# Edit .env with your HiveMQ credentials — never commit this file
```

---

## ▶️ Running the System

### 1. Synchronize the clocks

```bash
sudo sntp -sS <raspberry-pi-ip>
```

### 2. Start the CoAP server (MacBook)

```bash
python path_b_coap/coap_server.py

# For the stress-test variant:
python path_b_coap/coap_server_stress_test.py
```

### 3. Start the MQTT subscriber (MacBook)

```bash
python path_a_mqtt/mqtt_subscriber.py

# For QoS experiments:
python path_a_mqtt/mqtt_subscriber_qos.py --qos 0
python path_a_mqtt/mqtt_subscriber_qos.py --qos 1
python path_a_mqtt/mqtt_subscriber_qos.py --qos 2
```

### 4. Start the edge tracker (Raspberry Pi)

```bash
cd Raspberry_deploy
python tracker.py --source "rtsp://<camera-ip>:8554/live" --no-show
```

### 5. Run the stress tests (Raspberry Pi)

```bash
cd Raspberry_deploy

# Standard stress test
python stress_test.py

# Incremental stress test
python stress_test_intervalli_graduali.py
```

---

## 📊 Experimental Evaluation

### Path B — CoAP / LAN

The direct CoAP/LAN path avoids the BLE gateway and cloud/WAN segment. In the tested local-network configuration this architecture produced low communication latency and high delivery reliability.

### Path A — BLE + MQTT / Cloud

The BLE + MQTT architecture introduces additional communication stages:

```text
BLE → ESP32 Gateway → Wi-Fi → TLS → Cloud Broker → WAN → Subscriber
```

Measured end-to-end latency is affected by the combined behaviour of BLE, gateway processing, Wi-Fi, TLS, MQTT, cloud-broker routing, and Internet/WAN conditions.

### Load Dependence

Under increasing event rates, the system can experience increased queueing, wireless-interface contention, buffer pressure, higher latency, and packet losses. The stress-test scripts identify these behaviours experimentally.

> **📝 Experimental Note**
> Measured values depend on the specific hardware, firmware, software versions, wireless environment, broker configuration, geographic location, and workload. They should be interpreted as results of this testbed, not as universal protocol benchmarks.

---

## 📂 Experimental Outputs

Events and measurements are stored in **JSONL** format under `edge_ai/output/`.

A typical record:

```json
{
  "event_id": 1,
  "person_id": 123,
  "from_zone": "Zone_A",
  "to_zone": "Zone_D",
  "event": "zone_transition",
  "path": "CoAP",
  "latency_ms": 12.345
}
```

Output files can be processed to compute: min, max, mean, median, standard deviation, p95, p99, PDR, and RTT.

---

## 🔬 Reproducibility

For meaningful comparisons, maintain consistent: hardware configuration, firmware version, Python environment, wireless network, MQTT broker and region, QoS level, CoAP configuration, encryption configuration, event-generation rate, video/RTSP source, clock synchronization procedure, and experiment duration.

---

## 🛠️ Technologies

| Category | Technologies |
|---|---|
| **Programming** | Python, C++ / Arduino |
| **Edge Computing** | Raspberry Pi |
| **Embedded Systems** | ESP32, Arduino Nano ESP32 |
| **Computer Vision** | YOLO, ByteTrack, OpenCV |
| **Wireless Communication** | BLE, Wi-Fi |
| **IoT Protocols** | MQTT, MQTT/TLS, CoAP, UDP |
| **Security** | AES-GCM, TLS |
| **Cloud** | HiveMQ Cloud |
| **Streaming** | RTSP |
| **Network Analysis** | Wireshark, TShark |
| **Time Synchronization** | chrony, sntp |

---

## 🎓 Academic Context

This project was developed within the academic activities of the **Networking and IoT Systems** course at the University of Calabria.

It integrates concepts from: Internet of Things, edge computing, wireless and IP networking, application-layer communication protocols, distributed systems, network performance evaluation, network security, real-time event communication, and edge-based artificial intelligence.

---

## 👥 Authors

**Gianluca Perrotta** · **Marco Macrì** · **Orazio Ruberto** · **Asrar**

**University of Calabria — DIMES**
Department of Computer, Modeling, Electronics, and Systems Engineering

---

## 📄 License

This repository was developed for **academic and research purposes**.
The source code is intended for educational use, experimentation, research, and reproducibility of the presented testbed.
