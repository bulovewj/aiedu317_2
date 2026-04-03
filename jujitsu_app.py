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
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────
# CSS
# ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@900&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: #0a0a0a !important;
    color: #e0e0e0;
}
[data-testid="stSidebar"] { background: #111 !important; }
[data-testid="stHeader"]  { background: transparent !important; }

h1 { color: #c0392b !important; }

.stButton > button {
    background: linear-gradient(135deg, #8B0000, #4a0000) !important;
    color: #FFD700 !important;
    border: 1px solid #FF4500 !important;
    border-radius: 10px !important;
    font-weight: bold !important;
    font-size: 1.1rem !important;
    letter-spacing: 0.1em !important;
    padding: 0.6rem 1.2rem !important;
    transition: all 0.2s !important;
    width: 100%;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #c0392b, #8B0000) !important;
    box-shadow: 0 0 20px rgba(255,69,0,0.6) !important;
    transform: scale(1.02) !important;
}
.stButton > button:disabled {
    background: #1a1a1a !important;
    color: #444 !important;
    border-color: #333 !important;
    transform: none !important;
}

.domain-card {
    background: #161616;
    border: 2px solid #333;
    border-radius: 14px;
    padding: 16px 20px;
    margin: 8px 0;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
}
.domain-card:hover {
    border-color: #FF4500;
    background: #1f1010;
    box-shadow: 0 0 12px rgba(255,69,0,0.3);
}
.domain-card.active {
    border-color: #FFD700;
    background: #2a1500;
    box-shadow: 0 0 18px rgba(255,215,0,0.4);
}
.domain-card-title {
    font-size: 1rem;
    font-weight: bold;
    color: #FFD700;
    margin-bottom: 3px;
}
.domain-card-jp {
    font-family: 'Noto Serif JP', serif;
    font-size: 1.3rem;
    font-weight: 900;
}
.domain-card-pose {
    font-size: 0.78rem;
    color: #888;
    margin-top: 4px;
}

.status-box {
    background: #161616;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 10px 0;
    border: 1px solid #2a2a2a;
    font-size: 0.9rem;
    color: #bbb;
    line-height: 1.7;
}

.gauge-wrap { margin: 8px 0; }
.gauge-label {
    font-size: 0.82rem;
    color: #888;
    margin-bottom: 3px;
}
.gauge-bg {
    background: #222;
    border-radius: 6px;
    height: 16px;
    overflow: hidden;
}
.gauge-bar {
    height: 100%;
    border-radius: 6px;
    transition: width 0.4s ease;
}

.hint-box {
    background: #111;
    border: 1px dashed #333;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.8rem;
    color: #666;
    line-height: 1.8;
    margin-top: 12px;
}

hr { border-color: #222 !important; }

/* 카메라 영역 강조 */
[data-testid="stCameraInput"] > div {
    border: 2px solid #8B0000 !important;
    border-radius: 12px !important;
    box-shadow: 0 0 20px rgba(139,0,0,0.4) !important;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# 영역전개 오버레이 HTML
# ──────────────────────────────────────────
OVERLAY_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:transparent; overflow:hidden; }

#overlay {
    display: none;
    position: fixed;
    top:0; left:0; right:0; bottom:0;
    z-index: 99999;
    pointer-events: none;
    overflow: hidden;
}
#overlay.on { display: block; }

.bg {
    position: absolute;
    inset: 0;
    animation: pulse 2s ease-in-out infinite alternate;
}
@keyframes pulse { from{opacity:.85} to{opacity:1} }

.crack {
    position: absolute;
    height: 2px;
    width: 100%;
    animation: flicker 0.3s infinite;
}
@keyframes flicker { 0%,100%{opacity:1} 50%{opacity:.15} }

.ring {
    position: absolute;
    top:50%; left:50%;
    border-radius: 50%;
    animation: spin linear infinite;
}
@keyframes spin {
    from { transform: translate(-50%,-50%) rotate(0deg); }
    to   { transform: translate(-50%,-50%) rotate(360deg); }
}

.main-txt {
    position: absolute;
    top:43%; left:50%;
    font-family: 'Noto Serif JP', serif;
    font-size: clamp(2.8rem, 8vw, 6rem);
    font-weight: 900;
    color: #FFD700;
    white-space: nowrap;
    letter-spacing: 0.4em;
    animation: appear .7s ease-out forwards,
               glow 2s ease-in-out infinite alternate .7s;
    opacity: 0;
}
.sub-txt {
    position: absolute;
    top:62%; left:50%;
    font-family: 'Noto Serif JP', serif;
    font-size: clamp(1.2rem, 4vw, 2.4rem);
    color: rgba(255,215,0,0.9);
    letter-spacing: 0.3em;
    animation: fadeIn 1s ease-out .5s forwards;
    opacity: 0;
}

@keyframes appear {
    from { opacity:0; transform:translate(-50%,-50%) scale(.3); }
    to   { opacity:1; transform:translate(-50%,-50%) scale(1); }
}
@keyframes fadeIn {
    from { opacity:0; transform:translateX(-50%) translateY(10px); }
    to   { opacity:1; transform:translateX(-50%) translateY(0); }
}
@keyframes glow {
    from { text-shadow: 0 0 15px #FF4500, 0 0 40px #FF4500; }
    to   { text-shadow: 0 0 30px #FFD700, 0 0 80px #FF4500, 0 0 140px #FF0000; }
}

.close-btn {
    position: absolute;
    top:20px; right:32px;
    font-size: 2.5rem;
    color: rgba(255,215,0,0.65);
    cursor: pointer;
    pointer-events: all;
    z-index: 100001;
    user-select: none;
    transition: color 0.2s, transform 0.2s;
}
.close-btn:hover { color:#FFD700; transform:scale(1.15); }

.ptcl {
    position: absolute;
    border-radius: 50%;
    animation: rise linear infinite;
    pointer-events: none;
}
@keyframes rise {
    from { transform:translateY(108vh) scale(1); opacity:.9; }
    to   { transform:translateY(-10vh) scale(0); opacity:0; }
}
</style>
</head>
<body>
<div id="overlay">
  <div class="bg" id="dyn-bg"></div>

  <div class="crack" id="c1"></div>
  <div class="crack" id="c2"></div>
  <div class="crack" id="c3"></div>
  <div class="crack" id="c4"></div>

  <div class="ring" id="r1"></div>
  <div class="ring" id="r2"></div>
  <div class="ring" id="r3"></div>
  <div class="ring" id="r4"></div>

  <div class="main-txt" id="main-txt">領域展開</div>
  <div class="sub-txt"  id="sub-txt">無量空処</div>

  <div id="particles"></div>
  <span class="close-btn" onclick="closeOverlay()">✕</span>
</div>

<script>
var THEMES = {
    blue:   { bg:'rgba(0,50,120,0.96)',  crack:'#00BFFF', ring:'rgba(0,191,255,0.5)' },
    dark:   { bg:'rgba(10,0,30,0.97)',   crack:'#7B2FBE', ring:'rgba(123,47,190,0.5)' },
    red:    { bg:'rgba(139,0,0,0.96)',   crack:'#FF4500', ring:'rgba(255,69,0,0.55)' },
    crimson:{ bg:'rgba(100,0,0,0.97)',   crack:'#DC143C', ring:'rgba(220,20,60,0.5)' },
    purple: { bg:'rgba(40,0,80,0.97)',   crack:'#9B59B6', ring:'rgba(155,89,182,0.5)' }
};

function applyTheme(t) {
    var theme = THEMES[t] || THEMES.red;
    var bg = document.getElementById('dyn-bg');
    if (bg) bg.style.background =
        'radial-gradient(ellipse at center,' + theme.bg + ' 0%,rgba(0,0,0,0.99) 100%)';

    var cracks = [
        {id:'c1', top:'17%', rot:'-14deg', op:'1'},
        {id:'c2', top:'34%', rot:'8deg',   op:'.5'},
        {id:'c3', top:'63%', rot:'-5deg',  op:'.65'},
        {id:'c4', top:'83%', rot:'12deg',  op:'.4'}
    ];
    cracks.forEach(function(c) {
        var el = document.getElementById(c.id);
        if (!el) return;
        el.style.top = c.top;
        el.style.transform = 'rotate(' + c.rot + ')';
        el.style.opacity = c.op;
        el.style.background =
            'linear-gradient(90deg,transparent,' + theme.crack + ',transparent)';
    });

    var rings = [
        {id:'r1', size:'280px', dur:'5s',  dir:'normal',  style:'solid'},
        {id:'r2', size:'500px', dur:'9s',  dir:'reverse', style:'solid'},
        {id:'r3', size:'720px', dur:'13s', dir:'normal',  style:'dashed'},
        {id:'r4', size:'940px', dur:'17s', dir:'reverse', style:'dotted'}
    ];
    rings.forEach(function(r) {
        var el = document.getElementById(r.id);
        if (!el) return;
        el.style.width  = r.size;
        el.style.height = r.size;
        el.style.border = '2px ' + r.style + ' ' + theme.ring;
        el.style.animationDuration  = r.dur;
        el.style.animationDirection = r.dir;
    });
}

function makeParticles(crackColor) {
    var c = document.getElementById('particles');
    if (!c) return;
    c.innerHTML = '';
    for (var i = 0; i < 60; i++) {
        var p = document.createElement('div');
        p.className = 'ptcl';
        var s = Math.random() * 8 + 2;
        var useAccent = Math.random() > 0.5;
        p.style.cssText =
            'width:' + s + 'px;height:' + s + 'px;' +
            'left:' + (Math.random() * 100) + '%;' +
            'animation-duration:' + (Math.random() * 5 + 3) + 's;' +
            'animation-delay:' + (Math.random() * 4) + 's;' +
            'background:rgba(' + (useAccent ? '255,215,0' : crackColor) + ',0.85);';
        c.appendChild(p);
    }
}

function openOverlay(main, sub, theme) {
    var o  = document.getElementById('overlay');
    var mt = document.getElementById('main-txt');
    var st = document.getElementById('sub-txt');
    if (!o) return;

    if (mt) mt.textContent = main || '領域展開';
    if (st) st.textContent = sub  || '';

    // 애니메이션 재시작
    if (mt) { mt.style.animation = 'none'; mt.offsetHeight; mt.style.animation = ''; }
    if (st) { st.style.animation = 'none'; st.offsetHeight; st.style.animation = ''; }

    var t = theme || 'red';
    applyTheme(t);

    var themeObj = THEMES[t] || THEMES.red;
    var crackRGB = themeObj.crack.replace('#','');
    var r = parseInt(crackRGB.substring(0,2),16);
    var g = parseInt(crackRGB.substring(2,4),16);
    var b = parseInt(crackRGB.substring(4,6),16);
    makeParticles(r+','+g+','+b);

    o.classList.add('on');
    try { playSound(); } catch(e) {}
    clearTimeout(window._autoClose);
    window._autoClose = setTimeout(closeOverlay, 12000);
}

function closeOverlay() {
    var o = document.getElementById('overlay');
    if (o) o.classList.remove('on');
}

function playSound() {
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var o1 = ctx.createOscillator(), g1 = ctx.createGain();
    o1.type = 'sawtooth';
    o1.frequency.setValueAtTime(65, ctx.currentTime);
    o1.frequency.exponentialRampToValueAtTime(18, ctx.currentTime + 2);
    g1.gain.setValueAtTime(0.5, ctx.currentTime);
    g1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 2);
    o1.connect(g1); g1.connect(ctx.destination);
    o1.start(); o1.stop(ctx.currentTime + 2);

    var o2 = ctx.createOscillator(), g2 = ctx.createGain();
    o2.type = 'square';
    o2.frequency.setValueAtTime(1000, ctx.currentTime);
    o2.frequency.exponentialRampToValueAtTime(150, ctx.currentTime + 0.7);
    g2.gain.setValueAtTime(0.25, ctx.currentTime);
    g2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.7);
    o2.connect(g2); g2.connect(ctx.destination);
    o2.start(); o2.stop(ctx.currentTime + 0.7);
}

window.addEventListener('message', function(e) {
    if (!e.data) return;
    if (e.data.type === 'ACTIVATE') openOverlay(e.data.main, e.data.sub, e.data.theme);
    if (e.data.type === 'CLOSE')    closeOverlay();
});
</script>
</body>
</html>"""

st.components.v1.html(OVERLAY_HTML, height=0, scrolling=False)

# ──────────────────────────────────────────
# 영역전개 데이터
# ──────────────────────────────────────────
DOMAINS = {
    "무량공처": {
        "main":     "無量空処",
        "sub":      "「私が最強ですので」",
        "char":     "고죠 사토루",
        "color":    "#00BFFF",
        "theme":    "blue",
        "pose":     "양손 손가락을 서로 교차해 맞잡기",
        "keywords": ["양손 교차", "interlocked", "clasp", "두 손 맞잡기"],
        "emoji":    "🔵",
    },
    "폐옥염정": {
        "main":     "嵌合暗翳庭",
        "sub":      "「十種影法術」",
        "char":     "후시구로 메구미",
        "color":    "#7B2FBE",
        "theme":    "dark",
        "pose":     "검지+중지만 펴고 나머지 접기 (인/印)",
        "keywords": ["검지 중지", "peace sign", "victory", "두 손가락"],
        "emoji":    "🌑",
    },
    "흉흉욕식": {
        "main":     "凶凶呪胎",
        "sub":      "「特級呪霊」",
        "char":     "조로",
        "color":    "#FF4500",
        "theme":    "red",
        "pose":     "양손 모든 손가락 활짝 펴기",
        "keywords": ["양손 활짝", "spread fingers", "open hands", "모든 손가락"],
        "emoji":    "🔥",
    },
    "자충玫": {
        "main":     "蝶蛆嵐",
        "sub":      "「共鳴り」",
        "char":     "쿠기사키 노바라",
        "color":    "#DC143C",
        "theme":    "crimson",
        "pose":     "한 손 주먹 + 다른 손 검지만 펴서 가리키기",
        "keywords": ["주먹 검지", "fist pointing", "주먹과 검지"],
        "emoji":    "🔴",
    },
    "자수밀원": {
        "main":     "自閉円頓裹",
        "sub":      "「無為転変」",
        "char":     "마히토",
        "color":    "#9B59B6",
        "theme":    "purple",
        "pose":     "한 손 주먹 쥐기 (모든 손가락 접기)",
        "keywords": ["주먹", "fist", "closed hand", "손가락 접기"],
        "emoji":    "🟣",
    },
}

# ──────────────────────────────────────────
# JS 헬퍼
# ──────────────────────────────────────────
def fire_domain_js(main: str, sub: str, theme: str = "red"):
    safe_main  = main.replace("'", "\\'")
    safe_sub   = sub.replace("'", "\\'")
    safe_theme = theme.replace("'", "\\'")
    html = (
        "<script>(function(){"
        "var m={type:'ACTIVATE',"
        "main:'" + safe_main + "',"
        "sub:'" + safe_sub + "',"
        "theme:'" + safe_theme + "'};"
        "if(window.parent&&window.parent!==window)"
        "window.parent.postMessage(m,'*');"
        "})();</script>"
    )
    st.components.v1.html(html, height=0, scrolling=False)


def close_domain_js():
    html = (
        "<script>(function(){"
        "if(window.parent&&window.parent!==window)"
        "window.parent.postMessage({type:'CLOSE'},'*');"
        "})();</script>"
    )
    st.components.v1.html(html, height=0, scrolling=False)


# ──────────────────────────────────────────
# Claude Vision 손동작 분석
# ──────────────────────────────────────────
def pil_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def analyze_gesture(api_key: str, img: Image.Image) -> dict:
    client = anthropic.Anthropic(api_key=api_key)

    lines = []
    for name, data in DOMAINS.items():
        kw = ", ".join(data["keywords"][:3])
        lines.append("- " + name + " (" + data["char"] + "): " + data["pose"] + " / 키워드: " + kw)
    domain_str = "\n".join(lines)

    prompt = (
        "이미지에서 손동작을 분석해 아래 영역전개 중 하나와 매칭하세요.\n\n"
        "목록:\n" + domain_str + "\n\n"
        "JSON만 출력 (다른 텍스트 없음):\n"
        '{"hand_detected":true/false,'
        '"hand_description":"손동작 설명",'
        '"matched_domain":"매칭 이름 또는 null",'
        '"confidence":0.0~1.0,'
        '"reason":"이유"}\n\n'
        "손 없으면 hand_detected=false. 신뢰도 0.7 미만이면 matched_domain=null."
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": pil_to_base64(img),
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )

        raw = response.content[0].text.strip()
        if "
