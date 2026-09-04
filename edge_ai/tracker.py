import cv2
import numpy as np
import json
import time
import threading
import asyncio
import aiocoap
from ultralytics import YOLO
from collections import defaultdict
from bleak import BleakScanner, BleakClient

# ── 1. CLASSE PER IL CLIENT COAP ASINCRONO (Path B) ───────────────────────────
class CoapSenderThread(threading.Thread):
    def __init__(self, server_uri="coap://192.168.1.91/tracking"):
        super().__init__()
        self.server_uri = server_uri
        self.loop = asyncio.new_event_loop()
        self.queue = None  
        self.daemon = True 

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.queue = asyncio.Queue()  
        self.loop.run_until_complete(self.process_events())

    async def process_events(self):
        context = await aiocoap.Context.create_client_context()
        print(f"[CoAP Client] Pronta all'invio asincrono verso {self.server_uri}...")
        
        while True:
            event_data = await self.queue.get()
            payload = json.dumps(event_data).encode('utf-8')
            
            request = aiocoap.Message(code=aiocoap.POST, 
                                      payload=payload, 
                                      uri=self.server_uri,
                                      mtype=aiocoap.CON)
            try:
                response = await context.request(request).response
                print(f"   [CoAP Success] Evento {event_data['event_id']} consegnato (Risposta: {response.code})")
            except Exception as e:
                print(f"   [CoAP Error] Rete fallita per evento {event_data['event_id']}: {e}")

    def send_event(self, event_data):
        if self.queue is not None:
            self.loop.call_soon_threadsafe(self.queue.put_nowait, event_data)


# ── 2. CLASSE PER IL CLIENT BLE ASINCRONO (Path A) ────────────────────────────
class BleSenderThread(threading.Thread):
    def __init__(self, device_name="ESP32_Gateway_IoT", char_uuid="12345678-1234-1234-1234-123456789001"):
        super().__init__()
        self.device_name = device_name
        self.char_uuid = char_uuid
        self.loop = asyncio.new_event_loop()
        self.queue = None
        self.daemon = True

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.queue = asyncio.Queue()
        self.loop.run_until_complete(self.maintain_connection_and_send())

    async def maintain_connection_and_send(self):
        print(f"[BLE Client] Avvio gestione persistente verso {self.device_name}...")
        
        while True:
            try:
                # 1. Cerca e connettiti UNA VOLTA (resta agganciato)
                device = await BleakScanner.find_device_by_name(self.device_name, timeout=5.0)
                if not device:
                    print(f"   [BLE Warning] Gateway non trovato. Riprovo tra 2 secondi...")
                    await asyncio.sleep(2)
                    continue

                print(f"   [BLE Info] Connessione persistente stabilita con {device.address}")
                async with BleakClient(device) as client:
                    while client.is_connected:
                        # Prende l'evento dalla coda in tempo reale
                        event_data = await self.queue.get()
                        payload = json.dumps(event_data).encode('utf-8')
                        
                        # Scrittura istantanea senza rifare l'handshake
                        await client.write_gatt_char(self.char_uuid, payload)
                        print(f"   [BLE Success] Evento {event_data['event_id']} spedito via BLE")
                        
            except Exception as e:
                print(f"   [BLE Error] Connessione persa o errore: {e}. Riconnessione in corso...")
                await asyncio.sleep(1)

    def send_event(self, event_data):
        if self.queue is not None:
            self.loop.call_soon_threadsafe(self.queue.put_nowait, event_data)


# ── CONFIGURAZIONE ZONE E GRAFICA LASER ───────────────────────────────────────
def define_zones(frame_width, frame_height):
    zones = {
        "Zone_A": np.array([[4, 346], [5, 479], [281, 479], [275, 215], [177, 228]], dtype=np.int32),
        "Zone_B": np.array([[275, 347], [281, 479], [435, 479], [435, 331]], dtype=np.int32),
        "Zone_C": np.array([[435, 331], [435, 479], [565, 479], [565, 331]], dtype=np.int32),
        "Zone_D": np.array([[275, 215], [435, 184], [565, 184], [565, 331], [435, 331], [275, 347]], dtype=np.int32),
    }
    return zones

def get_zone(point, zones):
    for zone_name, polygon in zones.items():
        if cv2.pointPolygonTest(polygon, point, False) >= 0:
            return zone_name
    return None

