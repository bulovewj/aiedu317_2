import streamlit as st
import mediapipe as mp
import cv2
import av
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

st.set_page_config(page_title="고죠 사토루 - 무량공처", layout="wide")
st.title("고죠 사토루의 영역전개")
st.markdown("양손을 카메라 앞에 펼쳐 무량공처 손 모양을 만들어보세요!")

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


def all_fingers_extended(hand_landmarks):
    """5개 손가락 모두 펴져 있는지 확인"""
    tips = [8, 12, 16, 20]
    # 엄지
    if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x:
        return False
    # 나머지 4손가락
    for tip in tips:
        if hand_landmarks.landmark[tip].y > hand_landmarks.landmark[tip - 2].y:
            return False
    return True


class HandGestureProcessor(VideoProcessorBase):
    def __init__(self):
        self.hands = mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )
        self.gesture_label = ""

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)

        detected = False
        if results.multi_hand_landmarks and len(results.multi_hand_landmarks) == 2:
            both_open = all(
                all_fingers_extended(hl) for hl in results.multi_hand_landmarks
            )
            if both_open:
                detected = True

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                color = (0, 255, 255) if detected else (0, 200, 0)
                mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                h, w, _ = img.shape
                x = int(hand_landmarks.landmark[0].x * w)
                y = int(hand_landmarks.landmark[0].y * h) - 20
                if detected:
                    cv2.putText(img, "무량공처!", (x - 40, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        self.gesture_label = "무량공처" if detected else ""
        return av.VideoFrame.from_ndarray(img, format="bgr24")


# --- 레이아웃 ---
col1, col2 = st.columns(2)

VOID_HTML = """
<style>
@keyframes expand {
    0%   { transform: scale(0.8); opacity: 0.4; }
    50%  { transform: scale(1.05); opacity: 1; }
    100% { transform: scale(0.8); opacity: 0.4; }
}
@keyframes rotate {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
}
@keyframes rotate-rev {
    from { transform: rotate(0deg); }
    to   { transform: rotate(-360deg); }
}
.void-container {
    background: radial-gradient(ellipse at center, #1a0033 0%, #000000 70%);
    width: 100%;
    height: 420px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
    animation: expand 3s ease-in-out infinite;
}
.ring {
    position: absolute;
    border-radius: 50%;
    border: 2px solid rgba(160, 80, 255, 0.6);
}
.ring1 { width:80px;  height:80px;  animation: rotate 4s linear infinite; }
.ring2 { width:150px; height:150px; animation: rotate-rev 6s linear infinite; border-color: rgba(100,50,200,0.5);}
.ring3 { width:230px; height:230px; animation: rotate 9s linear infinite; border-color: rgba(80,0,180,0.4);}
.ring4 { width:320px; height:320px; animation: rotate-rev 12s linear infinite; border-color: rgba(60,0,140,0.3);}
.ring5 { width:420px; height:420px; animation: rotate 16s linear infinite; border-color: rgba(40,0,100,0.2);}
.void-text {
    position: absolute;
    color: rgba(220, 180, 255, 0.95);
    font-size: 28px;
    font-weight: bold;
    letter-spacing: 8px;
    text-shadow: 0 0 20px #a050ff, 0 0 40px #7000ff;
    z-index: 10;
    font-family: serif;
}
.void-sub {
    position: absolute;
    bottom: 40px;
    color: rgba(180, 140, 255, 0.7);
    font-size: 13px;
    letter-spacing: 4px;
}
</style>
<div class="void-container">
    <div class="ring ring1"></div>
    <div class="ring ring2"></div>
    <div class="ring ring3"></div>
    <div class="ring ring4"></div>
    <div class="ring ring5"></div>
    <div class="void-text">무 량 공 처</div>
    <div class="void-sub">Unlimited Void</div>
</div>
"""

WAIT_HTML = """
<div style="
    background: #0e0e0e;
    width: 100%;
    height: 420px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #444;
    font-size: 18px;
    letter-spacing: 3px;
    font-family: serif;
    border: 1px solid #222;
">
    양손을 펼치면 영역전개가 시작됩니다
</div>
"""

with col1:
    ctx = webrtc_streamer(
        key="hand-gesture",
        video_processor_factory=HandGestureProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

with col2:
    st.subheader("영역전개")
    area_placeholder = st.empty()

    if ctx.video_processor and ctx.video_processor.gesture_label == "무량공처":
        area_placeholder.markdown(VOID_HTML, unsafe_allow_html=True)
    else:
        area_placeholder.markdown(WAIT_HTML, unsafe_allow_html=True)
