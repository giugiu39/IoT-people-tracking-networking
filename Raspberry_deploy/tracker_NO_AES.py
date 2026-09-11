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
import os
import queue

# CLASSE PER IL LETTORE ASINCRONO DI STREAM RTSP (Previene saturazione buffer MediaMTX)
class RTSPVideoReader:
    def __init__(self, src):
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
        self.cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
        self.q = queue.Queue(maxsize=1)
        self.stopped = False
        self.thread = threading.Thread(target=self._update, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def _update(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret:
                self.stopped = True
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait() # Scarta il frame vecchio
                except queue.Empty:
                    pass
            self.q.put(frame) # Mantiene solo l'ultimo frame disponibile

    def read(self):
        if self.stopped and self.q.empty():
            return False, None
        return True, self.q.get()

    def release(self):
        self.stopped = True
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.cap.release()

# CLASSE PER IL CLIENT COAP ASINCRONO (Path B - NO_AES)
class CoapSenderThread(threading.Thread):
    def __init__(self, server_uri="coap://192.168.1.62/tracking"):
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
        print(f"[CoAP Client] Pronto all'invio asincrono (NO_AES) verso {self.server_uri}...")
    
        while True:
            event_data = await self.queue.get()
        
            # Payload in chiaro (JSON) senza cifratura AES-GCM
            payload = json.dumps(event_data).encode('utf-8')
        
            request = aiocoap.Message(code=aiocoap.POST, 
                                      payload=payload, 
                                      uri=self.server_uri,
                                      mtype=aiocoap.CON)
            try:
                # 1. Timestamp locale prima dell'invio (Raspberry Pi Clock)
                t_start = time.time_ns()
            
                # 2. Invio e attesa della conferma (ACK dal Server CoAP)
                response = await context.request(request).response
            
                # 3. Timestamp locale dopo la ricezione dell'ACK (Raspberry Pi Clock)
                t_end = time.time_ns()
            
                # 4. Calcolo RTT
                rtt_ms = (t_end - t_start) / 1_000_000.0
            
                print(f"   [CoAP Success NO_AES] Evento {event_data['event_id']} consegnato | "
                      f"RTT: {rtt_ms:.3f} ms")
                  
            except Exception as e:
                print(f"   [CoAP Error] Rete fallita per evento {event_data['event_id']}: {e}")

    def send_event(self, event_data):
        if self.queue is not None:
            self.loop.call_soon_threadsafe(self.queue.put_nowait, event_data)

# CLASSE PER IL CLIENT BLE ASINCRONO (Path A - NO_AES)
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
        print(f"[BLE Client] Avvio gestione persistente (NO_AES) verso {self.device_name}...")
        while True:
            try:
                device = await BleakScanner.find_device_by_name(self.device_name, timeout=5.0)
                if not device:
                    await asyncio.sleep(2)
                    continue

                print(f"   [BLE Info] Connessione persistente stabilita con {device.address}")
                async with BleakClient(device) as client:
                    while client.is_connected:
                        event_data = await self.queue.get()
                        
                        # Payload in chiaro (JSON) senza cifratura AES-GCM
                        payload = json.dumps(event_data).encode('utf-8')
                        
                        await client.write_gatt_char(self.char_uuid, payload)
                        print(f"   [BLE Success NO_AES] Evento {event_data['event_id']} spedito via BLE")
                        
            except Exception as e:
                await asyncio.sleep(1)

    def send_event(self, event_data):
        if self.queue is not None:
            self.loop.call_soon_threadsafe(self.queue.put_nowait, event_data)

# CONFIGURAZIONE ZONE
def define_zones(frame_width, frame_height):
    return {
        "Zone_A": np.array([[4, 346], [5, 479], [281, 479], [275, 215], [177, 228]], dtype=np.int32),
        "Zone_B": np.array([[275, 347], [281, 479], [435, 479], [435, 331]], dtype=np.int32),
        "Zone_C": np.array([[435, 331], [435, 479], [565, 479], [565, 331]], dtype=np.int32),
        "Zone_D": np.array([[275, 215], [435, 184], [565, 184], [565, 331], [435, 331], [275, 347]], dtype=np.int32),
    }

def get_zone(point, zones):
    for zone_name, polygon in zones.items():
        if cv2.pointPolygonTest(polygon, point, False) >= 0:
            return zone_name
    return None

class EventGenerator:
    def __init__(self):
        self.person_zones = {}   
        self.events = []
        self.event_counter = 0  

    def update(self, person_id, current_zone):
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
                "ts_send_ns": time.time_ns()
            }
            self.person_zones[person_id] = current_zone
            self.events.append(event)
            return event
        return None

    def remove_person(self, person_id):
        self.person_zones.pop(person_id, None)

# MAIN TRACKER
def run_tracker(video_source=0, show=True):
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
    os.environ["OPENCV_LOG_LEVEL"] = "OFF"
    os.environ["AV_LOG_FORCE_NOCOLOR"] = "1"

    coap_thread = CoapSenderThread(server_uri="coap://192.168.1.62/tracking")
    coap_thread.start()

    ble_thread = BleSenderThread(device_name="ESP32_Gateway_IoT")
    ble_thread.start()

    print("[tracker] Loading yolo11n...")
    model = YOLO("yolo11n.pt")  

    stream = RTSPVideoReader(video_source).start()
    time.sleep(1.0) # Attesa stabilizzazione buffer

    zones = define_zones(854, 480)
    ev_gen = EventGenerator()
    frame_count = 0
    active_ids = set()

    print("[tracker] Running con Threaded RTSP Reader (NO_AES)... Press Q to quit.")

    while True:
        ret, frame = stream.read()
        if not ret or frame is None:
            print("[tracker] Fine dello stream video.")
            break

        frame_count += 1
        
        results = model.track(
            frame, persist=True, device='cpu', classes=[0],
            conf=0.30, iou=0.5, imgsz=480, tracker="bytetrack.yaml", verbose=False
        )
        
        current_ids = set()
        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()    
            track_ids = results[0].boxes.id.cpu().numpy()

            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = map(int, box)
                tid = int(track_id)
                current_ids.add(tid)

                foot_x = (x1 + x2) // 2
                foot_y = y2
                zone = get_zone((foot_x, foot_y), zones)
                event = ev_gen.update(tid, zone)
                
                if event:
                    print(f"\n[EVENT NO_AES] Person {tid}: {event['from_zone']} → {event['to_zone']}")
                    coap_thread.send_event(event)
                    ble_thread.send_event(event)

        lost_ids = active_ids - current_ids
        for lid in lost_ids:
            ev_gen.remove_person(lid)
        active_ids = current_ids

    stream.release()
    print(f"\n[tracker] Concluso. Eventi generati: {len(ev_gen.events)}")
    return ev_gen.events

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="rtsp://192.168.1.62:8554/live")
    ap.add_argument("--no-show", action="store_true")
    args = ap.parse_args()

    run_tracker(video_source=args.source, show=not args.no_show)