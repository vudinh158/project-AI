import cv2
import time
import math
import numpy as np
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import setup_hand_tracker
import screen_brightness_control as sbc
import pyautogui

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = interface.QueryInterface(IAudioEndpointVolume)
vol_range = volume.GetVolumeRange()
minVol = vol_range[0]
maxVol = vol_range[1]


def get_current_volume():
    return volume.GetMasterVolumeLevelScalar() * 100


cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

detector = setup_hand_tracker.HandTracker(detectionCon=0.7)
pTime, cTime = 0, 0
vol, volBar, volPer = 0, 0, 0
brightPer = 0

mode = 'volume'
keyboard_visible = False

btn_volume = (20, 20, 140, 70)
btn_brightness = (160, 20, 300, 70)
btn_keyboard = (320, 20, 460, 70)


def click_event(event, x, y, flags, param):
    global mode, keyboard_visible
    if event == cv2.EVENT_LBUTTONDOWN:
        if btn_volume[0] <= x <= btn_volume[2] and btn_volume[1] <= y <= btn_volume[3]:
            mode = 'volume'
            keyboard_visible = False
        elif btn_brightness[0] <= x <= btn_brightness[2] and btn_brightness[1] <= y <= btn_brightness[3]:
            mode = 'brightness'
            keyboard_visible = False
        elif btn_keyboard[0] <= x <= btn_keyboard[2] and btn_keyboard[1] <= y <= btn_keyboard[3]:
            keyboard_visible = not keyboard_visible

            mode = 'keyboard' if keyboard_visible else mode


cv2.namedWindow("Control", cv2.WINDOW_NORMAL)

cv2.setMouseCallback("Control", click_event)


keyboard_keys = [
    "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P",
    "A", "S", "D", "F", "G", "H", "J", "K", "L", ";",
    "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"
]
key_positions = {}
input_text = ""
last_keypress_time = 0
KEYPRESS_DELAY = 1.0


