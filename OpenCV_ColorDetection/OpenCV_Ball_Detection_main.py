import cv2
import numpy as np
import json
import time
import sys
import math

# --- KAMERA & KONSTANTEN (Auf absolute Leistung getrimmt) ---
cap = cv2.VideoCapture(0)
frame_w, frame_h = 160, 120    # <--- NEU: Ultra-Low-Res (75% weniger Rechenlast!)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_w)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_h)

Bw_deg = 62.2  # FOV der Pi Kamera V2
DEADZONE_PIXELS = 10           # <--- NEU: Halbiert, da das Bild kleiner ist

# Raster für die Übertragung an den PC
GRID_W, GRID_H = 30, 30

# DEINE FESTEN HSV-WERTE
lower_bound = np.array([0, 118, 153])
upper_bound = np.array([18, 238, 255])

try:
    while True:
        ret, frame = cap.read()
        if not ret: 
            time.sleep(0.05)
            continue

        # 1. Bild filtern (Geht jetzt rasend schnell!)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        
        # Leichte Filterung (bei so kleinen Bildern reicht 1 Iteration völlig)
        mask = cv2.erode(mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=1)

        # --- TELEMETRIE BERECHNEN ---
        dist_cm = 0.0
        error_x = 0
        error_y = 0
        command = "SUCHE"
        quality_pct = 0.0

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            # <--- NEU: Der Ball besteht jetzt aus weniger Pixeln, daher reicht area > 12
            if area > 12: 
                ((cx, cy), radius) = cv2.minEnclosingCircle(largest_contour)
                
                # Distanz mit -2.1cm Radius-Korrektur
                # (Die Mathematik skaliert automatisch perfekt mit der neuen Auflösung!)
                opx = radius * 2.0
                Ow_rad = math.radians((Bw_deg / frame_w) * opx)
                if Ow_rad > 0:
                    dist_cm = max(0.0, (21.0 / math.tan(Ow_rad / 2.0)) / 10.0 - 2.1)
                
                # Positions-Error
                error_x = int(cx - (frame_w / 2.0))
                error_y = int(cy - (frame_h / 2.0))
                
                if error_x < -DEADZONE_PIXELS: command = "LINKS"
                elif error_x > DEADZONE_PIXELS: command = "RECHTS"
                else: command = "GERADEAUS"
                
                # Qualität (Wie kreisförmig ist der Fleck?)
                circle_area = math.pi * (radius ** 2)
                if circle_area > 0:
                    quality_pct = min(100.0, (area / circle_area) * 100.0)

        # --- RASTER-DATEN FÜR DEN PC BERECHNEN ---
        small_mask = cv2.resize(mask, (GRID_W, GRID_H), interpolation=cv2.INTER_NEAREST)
        y_coords, x_coords = np.where(small_mask > 0)
        
        # --- JSON ZUSAMMENBAUEN ---
        payload = {
            "telemetry": {
                "status": command,
                "distance_cm": round(dist_cm, 1),
                "error_x": error_x,
                "error_y": error_y,
                "quality_pct": round(quality_pct, 1)
            },
            "pixels": {}
        }
        
        for i in range(len(x_coords)):
            payload["pixels"][f"p{i+1}"] = [int(x_coords[i]), int(y_coords[i])]

        # --- STREAMING ---
        json_output = json.dumps(payload)
        print(json_output)
        sys.stdout.flush() 

        # Wir können die FPS jetzt etwas höher ansetzen, da die CPU kaum belastet wird (ca. 25-30 FPS)
        time.sleep(0.03) 

except KeyboardInterrupt:
    pass
finally:
    cap.release()