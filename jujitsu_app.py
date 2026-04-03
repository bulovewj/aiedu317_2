import streamlit as st
import anthropic
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import json

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="웹캠 카메라 & 손가락 인식 앱",
    page_icon="🖐️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── 커스텀 CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
        color: #e0e0e0;
    }
    .title-container {
        text-align: center;
        padding: 20px 0 10px 0;
    }
    .title-container h1 {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00d2ff, #7b2ff7, #ff6b6b, #00d2ff);
        background-size: 300% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 4s linear infinite;
    }
    @keyframes shine { to { background-position: 300% center; } }
    .title-container p { color: #888; font-size: 0.9rem; margin-top: -6px; }

    /* 상태 배지 */
    .status-badge {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 6px 18px; border-radius: 999px;
        font-size: 0.82rem; font-weight: 600;
    }
    .status-on  { background:rgba(0,255,128,0.15); border:1px solid rgba(0,255,128,0.4); color:#00ff80; }
    .status-off { background:rgba(255,80,80,0.15);  border:1px solid rgba(255,80,80,0.4);  color:#ff5050; }
    .dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
    .dot-on  { background:#00ff80; box-shadow:0 0 6px #00ff80; animation:blink 1.2s infinite; }
    .dot-off { background:#ff5050; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

    /* 버튼 */
    div.stButton > button {
        border-radius: 12px; font-weight: 700; font-size: 0.95rem;
        padding: 0.5rem 0; width: 100%; border: none;
        transition: all 0.25s ease;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00c853, #69f0ae);
        color: #000; box-shadow: 0 4px 18px rgba(0,200,83,0.4);
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px); box-shadow: 0 6px 24px rgba(0,200,83,0.6);
    }
    div.stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #e53935, #ff5252);
        color: #fff; box-shadow: 0 4px 18px rgba(229,57,53,0.4);
    }
    div.stButton > button[kind="secondary"]:hover {
        transform: translateY(-2px); box-shadow: 0 6px 24px rgba(229,57,53,0.6);
    }

    /* 손가락 인식 결과 카드 */
    .finger-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(0,210,255,0.3);
        border-radius: 16px; padding: 18px 22px; margin: 12px 0;
    }
    .finger-card h4 { color: #00d2ff; margin-bottom: 12px; font-size: 1rem; }

    /* 손가락 아이콘 그리드 */
    .finger-grid {
        display: flex; gap: 10px; flex-wrap: wrap; justify-content: center;
        margin: 10px 0;
    }
    .finger-chip {
        display: flex; flex-direction: column; align-items: center;
        padding: 10px 14px; border-radius: 12px; min-width: 62px;
        font-size: 0.78rem; font-weight: 600; gap: 4px;
        transition: transform 0.2s;
    }
    .finger-chip:hover { transform: scale(1.08); }
    .finger-up   { background:rgba(0,255,128,0.18); border:1.5px solid #00ff80; color:#00ff80; }
    .finger-down { background:rgba(255,80,80,0.12);  border:1.5px solid #ff5050; color:#ff5050; }
    .finger-chip .icon { font-size: 1.5rem; }

    /* 제스처 배너 */
    .gesture-banner {
        text-align: center; padding: 14px;
        border-radius: 14px; margin: 10px 0;
        background: linear-gradient(135deg, rgba(123,47,247,0.25), rgba(0,210,255,0.15));
        border: 1px solid rgba(123,47,247,0.4);
    }
    .gesture-banner .gesture-name {
        font-size: 1.6rem; font-weight: 800;
        background: linear-gradient(90deg, #7b2ff7, #00d2ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .gesture-banner .gesture-emoji { font-size: 2.8rem; }
    .gesture-banner .finger-count  { color: #aaa; font-size: 0.85rem; margin-top: 4px; }

    /* 분석 결과 */
    .analysis-box {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(123,47,247,0.4);
        border-radius: 14px; padding: 18px 22px; margin-top: 12px;
        line-height: 1.7; color: #d0d0e8;
    }

    /* 카메라 */
    div[data-testid="stCameraInput"] video {
        border-radius: 16px;
        border: 2px solid rgba(123,47,247,0.5);
        box-shadow: 0 0 32px rgba(0,210,255,0.15);
    }
    div[data-testid="stCameraInput"] img {
        border-radius: 16px;
        border: 2px solid rgba(0,255,128,0.4);
        box-shadow: 0 0 32px rgba(0,255,128,0.12);
    }
    div[data-testid="stCameraInput"] > div > button {
        background: linear-gradient(135deg, #7b2ff7, #00d2ff) !important;
        color: #fff !important; border-radius: 10px !important; font-weight: 600 !important;
    }

    /* 사이드바 */
    section[data-testid="stSidebar"] { background:rgba(255,255,255,0.03); }
    section[data-testid="stSidebar"] .stTextInput input {
        background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.15);
        color:#e0e0e0; border-radius:8px;
    }
    hr { border-color: rgba(255,255,255,0.08); }

    /* 탭 */
    div[data-testid="stTabs"] button {
        font-weight: 600; font-size: 0.9rem;
    }

    /* metric */
    div[data-testid="stMetricValue"] { color: #00d2ff; font-size: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Session State 초기화 ──────────────────────────────────────
defaults = {
    "camera_on": False,
    "captured_image": None,
    "analysis_result": "",
    "chat_history": [],
    "finger_result": None,
    "gesture_history": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════
#  손가락 인식 핵심 로직 (PIL 기반 — 서버 사이드)
# ══════════════════════════════════════════════════════════════

FINGER_NAMES = ["엄지", "검지", "중지", "약지", "새끼"]
FINGER_ICONS = ["👍", "☝️", "🖕", "💍", "🤙"]

GESTURE_MAP = {
    (0, 0, 0, 0, 0): ("주먹", "✊", "모든 손가락을 접은 상태"),
    (1, 1, 1, 1, 1): ("오픈 핸드", "🖐️", "모든 손가락을 편 상태"),
    (0, 1, 0, 0, 0): ("포인팅", "👆", "검지만 펴서 가리키는 제스처"),
    (0, 1, 1, 0, 0): ("피스", "✌️", "검지·중지를 펴 평화를 표현"),
    (1, 0, 0, 0, 0): ("좋아요", "👍", "엄지만 위로 올린 상태"),
    (1, 1, 1, 1, 0): ("넷", "4️⃣", "네 손가락을 편 상태"),
    (0, 1, 1, 1, 1): ("넷(엄지 제외)", "4️⃣", "엄지 제외 네 손가락"),
    (0, 1, 0, 0, 1): ("록", "🤘", "록 제스처"),
    (1, 0, 0, 0, 1): ("샤카", "🤙", "서핑·친근감 제스처"),
    (0, 0, 1, 0, 0): ("가운데 손가락", "🖕", "중지만 편 상태"),
    (1, 1, 0, 0, 0): ("총", "🔫", "엄지·검지를 편 상태"),
    (0, 0, 0, 1, 1): ("둘(약지·새끼)", "✌️", "약지·새끼를 편 상태"),
    (0, 1, 1, 1, 0): ("셋", "3️⃣", "세 손가락을 편 상태"),
    (1, 1, 1, 0, 0): ("셋(엄지 포함)", "3️⃣", "엄지·검지·중지"),
    (0, 0, 0, 0, 1): ("새끼 손가락", "🤙", "새끼만 편 상태"),
}


def analyze_fingers_with_claude(api_key: str, image_b64: str) -> dict:
    """
    Claude Vision으로 손가락 상태 + 제스처를 JSON으로 추출.
    실패 시 fallback dict 반환.
    """
    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = """당신은 손 제스처 인식 전문 AI입니다.
이미지에서 손이 보이면 다음 JSON 형식으로만 응답하세요 (코드블록 없이 순수 JSON):
{
  "hand_detected": true/false,
  "fingers": {
    "thumb":  true/false,
    "index":  true/false,
    "middle": true/false,
    "ring":   true/false,
    "pinky":  true/false
  },
  "extended_count": 0~5,
  "confidence": "high"/"medium"/"low",
  "notes": "간단한 관찰 메모"
}

판단 기준:
- 손가락이 완전히 펴져 있으면 true, 접혀 있으면 false
- 엄지(thumb): 옆으로 벌어져 있으면 true
- 손이 없으면 hand_detected: false 로만 반환"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=512,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64},
                },
                {"type": "text", "text": "이 이미지의 손 제스처를 분석하고 JSON으로만 응답해주세요."},
            ],
        }],
    )

    raw = message.content[0].text.strip()
    # JSON 파싱 (코드블록 제거)
    if "
