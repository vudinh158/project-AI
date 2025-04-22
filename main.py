
import cv2
import time
import math
import numpy as np
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import setup_hand_tracker

# khai báo biến để  thiết lập thanh bar 0-> 100%
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = interface.QueryInterface(IAudioEndpointVolume)

vol_range = volume.GetVolumeRange()
minVol = vol_range[0]
maxVol = vol_range[1]

# thiết lập cấu hình video
cap = cv2.VideoCapture(0)
cap.set(16, 640)
cap.set(9, 480)

# khai báo biến để khởi tạo trình nhận diện bàn tay-ngón tay
detector = setup_hand_tracker.HandTracker(detectionCon=0.7)

#  khai báo biến để khởi tạo khung hình/s (FPS)
pTime, cTime = 0, 0

#khai báo biến âm lượng
vol, volBar, volPer = 0, 0, 0

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

        # thiết lập các điểm trên ngón tay và kết nối chúng lại với nhau
        cv2.circle(img, (x1, y1), 10, (0, 255, 0), cv2.FILLED)
        cv2.circle(img, (x2, y2), 10, (0, 255, 0), cv2.FILLED)
        cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.circle(img, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

        # tính toán chiều cao giữa 2 điểm
        length = math.hypot(x2 - x1, y2 - y1)

        # quy đổi chiều dài sang giá trị âm lượng
        volBar = np.interp(length, [50, 150], [400, 150])
        volPer = np.interp(length, [50, 150], [0, 100])
        vol = np.interp(length, [50, 150], [minVol, maxVol])

        #đặt giá trị âm lượng
        volume.SetMasterVolumeLevel(vol, None)

        # vễ thanh âm lượng
        cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
        cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), cv2.FILLED)
        cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 2)


    # Show the image
    cv2.imshow('Image', img)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close windows
cap.release()
cv2.destroyAllWindows()
