import cv2
import numpy as np
import json
import time
from ultralytics import YOLO
from collections import defaultdict


# ── CONFIGURAZIONE ZONE ───────────────────────────────────────────────────────
# Definisci le zone come poligoni (x, y) in pixel
# Queste vanno calibrate sul tuo video specifico
# Esempio: video 1280x720, diviso in 3 zone verticali

def define_zones(frame_width, frame_height):

    zones = {

        # ─────────────────────────────────────────────
        # ZONA A
        # ─────────────────────────────────────────────
        "Zone_A": np.array([
            [4,   346],
            [5,   479],
            [281, 479],
            [275, 215],
            [177, 228]
        ], dtype=np.int32),

        # ─────────────────────────────────────────────
        # ZONA B
        # ─────────────────────────────────────────────
        "Zone_B": np.array([
            [275, 347],
            [281, 479],
            [435, 479],
            [435, 331]
        ], dtype=np.int32),

        # ─────────────────────────────────────────────
        # ZONA C
        # ─────────────────────────────────────────────
        "Zone_C": np.array([
            [435, 331],
            [435, 479],
            [565, 479],
            [565, 331]
        ], dtype=np.int32),

        # ─────────────────────────────────────────────
        # ZONA D
        # ─────────────────────────────────────────────
        "Zone_D": np.array([
            [275, 215],
            [435, 184],
            [565, 184],
            [565, 331],
            [435, 331],
            [275, 347]
        ], dtype=np.int32),
    }

    return zones

# ── ZONE UTILITIES ────────────────────────────────────────────────────────────

def get_zone(point, zones):
    """
    Restituisce il nome della zona in cui si trova il punto (x, y).
    Usa il centro-basso del bounding box (piedi della persona).
    """
    for zone_name, polygon in zones.items():
        if cv2.pointPolygonTest(polygon, point, False) >= 0:
            return zone_name
    return None  # fuori da tutte le zone


def draw_zones(frame, zones):
    """Disegna le zone sul frame con colori distinti."""
    colors = {
        "Zone_A": (255, 100, 100),  # blu
        "Zone_B": (100, 255, 100),  # verde
        "Zone_C": (100, 100, 255),  # rosso
        "Zone_D": (255, 255, 100),  # giallo
    }
    overlay = frame.copy()
    for zone_name, polygon in zones.items():
        color = colors.get(zone_name, (200, 200, 200))
        cv2.fillPoly(overlay, [polygon], color)
        # Label zona
        cx = int(polygon[:, 0].mean())
        cy = int(polygon[:, 1].mean())
        cv2.putText(frame, zone_name, (cx - 40, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    # Blend trasparente
    cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
    for polygon in zones.values():
        cv2.polylines(frame, [polygon], True, (255, 255, 255), 2)


# ── EVENT GENERATOR ───────────────────────────────────────────────────────────

class EventGenerator:
    """
    Tiene traccia della zona di ogni persona e genera eventi
    quando una persona cambia zona.
    """

    def __init__(self, log_path="edge_ai/output/events.jsonl"):
        self.person_zones = {}   # person_id → zona corrente
        self.events = []
        self.log_path = log_path
        open(log_path, "w").close()  # reset file

    def update(self, person_id, current_zone, confidence=1.0):
        """
        Aggiorna la zona di una persona.
        Se è cambiata, genera un evento.
        """
        previous_zone = self.person_zones.get(person_id)

        if previous_zone is None:
            # Prima volta che vediamo questa persona
            self.person_zones[person_id] = current_zone
            return None

        if current_zone != previous_zone and current_zone is not None:
            # Transizione di zona — genera evento
            event = {
                "person_id": int(person_id),
                "from_zone": previous_zone,
                "to_zone": current_zone,
                "ts_send_ns": time.time_ns(),
                "confidence": round(float(confidence), 2)
            }
            self.person_zones[person_id] = current_zone
            self.events.append(event)
            self._log(event)
            return event

        return None

    def _log(self, event):
        """Salva l'evento su file JSONL."""
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def remove_person(self, person_id):
        """Rimuovi persona persa dal tracker."""
        self.person_zones.pop(person_id, None)


# ── MAIN TRACKER ──────────────────────────────────────────────────────────────

def run_tracker(video_source=0, show=True):
    """
    video_source: 0 = webcam, oppure path al video locale
    """
    # Carica modello YOLO
    print("[tracker] Loading YOLOv8s...")
    model = YOLO("yolov8s.pt")  # scarica automaticamente al primo avvio

    # Apri sorgente video
    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"[tracker] ERROR: cannot open video source: {video_source}")
        return

    frame_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps          = cap.get(cv2.CAP_PROP_FPS) or 25
    print(f"[tracker] Video: {frame_width}x{frame_height} @ {fps:.1f} fps")

    # Definisci zone
    zones = define_zones(frame_width, frame_height)

    # Event generator
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

        # ── YOLO inference + ByteTrack ──────────────────────────────────────
        results = model.track(
            frame,
            persist=True,
            classes=[0],
            conf=0.30,
            iou=0.5,
            imgsz=960,
            tracker="bytetrack.yaml",
            verbose=False
        )
        # ── Disegna zone ────────────────────────────────────────────────────
        draw_zones(frame, zones)

        current_ids = set()

        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes      = results[0].boxes.xyxy.cpu().numpy()    # [x1,y1,x2,y2]
            track_ids  = results[0].boxes.id.cpu().numpy()
            confs      = results[0].boxes.conf.cpu().numpy()

            for box, track_id, conf in zip(boxes, track_ids, confs):
                x1, y1, x2, y2 = map(int, box)
                tid = int(track_id)
                current_ids.add(tid)

                # Piedi della persona = centro-basso del bbox
                foot_x = (x1 + x2) // 2
                foot_y = y2
                foot_point = (foot_x, foot_y)

                # Zona corrente
                zone = get_zone(foot_point, zones)

                # Genera evento se cambia zona
                event = ev_gen.update(tid, zone, conf)
                if event:
                    print(f"[EVENT] Person {tid}: {event['from_zone']} → {event['to_zone']}")
                    # TODO Fase 2: qui chiamerai il publisher MQTT/CoAP

                # ── Disegna bounding box e info ─────────────────────────────
                color = (0, 255, 0) if zone else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                label = f"{tid}"
                cv2.putText(frame, label, (x1, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

                # Punto piedi
                cv2.circle(frame, foot_point, 5, (0, 255, 255), -1)

        # Rimuovi persone perse
        lost_ids = active_ids - current_ids
        for lid in lost_ids:
            ev_gen.remove_person(lid)
        active_ids = current_ids

        # ── HUD ─────────────────────────────────────────────────────────────
        cv2.putText(frame, f"Frame: {frame_count}", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"People: {len(current_ids)}", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Events: {len(ev_gen.events)}", (10, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        if show:
            cv2.imshow("People Tracker", frame)
            elapsed = time.time() - frame_start
            wait_ms = max(1, int((1.0 / fps - elapsed) * 1000))
            if cv2.waitKey(wait_ms) & 0xFF == ord('q'):
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
                    help="Disabilita la finestra video (utile su Raspberry headless)")
    args = ap.parse_args()

    run_tracker(
        video_source=args.source,
        show=not args.no_show
    )