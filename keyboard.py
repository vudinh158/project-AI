import cv2
import mediapipe as mp
from pynput.keyboard import Controller
from time import sleep
import numpy as np

# Class HandTracker using Mediapipe


class HandTracker():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, modelComplexity=1, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.modelComplex = modelComplexity
        self.trackCon = trackCon
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.modelComplex,
                                        self.detectionCon, self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils

    def handsFinder(self, image, draw=True):
        imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imageRGB)
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(
                        image, handLms, self.mpHands.HAND_CONNECTIONS)
        return image

    def positionFinder(self, image, handNo=0, draw=True):
        lmlist = []
        if self.results.multi_hand_landmarks:
            Hand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(Hand.landmark):
                h, w, c = image.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmlist.append([id, cx, cy])
            if draw:
                for id, lm in enumerate(Hand.landmark):
                    cv2.circle(image, (int(lm.x * w), int(lm.y * h)),
                               15, (255, 0, 255), cv2.FILLED)
        return lmlist

    def findDistance(self, index1, index2, image, draw=True):
        x1, y1 = self.results.multi_hand_landmarks[0].landmark[
            index1].x, self.results.multi_hand_landmarks[0].landmark[index1].y
        x2, y2 = self.results.multi_hand_landmarks[0].landmark[
            index2].x, self.results.multi_hand_landmarks[0].landmark[index2].y
        distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        return distance

# Class Button


class Button():
    def __init__(self, pos, text, size=[50, ]):
        self.pos = pos
        self.size = size
        self.text = text

# Function to draw buttons on the image


def drawAll(img, buttonList):
    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        cv2.rectangle(img, button.pos, (x + w, y + h),
                      (255, 0, 255), cv2.FILLED)
        cv2.putText(img, button.text, (x + 30, y + 80),
                    cv2.FONT_HERSHEY_PLAIN, 5, (255, 255, 255), 5)
    return img

# Main function to run the virtual keyboard


def main():
    cap = cv2.VideoCapture(0)
    tracker = HandTracker()
    keyboard = Controller()

    # Define keys
    keys = [["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
            ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "<"],
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]]

    buttonList = []
    for i in range(len(keys)):
        for j, key in enumerate(keys[i]):
            buttonList.append(Button([130 * j + 50, 130 * i + 50], key))

    finalText = ""

    # Create window and set it to fullscreen
    cv2.namedWindow("Video", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(
        "Video", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        success, img = cap.read()
        img = tracker.handsFinder(img)
        lmList = tracker.positionFinder(img, draw=False)

        # Draw buttons on the screen
        img = drawAll(img, buttonList)

        if len(lmList) != 0:
            # Check each button's position
            for button in buttonList:
                x, y = button.pos
                w, h = button.size

                # Check if finger is over the button
                if x < lmList[8][1] < x + w and y < lmList[8][2] < y + h:
                    cv2.rectangle(img, (x - 5, y - 5), (x + w + 5,
                                  y + h + 5), (175, 0, 175), cv2.FILLED)
                    cv2.putText(img, button.text, (x + 30, y + 80),
                                cv2.FONT_HERSHEY_PLAIN, 5, (255, 255, 255), 5)
                    # Check distance between index and thumb
                    l = tracker.findDistance(8, 12, img)

                    if l < 0.1:  # When the index finger and thumb are close enough
                        keyboard.press(button.text)
                        cv2.rectangle(img, button.pos,
                                      (x + w, y + h), (0, 255, 0), cv2.FILLED)
                        cv2.putText(img, button.text, (x + 30, y + 80),
                                    cv2.FONT_HERSHEY_PLAIN, 5, (255, 255, 255), 5)

                        if button.text == '<':
                            if len(finalText) != 0:
                                finalText = finalText[0:len(finalText)-1]
                        else:
                            finalText += button.text
                        sleep(0.5)

        # Show the typed text
        cv2.rectangle(img, (50, 350), (700, 450), (175, 0, 175), cv2.FILLED)
        cv2.putText(img, finalText, (60, 430),
                    cv2.FONT_HERSHEY_PLAIN, 5, (255, 255, 255), 5)

        # Display the image
        cv2.imshow("Video", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
