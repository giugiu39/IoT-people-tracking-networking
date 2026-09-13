import asyncio
import json
import time
import random
import os
import aiocoap
from bleak import BleakScanner, BleakClient
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ── CONFIGURAZIONE ─────────────────────────────────────────────────────────

SHARED_AES_KEY = b"Networking_IoT_Project_Key_32B!!"
AES_GCM_CIPHER = AESGCM(SHARED_AES_KEY)

ZONES = ["Zone_A", "Zone_B", "Zone_C", "Zone_D"]

COAP_URI = "coap://192.168.1.81/tracking"

BLE_NAME = "ESP32_Gateway_IoT"
BLE_CHAR = "12345678-1234-1234-1234-123456789001"

# Configurazione basata su intervalli temporali fissi
TEST_STEPS = [
    {"name": "Step 1 (Basso)", "duration": 5, "eps": 5},
    {"name": "Step 2 (Medio)", "duration": 5, "eps": 15},
    {"name": "Step 3 (Alto)", "duration": 5, "eps": 30},
    {"name": "Step 4 (Stress BT)", "duration": 5, "eps": 50}
]


# ── WORKER ASINCRONO COAP ──────────────────────────────────────────────────

async def coap_time_injector(eps, duration, stats, step_idx, run_id):

    context = await aiocoap.Context.create_client_context()

    interval = 1.0 / eps
    t_end = time.time() + duration

    seq = 0

    while time.time() < t_end:

        t_loop_start = time.time()

        from_z, to_z = random.sample(ZONES, 2)

        seq += 1

        # Timestamp del SEND sul client
        ts_send_ns = time.time_ns()

        event_data = {
            "run_id": run_id,
            "step_id": step_idx,
            "seq": seq,

            "event_id": f"COAP_{run_id}_{step_idx}_{seq}",

            "person_id": random.randint(9000, 9999),

            "from_zone": from_z,
            "to_zone": to_z,

            "event": f"{from_z} -> {to_z}",

            "ts_send_ns": ts_send_ns
        }

        json_bytes = json.dumps(event_data).encode("utf-8")

        nonce = os.urandom(12)

        payload = nonce + AES_GCM_CIPHER.encrypt(
            nonce,
            json_bytes,
            None
        )

        request = aiocoap.Message(
            code=aiocoap.POST,
            payload=payload,
            uri=COAP_URI
        )

        request.transport_tuning.mtype = aiocoap.CON

        try:

            # IMPORTANTE:
            # NON misuriamo più il tempo totale request -> response.
            # Il server ci restituisce il proprio timestamp di ricezione.

            response = await asyncio.wait_for(
                context.request(request).response,
                timeout=2.0
            )

            # Il server deve restituire JSON:
            # {
            #     "event_id": "...",
            #     "ts_receive_ns": ...
            # }

            response_data = json.loads(
                response.payload.decode("utf-8")
            )

            if "ts_receive_ns" in response_data:

                ts_receive_ns = response_data["ts_receive_ns"]

                # ONE-WAY LATENCY
                latency_ms = (
                    ts_receive_ns - ts_send_ns
                ) / 1_000_000.0

                # Evita valori negativi dovuti a clock non sincronizzati
                if latency_ms >= 0:
                    stats["coap_latency"].append(latency_ms)
                    stats["coap_success"] += 1
                else:
                    stats["coap_invalid_timestamp"] += 1

            else:
                stats["coap_fail"] += 1

        except Exception:
            stats["coap_fail"] += 1

        # Pacing
        elapsed = time.time() - t_loop_start

        if elapsed < interval:
            await asyncio.sleep(interval)

    await context.shutdown()


# ── WORKER ASINCRONO BLE ───────────────────────────────────────────────────

async def ble_time_injector(
    client,
    char_uuid,
    eps,
    duration,
    stats,
    step_idx,
    run_id
):

    interval = 1.0 / eps
    t_end = time.time() + duration

    seq = 0

    while time.time() < t_end:

        t_loop_start = time.time()

        seq += 1

        # Timestamp del SEND
        ts_send_ns = time.time_ns()

        event_data = {
            "run_id": run_id,
            "step_id": step_idx,
            "seq": seq,

            "event_id": f"BLE_{run_id}_{step_idx}_{seq}",

            "ts_send_ns": ts_send_ns
        }

        json_bytes = json.dumps(event_data).encode("utf-8")

        nonce = os.urandom(12)

        payload = nonce + AES_GCM_CIPHER.encrypt(
            nonce,
            json_bytes,
            None
        )

        try:

            await client.write_gatt_char(
                char_uuid,
                payload,
                response=False
            )

            stats["ble_sent"] += 1

        except Exception:

            stats["ble_fail"] += 1

        # Pacing
        elapsed = time.time() - t_loop_start

        if elapsed < interval:
            await asyncio.sleep(interval)


