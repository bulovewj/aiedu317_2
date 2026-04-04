import streamlit as st
import mediapipe as mp
import cv2
import av
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

st.set_page_config(page_title="고죠 사토루 - 무량공처", layout="wide")
st.title("고죠 사토루의 영역전개")
st.markdown("고죠 사토루의 영역전개를 실행해보세요!")

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


def is_muryokusho(hand_landmarks):
    """검지, 중지만 펴져 있고 나머지는 접혀 있을 때 인식"""
    lm = hand_landmarks.landmark
    index_up = lm[8].y < lm[6].y
    middle_up = lm[12].y < lm[10].y
    ring_down = lm[16].y > lm[14].y
    pinky_down = lm[20].y > lm[18].y
    return index_up and middle_up and ring_down and pinky_down


class HandGestureProcessor(VideoProcessorBase):
    def __init__(self):
        self.hands = mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )
        self.gesture_label = ""
        self.gesture_start_time = None

    def recv(self, frame):
        import time
        img = frame.to_ndarray(format="bgr24")
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)

        detected = False
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                if is_muryokusho(hand_landmarks):
                    detected = True

        now = time.time()
        if detected:
            if self.gesture_start_time is None:
                self.gesture_start_time = now
            elapsed = now - self.gesture_start_time
            held = elapsed >= 3.0
        else:
            self.gesture_start_time = None
            elapsed = 0
            held = False

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                h, w, _ = img.shape
                x = int(hand_landmarks.landmark[0].x * w)
                y = int(hand_landmarks.landmark[0].y * h) - 20
                if detected and not held:
                    remaining = int(3 - elapsed) + 1
                    cv2.putText(img, f"Hold... {remaining}s", (x - 60, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 255), 2)
                elif held:
                    cv2.putText(img, "Unlimited Void!", (x - 60, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        self.gesture_label = "무량공처" if held else ""
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
    검지와 중지를 올리면 영역전개가 시작됩니다
</div>
"""

YOUTUBE_HTML = """
<iframe width="100%" height="420"
    src="https://www.youtube.com/embed/NOjxJ16d6NA?autoplay=1"
    frameborder="0"
    allow="autoplay; encrypted-media"
    allowfullscreen>
</iframe>
"""

with col1:
    ctx = webrtc_streamer(
        key="hand-gesture",
        video_processor_factory=HandGestureProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )
    status_placeholder = st.empty()

with col2:
    st.subheader("영역전개")
    area_placeholder = st.empty()

detected = (
    ctx.video_processor is not None
    and ctx.video_processor.gesture_label == "무량공처"
)

if detected:
    status_placeholder.markdown("## 🔮 영역전개 실행!")
    area_placeholder.markdown(YOUTUBE_HTML, unsafe_allow_html=True)
else:
    status_placeholder.markdown("")
    area_placeholder.markdown(WAIT_HTML, unsafe_allow_html=True)

# 웹캠 실행 중일 때 자동 새로고침
if ctx.state.playing:
    import time
    time.sleep(1)
    st.rerun()
