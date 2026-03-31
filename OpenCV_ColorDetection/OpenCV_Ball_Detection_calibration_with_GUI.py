import cv2
import numpy as np
import math

# --- SPEZIFIKATIONEN RASPBERRY PI CAM V2 ---
Bw_deg = 62.2  

def nothing(x):
    pass

# --- KAMERA STARTEN ---
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

cv2.namedWindow("Kalibrierung")
cv2.resizeWindow("Kalibrierung", 400, 250)

# Slider erstellen
cv2.createTrackbar("Hue Min", "Kalibrierung", 5, 179, nothing)
cv2.createTrackbar("Hue Max", "Kalibrierung", 25, 179, nothing)
cv2.createTrackbar("Sat Min", "Kalibrierung", 120, 255, nothing)
cv2.createTrackbar("Sat Max", "Kalibrierung", 255, 255, nothing)
cv2.createTrackbar("Val Min", "Kalibrierung", 100, 255, nothing)
cv2.createTrackbar("Val Max", "Kalibrierung", 255, 255, nothing)

# --- STEUERUNGS-KONSTANTEN ---
# Wie viele Pixel darf der Ball von der exakten Mitte abweichen,
# bevor der Roboter anfängt zu lenken? (Verhindert "Zittern" beim Fahren)
DEADZONE_PIXELS = 40 

print("Starte Objekterkennung, Abstandsmessung und Lenk-Logik.")
print("Drücke 'q' zum Beenden.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    npx = frame.shape[1] 
    image_center_x = npx / 2.0 # Die "Nase" des Roboters

    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    h_min = cv2.getTrackbarPos("Hue Min", "Kalibrierung")
    h_max = cv2.getTrackbarPos("Hue Max", "Kalibrierung")
    s_min = cv2.getTrackbarPos("Sat Min", "Kalibrierung")
    s_max = cv2.getTrackbarPos("Sat Max", "Kalibrierung")
    v_min = cv2.getTrackbarPos("Val Min", "Kalibrierung")
    v_max = cv2.getTrackbarPos("Val Max", "Kalibrierung")

    lower_orange = np.array([h_min, s_min, v_min])
    upper_orange = np.array([h_max, s_max, v_max])

    mask = cv2.inRange(hsv_frame, lower_orange, upper_orange)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        largest_contour = max(contours, key=cv2.contourArea)
        ((x_center, y_center), radius) = cv2.minEnclosingCircle(largest_contour)

        if radius > 5:
            
            # --- 1. ABSTANDSBERECHNUNG (FOV) ---
            opx = radius * 2.0
            Ow_deg = (Bw_deg / npx) * opx
            Ow_rad = math.radians(Ow_deg)
            
            if Ow_rad > 0:
                distance_mm = 21.0 / math.tan(Ow_rad / 2.0)
            else:
                distance_mm = 0.0
                
            distance_cm = distance_mm / 10.0

            # --- 2. LENK-LOGIK ---
            # Wir berechnen den "Error" (Wie weit ist der Ball von der Mitte weg?)
            # Negativer Wert = Ball ist links. Positiver Wert = Ball ist rechts.
            error_x = x_center - image_center_x
            
            command = "STOP"
            color_cmd = (0, 0, 255) # Rot für Stop

            # Ist der Ball weiter links als unsere Deadzone erlaubt?
            if error_x < -DEADZONE_PIXELS:
                command = "TURN LEFT"
                color_cmd = (0, 255, 255) # Gelb
            
            # Ist der Ball weiter rechts als unsere Deadzone erlaubt?
            elif error_x > DEADZONE_PIXELS:
                command = "TURN RIGHT"
                color_cmd = (0, 255, 255) # Gelb
            
            # Ball ist in der Mitte (innerhalb der Deadzone)!
            else:
                command = "FORWARD"
                color_cmd = (0, 255, 0) # Grün für Gas geben!

            # --- VISUALISIERUNG ---
            # Kreis um den Ball
            cv2.circle(frame, (int(x_center), int(y_center)), int(radius), (0, 255, 255), 2)
            cv2.circle(frame, (int(x_center), int(y_center)), 3, (0, 0, 255), -1) 

            # Zeichne die "Nase" des Roboters (Mittellinie)
            cv2.line(frame, (int(image_center_x), 0), (int(image_center_x), frame.shape[0]), (255, 255, 255), 1)
            
            # Zeichne die Deadzone ein (zwei vertikale Linien)
            cv2.line(frame, (int(image_center_x - DEADZONE_PIXELS), 0), 
                     (int(image_center_x - DEADZONE_PIXELS), frame.shape[0]), (100, 100, 100), 1)
            cv2.line(frame, (int(image_center_x + DEADZONE_PIXELS), 0), 
                     (int(image_center_x + DEADZONE_PIXELS), frame.shape[0]), (100, 100, 100), 1)

            # Zeichne eine Linie vom Ball zur Mitte (visualisiert den "Error")
            cv2.line(frame, (int(image_center_x), int(y_center)), (int(x_center), int(y_center)), color_cmd, 2)

            # Werte auf dem Bildschirm anzeigen
            cv2.putText(frame, f"Dist: {distance_cm:.1f} cm", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            cv2.putText(frame, f"Err_X: {int(error_x)} px", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Das fette Steuerungs-Kommando groß in die Mitte schreiben
            cv2.putText(frame, command, (int(image_center_x - 100), frame.shape[0] - 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, color_cmd, 3)

    cv2.imshow("Kamera", frame)
    cv2.imshow("Maske", mask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()