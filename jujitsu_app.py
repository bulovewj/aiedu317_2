import streamlit as st
import anthropic
import base64
import json
import time
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
[data-testid="stSidebar"] * { color: #e0e0e0 !important; }
h1, h2, h3 { color: #c0392b !important; }

/* ── 영역전개 오버레이 ── */
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
    to   { opacity: 1;   }
}

.crack {
    position: absolute;
    background: linear-gradient(90deg, transparent, #FF4500, transparent);
    height: 2px; width: 100%;
    animation: crackFlicker 0.25s infinite;
}
@keyframes crackFlicker {
    0%,100% { opacity:1;   }
    50%     { opacity:0.2; }
}

.curse-circle {
    position: absolute;
    top:50%; left:50%;
    border-radius:50%;
    border: 2px solid rgba(255,69,0,0.55);
    animation: circleRotate 8s linear infinite;
}
@keyframes circleRotate {
    from { transform: translate(-50%,-50%) rotate(0deg);   }
    to   { transform: translate(-50%,-50%) rotate(360deg); }
}

.domain-text {
    position: absolute;
    top:44%; left:50%;
    transform: translate(-50%,-50%);
    font-family: 'Noto Serif JP', serif;
    font-size: clamp(2.5rem, 7vw, 5.5rem);
    font-weight: 900;
    color: #FFD700;
    text-shadow: 0 0 12px #FF4500, 0 0 35px #FF4500,
                 0 0 70px #8B0000, 0 0 120px #FF0000;
    white-space: nowrap;
    letter-spacing: 0.35em;
    animation: textAppear 0.8s ease-out forwards,
               textGlow 2.5s ease-in-out infinite alternate 0.8s;
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
    top:60%; left:50%;
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
    top:18px; right:28px;
    font-size:2.2rem;
    color: rgba(255,215,0,0.7);
    cursor: pointer;
    pointer-events: all;
    z-index: 100000;
    line-height: 1;
    user-select: none;
}
.domain-close-btn:hover { color:#FFD700; }

.particle {
    position: absolute;
    border-radius: 50%;
    animation: floatUp linear infinite;
    pointer-events: none;
}
@keyframes floatUp {
    from { transform:translateY(105vh) scale(1); opacity:0.85; }
    to   { transform:translateY(-8vh) scale(0);  opacity:0;    }
}

/* ── UI 컴포넌트 ── */
.stButton > button {
    background: linear-gradient(135deg,#8B0000,#4a0000) !important;
    color: #FFD700 !important;
    border: 1px solid #FF4500 !important;
    border-radius: 8px !important;
    font-weight: bold !important;
    letter-spacing: 0.08em !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg,#c0392b,#8B0000) !important;
    box-shadow: 0 0 18px rgba(255,69,0,0.55) !important;
}

.badge {
    display:inline-block; padding:5px 14px;
    border-radius:20px; font-size:0.82rem;
    font-weight:bold; letter-spacing:0.04em; margin:3px;
}
.badge-on  { background:#8B0000; color:#FFD700; border:1px solid #FF4500; }
.badge-off { background:#1a1a1a; color:#777;    border:1px solid #333; }
.badge-ok  { background:#103010; color:#00EE00; border:1px solid #009900; }
.badge-warn{ background:#2a1a00; color:#FFA500; border:1px solid #FF8C00; }

.ibox {
    background:#161616; border-left:3px solid #FF4500;
    padding:10px 15px; border-radius:0 8px 8px 0;
    margin:7px 0; font-size:0.88rem; color:#ccc; line-height:1.65;
}

.pcard {
    background:#1a1a1a; border:1px solid #333;
    border-radius:9px; padding:10px 13px; margin:5px 0;
    transition: border-color 0.2s, background 0.2s;
}
.pcard.sel { border-color:#FF4500; background:#2a1010; }
.pcard-t   { color:#FFD700; font-weight:bold; font-size:0.95rem; }
.pcard-d   { color:#999; font-size:0.78rem; margin-top:3px; }

.gauge-bg  { background:#222; border-radius:4px; height:14px; overflow:hidden; margin:4px 0; }
.gauge-bar { height:100%; border-radius:4px; transition:width 0.4s; }

.result-card {
    background:#161616; border:1px solid #333;
    border-radius:12px; padding:18px; margin:10px 0;
}
.result-title {
    font-family:'Noto Serif JP',serif;
    font-size:1.6rem; font-weight:900;
    letter-spacing:0.2em; margin-bottom:6px;
}

hr { border-color:#2a2a2a !important; }

/* 카메라 입력 스타일 */
[data-testid="stCameraInput"] {
    border: 2px solid #8B0000 !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# 영역전개 오버레이 HTML + JS
# ──────────────────────────────────────────
st.components.v1.html("""
<!DOCTYPE html>
<html>
<head>
<style>
body { margin:0; padding:0; background:transparent; }
#domain-overlay {
    display:none; position:fixed; inset:0;
    z-index:99999; overflow:hidden; pointer-events:none;
}
#domain-overlay.active { display:block; }
.domain-bg {
    position:absolute; inset:0;
    background:radial-gradient(ellipse at center,
        rgba(139,0,0,0.96) 0%, rgba(20,0,0,0.98) 55%, rgba(0,0,0,1) 100%);
    animation:domainPulse 1.8s ease-in-out infinite alternate;
}
@keyframes domainPulse { from{opacity:.8} to{opacity:1} }
.crack {
    position:absolute; height:2px; width:100%;
    background:linear-gradient(90deg,transparent,#FF4500,transparent);
    animation:crackFlicker 0.25s infinite;
}
@keyframes crackFlicker { 0%,100%{opacity:1} 50%{opacity:.2} }
.curse-circle {
    position:absolute; top:50%; left:50%; border-radius:50%;
    border:2px solid rgba(255,69,0,.55);
    animation:circleRotate 8s linear infinite;
}
@keyframes circleRotate {
    from{transform:translate(-50%,-50%) rotate(0deg)}
    to{transform:translate(-50%,-50%) rotate(360deg)}
}
.domain-text {
    position:absolute; top:44%; left:50%;
    transform:translate(-50%,-50%);
    font-family:'Noto Serif JP',serif;
    font-size:clamp(2.5rem,7vw,5.5rem); font-weight:900;
    color:#FFD700; white-space:nowrap; letter-spacing:.35em;
    text-shadow:0 0 12px #FF4500,0 0 35px #FF4500,0 0 70px #8B0000,0 0 120px #FF0000;
    animation:textAppear .8s ease-out forwards,textGlow 2.5s ease-in-out infinite alternate .8s;
    opacity:0;
}
.domain-subtitle {
    position:absolute; top:60%; left:50%;
    transform:translateX(-50%);
    font-family:'Noto Serif JP',serif;
    font-size:clamp(1.1rem,3.5vw,2.2rem);
    color:rgba(255,215,0,.85); letter-spacing:.25em;
    animation:textAppear 1.2s ease-out .4s forwards; opacity:0;
}
@keyframes textAppear {
    from{opacity:0;transform:translate(-50%,-50%) scale(.4)}
    to{opacity:1;transform:translate(-50%,-50%) scale(1)}
}
@keyframes textGlow {
    from{text-shadow:0 0 12px #FF4500,0 0 35px #FF4500}
    to{text-shadow:0 0 25px #FFD700,0 0 70px #FF4500,0 0 120px #FF0000}
}
.domain-close-btn {
    position:absolute; top:18px; right:28px;
    font-size:2.2rem; color:rgba(255,215,0,.7);
    cursor:pointer; pointer-events:all; z-index:100000;
    line-height:1; user-select:none;
}
.domain-close-btn:hover{color:#FFD700}
.particle {
    position:absolute; border-radius:50%;
    animation:floatUp linear infinite; pointer-events:none;
}
@keyframes floatUp {
    from{transform:translateY(105vh) scale(1);opacity:.85}
    to{transform:translateY(-8vh) scale(0);opacity:0}
}
</style>
</head>
<body>
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
  <div class="domain-text"     id="dom-main">領域展開</div>
  <div class="domain-subtitle" id="dom-sub">無量空処</div>
  <div id="ptcl"></div>
  <span class="domain-close-btn" onclick="closeDomain()">✕</span>
</div>

<script>
function mkParticles(){
  var c=document.getElementById('ptcl');
  if(!c)return; c.innerHTML='';
  for(var i=0;i<55;i++){
    var p=document.createElement('div');
    p.className='particle';
    var s=Math.random()*7+2;
    var isOrange=Math.random()>.5;
    p.style.cssText='width:'+s+'px;height:'+s+'px;left:'+(Math.random()*100)
      +'%;animation-duration:'+(Math.random()*4+3)+'s;animation-delay:'
      +(Math.random()*3)+'s;background:rgba('
      +(isOrange?'255,69,0':'255,215,0')+',0.8);';
    c.appendChild(p);
  }
}
function activateDomain(main,sub){
  var o=document.getElementById('domain-overlay');
  var m=document.getElementById('dom-main');
  var s=document.getElementById('dom-sub');
  if(!o)return;
  if(m&&main)m.textContent=main;
  if(s&&sub)s.textContent=sub;
  mkParticles();
  o.classList.add('active');
  try{playSound();}catch(e){}
  clearTimeout(window._dt);
  window._dt=setTimeout(closeDomain,10000);
}
function closeDomain(){
  var o=document.getElementById('domain-overlay');
  if(o)o.classList.remove('active');
}
function playSound(){
  var ctx=new(window.AudioContext||window.webkitAudioContext)();
  var o1=ctx.createOscillator(),g1=ctx.createGain();
  o1.type='sawtooth';
  o1.frequency.setValueAtTime(65,ctx.currentTime);
  o1.frequency.exponentialRampToValueAtTime(18,ctx.currentTime+1.8);
  g1.gain.setValueAtTime(0.45,ctx.currentTime);
  g1.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+1.8);
  o1.connect(g1);g1.connect(ctx.destination);
  o1.start();o1.stop(ctx.currentTime+1.8);
  var o2=ctx.createOscillator(),g2=ctx.createGain();
  o2.type='square';
  o2.frequency.setValueAtTime(900,ctx.currentTime);
  o2.frequency.exponentialRampToValueAtTime(180,ctx.currentTime+0.6);
  g2.gain.setValueAtTime(0.22,ctx.currentTime);
  g2.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+0.6);
  o2.connect(g2);g2.connect(ctx.destination);
  o2.start();o2.stop(ctx.currentTime+0.6);
}
window.addEventListener('message',function(e){
  if(!e.data)return;
  if(e.data.type==='ACTIVATE')activateDomain(e.data.main,e.data.sub);
  if(e.data.type==='CLOSE')closeDomain();
});
</script>
</body>
</html>
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
        "pose": "양손 손가락을 서로 교차해 맞잡는 형태 (양손 모두 손가락 펴기)",
        "ai_keyword": ["양손 교차", "손가락 맞잡기", "interlocked fingers", "clasp hands"],
        "emoji": "🔵",
    },
    "폐옥염정 — 후시구로 메구미": {
        "main": "嵌合暗翳庭",
        "sub": "「十種影法術」",
        "desc": "십종영법술로 만든 식신들의 세계를 펼친다.",
        "color": "#4B0082",
        "pose": "검지+중지만 펴고 나머지 손가락 접기 (인/印 모양)",
        "ai_keyword": ["검지 중지", "두 손가락", "peace sign", "victory sign", "인 모양"],
        "emoji": "🌑",
    },
    "흉흉욕식 — 조로": {
        "main": "凶凶呪胎",
        "sub": "「特級呪霊」",
        "desc": "용암과 화염으로 가득한 세계를 펼친다.",
        "color": "#FF4500",
        "pose": "양손 모든 손가락 활짝 펴기",
        "ai_keyword": ["양손 활짝", "모든 손가락", "both hands open", "spread fingers"],
        "emoji": "🔥",
    },
    "자충玫 — 쿠기사키 노바라": {
        "main": "蝶蛆嵐",
        "sub": "「共鳴り」",
        "desc": "못을 통해 원거리 타격하는 공명 기법.",
        "color": "#8B0000",
        "pose": "한 손 주먹 + 다른 손 검지만 펴서 가리키기",
        "ai_keyword": ["주먹", "검지", "pointing", "fist and index", "가리키기"],
        "emoji": "🔴",
    },
    "자수밀원 — 마히토": {
        "main": "自閉円頓裹",
        "sub": "「無為転変」",
        "desc": "영혼을 직접 조작하는 무위전변.",
        "color": "#9B59B6",
        "pose": "한 손으로 주먹 쥐기 (모든 손가락 접기)",
        "ai_keyword": ["주먹", "fist", "closed hand", "손가락 모두 접기"],
        "emoji": "🟣",
    },
}

# ──────────────────────────────────────────
# Claude API 함수들
# ──────────────────────────────────────────
def pil_to_base64(img: Image.Image, fmt: str = "JPEG") -> str:
    """PIL 이미지를 base64 문자열로 변환."""
    buf = io.BytesIO()
    rgb_img = img.convert("RGB")
    rgb_img.save(buf, format=fmt, quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def analyze_hand_gesture(api_key: str, img: Image.Image) -> dict:
    """
    Claude Vision으로 손동작을 분석하여 영역전개 매칭 결과 반환.
    반환: { "detected": bool, "domain": str|None, "confidence": float,
             "description": str, "hand_desc": str }
    """
    client = anthropic.Anthropic(api_key=api_key)

    domain_list = "\n".join([
        f"- {name}: {data['pose']} (키워드: {', '.join(data['ai_keyword'][:3])})"
        for name, data in DOMAINS.items()
    ])

    prompt = f"""이 이미지에서 손동작을 분석해주세요.

분석 대상 영역전개 손동작 목록:
{domain_list}

다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{{
  "hand_detected": true/false,
  "hand_description": "손동작에 대한 간단한 설명",
  "matched_domain": "매칭된 영역전개 이름 (없으면 null)",
  "confidence": 0.0~1.0,
  "reason": "매칭 이유 또는 미매칭 이유"
}}

손이 보이지 않으면 hand_detected를 false로 설정하세요.
신뢰도 0.7 이상일 때만 matched_domain을 설정하세요."""

    img_b64 = pil_to_base64(img)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )

        raw = response.content[0].text.strip()
        # JSON 블록 추출
        if "