def setup_virtual_keyboard():
    x_start, y_start = 25, 150
    width, height = 50, 50
    margin = 10
    for i, key in enumerate(keyboard_keys):

        x = x_start + (i % 10) * (width + margin)

        y = y_start + (i // 10) * (height + margin)

        key_positions[key] = (x, y, width, height)


def draw_virtual_keyboard(img):
    global input_text
    if keyboard_visible and mode == 'keyboard':
        for key, (x, y, w, h) in key_positions.items():
            cv2.rectangle(img, (x, y), (x + w, y + h),
                          (135, 206, 250), -1)
            cv2.rectangle(img, (x, y), (x + w, y + h),
                          (255, 255, 255), 2)

            text_size = cv2.getTextSize(
                key, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            text_x = x + (w - text_size[0]) // 2
            text_y = y + (h + text_size[1]) // 2
            cv2.putText(img, key, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

        text_box_x, text_box_y = 25, 100
        text_box_width, text_box_height = 590, 40
        cv2.rectangle(img, (text_box_x, text_box_y), (text_box_x +
                      text_box_width, text_box_y + text_box_height), (255, 255, 255), -1)  # Nền trắng
        cv2.rectangle(img, (text_box_x, text_box_y), (text_box_x +
                      text_box_width, text_box_y + text_box_height), (0, 0, 0), 2)
        cv2.putText(img, input_text, (text_box_x + 5, text_box_y + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        if lmList:
            x1, y1 = lmList[4][1], lmList[4][2]
            x2, y2 = lmList[8][1], lmList[8][2]
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            cv2.circle(img, (x1, y1), 10, (255, 255, 255),
                       cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (255, 255, 255),
                       cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2),
                     (255, 255, 255), 3)
            cv2.circle(img, (cx, cy), 10, (255, 255, 255),
                       cv2.FILLED)


setup_virtual_keyboard()


while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)

    img = detector.handsFinder(img)

    lmList = detector.positionFinder(img, draw=False)
    if lmList:
        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[8][1], lmList[8][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        cv2.circle(img, (x1, y1), 10, (255, 255, 255),
                   cv2.FILLED)
        cv2.circle(img, (x2, y2), 10, (255, 255, 255),
                   cv2.FILLED)
        cv2.line(img, (x1, y1), (x2, y2), (255, 255, 255), 3)
        cv2.circle(img, (cx, cy), 10, (255, 255, 255),
                   cv2.FILLED)

        length = math.hypot(lmList[8][1] - lmList[4]
                            [1], lmList[8][2] - lmList[4][2])

        if mode == 'volume':

            vol = np.interp(length, [50, 150], [minVol, maxVol])
            volBar = np.interp(volPer, [0, 100], [400, 150])

            volPer = np.interp(length, [50, 150], [0, 100])
            volume.SetMasterVolumeLevel(vol, None)

        elif mode == 'brightness':

            brightPer = int(np.interp(length, [50, 150], [0, 100]))
            sbc.set_brightness(brightPer)

        elif mode == 'keyboard':

            current_time = time.time()
            if length < 30 and (current_time - last_keypress_time) >= KEYPRESS_DELAY:
                for key, (x, y, w, h) in key_positions.items():

                    if x <= lmList[8][1] <= x + w and y <= lmList[8][2] <= y + h:
                        input_text += key
                        pyautogui.write(key)
                        last_keypress_time = current_time
                        break

    volPer = get_current_volume() if get_current_volume(
    ) is not None else 0
    brightPer = sbc.get_brightness()[0] if sbc.get_brightness() else 0

    if mode == 'volume':

        cv2.rectangle(img, (50, 150), (85, 400),
                      (255, 255, 255), 3)

        volBar = np.interp(volPer, [0, 100], [400, 150])
        cv2.rectangle(img, (50, int(volBar)), (85, 400),
                      (255, 215, 0), cv2.FILLED)
        cv2.putText(img, f'Volume: {int(volPer)} %', (30, 450),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 215, 0), 2)
    elif mode == 'brightness':
        cv2.rectangle(img, (50, 150), (85, 400),
                      (255, 255, 255), 3)  # Viền trắng
        # Tính vị trí thanh độ sáng
        brightBar = np.interp(brightPer, [0, 100], [400, 150])
        cv2.rectangle(img, (50, int(brightBar)), (85, 400),
                      (255, 215, 0), cv2.FILLED)  # Màu vàng
        cv2.putText(img, f'Bright: {int(brightPer)} %', (30, 450),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 215, 0), 2)

    vol_color = (255, 215, 0) if mode == 'volume' else (255, 165, 0)
    cv2.rectangle(img, (btn_volume[0], btn_volume[1]),
                  (btn_volume[2], btn_volume[3]), vol_color, cv2.FILLED)
    cv2.rectangle(img, (btn_volume[0], btn_volume[1]), (btn_volume[2],
                  btn_volume[3]), (255, 255, 255), 2)  # Viền trắng
    cv2.putText(img, 'Volume', (btn_volume[0] + 15, btn_volume[3] - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Nút Brightness
    bright_color = (255, 215, 0) if mode == 'brightness' else (255, 165, 0)
    cv2.rectangle(img, (btn_brightness[0], btn_brightness[1]), (
        btn_brightness[2], btn_brightness[3]), bright_color, cv2.FILLED)
    cv2.rectangle(img, (btn_brightness[0], btn_brightness[1]), (
        btn_brightness[2], btn_brightness[3]), (255, 255, 255), 2)  # Viền trắng
    cv2.putText(img, 'Brightness', (btn_brightness[0] + 15, btn_brightness[3] - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Nút Keyboard
    keyboard_color = (
        255, 215, 0) if mode == 'keyboard' and keyboard_visible else (255, 165, 0)
    cv2.rectangle(img, (btn_keyboard[0], btn_keyboard[1]),
                  (btn_keyboard[2], btn_keyboard[3]), keyboard_color, cv2.FILLED)
    cv2.rectangle(img, (btn_keyboard[0], btn_keyboard[1]), (
        btn_keyboard[2], btn_keyboard[3]), (255, 255, 255), 2)  # Viền trắng
    cv2.putText(img, 'Keyboard', (btn_keyboard[0] + 15, btn_keyboard[3] - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    draw_virtual_keyboard(img)

    cv2.imshow('Control', img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
