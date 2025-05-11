import cv2
import time
import math
import numpy as np
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import setup_hand_tracker
import screen_brightness_control as sbc
import pyautogui  # To simulate keyboard input

# ==================== Âm lượng ====================
# Khởi tạo giao diện điều khiển âm lượng của hệ thống bằng thư viện pycaw
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = interface.QueryInterface(IAudioEndpointVolume)
vol_range = volume.GetVolumeRange()
minVol = vol_range[0]  # Giá trị âm lượng nhỏ nhất của hệ thống
maxVol = vol_range[1]  # Giá trị âm lượng lớn nhất của hệ thống

# Lấy âm lượng hiện tại của hệ thống


def get_current_volume():
    # Trả về giá trị âm lượng dưới dạng phần trăm (0-100)
    return volume.GetMasterVolumeLevelScalar() * 100


# ==================== Camera ====================
# Khởi tạo camera với độ phân giải 640x480
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # Chiều rộng
cap.set(4, 480)  # Chiều cao

# ==================== Hand Tracker ====================
# Khởi tạo đối tượng HandTracker để phát hiện tay với độ tin cậy 0.7
detector = setup_hand_tracker.HandTracker(detectionCon=0.7)
# Khởi tạo các biến để theo dõi FPS và giá trị âm lượng/độ sáng
pTime, cTime = 0, 0
vol, volBar, volPer = 0, 0, 0
brightPer = 0

# Khởi tạo trạng thái ban đầu
mode = 'volume'  # Chế độ mặc định là điều chỉnh âm lượng
keyboard_visible = False  # Bàn phím ảo mặc định ẩn

# ==================== Khu vực nút ====================
# Định nghĩa vùng tọa độ cho các nút điều khiển
btn_volume = (20, 20, 140, 70)  # Vùng nút Volume (x1, y1, x2, y2)
btn_brightness = (160, 20, 300, 70)  # Vùng nút Brightness
btn_keyboard = (320, 20, 460, 70)  # Vùng nút Keyboard

# Hàm xử lý sự kiện click chuột để chuyển đổi chế độ


def click_event(event, x, y, flags, param):
    global mode, keyboard_visible
    if event == cv2.EVENT_LBUTTONDOWN:  # Khi nhấn chuột trái
        if btn_volume[0] <= x <= btn_volume[2] and btn_volume[1] <= y <= btn_volume[3]:
            mode = 'volume'  # Chuyển sang chế độ điều chỉnh âm lượng
            keyboard_visible = False  # Ẩn bàn phím ảo
        elif btn_brightness[0] <= x <= btn_brightness[2] and btn_brightness[1] <= y <= btn_brightness[3]:
            mode = 'brightness'  # Chuyển sang chế độ điều chỉnh độ sáng
            keyboard_visible = False  # Ẩn bàn phím ảo
        elif btn_keyboard[0] <= x <= btn_keyboard[2] and btn_keyboard[1] <= y <= btn_keyboard[3]:
            keyboard_visible = not keyboard_visible  # Bật/tắt bàn phím ảo
            # Chuyển sang chế độ bàn phím nếu bật
            mode = 'keyboard' if keyboard_visible else mode


# Thiết lập cửa sổ hiển thị và gắn sự kiện click chuột
# Tạo cửa sổ có thể thay đổi kích thước
cv2.namedWindow("Control", cv2.WINDOW_NORMAL)
# Gắn hàm xử lý click chuột vào cửa sổ
cv2.setMouseCallback("Control", click_event)

# ==================== Bàn phím ảo ====================
# Danh sách các phím trên bàn phím ảo
keyboard_keys = [
    "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P",
    "A", "S", "D", "F", "G", "H", "J", "K", "L", ";",
    "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"
]
key_positions = {}  # Lưu tọa độ của từng phím
input_text = ""  # Chuỗi để lưu văn bản đã nhập
last_keypress_time = 0  # Thời gian lần nhấn phím cuối cùng
KEYPRESS_DELAY = 1.0  # Độ trễ 1 giây giữa các lần nhấn phím

# Hàm thiết lập vị trí các phím trên bàn phím ảo


