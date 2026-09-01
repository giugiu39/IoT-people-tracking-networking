import asyncio
import json
import time
from bleak import BleakScanner, BleakClient

# Gli UUID devono corrispondere esattamente a quelli definiti nell'ESP32
SERVICE_UUID = "12345678-1234-1234-1234-123456789000"
CHARACTERISTIC_UUID = "12345678-1234-1234-1234-123456789001"
DEVICE_NAME = "ESP32_Gateway_IoT"

async def run():
    print(f"Scansione dispositivi BLE nelle vicinanze in corso...")
    
    # Cerca l'ESP32 per nome
    device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10.0)
    
    if not device:
        print(f"ERRORE: Dispositivo BLE '{DEVICE_NAME}' non trovato. Assicurati che l'ESP32 sia acceso e alimentato.")
        return

    print(f"Trovato! Connessione a {device.name} ({device.address})...")

    async with BleakClient(device) as client:
        if client.is_connected:
            print("Connessione BLE stabilita con successo!")
            
            # Prepariamo un payload JSON identico a quello del nostro tracker di YOLO
            test_event = {
                "event_id": 999,
                "person_id": 13,
                "from_zone": "Zone_C",
                "to_zone": "Zone_B",
                "ts_send_ns": time.time_ns(),
                "confidence": 0.92
            }
            
            payload_str = json.dumps(test_event)
            data_bytes = payload_str.encode('utf-8')
            
            print(f"Invio payload via BLE all'ESP32: {payload_str}")
            
            # Scrive i byte sulla caratteristica Bluetooth dell'ESP32
            await client.write_gatt_char(CHARACTERISTIC_UUID, data_bytes)
            print("Messaggio inviato con successo via BLE!")
            
            # Pausa per dare tempo all'ESP32 di inoltrarlo via MQTT
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(run())