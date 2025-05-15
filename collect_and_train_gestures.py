import cv2
import numpy as np
import pandas as pd
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import setup_hand_tracker
import os

# Khởi tạo Hand Tracker
detector = setup_hand_tracker.HandTracker(detectionCon=0.7)

# Danh sách cử chỉ
GESTURES = ["swipe_left", "swipe_right", "fist", "open_hand"]
NUM_SAMPLES_PER_GESTURE = 100  # Số mẫu mỗi cử chỉ

# Hàm thu thập dữ liệu (giữ nguyên từ mã gốc)
def collect_gesture_data():
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    data = []
    
    for gesture in GESTURES:
        print(f"Thu thập dữ liệu cho cử chỉ: {gesture}")
        print("Nhấn 's' để bắt đầu thu thập, 'q' để thoát")
        while True:
            ret, img = cap.read()
            if not ret:
                break
            img = cv2.flip(img, 1)
            cv2.putText(img, f"Gesture: {gesture}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Collect Data", img)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                print(f"Đang thu thập {NUM_SAMPLES_PER_GESTURE} mẫu cho {gesture}...")
                count = 0
                while count < NUM_SAMPLES_PER_GESTURE:
                    ret, img = cap.read()
                    if not ret:
                        break
                    img = cv2.flip(img, 1)
                    img = detector.handsFinder(img)
                    lmList = detector.positionFinder(img, draw=False)
                    
                    if lmList:
                        landmarks = []
                        for lm in lmList:
                            landmarks.extend([lm[1], lm[2]])  # x, y
                        data.append(landmarks + [gesture])
                        count += 1
                        cv2.putText(img, f"Sample: {count}/{NUM_SAMPLES_PER_GESTURE}", (10, 100), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.imshow("Collect Data", img)
                    cv2.waitKey(1)
            elif key == ord('q'):
                break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Lưu dữ liệu vào CSV
    df = pd.DataFrame(data, columns=[f"lm_{i}" for i in range(42)] + ["gesture"])
    df.to_csv("gesture_data.csv", index=False)
    print("Dữ liệu đã được lưu vào gesture_data.csv")

# Hàm huấn luyện mô hình với SVM
def train_gesture_model():
    # Đọc dữ liệu
    df = pd.read_csv("gesture_data.csv")
    X = df.iloc[:, :-1].values  # Tọa độ landmark
    y = df["gesture"].values  # Nhãn cử chỉ
    
    # Chuyển nhãn thành số
    gesture_to_idx = {g: i for i, g in enumerate(GESTURES)}
    y = np.array([gesture_to_idx[g] for g in y])
    
    # Chia dữ liệu
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Huấn luyện mô hình SVM
    model = SVC(kernel='rbf', probability=True, random_state=42)  # Sử dụng kernel RBF
    model.fit(X_train, y_train)
    
    # Đánh giá mô hình
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy trên tập kiểm tra: {accuracy:.2f}")
    
    # Lưu mô hình
    joblib.dump(model, "gesture_model_svm.joblib")
    print("Mô hình SVM đã được lưu vào gesture_model_svm.joblib")

if __name__ == "__main__":
    if not os.path.exists("gesture_data.csv"):
        collect_gesture_data()
    train_gesture_model()