def setup_virtual_keyboard():
    x_start, y_start = 25, 150  # Vị trí bắt đầu của bàn phím
    width, height = 50, 50  # Kích thước mỗi phím
    margin = 10  # Khoảng cách giữa các phím
    for i, key in enumerate(keyboard_keys):
        # Tính tọa độ x (10 phím mỗi hàng)
        x = x_start + (i % 10) * (width + margin)
        # Tính tọa độ y (tăng hàng khi i >= 10)
        y = y_start + (i // 10) * (height + margin)
        # Lưu tọa độ và kích thước của phím
        key_positions[key] = (x, y, width, height)

# Hàm vẽ bàn phím ảo lên hình ảnh và hiển thị cử chỉ tay


def draw_virtual_keyboard(img):
    global input_text
    if keyboard_visible and mode == 'keyboard':  # Chỉ hiển thị bàn phím nếu ở chế độ keyboard
        for key, (x, y, w, h) in key_positions.items():
            # Vẽ phím với màu nền xanh dương nhạt và viền trắng
            cv2.rectangle(img, (x, y), (x + w, y + h),
                          (135, 206, 250), -1)  # Màu nền
            cv2.rectangle(img, (x, y), (x + w, y + h),
                          (255, 255, 255), 2)  # Viền trắng
            # Căn giữa văn bản trên phím
            text_size = cv2.getTextSize(
                key, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            text_x = x + (w - text_size[0]) // 2  # Tọa độ x của chữ
            text_y = y + (h + text_size[1]) // 2  # Tọa độ y của chữ
            cv2.putText(img, key, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

        # Vẽ ô hiển thị văn bản đã nhập
        text_box_x, text_box_y = 25, 100
        text_box_width, text_box_height = 590, 40
        cv2.rectangle(img, (text_box_x, text_box_y), (text_box_x +
                      text_box_width, text_box_y + text_box_height), (255, 255, 255), -1)  # Nền trắng
        cv2.rectangle(img, (text_box_x, text_box_y), (text_box_x +
                      text_box_width, text_box_y + text_box_height), (0, 0, 0), 2)  # Viền đen
        cv2.putText(img, input_text, (text_box_x + 5, text_box_y + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)  # Hiển thị văn bản đã nhập

        # Hiển thị cử chỉ tay trên bàn phím ảo
        if lmList:  # Nếu phát hiện được tay
            x1, y1 = lmList[4][1], lmList[4][2]  # Ngón cái
            x2, y2 = lmList[8][1], lmList[8][2]  # Ngón trỏ
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2  # Tọa độ trung điểm

            # Vẽ các điểm và đường nối
            cv2.circle(img, (x1, y1), 10, (255, 255, 255),
                       cv2.FILLED)  # Vẽ điểm ngón cái
            cv2.circle(img, (x2, y2), 10, (255, 255, 255),
                       cv2.FILLED)  # Vẽ điểm ngón trỏ
            cv2.line(img, (x1, y1), (x2, y2),
                     (255, 255, 255), 3)  # Vẽ đường nối
            cv2.circle(img, (cx, cy), 10, (255, 255, 255),
                       cv2.FILLED)  # Vẽ điểm trung tâm


# Khởi tạo bàn phím ảo
setup_virtual_keyboard()

# Vòng lặp chính để xử lý video từ camera
while True:
    success, img = cap.read()  # Đọc khung hình từ camera
    if not success:
        break

    # Lật ngang hình ảnh để sửa lỗi camera (hình ảnh không bị lật trái-phải)
    img = cv2.flip(img, 1)

    # Phát hiện tay trong khung hình
    img = detector.handsFinder(img)
    # Lấy danh sách tọa độ các điểm trên tay
    lmList = detector.positionFinder(img, draw=False)

    if lmList:  # Nếu phát hiện được tay
        # Tính khoảng cách giữa ngón cái và ngón trỏ (dùng để điều khiển âm lượng, độ sáng, hoặc nhấn phím)
        length = math.hypot(lmList[8][1] - lmList[4]
                            [1], lmList[8][2] - lmList[4][2])

        # Điều khiển âm lượng dựa trên khoảng cách giữa ngón cái và ngón trỏ
        if mode == 'volume':
            # Chuyển đổi khoảng cách (length) thành giá trị âm lượng trong khoảng minVol đến maxVol
            vol = np.interp(length, [50, 150], [minVol, maxVol])
            # Chuyển đổi giá trị âm lượng thành vị trí trên thanh hiển thị (150-400)
            volBar = np.interp(volPer, [0, 100], [400, 150])
            # Chuyển đổi khoảng cách thành giá trị phần trăm (0-100)
            volPer = np.interp(length, [50, 150], [0, 100])
            # Áp dụng giá trị âm lượng cho hệ thống
            volume.SetMasterVolumeLevel(vol, None)

        # Điều khiển độ sáng dựa trên khoảng cách giữa ngón cái và ngón trỏ
        elif mode == 'brightness':
            # Chuyển đổi khoảng cách thành giá trị độ sáng (0-100)
            brightPer = int(np.interp(length, [50, 150], [0, 100]))
            # Áp dụng giá trị độ sáng cho màn hình
            sbc.set_brightness(brightPer)

        # Xử lý nhập liệu bàn phím ảo
        elif mode == 'keyboard':
            # Phát hiện khi ngón cái và ngón trỏ chạm nhau (length < 30)
            current_time = time.time()
            if length < 30 and (current_time - last_keypress_time) >= KEYPRESS_DELAY:
                for key, (x, y, w, h) in key_positions.items():
                    # Kiểm tra xem trung điểm (cx, cy) có nằm trong vùng của phím không
                    if x <= lmList[8][1] <= x + w and y <= lmList[8][2] <= y + h:
                        input_text += key  # Thêm ký tự vào chuỗi văn bản
                        pyautogui.write(key)  # Nhập ký tự bằng pyautogui
                        last_keypress_time = current_time  # Cập nhật thời gian nhấn
                        break

    # Lấy giá trị âm lượng và độ sáng hiện tại của hệ thống
    volPer = get_current_volume() if get_current_volume(
    ) is not None else 0  # Lấy âm lượng hệ thống
    # Lấy độ sáng hệ thống (giá trị đầu tiên)
    brightPer = sbc.get_brightness()[0] if sbc.get_brightness() else 0

    # Hiển thị thanh âm lượng hoặc độ sáng tùy thuộc vào chế độ
    if mode == 'volume':
        # Vẽ thanh âm lượng
        cv2.rectangle(img, (50, 150), (85, 400),
                      (255, 255, 255), 3)  # Viền trắng
        # Tính vị trí thanh âm lượng
        volBar = np.interp(volPer, [0, 100], [400, 150])
        cv2.rectangle(img, (50, int(volBar)), (85, 400),
                      (255, 215, 0), cv2.FILLED)  # Màu vàng
        cv2.putText(img, f'Volume: {int(volPer)} %', (30, 450),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 215, 0), 2)
    elif mode == 'brightness':
        # Vẽ thanh độ sáng
        cv2.rectangle(img, (50, 150), (85, 400),
                      (255, 255, 255), 3)  # Viền trắng
        # Tính vị trí thanh độ sáng
        brightBar = np.interp(brightPer, [0, 100], [400, 150])
        cv2.rectangle(img, (50, int(brightBar)), (85, 400),
                      (255, 215, 0), cv2.FILLED)  # Màu vàng
        cv2.putText(img, f'Bright: {int(brightPer)} %', (30, 450),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 215, 0), 2)

    # Vẽ các nút điều khiển
    # Nút Volume
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

    # Vẽ bàn phím ảo và cử chỉ tay
    draw_virtual_keyboard(img)

    # # Hiển thị chế độ hiện tại ở góc phải dưới
    # cv2.putText(img, f'Mode: {mode}', (620, 470),  # Tọa độ (x=620, y=470) gần góc phải dưới
    #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Hiển thị khung hình
    cv2.imshow('Control', img)

    # Thoát chương trình khi nhấn phím 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Giải phóng tài nguyên
cap.release()
cv2.destroyAllWindows()
