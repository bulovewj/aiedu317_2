import streamlit as st
import mediapipe as mp
import cv2
import av
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

st.set_page_config(page_title="손가락 제스처 인식", layout="centered")
st.title("✋ 손가락 제스처 인식")
st.markdown("웹캠을 켜고 손을 보여주세요!")

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


def count_fingers(hand_landmarks):
    tips = [8, 12, 16, 20]
    count = 0
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        count += 1
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            count += 1
    return count


GESTURES = {0: "✊ 주먹", 1: "☝️ 1", 2: "✌️ 2", 3: "🤟 3", 4: "🖖 4", 5: "🖐️ 5"}


class HandGestureProcessor(VideoProcessorBase):
    def __init__(self):
        self.hands = mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )
        self.gesture_label = "손을 보여주세요"

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)

        labels = []
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                count = count_fingers(hand_landmarks)
                label = GESTURES.get(count, "")
                labels.append(label)
                h, w, _ = img.shape
                x = int(hand_landmarks.landmark[0].x * w)
                y = int(hand_landmarks.landmark[0].y * h) - 20
                cv2.putText(img, label, (x - 30, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        self.gesture_label = " / ".join(labels) if labels else "손을 보여주세요"
        return av.VideoFrame.from_ndarray(img, format="bgr24")


with st.expander("인식 가능한 제스처"):
    st.markdown("""
| 제스처 | 설명 |
|---|---|
| ✊ | 주먹 | ☝️ | 1 | ✌️ | 2 | 🤟 | 3 | 🖖 | 4 | 🖐️ | 5 |
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
