import cv2
import numpy as np
import json
import math

# --- KAMERA & KONSTANTEN (Für Windows angepasst) ---
cap = cv2.VideoCapture(0)      # 0 ist in der Regel deine PC-Webcam
frame_w, frame_h = 160, 120    # Die ultra-niedrige Auflösung zum Testen
cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_w)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_h)

Bw_deg = 62.2  # Pi Kamera FOV (Wir nutzen ihn auch hier für die Formel)
DEADZONE_PIXELS = 10

# Raster für das JSON-Paket
GRID_W, GRID_H = 30, 30

# DEINE FESTEN HSV-WERTE
lower_bound = np.array([0, 118, 153])
upper_bound = np.array([18, 238, 255])

print("Starte Windows-Testlauf...")
print("Drücke die Taste 'q' in einem der Videofenster, um zu beenden.\n")

while True:
    ret, frame = cap.read()
    if not ret: 
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
        
        if area > 12: 
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

            # Für Windows: Grünen Kreis um den gefundenen Ball malen
            cv2.circle(frame, (int(cx), int(cy)), int(radius), (0, 255, 0), 2)

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

    json_output = json.dumps(payload)
    
    # Text in der Konsole ausgeben, damit du siehst, dass das JSON generiert wird
    print(f"[{command:<10}] Distanz: {dist_cm:>5.1f}cm | Error X: {error_x:>3}px | JSON Size: {len(json_output)} Bytes", end="\r")

    # --- VISUALISIERUNG FÜR WINDOWS ---
    # Da 160x120 sehr klein ist, skalieren wir die Anzeige-Fenster künstlich hoch (z.B. x3)
    # Wichtig: Das beeinflusst NICHT unsere Logik, es ist nur für deine Augen!
    display_frame = cv2.resize(frame, (480, 360), interpolation=cv2.INTER_NEAREST)
    display_mask = cv2.resize(mask, (480, 360), interpolation=cv2.INTER_NEAREST)

    cv2.imshow("Kamera (160x120 Skaliert)", display_frame)
    cv2.imshow("Maske (160x120 Skaliert)", display_mask)

    # cv2.waitKey wartet 30ms auf eine Eingabe und hält das Bild flüssig (ca. 30 FPS)
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("\nTest beendet.")