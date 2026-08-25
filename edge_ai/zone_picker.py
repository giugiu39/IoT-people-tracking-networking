"""
Zone picker — mostra il frame a 5 secondi e
permette di cliccare per ottenere le coordinate.
Premi Q per uscire.
"""

import cv2

VIDEO = "edge_ai/videos/mall.mp4"

cap = cv2.VideoCapture(VIDEO)

if not cap.isOpened():
    print("Errore apertura video")
    exit()

# Vai a 5 secondi dall'inizio
cap.set(cv2.CAP_PROP_POS_MSEC, 5000)

ret, frame = cap.read()
cap.release()

if not ret:
    print("Errore lettura frame a 5 secondi")
    exit()

h, w = frame.shape[:2]

print(f"Frame size: {w}x{h}")
print("Frame selezionato: 5 secondi")
print("Clicca sul frame per vedere le coordinate.")
print("Premi Q per uscire.")


def on_click(event, x, y, flags, param):

    if event == cv2.EVENT_LBUTTONDOWN:

        print(f"  click → x={x}, y={y}")

        cv2.circle(
            frame,
            (x, y),
            5,
            (0, 0, 255),
            -1
        )

        cv2.putText(
            frame,
            f"({x},{y})",
            (x + 8, y - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 255),
            1
        )

        cv2.imshow(
            "Zone Picker",
            frame
        )


cv2.imshow(
    "Zone Picker",
    frame
)

cv2.setMouseCallback(
    "Zone Picker",
    on_click
)


while True:

    if cv2.waitKey(0) & 0xFF == ord("q"):
        break


cv2.destroyAllWindows()