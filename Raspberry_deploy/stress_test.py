import asyncio
import json
import time
import threading
import argparse
import random
import os
import queue
import aiocoap
from bleak import BleakScanner, BleakClient
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── CONFIGURAZIONE AES-GCM ─────────────────────────────────────────────────
SHARED_AES_KEY = b"Networking_IoT_Project_Key_32B!!" 
AES_GCM_CIPHER = AESGCM(SHARED_AES_KEY)

ZONES = ["Zone_A", "Zone_B", "Zone_C", "Zone_D"]

# ── WORKER ASINCRONO COAP STRESS TEST ───────────────────────────────────────
async def coap_worker(worker_id, num_requests, server_uri, stats):
    context = await aiocoap.Context.create_client_context()
    
    for i in range(num_requests):
        from_z, to_z = random.sample(ZONES, 2)
        event_data = {
            "event_id": f"STRESS_COAP_{worker_id}_{i}",
            "person_id": random.randint(9000, 9999),
            "from_zone": from_z,
            "to_zone": to_z,
            "event": f"{from_z} -> {to_z}",
            "ts_send_ns": time.time_ns()
        }
        
        json_bytes = json.dumps(event_data).encode('utf-8')
        nonce = os.urandom(12)
        encrypted_data = AES_GCM_CIPHER.encrypt(nonce, json_bytes, None)
        payload = nonce + encrypted_data
        
        request = aiocoap.Message(code=aiocoap.POST, payload=payload, uri=server_uri, mtype=aiocoap.CON)
        
        t_start = time.time_ns()
        try:
            # Timeout di 3 secondi per rilevare la saturazione del server
            response = await asyncio.wait_for(context.request(request).response, timeout=3.0)
            t_end = time.time_ns()
            rtt_ms = (t_end - t_start) / 1_000_000.0
            
            stats["coap_success"] += 1
            stats["coap_rtt"].append(rtt_ms)
        except Exception as e:
            stats["coap_fail"] += 1
            
        await asyncio.sleep(random.uniform(0.01, 0.05)) # Micro-pausa tra le raffiche

# ── WORKER ASINCRONO BLE STRESS TEST ────────────────────────────────────────
async def ble_stress_producer(event_queue, num_workers, requests_per_worker):
    total_events = num_workers * requests_per_worker
    for i in range(total_events):
        from_z, to_z = random.sample(ZONES, 2)
        event_data = {
            "event_id": f"STRESS_BLE_{i}",
            "person_id": random.randint(9000, 9999),
            "from_zone": from_z,
            "to_zone": to_z,
            "event": f"{from_z} -> {to_z}",
            "ts_send_ns": time.time_ns()
        }
        await event_queue.put(event_data)
        await asyncio.sleep(0.01)

async def ble_worker_consumer(device_name, char_uuid, event_queue, stats, expected_total):
    print(f"[BLE Stress] Ricerca del gateway {device_name}...")
    device = await BleakScanner.find_device_by_name(device_name, timeout=5.0)
    if not device:
        print("[BLE Stress Error] Gateway ESP32 non trovato!")
        stats["ble_fail"] += expected_total
        return

    try:
        async with BleakClient(device) as client:
            print(f"[BLE Stress] Connesso a {device.address}. Inizio invio massivo...")
            processed = 0
            while processed < expected_total:
                try:
                    event_data = await asyncio.wait_for(event_queue.get(), timeout=3.0)
                except asyncio.TimeoutError:
                    break
                
                json_bytes = json.dumps(event_data).encode('utf-8')
                nonce = os.urandom(12)
                encrypted_data = AES_GCM_CIPHER.encrypt(nonce, json_bytes, None)
                payload = nonce + encrypted_data
                
                try:
                    await client.write_gatt_char(char_uuid, payload)
                    stats["ble_success"] += 1
                except Exception as e:
                    stats["ble_fail"] += 1
                
                processed += 1
                event_queue.task_done()
    except Exception as e:
        print(f"[BLE Stress Error] Connessione BLE interrotta/fallita: {e}")
        stats["ble_fail"] += (expected_total - stats["ble_success"])

# ── MAIN BENCHMARK ENGINE ───────────────────────────────────────────────────
async def main():
    parser = argparse.ArgumentParser(description="Stress Test Parallel Loading su CoAP e BLE")
    parser.add_argument("--workers", type=int, default=10, help="Numero di client/thread concorrenti")
    parser.add_argument("--reqs", type=int, default=20, help="Numero di richieste per worker")
    parser.add_argument("--coap-uri", default="coap://192.168.1.151/tracking", help="URI CoAP del Server")
    parser.add_argument("--ble-name", default="ESP32_Gateway_IoT", help="Nome BLE dell'ESP32")
    args = parser.parse_args()

    stats = {
        "coap_success": 0, "coap_fail": 0, "coap_rtt": [],
        "ble_success": 0, "ble_fail": 0
    }
    
    total_events = args.workers * args.reqs
    print("=================================================================")
    print(f" AVVIO STRESS TEST PARALLELO: {args.workers} Worker x {args.reqs} Req ({total_events} Eventi Totali)")
    print("=================================================================")

    # 1. Avvio Stress Test CoAP
    print("\n[1/2] Testando saturazione Path B (CoAP over UDP)...")
    coap_tasks = [
        coap_worker(w_id, args.reqs, args.coap_uri, stats) 
        for w_id in range(args.workers)
    ]
    t0 = time.time()
    await asyncio.gather(*coap_tasks)
    t_coap = time.time() - t0

    # 2. Avvio Stress Test BLE
    print("\n[2/2] Testando saturazione Path A (BLE GATT Char)...")
    ble_queue = asyncio.Queue()
    t0 = time.time()
    await asyncio.gather(
        ble_stress_producer(ble_queue, args.workers, args.reqs),
        ble_worker_consumer(args.ble_name, "12345678-1234-1234-1234-123456789001", ble_queue, stats, total_events)
    )
    t_ble = time.time() - t0

    # ── METRICHE E RISULTATI ────────────────────────────────────────────────
    avg_coap_rtt = sum(stats["coap_rtt"]) / len(stats["coap_rtt"]) if stats["coap_rtt"] else 0
    
    print("\n=================================================================")
    print(" RISULTATI DELLO STRESS TEST")
    print("=================================================================")
    print(f"PATH B (CoAP UDP):")
    print(f"  - Tempo totale completamento: {t_coap:.2f} s")
    print(f"  - Pacchetti Consegnati (Success): {stats['coap_success']} / {total_events} (PDR: {(stats['coap_success']/total_events)*100:.1f}%)")
    print(f"  - Pacchetti Persi/Timeout (Fail): {stats['coap_fail']}")
    print(f"  - RTT Medio durante lo Stress: {avg_coap_rtt:.2f} ms")
    print("-----------------------------------------------------------------")
    print(f"PATH A (BLE + MQTT Gateway):")
    print(f"  - Tempo totale completamento: {t_ble:.2f} s")
    print(f"  - Pacchetti Inviati via BLE (Success): {stats['ble_success']} / {total_events} (PDR: {(stats['ble_success']/total_events)*100:.1f}%)")
    print(f"  - Pacchetti Scartati/Falliti (Fail): {stats['ble_fail']}")
    print("=================================================================")

if __name__ == "__main__":
    asyncio.run(main())