import streamlit as st
import anthropic
import base64
import json
import math
import time
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import av
import cv2
import numpy as np
import mediapipe as mp

# ──────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────
st.set_page_config(
    page_title="呪術廻戦 領域展開",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────
# CSS / 애니메이션 스타일
# ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;700;900&display=swap');

:root {
    --domain-color: #8B0000;
    --glow-color: #FF4500;
    --accent: #FFD700;
}

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0a0a !important;
    color: #e0e0e0;
}

[data-testid="stSidebar"] {
    background: #111 !important;
    border-right: 1px solid #333;
}

h1, h2, h3 { color: #c0392b !important; }

/* ── 영역전개 오버레이 ── */
#domain-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: none;
    pointer-events: none;
    overflow: hidden;
}

#domain-overlay.active { display: block; }

/* 배경 파동 */
.domain-bg {
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at center,
        rgba(139,0,0,0.95) 0%,
        rgba(20,0,0,0.98) 60%,
        rgba(0,0,0,1) 100%);
    animation: domainPulse 2s ease-in-out infinite alternate;
}

@keyframes domainPulse {
    from { opacity: 0.85; }
    to   { opacity: 1; }
}

/* 균열 선들 */
.crack {
    position: absolute;
    background: linear-gradient(90deg, transparent, #FF4500, transparent);
    height: 1px;
    width: 100%;
    animation: crackFlicker 0.3s infinite;
    transform-origin: center;
}
@keyframes crackFlicker {
    0%,100% { opacity:1; }
    50%      { opacity:0.3; }
}

/* 주문(呪文) 원형 */
.curse-circle {
    position: absolute;
    top: 50%; left: 50%;
    border: 2px solid rgba(255,69,0,0.6);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    animation: circleRotate 8s linear infinite;
}
@keyframes circleRotate {
    from { transform: translate(-50%,-50%) rotate(0deg); }
    to   { transform: translate(-50%,-50%) rotate(360deg); }
}

/* 주술 텍스트 */
.domain-text {
    position: absolute;
    top: 45%; left: 50%;
    transform: translate(-50%, -50%);
    font-family: 'Noto Serif JP', serif;
    font-size: clamp(2rem, 6vw, 5rem);
    font-weight: 900;
    color: #FFD700;
    text-shadow:
        0 0 10px #FF4500,
        0 0 30px #FF4500,
        0 0 60px #8B0000,
        0 0 100px #FF0000;
    white-space: nowrap;
    animation: textAppear 1s ease-out forwards, textGlow 2s ease-in-out infinite alternate 1s;
    opacity: 0;
    letter-spacing: 0.3em;
}
@keyframes textAppear {
    from { opacity:0; transform:translate(-50%,-50%) scale(0.5); }
    to   { opacity:1; transform:translate(-50%,-50%) scale(1); }
}
@keyframes textGlow {
    from { text-shadow: 0 0 10px #FF4500, 0 0 30px #FF4500; }
    to   { text-shadow: 0 0 20px #FFD700, 0 0 60px #FF4500, 0 0 100px #FF0000; }
}

/* 부제목 */
.domain-subtitle {
    position: absolute;
    top: 58%; left: 50%;
    transform: translateX(-50%);
    font-family: 'Noto Serif JP', serif;
    font-size: clamp(1rem, 3vw, 2rem);
    color: rgba(255,215,0,0.8);
    text-align: center;
    animation: textAppear 1.5s ease-out 0.5s forwards;
    opacity: 0;
    letter-spacing: 0.2em;
}

/* 닫기 버튼 */
.domain-close {
    position: absolute;
    top: 20px; right: 30px;
    font-size: 2rem;
    color: rgba(255,215,0,0.7);
    cursor: pointer;
    pointer-events: all;
    z-index: 10000;
    transition: color 0.2s;
}
.domain-close:hover { color: #FFD700; }

/* 부유 입자 */
.particle {
    position: absolute;
    border-radius: 50%;
    background: rgba(255,69,0,0.8);
    animation: floatUp linear infinite;
    pointer-events: none;
}
@keyframes floatUp {
    from { transform: translateY(100vh) scale(1); opacity: 0.8; }
    to   { transform: translateY(-10vh) scale(0); opacity: 0; }
}

/* ── 상태 표시 배지 ── */
.status-badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: bold;
    letter-spacing: 0.05em;
    margin: 4px;
}
.badge-active   { background:#8B0000; color:#FFD700; border:1px solid #FF4500; }
.badge-inactive { background:#1a1a1a; color:#888;    border:1px solid #333; }
.badge-detected { background:#1a4a1a; color:#00FF00; border:1px solid #00AA00; }

/* ── 손 포즈 카드 ── */
.pose-card {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 12px;
    margin: 6px 0;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
}
.pose-card:hover, .pose-card.selected {
    border-color: #FF4500;
    background: #2a1010;
}
.pose-card-title { color: #FFD700; font-weight: bold; font-size:1rem; }
.pose-card-desc  { color: #aaa;    font-size: 0.8rem; margin-top:4px; }

/* ── 웹캠 컨테이너 ── */
.webcam-frame {
    border: 2px solid #8B0000;
    border-radius: 8px;
    box-shadow: 0 0 20px rgba(139,0,0,0.5), 0 0 40px rgba(139,0,0,0.2);
    overflow: hidden;
}

/* ── 커스텀 버튼 ── */
.stButton > button {
    background: linear-gradient(135deg, #8B0000, #4a0000) !important;
    color: #FFD700 !important;
    border: 1px solid #FF4500 !important;
    border-radius: 8px !important;
    font-weight: bold !important;
    letter-spacing: 0.1em !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #c0392b, #8B0000) !important;
    box-shadow: 0 0 15px rgba(255,69,0,0.5) !important;
}

/* 구분선 */
hr { border-color: #333 !important; }

/* 정보 박스 */
.info-box {
    background: #1a1a1a;
    border-left: 3px solid #FF4500;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    margin: 8px 0;
    font-size: 0.9rem;
    color: #ccc;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# 영역전개 오버레이 HTML / JS
# ──────────────────────────────────────────
DOMAIN_OVERLAY_HTML = """
<div id="domain-overlay">
  <!-- 배경 -->
  <div class="domain-bg"></div>

  <!-- 균열들 -->
  <div class="crack" style="top:20%;transform:rotate(-15deg);opacity:0.7;"></div>
  <div class="crack" style="top:35%;transform:rotate(8deg);opacity:0.5;"></div>
  <div class="crack" style="top:65%;transform:rotate(-5deg);opacity:0.6;"></div>
  <div class="crack" style="top:80%;transform:rotate(12deg);opacity:0.4;"></div>

  <!-- 동심원 -->
  <div class="curse-circle" style="width:300px;height:300px;animation-duration:6s;"></div>
  <div class="curse-circle" style="width:500px;height:500px;animation-duration:10s;animation-direction:reverse;"></div>
  <div class="curse-circle" style="width:700px;height:700px;animation-duration:14s;border-style:dashed;"></div>
  <div class="curse-circle" style="width:900px;height:900px;animation-duration:18s;animation-direction:reverse;border-style:dotted;"></div>

  <!-- 텍스트 -->
  <div class="domain-text" id="domain-main-text">領域展開</div>
  <div class="domain-subtitle" id="domain-sub-text">無量空処</div>

  <!-- 입자들 (JS로 동적 생성) -->
  <div id="particles-container"></div>

  <!-- 닫기 -->
  <span class="domain-close" onclick="closeDomain()">✕</span>
</div>

<script>
// ── 입자 생성 ──
function createParticles() {
    const container = document.getElementById('particles-container');
    if (!container) return;
    container.innerHTML = '';
    for (let i = 0; i < 60; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        const size = Math.random() * 8 + 2;
        p.style.cssText = `
            width:${size}px; height:${size}px;
            left:${Math.random()*100}%;
            animation-duration:${Math.random()*4+3}s;
            animation-delay:${Math.random()*3}s;
            background:rgba(${Math.random()>0.5?'255,69,0':'255,215,0'},0.8);
        `;
        container.appendChild(p);
    }
}

// ── 영역전개 실행 ──
function activateDomain(mainText, subText) {
    const overlay = document.getElementById('domain-overlay');
    const mt = document.getElementById('domain-main-text');
    const st = document.getElementById('domain-sub-text');
    if (!overlay) return;
    if (mt && mainText) mt.textContent = mainText;
    if (st && subText)  st.textContent = subText;
    createParticles();
    overlay.classList.add('active');
    // 사운드 효과 (Web Audio API)
    try { playDomainSound(); } catch(e) {}
    // 자동 닫기 (10초)
    clearTimeout(window._domainTimer);
    window._domainTimer = setTimeout(closeDomain, 10000);
}

// ── 닫기 ──
function closeDomain() {
    const overlay = document.getElementById('domain-overlay');
    if (overlay) overlay.classList.remove('active');
}

// ── Web Audio: 저음 폭발 효과 ──
function playDomainSound() {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    // 저음 붐
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.type = 'sawtooth';
    osc1.frequency.setValueAtTime(60, ctx.currentTime);
    osc1.frequency.exponentialRampToValueAtTime(20, ctx.currentTime + 1.5);
    gain1.gain.setValueAtTime(0.4, ctx.currentTime);
    gain1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.5);
    osc1.connect(gain1); gain1.connect(ctx.destination);
    osc1.start(); osc1.stop(ctx.currentTime + 1.5);
    // 고음 파열
    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.type = 'square';
    osc2.frequency.setValueAtTime(800, ctx.currentTime);
    osc2.frequency.exponentialRampToValueAtTime(200, ctx.currentTime + 0.5);
    gain2.gain.setValueAtTime(0.2, ctx.currentTime);
    gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
    osc2.connect(gain2); gain2.connect(ctx.destination);
    osc2.start(); osc2.stop(ctx.currentTime + 0.5);
}

// ── Streamlit 메시지 수신 ──
window.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'ACTIVATE_DOMAIN') {
        activateDomain(e.data.mainText, e.data.subText);
    }
    if (e.data && e.data.type === 'CLOSE_DOMAIN') {
        closeDomain();
    }
});
</script>
"""

# ──────────────────────────────────────────
# 영역전개 정보 (캐릭터별)
# ──────────────────────────────────────────
DOMAIN_INFO = {
    "무량공처 (五条悟)": {
        "main": "無量空処",
        "sub": "「私が最強ですので」",
        "desc": "고죠 사토루의 영역전개. 무한을 내재화하여 감각 정보를 무한히 처리하게 만들어 뇌를 마비시킨다.",
        "color": "#00BFFF",
        "hand_pose": "양손을 얼굴 앞에서 마주보게 모은 후, 손가락을 서로 끼운 형태",
        "emoji": "🔵"
    },
    "폐옥염정 (伏黒恵)": {
        "main": "嵌合暗翳庭",
        "sub": "「十種影法術」",
        "desc": "후시구로 메구미의 영역전개. 십종영법술로 만든 식신들의 세계를 펼친다.",
        "color": "#1a1a2e",
        "hand_pose": "검지와 중지를 교차시키고 나머지는 접는 인(印) 형태",
        "emoji": "🌑"
    },
    "자충玫 (釘崎野薔薇)": {
        "main": "蝶蛆嵐",
        "sub": "「共鳴り」",
        "desc": "쿠기사키 노바라의 공명 기법. 못을 통해 원거리 타격.",
        "color": "#8B0000",
        "hand_pose": "한 손은 주먹, 다른 손은 검지만 펴서 찌르는 자세",
        "emoji": "🔴"
    },
    "흉흉욕식 (漏瑚)": {
        "main": "凶凶呪胎",
        "sub": "「特級呪霊」",
        "desc": "조로의 영역전개. 용암과 화염으로 가득한 세계를 펼친다.",
        "color": "#FF4500",
        "hand_pose": "두 손 손가락 전체를 크게 벌린 채 위로 들어올리는 자세",
        "emoji": "🔥"
    },
    "자수밀원 (真人)": {
        "main": "自閉円頓裹",
        "sub": "「無為転変」",
        "desc": "마히토의 영역전개. 영혼을 직접 조작하는 무위전변.",
        "color": "#9B59B6",
        "hand_pose": "양손을 가슴 앞에서 원을 그리며 마주보는 형태",
        "emoji": "🟣"
    },
}

# ──────────────────────────────────────────
# MediaPipe 손 인식 프로세서
# ──────────────────────────────────────────
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

class HandGestureProcessor(VideoProcessorBase):
    """WebRTC 비디오 프레임에서 손 랜드마크를 추출하고 오버레이한다."""

    def __init__(self):
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5,
        )
        self.last_gesture = "없음"
        self.gesture_score = 0.0
        self.domain_active = False
        self.frame_count = 0
        self.detected_domain = None
        self._lock = False

    # ── 손가락 펴짐 여부 판단 ──
    @staticmethod
    def _finger_extended(lm, tip_id, pip_id):
        return lm[tip_id].y < lm[pip_id].y  # 위로 펴졌으면 True

    # ── 영역전개 손동작 감지 ──
    def detect_domain_gesture(self, hands_results) -> tuple[str, float]:
        if not hands_results.multi_hand_landmarks:
            return "없음", 0.0

        num_hands = len(hands_results.multi_hand_landmarks)
        lms_list = [h.landmark for h in hands_results.multi_hand_landmarks]

        # 각 손의 손가락 펴짐 상태
        fingers_state = []
        for lm in lms_list:
            ext = [
                self._finger_extended(lm, 8, 6),   # 검지
                self._finger_extended(lm, 12, 10),  # 중지
                self._finger_extended(lm, 16, 14),  # 약지
                self._finger_extended(lm, 20, 18),  # 소지
            ]
            # 엄지: x축 비교
            thumb_ext = lm[4].x < lm[3].x if lm[17].x > lm[5].x else lm[4].x > lm[3].x
            ext.insert(0, thumb_ext)
            fingers_state.append(ext)

        extended_counts = [sum(f) for f in fingers_state]

        # ── 고죠: 양손 손가락 교차 (양손 손가락 3~5개) ──
        if num_hands == 2:
            total = sum(extended_counts)
            if 6 <= total <= 10:
                return "무량공처 (五条悟)", min(1.0, total / 10)

        # ── 후시구로: 한 손, 검지+중지 교차, 나머지 접음 ──
        for fs in fingers_state:
            if fs[1] and fs[2] and not fs[3] and not fs[4]:
                return "폐옥염정 (伏黒恵)", 0.85

        # ── 흉흉욕식: 양손 모두 활짝 ──
        if num_hands == 2 and all(c == 5 for c in extended_counts):
            return "흉흉욕식 (漏瑚)", 0.95

        # ── 자수밀원: 한 손, 모든 손가락 오므림 (주먹) ──
        for fs in fingers_state:
            if sum(fs) == 0:
                return "자수밀원 (真人)", 0.75

        # ── 쿠기사키: 한 손 주먹 + 한 손 검지만 폄 ──
        if num_hands == 2:
            cnts = sorted(extended_counts)
            if cnts[0] == 0 and cnts[1] == 1:
                return "자충玫 (釘崎野薔薇)", 0.80

        # 손은 있지만 특정 패턴 없음
        return "손 감지됨", 0.3

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)  # 좌우 반전 (거울 효과)
        self.frame_count += 1

        h, w = img.shape[:2]
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        gesture, score = self.detect_domain_gesture(results)
        self.last_gesture = gesture
        self.gesture_score = score

        # 영역 활성화 판단
        if score >= 0.75 and gesture in DOMAIN_INFO:
            self.domain_active = True
            self.detected_domain = gesture
        else:
            self.domain_active = False

        # ── 랜드마크 그리기 ──
        if results.multi_hand_landmarks:
            for hl in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    img, hl, mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style(),
                )

        # ── 손목 위에 텍스트 ──
        if results.multi_hand_landmarks:
            for hl in results.multi_hand_landmarks:
                wrist = hl.landmark[0]
                cx, cy = int(wrist.x * w), int(wrist.y * h)
                cv2.putText(img, gesture, (cx - 80, cy - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (0, 255, 255) if score >= 0.75 else (200, 200, 200),
                            2, cv2.LINE_AA)

        # ── 상태 바 ──
        bar_color = (0, 0, 180) if score < 0.5 else (0, 100, 255) if score < 0.75 else (0, 30, 200)
        bar_w = int(w * score)
        cv2.rectangle(img, (0, h - 8), (w, h), (30, 30, 30), -1)
        cv2.rectangle(img, (0, h - 8), (bar_w, h), bar_color, -1)

        # ── 영역전개 활성 시 빨간 테두리 ──
        if self.domain_active:
            thickness = max(4, int(8 * score))
            cv2.rectangle(img, (0, 0), (w - 1, h - 1), (0, 0, 200), thickness)
            cv2.putText(img, "領域展開 !", (w // 2 - 120, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 50, 255), 3, cv2.LINE_AA)

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ──────────────────────────────────────────
# Claude AI 분석 함수
# ──────────────────────────────────────────
def analyze_with_claude(api_key: str, user_query: str, context: str = "") -> str:
    """Claude Sonnet 4로 주술회전 관련 질의응답."""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        system_prompt = """당신은 주술회전(呪術廻戦) 전문 AI 보조사입니다.
영역전개, 술식, 주술사 등 주술회전 세계관을 깊이 이해하고 있습니다.
한국어로 친절하고 상세하게 답변하세요.
영역전개 손동작에 대한 분석이나 설명을 요청받으면 구체적으로 알려주세요."""

        messages = [{"role": "user", "content": user_query}]
        if context:
            messages[0]["content"] = f"[현재 감지된 손동작: {context}]\n\n{user_query}"

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        return f"❌ Claude API 오류: {str(e)}"


# ──────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔮 呪術廻戦 設定")
    st.markdown("---")

    # API 키 입력
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Claude AI 분석 기능을 사용하려면 API 키가 필요합니다.",
    )
    if api_key:
        st.markdown('<span class="status-badge badge-active">✅ API 연결됨</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge badge-inactive">⚪ API 미연결</span>', unsafe_allow_html=True)

    st.markdown("---")

    # 영역전개 캐릭터 선택
    st.markdown("#### ⚔️ 영역전개 선택")
    selected_domain = st.selectbox(
        "캐릭터 영역 선택",
        list(DOMAIN_INFO.keys()),
        index=0,
    )
    info = DOMAIN_INFO[selected_domain]
    st.markdown(f"""
<div class="info-box">
  <b>{info['emoji']} {selected_domain}</b><br>
  <span style="color:#FFD700;font-size:1.1em;">{info['main']}</span><br>
  <small style="color:#aaa;">{info['sub']}</small><br><br>
  <span style="color:#ccc;font-size:0.85em;">{info['desc']}</span><br><br>
  <span style="color:#888;font-size:0.8em;">📌 손동작: {info['hand_pose']}</span>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # 수동 발동 버튼
    st.markdown("#### 🎮 수동 제어")
    if st.button("🔥 영역전개 발동!", use_container_width=True):
        st.session_state.trigger_domain = True
        st.session_state.domain_main = info["main"]
        st.session_state.domain_sub = info["sub"]

    if st.button("❌ 영역 해제", use_container_width=True):
        st.session_state.trigger_close = True

    st.markdown("---")
    st.markdown("""
<div style="color:#666;font-size:0.75em;line-height:1.6;">
📹 <b>웹캠 손동작 가이드</b><br>
• 양손 손가락 교차 → 무량공처<br>
• 검지+중지만 폄 → 폐옥염정<br>
• 양손 활짝 → 흉흉욕식<br>
• 주먹 쥐기 → 자수밀원<br>
• 주먹+검지 → 자충玫
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────
# Session State 초기화
# ──────────────────────────────────────────
for key, val in {
    "trigger_domain": False,
    "trigger_close": False,
    "domain_main": "領域展開",
    "domain_sub": "無量空処",
    "chat_history": [],
    "last_gesture": "없음",
}.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ──────────────────────────────────────────
# 메인 UI
# ──────────────────────────────────────────
st.markdown("<h1 style='text-align:center;letter-spacing:0.3em;'>⚔️ 呪術廻戦 領域展開 ⚔️</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#888;'>손동작으로 영역전개를 발동하세요</p>", unsafe_allow_html=True)
st.markdown("---")

# 오버레이 삽입
st.components.v1.html(DOMAIN_OVERLAY_HTML, height=0)

# 영역전개 트리거 JS
if st.session_state.get("trigger_domain"):
    st.session_state.trigger_domain = False
    main_t = st.session_state.domain_main
    sub_t  = st.session_state.domain_sub
    st.components.v1.html(f"""
<script>
(function(){{
    function send(){{
        window.parent.postMessage({{
            type:'ACTIVATE_DOMAIN',
            mainText:'{main_t}',
            subText:'{sub_t}'
        }}, '*');
    }}
    // iframe 내부 → 부모로 전달
    if (window.parent !== window) {{ send(); }}
    else {{ activateDomain('{main_t}', '{sub_t}'); }}
}})();
</script>
""", height=0)

if st.session_state.get("trigger_close"):
    st.session_state.trigger_close = False
    st.components.v1.html("""
<script>
if(window.parent!==window)
    window.parent.postMessage({type:'CLOSE_DOMAIN'},'*');
else closeDomain();
</script>
""", height=0)

# ──────────────────────────────────────────
# 탭 구성
# ──────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📹 웹캠 손동작 인식", "💬 AI 주술 분석", "📖 영역전개 도감"])

# ════════════════════════════════════════
# TAB 1 : 웹캠
# ════════════════════════════════════════
with tab1:
    col_cam, col_info = st.columns([3, 2])

    with col_cam:
        st.markdown("### 📷 실시간 손 인식")
        st.markdown('<div class="info-box">💡 웹캠을 켜고 손동작을 취하면 영역전개가 자동 발동됩니다!</div>', unsafe_allow_html=True)

        # RTC 설정
        rtc_config = RTCConfiguration(
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        )

        ctx = webrtc_streamer(
            key="domain-cam",
            video_processor_factory=HandGestureProcessor,
            rtc_configuration=rtc_config,
            media_stream_constraints={
                "video": {"width": 640, "height": 480},
                "audio": False,
            },
            async_processing=True,
        )

        # 영역전개 자동 발동 로직
        if ctx.video_processor:
            proc: HandGestureProcessor = ctx.video_processor
            gesture  = proc.last_gesture
            score    = proc.gesture_score
            is_active = proc.domain_active

            st.session_state.last_gesture = gesture

            if is_active and gesture in DOMAIN_INFO:
                d = DOMAIN_INFO[gesture]
                st.session_state.trigger_domain = True
                st.session_state.domain_main = d["main"]
                st.session_state.domain_sub  = d["sub"]
                st.rerun()

    with col_info:
        st.markdown("### 🔍 감지 정보")

        g = st.session_state.get("last_gesture", "없음")
        if g in DOMAIN_INFO:
            d = DOMAIN_INFO[g]
            badge_cls = "badge-detected"
            badge_txt = f"✅ {g} 감지!"
        elif g == "손 감지됨":
            badge_cls = "badge-inactive"
            badge_txt = "👋 손 감지됨 (인식 중...)"
        else:
            badge_cls = "badge-inactive"
            badge_txt = "⚪ 손동작 없음"

        st.markdown(f'<span class="status-badge {badge_cls}">{badge_txt}</span>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # 각 영역전개 포즈 안내
        st.markdown("#### 📋 포즈 가이드")
        for name, data in DOMAIN_INFO.items():
            is_sel = (g == name)
            cls = "pose-card selected" if is_sel else "pose-card"
            st.markdown(f"""
<div class="{cls}">
  <div class="pose-card-title">{data['emoji']} {name}</div>
  <div class="pose-card-desc">{data['hand_pose']}</div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
<div class="info-box">
<b>🎯 인식 팁</b><br>
• 밝은 배경에서 선명하게<br>
• 카메라 30cm~1m 거리<br>
• 천천히 손동작 완성<br>
• 75% 이상 신뢰도 시 발동
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════
# TAB 2 : AI 채팅
# ════════════════════════════════════════
with tab2:
    st.markdown("### 💬 주술 AI 상담사")
    st.markdown('<div class="info-box">🤖 주술회전 세계관, 영역전개, 손동작에 대해 Claude AI에게 물어보세요!</div>', unsafe_allow_html=True)

    # 채팅 기록 표시
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            role = msg["role"]
            content = msg["content"]
            with st.chat_message(role, avatar="🔮" if role == "assistant" else "👤"):
                st.markdown(content)

    # 입력
    if prompt := st.chat_input("영역전개에 대해 궁금한 점을 물어보세요..."):
        if not api_key:
            st.error("❌ 사이드바에서 Anthropic API 키를 입력해주세요.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            context = st.session_state.get("last_gesture", "없음")
            with st.chat_message("assistant", avatar="🔮"):
                with st.spinner("주술 분석 중..."):
                    reply = analyze_with_claude(api_key, prompt, context)
                st.markdown(reply)

            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            st.rerun()

    # 빠른 질문 버튼
    st.markdown("#### ⚡ 빠른 질문")
    quick_qs = [
        "고죠 사토루의 무량공처 손동작을 자세히 설명해줘",
        "영역전개와 영역팽창의 차이점은?",
        "후시구로 메구미의 인(印) 손동작 방법은?",
        "영역전개를 실제로 따라해볼 수 있는 손동작 순서 알려줘",
    ]
    cols = st.columns(2)
    for i, q in enumerate(quick_qs):
        with cols[i % 2]:
            if st.button(q, key=f"quick_{i}", use_container_width=True):
                if not api_key:
                    st.error("❌ API 키를 입력해주세요.")
                else:
                    st.session_state.chat_history.append({"role": "user", "content": q})
                    reply = analyze_with_claude(api_key, q)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()


# ════════════════════════════════════════
# TAB 3 : 도감
# ════════════════════════════════════════
with tab3:
    st.markdown("### 📖 영역전개 도감")
    st.markdown("주술회전에 등장하는 영역전개 목록과 손동작 가이드입니다.")
    st.markdown("---")

    for name, data in DOMAIN_INFO.items():
        with st.expander(f"{data['emoji']} {name} — {data['main']}", expanded=False):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(f"""
<div style="text-align:center;padding:20px;background:#1a1a1a;border-radius:10px;
            border:2px solid {data['color']};">
  <div style="font-size:3rem;">{data['emoji']}</div>
  <div style="color:{data['color']};font-size:1.5rem;font-weight:bold;
              text-shadow:0 0 10px {data['color']};">{data['main']}</div>
  <div style="color:#aaa;font-size:0.9rem;margin-top:8px;">{data['sub']}</div>
</div>
""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"**설명**: {data['desc']}")
                st.markdown(f"**손동작**: `{data['hand_pose']}`")
                st.markdown("---")
                if st.button(f"🔥 {data['main']} 발동!", key=f"domain_btn_{name}", use_container_width=True):
                    st.session_state.trigger_domain = True
                    st.session_state.domain_main = data["main"]
                    st.session_state.domain_sub  = data["sub"]
                    st.rerun()

    st.markdown("---")
    st.markdown("""
<div class="info-box">
<b>📌 참고</b><br>
영역전개(領域展開)는 주술회전에서 술사가 자신의 술식으로 이루어진 공간을 펼치는 최고 기술입니다.
각 캐릭터마다 고유한 인(印)과 손동작으로 발동하며, 이 앱에서는 그 손동작을 MediaPipe로 인식합니다.
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────
# 푸터
# ──────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#555;font-size:0.8rem;padding:10px;">
  ⚔️ 呪術廻戦 領域展開 Simulator &nbsp;|&nbsp; MediaPipe + Anthropic Claude &nbsp;|&nbsp; Fan-made Project<br>
  <span style="color:#333;">※ 이 프로그램은 팬 제작 비상업적 프로젝트입니다.</span>
</div>
""", unsafe_allow_html=True)