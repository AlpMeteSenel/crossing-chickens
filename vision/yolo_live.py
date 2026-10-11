#!/usr/bin/env python3
"""SWARMFLOW YOLO worker: int8 yolo26n -> /tmp/swarm_dets.json (frame + boxes).
Camera first, test-image fallback until TASK-001 (STREAMON -32) is fixed."""
import time, json, base64, cv2
from ultralytics import YOLO

MODEL = "/home/arduino/yolo26n_int8.onnx"
OUT = "/tmp/swarm_dets.json"
TARGET_FPS = 4

m = YOLO(MODEL)
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
test = cv2.imread("/home/arduino/swarm/shared/collector/bus.jpg")
if test is None:
    import numpy as np
    test = (cv2.randn((480, 640, 3), 100, 60).astype("uint8"))

while True:
    t0 = time.time()
    ok, frame = cap.read()
    src = "camera"
    if not ok or frame is None:
        frame, src = test, "bus.jpg-test"
    r = m.predict(frame, imgsz=640, conf=0.4, verbose=False)[0]
    dets = [
        {"cls": r.names[int(c)], "conf": round(min(float(cf), 1.0), 2),
         "box": [round(float(v), 1) for v in b]}
        for c, cf, b in zip(r.boxes.cls, r.boxes.conf, r.boxes.xyxy)
    ]
    ok2, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 72])
    payload = {
        "ts": time.time(), "src": src,
        "w": int(frame.shape[1]), "h": int(frame.shape[0]),
        "fps": round(1 / max(time.time() - t0, 0.001), 1),
        "dets": dets,
        "frame": base64.b64encode(jpg.tobytes()).decode() if ok2 else None,
    }
    with open(OUT, "w") as f:
        json.dump(payload, f)
    time.sleep(max(0.0, 1 / TARGET_FPS - (time.time() - t0)))
