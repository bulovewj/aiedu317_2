import streamlit as st
import anthropic
import cv2
import numpy as np
import mediapipe as mp
import time
import base64
from PIL import Image
import io

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
# CSS 스타일
# ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;700;900&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0a0a !important;
    color: #e0e0e0;
}
[data-testid="stSidebar"] {
    background: #111 !important;
    border-right: 1px solid #333;
}
h1, h2, h3 { color: #c0392b !important; }

/* 영역전개 오버레이 */
#domain-overlay {
    display: none;
    position: fixed;
    inset: 0;
    z-index: 99999;
    overflow: hidden;
    pointer-events: none;
}
#domain-overlay.active { display: block; }

.domain-bg {
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at center,
        rgba(139,0,0,0.96) 0%,
        rgba(20,0,0,0.98) 55%,
        rgba(0,0,0,1) 100%);
    animation: domainPulse 1.8s ease-in-out infinite alternate;
}
@keyframes domainPulse {
    from { opacity: 0.8; }
    to   { opacity: 1; }
}

.crack {
    position: absolute;
    background: linear-gradient(90deg, transparent, #FF4500, transparent);
    height: 2px;
    width: 100%;
    animation: crackFlicker 0.25s infinite;
}
@keyframes crackFlicker {
    0%,100% { opacity:1; }
    50%     { opacity:0.2; }
}

.curse-circle {
    position: absolute;
    top: 50%; left: 50%;
    border-radius: 50%;
    transform: translate(-50%, -50%);
    border: 2px solid rgba(255,69,0,0.55);
    animation: circleRotate 8s linear infinite;
}
@keyframes circleRotate {
    from { transform: translate(-50%,-50%) rotate(0deg);   }
    to   { transform: translate(-50%,-50%) rotate(360deg); }
}

.domain-text {
    position: absolute;
    top: 44%; left: 50%;
    transform: translate(-50%, -50%);
    font-family: 'Noto Serif JP', serif;
    font-size: clamp(2.5rem, 7vw, 5.5rem);
    font-weight: 900;
    color: #FFD700;
    text-shadow: 0 0 12px #FF4500, 0 0 35px #FF4500,
                 0 0 70px #8B0000, 0 0 120px #FF0000;
    white-space: nowrap;
    letter-spacing: 0.35em;
    animation: textAppear 0.8s ease-out forwards,
               textGlow   2.5s ease-in-out infinite alternate 0.8s;
    opacity: 0;
}
@keyframes textAppear {
    from { opacity:0; transform:translate(-50%,-50%) scale(0.4); }
    to   { opacity:1; transform:translate(-50%,-50%) scale(1);   }
}
@keyframes textGlow {
    from { text-shadow: 0 0 12px #FF4500, 0 0 35px #FF4500; }
    to   { text-shadow: 0 0 25px #FFD700, 0 0 70px #FF4500, 0 0 120px #FF0000; }
}

.domain-subtitle {
    position: absolute;
    top: 60%; left: 50%;
    transform: translateX(-50%);
    font-family: 'Noto Serif JP', serif;
    font-size: clamp(1.1rem, 3.5vw, 2.2rem);
    color: rgba(255,215,0,0.85);
    letter-spacing: 0.25em;
    animation: textAppear 1.2s ease-out 0.4s forwards;
    opacity: 0;
}

.domain-close-btn {
    position: absolute;
    top: 18px; right: 28px;
    font-size: 2.2rem;
    color: rgba(255,215,0,0.7);
    cursor: pointer;
    pointer-events: all;
    z-index: 100000;
    line-height: 1;
    user-select: none;
}
.domain-close-btn:hover { color: #FFD700; }

.particle {
    position: absolute;
    border-radius: 50%;
    animation: floatUp linear infinite;
    pointer-events: none;
}
@keyframes floatUp {
    from { transform: translateY(105vh) scale(1); opacity: 0.85; }
    to   { transform: translateY(-8vh)  scale(0); opacity: 0; }
}

/* 버튼 스타일 */
.stButton > button {
    background: linear-gradient(135deg, #8B0000, #4a0000) !important;
    color: #FFD700 !important;
    border: 1px solid #FF4500 !important;
    border-radius: 8px !important;
    font-weight: bold !important;
    letter-spacing: 0.08em !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #c0392b, #8B0000) !important;
    box-shadow: 0 0 18px rgba(255,69,0,0.55) !important;
}

/* 배지 */
.badge {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: bold;
    letter-spacing: 0.04em;
    margin: 3px;
}
.badge-on  { background:#8B0000; color:#FFD700; border:1px solid #FF4500; }
.badge-off { background:#1a1a1a; color:#777;    border:1px solid #333; }
.badge-ok  { background:#103010; color:#00EE00; border:1px solid #009900; }

/* 정보 박스 */
.ibox {
    background: #161616;
    border-left: 3px solid #FF4500;
    padding: 10px 15px;
    border-radius: 0 8px 8px 0;
    margin: 7px 0;
    font-size: 0.88rem;
    color: #ccc;
    line-height: 1.65;
}

/* 포즈 카드 */
.pcard {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 9px;
    padding: 10px 13px;
    margin: 5px 0;
    transition: border-color 0.2s, background 0.2s;
}
.pcard.sel { border-color:#FF4500; background:#2a1010; }
.pcard-t   { color:#FFD700; font-weight:bold; font-size:0.95rem; }
.pcard-d   { color:#999;    font-size:0.78rem; margin-top:3px; }

/* 신뢰도 게이지 */
.gauge-bg  { background:#222; border-radius:4px; height:12px; overflow:hidden; margin:4px 0; }
.gauge-bar { height:100%; border-radius:4px; transition:width 0.3s; }

hr { border-color:#2a2a2a !important; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# 영역전개 오버레이 HTML + JS (한 번만 삽입)
# ──────────────────────────────────────────
st.components.v1.html("""
<div id="domain-overlay">
  <div class="domain-bg"></div>

  <div class="crack" style="top:18%;transform:rotate(-13deg);"></div>
  <div class="crack" style="top:33%;transform:rotate(7deg);opacity:.55;"></div>
  <div class="crack" style="top:62%;transform:rotate(-6deg);opacity:.65;"></div>
  <div class="crack" style="top:82%;transform:rotate(11deg);opacity:.45;"></div>

  <div class="curse-circle" style="width:260px;height:260px;animation-duration:5s;"></div>
  <div class="curse-circle" style="width:460px;height:460px;animation-duration:9s;animation-direction:reverse;"></div>
  <div class="curse-circle" style="width:660px;height:660px;animation-duration:13s;border-style:dashed;"></div>
  <div class="curse-circle" style="width:860px;height:860px;animation-duration:17s;animation-direction:reverse;border-style:dotted;"></div>

  <div class="domain-text"    id="dom-main">領域展開</div>
  <div class="domain-subtitle" id="dom-sub">無量空処</div>

  <div id="ptcl"></div>
  <span class="domain-close-btn" onclick="closeDomain()">✕</span>
</div>

<style>
.domain-bg,.crack,.curse-circle,.domain-text,.domain-subtitle,
.domain-close-btn,.particle { position:absolute; }
</style>

<script>
function mkParticles(){
  var c=document.getElementById('ptcl');
  if(!c)return; c.innerHTML='';
  for(var i=0;i<55;i++){
    var p=document.createElement('div');
    p.className='particle';
    var s=Math.random()*7+2;
    p.style.cssText='width:'+s+'px;height:'+s+'px;left:'+(Math.random()*100)+'%;'
      +'animation-duration:'+(Math.random()*4+3)+'s;animation-delay:'+(Math.random()*3)+'s;'
      +'background:rgba('+(Math.random()>.5?'255,69,0':'255,215,0')+',0.8);';
    c.appendChild(p);
  }
}

function activateDomain(main, sub){
  var o=document.getElementById('domain-overlay');
  var m=document.getElementById('dom-main');
  var s=document.getElementById('dom-sub');
  if(!o)return;
  if(m && main) m.textContent=main;
  if(s && sub)  s.textContent=sub;
  mkParticles();
  o.classList.add('active');
  try{ playSound(); }catch(e){}
  clearTimeout(window._dt);
  window._dt=setTimeout(closeDomain,10000);
}

function closeDomain(){
  var o=document.getElementById('domain-overlay');
  if(o) o.classList.remove('active');
}

function playSound(){
  var ctx=new(window.AudioContext||window.webkitAudioContext)();
  var o1=ctx.createOscillator(), g1=ctx.createGain();
  o1.type='sawtooth';
  o1.frequency.setValueAtTime(65,ctx.currentTime);
  o1.frequency.exponentialRampToValueAtTime(18,ctx.currentTime+1.8);
  g1.gain.setValueAtTime(0.45,ctx.currentTime);
  g1.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+1.8);
  o1.connect(g1); g1.connect(ctx.destination);
  o1.start(); o1.stop(ctx.currentTime+1.8);

  var o2=ctx.createOscillator(), g2=ctx.createGain();
  o2.type='square';
  o2.frequency.setValueAtTime(900,ctx.currentTime);
  o2.frequency.exponentialRampToValueAtTime(180,ctx.currentTime+0.6);
  g2.gain.setValueAtTime(0.22,ctx.currentTime);
  g2.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+0.6);
  o2.connect(g2); g2.connect(ctx.destination);
  o2.start(); o2.stop(ctx.currentTime+0.6);
}

window.addEventListener('message',function(e){
  if(!e.data) return;
  if(e.data.type==='ACTIVATE') activateDomain(e.data.main, e.data.sub);
  if(e.data.type==='CLOSE')    closeDomain();
});
</script>
""", height=0, scrolling=False)

# ──────────────────────────────────────────
# 영역전개 데이터
# ──────────────────────────────────────────
DOMAINS = {
    "무량공처 — 고죠 사토루": {
        "main": "無量空処",
        "sub": "「私が最強ですので」",
        "desc": "무한을 내재화하여 감각 정보를 무한히 처리하게 만들어 뇌를 마비시킨다.",
        "color": "#00BFFF",
        "pose": "양손 손가락을 서로 교차해 맞잡는 형태 (양손 모두 3~5개 손가락 펴기)",
        "emoji": "🔵",
        "condition": "two_hands_interlocked",
    },
    "폐옥염정 — 후시구로 메구미": {
        "main": "嵌合暗翳庭",
        "sub": "「十種影法術」",
        "desc": "십종영법술로 만든 식신들의 세계를 펼친다.",
        "color": "#4B0082",
        "pose": "검지+중지만 펴고 나머지 접기 (인 모양)",
        "emoji": "🌑",
        "condition": "two_fingers_up",
    },
    "흉흉욕식 — 조로": {
        "main": "凶凶呪胎",
        "sub": "「特級呪霊」",
        "desc": "용암과 화염으로 가득한 세계를 펼친다.",
        "color": "#FF4500",
        "pose": "양손 모든 손가락 활짝 펴기",
        "emoji": "🔥",
        "condition": "both_hands_open",
    },
    "자충玫 — 쿠기사키 노바라": {
        "main": "蝶蛆嵐",
        "sub": "「共鳴り」",
        "desc": "못을 통해 원거리 타격하는 공명 기법.",
        "color": "#8B0000",
        "pose": "한 손 주먹 + 다른 손 검지만 펴기",
        "emoji": "🔴",
        "condition": "fist_plus_point",
    },
    "자수밀원 — 마히토": {
        "main": "自閉円頓裹",
        "sub": "「無為転変」",
        "desc": "영혼을 직접 조작하는 무위전변.",
        "color": "#9B59B6",
        "pose": "한 손으로 주먹 쥐기 (모든 손가락 접기)",
        "emoji": "🟣",
        "condition": "one_fist",
    },
}

# ──────────────────────────────────────────
# MediaPipe 초기화
# ──────────────────────────────────────────
@st.cache_resource
def load_mediapipe():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=True,
        max_num_hands=2,
        min_detection_confidence=0.55,
        min_tracking_confidence=0.45,
    )
    return hands, mp_hands, mp.solutions.drawing_utils, mp.solutions.drawing_styles

hands_model, mp_hands, mp_draw, mp_draw_styles = load_mediapipe()

# ──────────────────────────────────────────
# 손 분석 함수
# ──────────────────────────────────────────
def finger_extended(lm, tip: int, pip: int) -> bool:
    return lm[tip].y < lm[pip].y

def thumb_extended(lm, handedness: str) -> bool:
    if handedness == "Right":
        return lm[4].x < lm[3].x
    return lm[4].x > lm[3].x

def get_finger_states(lm, handedness: str) -> list[bool]:
    return [
        thumb_extended(lm, handedness),
        finger_extended(lm, 8,  6),
        finger_extended(lm, 12, 10),
        finger_extended(lm, 16, 14),
        finger_extended(lm, 20, 18),
    ]

def analyze_gesture(results, handedness_list) -> tuple[str, float, str]:
    """
    returns (domain_key_or_status, confidence_0_to_1, description)
    """
    if not results.multi_hand_landmarks:
        return "none", 0.0, "손이 감지되지 않았습니다."

    lm_list = [h.landmark for h in results.multi_hand_landmarks]
    n = len(lm_list)

    hand_names = []
    if handedness_list:
        for h in handedness_list:
            hand_names.append(h.classification[0].label)
    else:
        hand_names = ["Right"] * n

    finger_states = [get_finger_states(lm_list[i], hand_names[i] if i < len(hand_names) else "Right")
                     for i in range(n)]
    ext_counts = [sum(fs) for fs in finger_states]

    # ── 흉흉욕식: 양손 모두 활짝 (5+5) ──
    if n == 2 and all(c == 5 for c in ext_counts):
        return "흉흉욕식 — 조로", 0.97, "양손 활짝! 흉흉욕식 발동 조건 달성!"

    # ── 무량공처: 양손 교차 (합산 6~9개) ──
    if n == 2:
        total = sum(ext_counts)
        if 5 <= total <= 9:
            score = 0.7 + (min(total, 8) - 5) * 0.05
            return "무량공처 — 고죠 사토루", round(score, 2), f"양손 교차 (총 {total}개 펴짐) → 무량공처!"

    # ── 자충玫: 주먹(0) + 검지만(1) ──
    if n == 2:
        cnts = sorted(ext_counts)
        if cnts[0] == 0 and cnts[1] == 1:
            # 검지 폄 확인
            for i, fs in enumerate(finger_states):
                if ext_counts[i] == 1 and fs[1]:
                    return "자충玫 — 쿠기사키 노바라", 0.88, "주먹 + 검지 → 자충玫 발동!"

    # ── 폐옥염정: 검지+중지만 폄 ──
    for fs in finger_states:
        if fs[1] and fs[2] and not fs[3] and not fs[4] and not fs[0]:
            return "폐옥염정 — 후시구로 메구미", 0.90, "검지+중지 인(印) → 폐옥염정 발동!"

    # ── 자수밀원: 주먹 ──
    for c in ext_counts:
        if c == 0:
            return "자수밀원 — 마히토", 0.82, "주먹 → 자수밀원 발동!"

    # 손은 있지만 패턴 불일치
    total_ext = sum(ext_counts)
    return "detecting", 0.25 + min(total_ext / 20, 0.3), f"손 감지됨 ({n}개) — 특정 패턴 인식 중..."


def process_image(pil_image: Image.Image) -> tuple[np.ndarray, str, float, str]:
    """PIL 이미지 → 분석된 numpy 배열 + 제스처 정보 반환."""
    img = np.array(pil_image.convert("RGB"))
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    img_bgr = cv2.flip(img_bgr, 1)

    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    results = hands_model.process(rgb)

    gesture, score, desc = analyze_gesture(
        results,
        results.multi_handedness if results.multi_handedness else []
    )

    h, w = img_bgr.shape[:2]

    # 랜드마크 그리기
    if results.multi_hand_landmarks:
        for hl in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                img_bgr, hl, mp_hands.HAND_CONNECTIONS,
                mp_draw_styles.get_default_hand_landmarks_style(),
                mp_draw_styles.get_default_hand_connections_style(),
            )
        # 손목 위 텍스트
        for hl in results.multi_hand_landmarks:
            wx = int(hl.landmark[0].x * w)
            wy = int(hl.landmark[0].y * h)
            color = (0, 255, 100) if score >= 0.75 else (200, 200, 200)
            short = gesture.split("—")[0].strip() if "—" in gesture else gesture
            cv2.putText(img_bgr, short,
                        (max(wx - 90, 0), max(wy - 15, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2, cv2.LINE_AA)

    # 테두리 및 상태 텍스트
    if score >= 0.75 and gesture in DOMAINS:
        cv2.rectangle(img_bgr, (0, 0), (w - 1, h - 1), (0, 0, 220), 6)
        cv2.putText(img_bgr, "! DOMAIN !", (w // 2 - 100, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 40, 255), 3, cv2.LINE_AA)

    # 하단 게이지
    bar_w = int(w * score)
    cv2.rectangle(img_bgr, (0, h - 10), (w, h), (25, 25, 25), -1)
    bar_color = (0, 200, 80) if score >= 0.75 else (0, 140, 255) if score >= 0.45 else (80, 80, 200)
    cv2.rectangle(img_bgr, (0, h - 10), (bar_w, h), bar_color, -1)

    return img_bgr, gesture, score, desc


# ──────────────────────────────────────────
# Claude AI 분석
# ──────────────────────────────────────────
def ask_claude(api_key: str, user_msg: str, gesture_ctx: str = "") -> str:
    try:
        client = anthropic.Anthropic(api_key=api_key)
        system = (
            "당신은 주술회전(呪術廻戦) 전문 AI입니다. "
            "영역전개, 술식, 인(印), 손동작 등 주술회전 세계관을 깊이 이해합니다. "
            "한국어로 친절하고 상세하게 답변하세요."
        )
        content = user_msg
        if gesture_ctx and gesture_ctx not in ("none", "detecting"):
            content = f"[현재 인식된 손동작: {gesture_ctx}]\n\n{user_msg}"

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": content}],
        )
        return response.content[0].text
    except anthropic.AuthenticationError:
        return "❌ API 키가 올바르지 않습니다. 사이드바에서 다시 확인해주세요."
    except anthropic.RateLimitError:
        return "⚠️ API 요청 한도 초과. 잠시 후 다시 시도해주세요."
    except Exception as e:
        return f"❌ 오류 발생: {str(e)}"


# ──────────────────────────────────────────
# Session State 초기화
# ──────────────────────────────────────────
defaults = {
    "chat_history": [],
    "last_gesture": "none",
    "last_score": 0.0,
    "last_desc": "",
    "trigger_domain": False,
    "domain_main": "領域展開",
    "domain_sub": "無量空処",
    "auto_detect": True,
    "prev_trigger_time": 0.0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ──────────────────────────────────────────
# JS 트리거 헬퍼
# ──────────────────────────────────────────
def fire_domain_js(main: str, sub: str):
    """부모 창으로 영역전개 메시지를 전송하는 iframe JS."""
    st.components.v1.html(f"""
<script>
(function(){{
  var msg = {{type:'ACTIVATE', main:'{main}', sub:'{sub}'}};
  if(window.parent && window.parent !== window)
      window.parent.postMessage(msg, '*');
  else if(typeof activateDomain === 'function')
      activateDomain('{main}', '{sub}');
}})();
</script>
""", height=0, scrolling=False)


def close_domain_js():
    st.components.v1.html("""
<script>
(function(){
  var msg={type:'CLOSE'};
  if(window.parent && window.parent!==window)
      window.parent.postMessage(msg,'*');
  else if(typeof closeDomain==='function') closeDomain();
})();
</script>
""", height=0, scrolling=False)


# ──────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔮 呪術廻戦 設定")
    st.markdown("---")

    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Claude AI 분석 기능에 필요합니다.",
    )
    if api_key:
        st.markdown('<span class="badge badge-on">✅ API 연결됨</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-off">⚪ API 미연결</span>', unsafe_allow_html=True)

    st.markdown("---")

    sel_domain = st.selectbox("영역전개 선택", list(DOMAINS.keys()))
    d_info = DOMAINS[sel_domain]

    st.markdown(f"""
<div class="ibox">
  <b>{d_info['emoji']} {sel_domain}</b><br>
  <span style="color:{d_info['color']};font-size:1.15em;font-weight:bold;">{d_info['main']}</span><br>
  <small style="color:#999;">{d_info['sub']}</small><br><br>
  <span style="color:#bbb;font-size:0.83em;">{d_info['desc']}</span><br><br>
  <span style="color:#777;font-size:0.78em;">✋ {d_info['pose']}</span>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🎮 수동 제어")

    if st.button("🔥 영역전개 발동!", use_container_width=True):
        fire_domain_js(d_info["main"], d_info["sub"])

    if st.button("❌ 영역 해제", use_container_width=True):
        close_domain_js()

    st.markdown("---")
    auto_detect = st.toggle("🤖 자동 감지 발동", value=st.session_state.auto_detect)
    st.session_state.auto_detect = auto_detect

    st.markdown("""
<div class="ibox" style="font-size:0.78em;">
<b>📸 사용 방법</b><br>
1. 카메라 탭에서 📷 촬영<br>
2. 손동작 분석 자동 실행<br>
3. 75% 이상 신뢰도 → 영역전개!<br><br>
<b>손동작 목록</b><br>
• 양손 교차 → 무량공처<br>
• 검지+중지 인(印) → 폐옥염정<br>
• 양손 활짝 → 흉흉욕식<br>
• 주먹+검지 → 자충玫<br>
• 주먹 쥐기 → 자수밀원
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────
# 메인 헤더
# ──────────────────────────────────────────
st.markdown(
    "<h1 style='text-align:center;letter-spacing:.35em;'>⚔️ 呪術廻戦 領域展開 ⚔️</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center;color:#777;margin-top:-10px;'>"
    "카메라로 손동작을 촬영하면 영역전개가 발동됩니다</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ──────────────────────────────────────────
# 탭
# ──────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📷 카메라 손동작 인식", "💬 AI 주술 분석", "📖 영역전개 도감"])

# ══════════════════════════════════════════
# TAB 1 : 카메라
# ══════════════════════════════════════════
with tab1:
    col_cam, col_result = st.columns([3, 2], gap="medium")

    with col_cam:
        st.markdown("### 📷 손동작 촬영")
        st.markdown(
            '<div class="ibox">💡 <b>카메라 버튼</b>을 눌러 사진을 찍으세요. '
            '손동작이 자동으로 분석되어 영역전개가 발동됩니다!</div>',
            unsafe_allow_html=True,
        )

        captured = st.camera_input(
            label="카메라 (손동작을 화면 중앙에 위치시키세요)",
            key="cam_input",
            help="셔터 버튼을 눌러 손동작을 캡처하세요.",
        )

        if captured is not None:
            pil_img = Image.open(captured)
            processed_bgr, gesture, score, desc = process_image(pil_img)

            # BGR → RGB 변환 후 표시
            processed_rgb = cv2.cvtColor(processed_bgr, cv2.COLOR_BGR2RGB)
            st.image(processed_rgb, caption="📊 손동작 분석 결과", use_column_width=True)

            # 세션 업데이트
            st.session_state.last_gesture = gesture
            st.session_state.last_score   = score
            st.session_state.last_desc    = desc

            # 자동 발동
            now = time.time()
            cooldown_ok = (now - st.session_state.prev_trigger_time) > 3.0
            if (st.session_state.auto_detect
                    and score >= 0.75
                    and gesture in DOMAINS
                    and cooldown_ok):
                st.session_state.prev_trigger_time = now
                d = DOMAINS[gesture]
                fire_domain_js(d["main"], d["sub"])
                st.balloons()

    with col_result:
        st.markdown("### 🔍 분석 결과")

        g = st.session_state.last_gesture
        s = st.session_state.last_score
        d_txt = st.session_state.last_desc

        # 상태 배지
        if g in DOMAINS and s >= 0.75:
            badge_html = f'<span class="badge badge-ok">✅ {g.split("—")[0].strip()} 감지!</span>'
        elif g == "detecting":
            badge_html = '<span class="badge badge-off">👋 손 인식 중...</span>'
        else:
            badge_html = '<span class="badge badge-off">⚪ 대기 중</span>'
        st.markdown(badge_html, unsafe_allow_html=True)

        if d_txt:
            st.markdown(f'<div class="ibox">{d_txt}</div>', unsafe_allow_html=True)

        # 신뢰도 게이지
        if s > 0:
            pct = int(s * 100)
            bar_color = "#00EE00" if s >= 0.75 else "#FFA500" if s >= 0.45 else "#4466FF"
            st.markdown(f"""
<div style="margin:10px 0;">
  <div style="color:#aaa;font-size:0.82rem;margin-bottom:3px;">
    인식 신뢰도: <b style="color:{bar_color};">{pct}%</b>
    {"🔥 발동!" if s >= 0.75 else ""}
  </div>
  <div class="gauge-bg">
    <div class="gauge-bar" style="width:{pct}%;background:{bar_color};"></div>
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 📋 손동작 가이드")
        for name, data in DOMAINS.items():
            is_sel = (g == name and s >= 0.75)
            cls = "pcard sel" if is_sel else "pcard"
            st.markdown(f"""
<div class="{cls}">
  <div class="pcard-t">{data['emoji']} {name.split('—')[0].strip()}</div>
  <div class="pcard-d">{data['pose']}</div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
<div class="ibox" style="font-size:0.8em;">
<b>🎯 촬영 팁</b><br>
• 밝은 환경 권장<br>
• 손이 화면 중앙에 오도록<br>
• 배경은 단색이 유리<br>
• 카메라와 30cm~80cm 거리<br>
• 천천히 손동작 완성 후 촬영
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════
# TAB 2 : AI 채팅
# ══════════════════════════════════════════
with tab2:
    st.markdown("### 💬 주술 AI 상담사")
    st.markdown(
        '<div class="ibox">🤖 주술회전 세계관, 영역전개 손동작, 술식 등 무엇이든 물어보세요!</div>',
        unsafe_allow_html=True,
    )

    # 채팅 기록
    for msg in st.session_state.chat_history:
        icon = "🔮" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=icon):
            st.markdown(msg["content"])

    # 입력
    if prompt := st.chat_input("영역전개에 대해 궁금한 점을 입력하세요..."):
        if not api_key:
            st.error("❌ 사이드바에서 Anthropic API 키를 입력해주세요.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="🔮"):
                with st.spinner("주술 분석 중..."):
                    reply = ask_claude(api_key, prompt, st.session_state.last_gesture)
                st.markdown(reply)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            st.rerun()

    # 빠른 질문
    st.markdown("#### ⚡ 빠른 질문")
    quick_list = [
        "고죠 사토루의 무량공처 손동작을 자세히 설명해줘",
        "영역전개와 영역팽창의 차이는?",
        "후시구로 메구미의 인(印) 손동작 순서를 알려줘",
        "주술회전에서 영역전개가 강한 이유는?",
    ]
    c1, c2 = st.columns(2)
    for i, q in enumerate(quick_list):
        col = c1 if i % 2 == 0 else c2
        with col:
            if st.button(q, key=f"q{i}", use_container_width=True):
                if not api_key:
                    st.error("❌ API 키를 입력해주세요.")
                else:
                    st.session_state.chat_history.append({"role": "user", "content": q})
                    reply = ask_claude(api_key, q)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()

    if st.button("🗑️ 대화 초기화", use_container_width=True, key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun()


# ══════════════════════════════════════════
# TAB 3 : 도감
# ══════════════════════════════════════════
with tab3:
    st.markdown("### 📖 영역전개 도감")
    st.markdown("각 캐릭터의 영역전개 정보와 손동작 가이드입니다.")
    st.markdown("---")

    for name, data in DOMAINS.items():
        with st.expander(f"{data['emoji']} {name} ─ {data['main']}", expanded=False):
            ca, cb = st.columns([1, 2])
            with ca:
                st.markdown(f"""
<div style="text-align:center;padding:22px 10px;
            background:#161616;border-radius:10px;
            border:2px solid {data['color']};">
  <div style="font-size:3rem;line-height:1;">{data['emoji']}</div>
  <div style="color:{data['color']};font-size:1.6rem;font-weight:900;
              margin:8px 0;text-shadow:0 0 12px {data['color']};">
    {data['main']}
  </div>
  <div style="color:#999;font-size:0.88rem;">{data['sub']}</div>
</div>
""", unsafe_allow_html=True)
            with cb:
                st.markdown(f"**설명**: {data['desc']}")
                st.markdown(f"**손동작**: `{data['pose']}`")
                st.markdown("---")
                if st.button(
                    f"🔥 {data['main']} 발동!",
                    key=f"fire_{name}",
                    use_container_width=True,
                ):
                    fire_domain_js(data["main"], data["sub"])
                    st.success(f"✅ {data['main']} 발동!")

    st.markdown("---")
    st.markdown("""
<div class="ibox">
<b>📌 영역전개(領域展開)란?</b><br>
주술회전에서 술사가 자신의 술식으로 이루어진 공간(영역)을 펼치는 최고급 기술입니다.
영역 안에서는 시전자의 술식이 반드시 상대에게 적중하게 됩니다.
각 캐릭터마다 고유한 인(印)과 손동작으로 발동하며,
이 앱에서는 MediaPipe로 그 손동작을 인식합니다.
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# 푸터
# ──────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#444;font-size:0.76rem;padding:8px;">
  ⚔️ 呪術廻戦 領域展開 Simulator &nbsp;|&nbsp;
  MediaPipe + Anthropic Claude Sonnet &nbsp;|&nbsp; Fan-made / Non-commercial<br>
  <span style="color:#333;">※ 이 프로그램은 팬 제작 비상업적 프로젝트입니다.</span>
</div>
""", unsafe_allow_html=True)
