import cv2
import numpy as np
import time
import sys

# --- KAMERA STARTEN ---
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

GRID_W, GRID_H = 30, 30

def extract_ball_pixels(frame, rough_lower, rough_upper):
    """Findet den Ball und gibt alle H, S und V Pixel zurück."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, rough_lower, rough_upper)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours: return None, None, None
        
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < 100: return None, None, None
        
    ball_mask = np.zeros(frame.shape[:2], dtype="uint8")
    cv2.drawContours(ball_mask, [largest], -1, 255, -1)
    
    h_chan, s_chan, v_chan = cv2.split(hsv)
    return h_chan[ball_mask==255], s_chan[ball_mask==255], v_chan[ball_mask==255]

print("\n" + "="*55)
print(" RASPBERRY PI - KALIBRIERUNG MIT LIVE-RADAR")
print("="*55)
time.sleep(2)
input(">>> Halte den Ball vor die Kamera und druecke ENTER... ")

# Grobe Werte, damit wir den Ball überhaupt im Radar sehen
rough_lower = np.array([0, 80, 80])
rough_upper = np.array([30, 255, 255])

medians_H, medians_S, medians_V = [], [], []
TOTAL_FRAMES = 10   
frames_taken = 0

while frames_taken < TOTAL_FRAMES:
    
    # --- LIVE-VORSCHAU PHASE (5 Sekunden) ---
    start_time = time.time()
    while time.time() - start_time < 5.0:
        ret, frame = cap.read()
        if not ret: continue
        
        # 1. Maske für das Vorschau-Radar
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, rough_lower, rough_upper)
        small_mask = cv2.resize(mask, (GRID_W, GRID_H), interpolation=cv2.INTER_NEAREST)
        
        # 2. Terminal leeren & Radar zeichnen
        sys.stdout.write("\033[H\033[J")
        print(f"FOTO {frames_taken + 1} VON {TOTAL_FRAMES} WIRD VORBEREITET...")
        countdown = 5.0 - (time.time() - start_time)
        print(f"Naechstes Bild in: {countdown:.1f} Sekunden (Bewege den Ball leicht)")
        print("-" * (GRID_W * 2))
        
        for y in range(GRID_H):
            row_str = ""
            for x in range(GRID_W):
                row_str += "██" if small_mask[y, x] > 0 else "  "
            print(row_str)
        print("-" * (GRID_W * 2))
        time.sleep(0.1) # Terminal-FPS begrenzen

    # --- FOTO SCHIESSEN ---
    # Puffer leeren für ein frisches Bild
    for _ in range(5): cap.read()
    ret, frame = cap.read()
    
    h_p, s_p, v_p = extract_ball_pixels(frame, rough_lower, rough_upper)
    
    if h_p is not None:
        med_h, med_s, med_v = np.median(h_p), np.median(s_p), np.median(v_p)
        medians_H.append(med_h)
        medians_S.append(med_s)
        medians_V.append(med_v)
        frames_taken += 1
        print(f"\n[+] KLICK! Werte gespeichert (H:{med_h:.1f} S:{med_s:.1f} V:{med_v:.1f})")
        time.sleep(1.5)
    else:
        print("\n[!] FEHLER: Ball beim Klick nicht gefunden! Versuche es nochmal.")
        time.sleep(2)

# --- FINALE BERECHNUNG ---
sys.stdout.write("\033[H\033[J")
final_h, final_s, final_v = int(np.mean(medians_H)), int(np.mean(medians_S)), int(np.mean(medians_V))

# Toleranzen
tol_h, tol_s, tol_v = 10, 60, 60

lower_bound = np.array([max(0, final_h - tol_h), max(0, final_s - tol_s), max(0, final_v - tol_v)])
upper_bound = np.array([min(179, final_h + tol_h), min(255, final_s + tol_s), min(255, final_v + tol_v)])

print("="*55)
print(" KALIBRIERUNG ERFOLGREICH BEENDET!")
print("="*55)
print("Kopiere diese perfekten Werte in dein main_streamer.py Skript:\n")
print(f"lower_bound = np.array([{lower_bound[0]}, {lower_bound[1]}, {lower_bound[2]}])")
print(f"upper_bound = np.array([{upper_bound[0]}, {upper_bound[1]}, {upper_bound[2]}])\n")
print("="*55)

cap.release()