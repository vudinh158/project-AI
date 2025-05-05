import cv2
import time
import math
import numpy as np
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import setup_hand_tracker
import screen_brightness_control as sbc

# ==================== Âm lượng ====================
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = interface.QueryInterface(IAudioEndpointVolume)
vol_range = volume.GetVolumeRange()
minVol = vol_range[0]
maxVol = vol_range[1]

# ==================== Camera ====================
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# ==================== Hand Tracker ====================
detector = setup_hand_tracker.HandTracker(detectionCon=0.7)
pTime, cTime = 0, 0
vol, volBar, volPer = 0, 0, 0
brightPer = 0

mode = 'volume'  # chế độ mặc định

# ==================== Khu vực nút ====================
btn_volume = (10, 10, 120, 60)  # x1, y1, x2, y2
btn_brightness = (140, 10, 300, 60)

def click_event(event, x, y, flags, param):
    global mode
    if event == cv2.EVENT_LBUTTONDOWN:
        if btn_volume[0] <= x <= btn_volume[2] and btn_volume[1] <= y <= btn_volume[3]:
            mode = 'volume'
        elif btn_brightness[0] <= x <= btn_brightness[2] and btn_brightness[1] <= y <= btn_brightness[3]:
            mode = 'brightness'

cv2.namedWindow("Control")
cv2.setMouseCallback("Control", click_event)

while True:
    success, img = cap.read()
    if not success:
        break

    img = detector.handsFinder(img)
    lmList = detector.positionFinder(img, draw=False)

    if lmList:
        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[8][1], lmList[8][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        cv2.circle(img, (x1, y1), 10, (255, 255, 255), cv2.FILLED)
        cv2.circle(img, (x2, y2), 10, (255, 255, 255), cv2.FILLED)
        cv2.line(img, (x1, y1), (x2, y2), (255, 255, 255), 3)
        cv2.circle(img, (cx, cy), 10, (255, 255, 255), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)

        if mode == 'volume':
            vol = np.interp(length, [50, 150], [minVol, maxVol])
            volBar = np.interp(length, [50, 150], [400, 150])
            volPer = np.interp(length, [50, 150], [0, 100])
            volume.SetMasterVolumeLevel(vol, None)
        elif mode == 'brightness':
            brightPer = int(np.interp(length, [50, 150], [0, 100]))
            sbc.set_brightness(brightPer)

    # ==================== Giao diện thanh ====================
    cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 255), 3)
    if mode == 'volume':
        cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), cv2.FILLED)
        cv2.putText(img, f'Volume: {int(volPer)} %', (30, 450), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
    else:
        brightBar = np.interp(brightPer, [0, 100], [400, 150])
        cv2.rectangle(img, (50, int(brightBar)), (85, 400), (0, 255, 255), cv2.FILLED)
        cv2.putText(img, f'Bright: {int(brightPer)} %', (30, 450), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)

    # ==================== Vẽ nút điều khiển ====================
    # Nút Volume
    vol_color = (0, 255, 0) if mode == 'volume' else (100, 100, 255)
    cv2.rectangle(img, (btn_volume[0], btn_volume[1]), (btn_volume[2], btn_volume[3]), vol_color, cv2.FILLED)
    cv2.putText(img, 'Volume', (btn_volume[0] + 10, btn_volume[3] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Nút Brightness
    bright_color = (0, 255, 255) if mode == 'brightness' else (0, 150, 255)
    cv2.rectangle(img, (btn_brightness[0], btn_brightness[1]), (btn_brightness[2], btn_brightness[3]), bright_color, cv2.FILLED)
    cv2.putText(img, 'Brightness', (btn_brightness[0] + 10, btn_brightness[3] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.putText(img, f'Mode: {mode}', (400, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)

    cv2.imshow('Control', img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