# ── MAIN BENCHMARK ENGINE ──────────────────────────────────────────────────

async def main():

    # Identificatore univoco dell'intera esecuzione
    run_id = str(time.time_ns())

    print(f"Run ID: {run_id}")

    print(f"Ricerca del gateway BLE {BLE_NAME}...")

    device = await BleakScanner.find_device_by_name(
        BLE_NAME,
        timeout=5.0
    )

    if not device:

        print("[Errore] Gateway ESP32 non trovato!")

        return

    async with BleakClient(device) as ble_client:

        print(
            f"Connesso a {device.address}. "
            "Inizio Benchmark Temporale a Step...\n"
        )

        for step_idx, step in enumerate(TEST_STEPS, 1):

            duration = step["duration"]
            eps = step["eps"]

            expected_events = eps * duration

            stats = {

                # CoAP
                "coap_success": 0,
                "coap_fail": 0,
                "coap_latency": [],
                "coap_invalid_timestamp": 0,

                # BLE
                "ble_sent": 0,
                "ble_fail": 0
            }

            print(
                f"--- AVVIO {step_idx}: "
                f"{step['name']} "
                f"({eps} pacchetti/sec per {duration}s "
                f"-> {expected_events} eventi) ---"
            )

            t0 = time.time()

            # Esecuzione contemporanea dei due path
            await asyncio.gather(

                coap_time_injector(
                    eps,
                    duration,
                    stats,
                    step_idx,
                    run_id
                ),

                ble_time_injector(
                    ble_client,
                    BLE_CHAR,
                    eps,
                    duration,
                    stats,
                    step_idx,
                    run_id
                )
            )

            t_total = time.time() - t0

            # ---------------------------------------------------------------
            # COAP LATENCY STATISTICS
            # ---------------------------------------------------------------

            if stats["coap_latency"]:

                avg_coap = (
                    sum(stats["coap_latency"])
                    / len(stats["coap_latency"])
                )

                sorted_coap = sorted(
                    stats["coap_latency"]
                )

                median_coap = sorted_coap[
                    len(sorted_coap) // 2
                ]

            else:

                avg_coap = 0
                median_coap = 0

            # ---------------------------------------------------------------
            # PDR
            # ---------------------------------------------------------------

            pdr_coap = (
                stats["coap_success"]
                / expected_events
            ) * 100 if expected_events > 0 else 0

            pdr_ble_local = (
                stats["ble_sent"]
                / expected_events
            ) * 100 if expected_events > 0 else 0

            # ---------------------------------------------------------------
            # REPORT
            # ---------------------------------------------------------------

            print(
                "================================================================="
            )

            print(
                f" REPORT {step_idx}: "
                f"{step['name']} "
                f"({eps} EPS x {duration}s)"
            )

            print(
                "================================================================="
            )

            # PATH B
            print("PATH B (CoAP UDP):")

            print(
                f"  - Durata effettiva: "
                f"{t_total:.2f} s"
            )

            print(
                f"  - Consegnati: "
                f"{stats['coap_success']} / "
                f"{expected_events} "
                f"(PDR: {pdr_coap:.1f}%)"
            )

            print(
                f"  - Latenza One-Way Media: "
                f"{avg_coap:.2f} ms"
            )

            print(
                f"  - Latenza One-Way Mediana: "
                f"{median_coap:.2f} ms"
            )

            print(
                f"  - Timestamp non validi: "
                f"{stats['coap_invalid_timestamp']}"
            )

            print(
                "-----------------------------------------------------------------"
            )

            # PATH A
            print("PATH A (BLE + MQTT E2E):")

            print(
                f"  - Inviati via BLE: "
                f"{stats['ble_sent']} / "
                f"{expected_events} "
                f"({pdr_ble_local:.1f}%)"
            )

            print(
                f"  - Errori BLE: "
                f"{stats['ble_fail']}"
            )

            print(
                "  - Latenza BLE + MQTT E2E: "
                "calcolata dal subscriber MQTT"
            )

            print(
                "  - PDR BLE + MQTT E2E: "
                "calcolato dal subscriber MQTT"
            )

            print(
                "=================================================================\n"
            )

            if step_idx < len(TEST_STEPS):

                print(
                    "[Cooling] Pausa di raffreddamento "
                    "buffer di 8 secondi...\n"
                )

                await asyncio.sleep(8.0)


if __name__ == "__main__":
    asyncio.run(main())