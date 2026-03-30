# 🤖 Pi Zero OpenCV Ball Tracker

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)

A lightweight, headless computer vision script optimized for the Raspberry Pi Zero. It calibrates HSV color values using statistical medians and provides live distance and steering telemetry for RoboCup robots.

---

## 📋 Prerequisites

Before you begin, ensure you have the following hardware and software:
* **Hardware:** Raspberry Pi Zero (W/2W), Raspberry Pi Camera Module V2, an orange golf ball.
* **OS:** Raspberry Pi OS (Bullseye or newer).
* **Network:** SSH access to your Pi.

---

## 🚀 Installation

Follow these steps to set up the project on your Raspberry Pi. 

**1. Clone the repository:**
```bash
git clone https://github.com/Robocup-Junior-Open-League/AI_Golf_Ball_Detection.git
cd LocationOfYourDirectory
```

**2. Update your system and install OpenCV dependencies:**
```bash
sudo apt-get update
sudo apt-get install python3-opencv -y
sudo apt-get install libqt4-test python3-sip python3-pyqt5 libqtgui4 libjasper-dev libatlas-base-dev -y
```

**3. Install required Python packages:**
```bash
pip install numpy
```

---

## ⚙️ Usage

**1. Auto-Calibration**
To adapt the camera to your current room lighting, run the calibration script first. Hold the orange ball in front of the camera.
```bash
python calibration_without_GUI.py
```
**Note:** The script will take 10 photos with a 5-second delay to calculate the perfect HSV median.

---

## 🛠️ Troubleshooting

* **Camera not found:** Ensure the ribbon cable is seated correctly and the legacy camera stack is enabled via sudo raspi-config.
* **Low Framerate:** The Pi Zero is limited. Ensure the camera resolution in the script is set to 320x240.
