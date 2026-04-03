import streamlit as st
import mediapipe as mp
import cv2
import av
import os
import urllib.request
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

st.set_page_config(page_title="손가락 제스처 인식", layout="centered")
st.title("✋ 손가락 제스처 인식")
st.markdown("웹캠을 켜고 손을 보여주세요!")

# 모델 다운로드
MODEL_PATH = "hand_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

if not os.path.exists(MODEL_PATH):
    with st.spinner("모델 다운로드 중... (최초 1회)"):
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

# 손 연결선 정의
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20),
    (5,9),(9,13),(13,17),
]

GESTURES = {0: "✊ 주먹", 1: "☝️ 1", 2: "✌️ 2", 3: "🤟 3", 4: "🖖 4", 5: "🖐️ 5"}


def count_fingers(landmarks):
    tips = [8, 12, 16, 20]
    count = 0
    if landmarks[4].x < landmarks[3].x:
        count += 1
    for tip in tips:
        if landmarks[tip].y < landmarks[tip - 2].y:
            count += 1
    return count


def draw_landmarks(img, landmarks, h, w):
    points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    for start, end in HAND_CONNECTIONS:
        cv2.line(img, points[start], points[end], (0, 200, 0), 2)
    for pt in points:
        cv2.circle(img, pt, 5, (255, 255, 255), -1)
        cv2.circle(img, pt, 5, (0, 150, 0), 1)


class HandGestureProcessor(VideoProcessorBase):
    def __init__(self):
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)
        self.timestamp = 0
        self.gesture_label = "손을 보여주세요"

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        h, w, _ = img.shape
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        self.timestamp += 33
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        result = self.landmarker.detect_for_video(mp_image, self.timestamp)

        labels = []
        if result.hand_landmarks:
            for landmarks in result.hand_landmarks:
                draw_landmarks(img, landmarks, h, w)
                count = count_fingers(landmarks)
                label = GESTURES.get(count, "")
                labels.append(label)
                x = int(landmarks[0].x * w)
                y = int(landmarks[0].y * h) - 20
                cv2.putText(img, label, (x - 30, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        self.gesture_label = " / ".join(labels) if labels else "손을 보여주세요"
        return av.VideoFrame.from_ndarray(img, format="bgr24")


with st.expander("인식 가능한 제스처"):
    st.markdown("""
| 제스처 | 설명 |
|---|---|
| ✊ | 주먹 |
| ☝️ | 1 |
| ✌️ | 2 |
| 🤟 | 3 |
| 🖖 | 4 |
| 🖐️ | 5 |
""")

ctx = webrtc_streamer(
    key="hand-gesture",
    video_processor_factory=HandGestureProcessor,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)

if ctx.video_processor:
    st.subheader("인식된 제스처:")
    st.markdown(f"## {ctx.video_processor.gesture_label}")
