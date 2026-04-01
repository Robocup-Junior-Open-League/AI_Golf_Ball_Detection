import subprocess
import cv2
import numpy as np
import json
import sys

# ==========================================
# ⚙️ EINSTELLUNGEN (HIER ANPASSEN)
# ==========================================
PI_USER = "pi"                 # Dein Raspberry Pi Benutzername
PI_IP = "192.168.178.50"       # <-- WICHTIG: Hier die IP deines Pi eintragen!
PI_SCRIPT = "main_streamer.py" # Der Name deines Skripts auf dem Pi

# Darstellungs-Größen
GRID_W, GRID_H = 30, 30
SCALE = 15  # Macht aus den kleinen 30x30 Pixeln ein großes 450x450 Radar
RADAR_SIZE = GRID_W * SCALE
WINDOW_W = RADAR_SIZE + 350
WINDOW_H = max(RADAR_SIZE, 400)

print(f"[*] Verbinde mit {PI_USER}@{PI_IP} über SSH...")
print("[*] HINWEIS: Falls dein Pi ein Passwort hat, tippe es jetzt hier in die Konsole ein!\n")

# SSH-Verbindung aufbauen und das Streamer-Skript starten
cmd = ["ssh", f"{PI_USER}@{PI_IP}", "python", PI_SCRIPT]
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)

cv2.namedWindow("RoboCup Telemetrie Dashboard", cv2.WINDOW_AUTOSIZE)

try:
    while True:
        # Lese die nächste JSON-Zeile aus dem unsichtbaren SSH-Kabel
        line = process.stdout.readline()
        if not line: break
            
        line = line.strip()
        if not line.startswith("{"): continue # Ignoriere Text, der kein JSON ist

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        # === 1. LEERE LEINWAND ERSTELLEN ===
        dashboard = np.zeros((WINDOW_H, WINDOW_W, 3), dtype=np.uint8)

        # === 2. RADAR ZEICHNEN ===
        # Hintergrund für Radar (Dunkelgrau)
        cv2.rectangle(dashboard, (0, 0), (RADAR_SIZE, RADAR_SIZE), (30, 30, 30), -1)
        
        # Fadenkreuz in die Mitte zeichnen (als Zielhilfe)
        center_x, center_y = RADAR_SIZE // 2, RADAR_SIZE // 2
        cv2.line(dashboard, (center_x, 0), (center_x, RADAR_SIZE), (80, 80, 80), 1)
        cv2.line(dashboard, (0, center_y), (RADAR_SIZE, center_y), (80, 80, 80), 1)

        # Weiße Pixel aus dem JSON eintragen (als leuchtend orange Kästchen)
        pixels = data.get("pixels", {})
        for coords in pixels.values():
            px, py = coords[0], coords[1]
            x1, y1 = px * SCALE, py * SCALE
            x2, y2 = (px + 1) * SCALE, (py + 1) * SCALE
            cv2.rectangle(dashboard, (x1, y1), (x2, y2), (0, 140, 255), -1) # BGR Orange

        # === 3. TELEMETRIE-TEXT ZEICHNEN ===
        telemetry = data.get("telemetry", {})
        cmd_status = telemetry.get("status", "SUCHE")
        dist = telemetry.get("distance_cm", 0.0)
        err_x = telemetry.get("error_x", 0)
        err_y = telemetry.get("error_y", 0)
        qual = telemetry.get("quality_pct", 0.0)

        # Text-Farbe je nach Lenk-Kommando anpassen
        if cmd_status == "GERADEAUS": color = (0, 255, 0)       # Grün (Ziel erfasst)
        elif cmd_status in ["LINKS", "RECHTS"]: color = (0, 255, 255) # Gelb (Korrigieren)
        else: color = (0, 0, 255)                               # Rot (Suchen)

        text_x = RADAR_SIZE + 20
        
        # Überschrift
        cv2.putText(dashboard, "ROBOCUP DASHBOARD", (text_x, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.line(dashboard, (text_x, 50), (WINDOW_W - 20, 50), (255, 255, 255), 1)

        # Telemetrie-Werte
        cv2.putText(dashboard, f"STATUS:  {cmd_status}", (text_x, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(dashboard, f"DISTANZ: {dist} cm", (text_x, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(dashboard, f"ERROR X: {err_x} px", (text_x, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(dashboard, f"ERROR Y: {err_y} px", (text_x, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Optischer Qualitäts-Balken
        cv2.putText(dashboard, f"SICHERHEIT: {qual}%", (text_x, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        bar_width = int(qual * 2) # Skaliert 100% auf 200 Pixel Breite
        cv2.rectangle(dashboard, (text_x, 340), (text_x + bar_width, 360), (0, 255, 0), -1) # Grüner Füllstand
        cv2.rectangle(dashboard, (text_x, 340), (text_x + 200, 360), (255, 255, 255), 1)    # Weißer Rahmen

        # Bild anzeigen
        cv2.imshow("RoboCup Telemetrie Dashboard", dashboard)

        # Beenden mit ESC-Taste
        if cv2.waitKey(1) & 0xFF == 27:
            break

except KeyboardInterrupt:
    pass
finally:
    print("\n[*] Beende SSH-Verbindung...")
    process.terminate()
    cv2.destroyAllWindows()