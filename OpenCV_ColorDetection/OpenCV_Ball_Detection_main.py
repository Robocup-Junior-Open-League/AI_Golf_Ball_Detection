import cv2
import numpy as np
import json
import time
import sys
import math

# --- KAMERA & KONSTANTEN ---
cap = cv2.VideoCapture(0)
frame_w, frame_h = 320, 240
cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_w)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_h)

Bw_deg = 62.2  # FOV der Pi Kamera
DEADZONE_PIXELS = 20

# Raster für die Übertragung
GRID_W, GRID_H = 30, 30

# DEINE FESTEN HSV-WERTE (Keine Eingabe mehr nötig)
lower_bound = np.array([3, 56, 220])
upper_bound = np.array([23, 165, 255])

try:
    while True:
        ret, frame = cap.read()
        if not ret: 
            time.sleep(0.1)
            continue

        # 1. Bild filtern
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        
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
            
            if area > 50:
                ((cx, cy), radius) = cv2.minEnclosingCircle(largest_contour)
                
                # Distanz mit -2.1cm Radius-Korrektur
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
                
                # Qualität
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

        # --- STREAMING (Nur das reine JSON in EINER Zeile) ---
        json_output = json.dumps(payload)
        print(json_output)
        
        # WICHTIG: Zwingt den Pi, das Paket SOFORT in die SSH-Leitung zu drücken
        sys.stdout.flush() 

        # Kurze Pause für stabile FPS und um den SSH-Kanal nicht zu überlasten (ca. 20 FPS)
        time.sleep(0.05) 

except KeyboardInterrupt:
    pass
finally:
    cap.release()