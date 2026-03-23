import os
import sys
import argparse
import glob
import time

import cv2
import numpy as np
from ultralytics import YOLO

# Define and parse user input arguments
parser = argparse.ArgumentParser()
parser.add_argument('--model', help='Path to YOLO model file', required=True)
parser.add_argument('--source', help='Image source (e.g. "usb0" for webcam)', required=True)
parser.add_argument('--thresh', help='Minimum confidence threshold', default=0.5)
parser.add_argument('--resolution', help='Resolution in WxH', default=None)
args = parser.parse_args()

model_path = args.model
img_source = args.source
min_thresh = float(args.thresh)
user_res = args.resolution

if not os.path.exists(model_path):
    print('ERROR: Model path is invalid or model was not found.')
    sys.exit(0)

# Load the model directly to CPU
print("Loading model on CPU...")
model = YOLO(model_path)
labels = model.names
print("Model loaded successfully.")

# Setup Camera (CAP_DSHOW prevents Windows webcam lag)
usb_idx = int(img_source.replace('usb', ''))
cap = cv2.VideoCapture(usb_idx, cv2.CAP_DSHOW)

resize = False
if user_res:
    resize = True
    resW, resH = int(user_res.split('x')[0]), int(user_res.split('x')[1])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resW)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resH)

bbox_colors = [(164,120,87), (68,148,228), (93,97,209), (178,182,133)]
avg_frame_rate = 0
frame_rate_buffer = []
print("Starting inference loop. Press 'q' to quit.")

while True:
    t_start = time.perf_counter()
    ret, frame = cap.read()
    
    if not ret or frame is None:
        print('Camera disconnected.')
        break

    if resize:
        frame = cv2.resize(frame, (resW, resH))

    # Run inference on CPU
    results = model(frame, verbose=False)
    detections = results[0].boxes
    object_count = 0

    for i in range(len(detections)):
        conf = detections[i].conf.item()
        
        if conf > min_thresh:
            xyxy = detections[i].xyxy.cpu().numpy().squeeze().astype(int) 
            xmin, ymin, xmax, ymax = xyxy
            classidx = int(detections[i].cls.item())
            classname = labels[classidx]
            
            color = bbox_colors[classidx % len(bbox_colors)]
            cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), color, 2)
            label = f'{classname}: {int(conf*100)}%'
            cv2.putText(frame, label, (xmin, ymin-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            object_count += 1

    # Draw FPS
    cv2.putText(frame, f'FPS: {avg_frame_rate:0.1f}', (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.imshow('RoboCup Vision Test', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'): 
        break

    # Calculate FPS
    t_stop = time.perf_counter()
    frame_rate_buffer.append(1/(t_stop - t_start))
    if len(frame_rate_buffer) > 15:
        frame_rate_buffer.pop(0)
    avg_frame_rate = np.mean(frame_rate_buffer)

cap.release()
cv2.destroyAllWindows()