def draw_zones(frame, zones):
    colors = {
        "Zone_A": (255, 100, 100),
        "Zone_B": (100, 255, 100),
        "Zone_C": (100, 100, 255),
        "Zone_D": (255, 255, 100),
    }
    overlay = frame.copy()
    for zone_name, polygon in zones.items():
        color = colors.get(zone_name, (200, 200, 200))
        cv2.fillPoly(overlay, [polygon], color)
        cx = int(polygon[:, 0].mean())
        cy = int(polygon[:, 1].mean())
        cv2.putText(frame, zone_name, (cx - 40, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
    for polygon in zones.values():
        cv2.polylines(frame, [polygon], True, (255, 255, 255), 2)

def draw_laser_bbox(frame, x1, y1, x2, y2, color=(0, 255, 255), thickness=1, length=15):
    l_type = cv2.LINE_AA 
    cv2.line(frame, (x1, y1), (x1 + length, y1), color, thickness, l_type)
    cv2.line(frame, (x1, y1), (x1, y1 + length), color, thickness, l_type)
    cv2.line(frame, (x2, y1), (x2 - length, y1), color, thickness, l_type)
    cv2.line(frame, (x2, y1), (x2, y1 + length), color, thickness, l_type)
    cv2.line(frame, (x1, y2), (x1 + length, y2), color, thickness, l_type)
    cv2.line(frame, (x1, y2), (x1, y2 - length), color, thickness, l_type)
    cv2.line(frame, (x2, y2), (x2 - length, y2), color, thickness, l_type)
    cv2.line(frame, (x2, y2), (x2, y2 - length), color, thickness, l_type)
    
    feet_x = int((x1 + x2) / 2)
    feet_y = int(y2)
    cv2.line(frame, (feet_x - 6, feet_y - 6), (feet_x + 6, feet_y + 6), (0, 0, 255), thickness, l_type)
    cv2.line(frame, (feet_x - 6, feet_y + 6), (feet_x + 6, feet_y - 6), (0, 0, 255), thickness, l_type)


# ── EVENT GENERATOR ───────────────────────────────────────────────────────────
class EventGenerator:
    def __init__(self, log_path="edge_ai/output/events.jsonl"):
        self.person_zones = {}   
        self.events = []
        self.log_path = log_path
        self.event_counter = 0  
        open(log_path, "w").close() 

    def update(self, person_id, current_zone, confidence=1.0):
        previous_zone = self.person_zones.get(person_id)

        if previous_zone is None:
            self.person_zones[person_id] = current_zone
            return None

        if current_zone != previous_zone and current_zone is not None:
            self.event_counter += 1
            event = {
                "event_id": self.event_counter,
                "person_id": int(person_id),
                "from_zone": previous_zone,
                "to_zone": current_zone,
                "event": f"{previous_zone} -> {current_zone}", 
                "ts_send_ns": time.time_ns(),
                "confidence": round(float(confidence), 2)
            }
            self.person_zones[person_id] = current_zone
            self.events.append(event)
            self._log(event)
            return event

        return None

    def _log(self, event):
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def remove_person(self, person_id):
        self.person_zones.pop(person_id, None)


# ── MAIN TRACKER ──────────────────────────────────────────────────────────────
def run_tracker(video_source=0, show=True):
    # Avvia i thread asincroni per ENTRAMBI i percorsi di rete (Dual-Path)
    coap_thread = CoapSenderThread(server_uri="coap://192.168.1.91/tracking")
    coap_thread.start()

    ble_thread = BleSenderThread(device_name="ESP32_Gateway_IoT")
    ble_thread.start()

    print("[tracker] Loading yolo11s...")
    model = YOLO("yolo11s.pt")  

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"[tracker] ERROR: cannot open video source: {video_source}")
        return

    frame_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps          = cap.get(cv2.CAP_PROP_FPS) or 25
    print(f"[tracker] Video: {frame_width}x{frame_height} @ {fps:.1f} fps")

    zones = define_zones(frame_width, frame_height)
    ev_gen = EventGenerator()
    frame_count = 0
    active_ids  = set()

    print("[tracker] Running... Press Q to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[tracker] End of video.")
            break

        frame_count += 1
        frame_start = time.time()

        results = model.track(
            frame, persist=True, device='mps', classes=[0],
            conf=0.30, iou=0.5, imgsz=960, tracker="bytetrack.yaml", verbose=False
        )
        
        draw_zones(frame, zones)
        current_ids = set()

        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes      = results[0].boxes.xyxy.cpu().numpy()    
            track_ids  = results[0].boxes.id.cpu().numpy()
            confs      = results[0].boxes.conf.cpu().numpy()

            for box, track_id, conf in zip(boxes, track_ids, confs):
                x1, y1, x2, y2 = map(int, box)
                tid = int(track_id)
                current_ids.add(tid)

                foot_x = (x1 + x2) // 2
                foot_y = y2
                foot_point = (foot_x, foot_y)

                zone = get_zone(foot_point, zones)
                event = ev_gen.update(tid, zone, conf)
                
                if event:
                    print(f"\n[EVENT] Person {tid}: {event['from_zone']} → {event['to_zone']}")
                    # INVIO DUAL-PATH: Invia contemporaneamente su CoAP (Path B) e BLE/MQTT (Path A)
                    coap_thread.send_event(event)
                    ble_thread.send_event(event)

                color = (0, 255, 255) if zone else (200, 200, 200)
                draw_laser_bbox(frame, x1, y1, x2, y2, color=color, thickness=1, length=15)
                cv2.putText(frame, f"ID:{tid}", (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        lost_ids = active_ids - current_ids
        for lid in lost_ids:
            ev_gen.remove_person(lid)
        active_ids = current_ids

        cv2.putText(frame, f"Frame: {frame_count}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"People: {len(current_ids)}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Events: {len(ev_gen.events)}", (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        if show:
            cv2.imshow("People Tracker", frame)
            if cv2.waitKey(33) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

    print(f"\n[tracker] Done. Total events generated: {len(ev_gen.events)}")
    print(f"[tracker] Events saved to: {ev_gen.log_path}")
    return ev_gen.events


# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="edge_ai/videos/mall.mp4",
                    help="Video source: path al file oppure 0 per webcam")
    ap.add_argument("--no-show", action="store_true",
                    help="Disabilita la finestra video")
    args = ap.parse_args()

    run_tracker(
        video_source=args.source,
        show=not args.no_show
    )