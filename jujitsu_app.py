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

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: #0a0a0a !important;
    color: #e0e0e0;
}
[data-testid="stSidebar"]  { background: #111 !important; }
[data-testid="stHeader"]   { background: transparent !important; }
h1 { color: #c0392b !important; }

.stButton > button {
    background: linear-gradient(135deg,#8B0000,#4a0000) !important;
    color: #FFD700 !important;
    border: 1px solid #FF4500 !important;
    border-radius: 10px !important;
    font-weight: bold !important;
    font-size: 1rem !important;
    letter-spacing: 0.08em !important;
    padding: 0.55rem 1rem !important;
    transition: all 0.2s !important;
    width: 100%;
}
.stButton > button:hover {
    background: linear-gradient(135deg,#c0392b,#8B0000) !important;
    box-shadow: 0 0 20px rgba(255,69,0,0.6) !important;
}
.stButton > button:disabled {
    background: #1a1a1a !important;
    color: #444 !important;
    border-color: #333 !important;
}

.tip-box {
    background: #111;
    border: 1px dashed #2a2a2a;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.78rem;
    color: #555;
    line-height: 1.85;
    margin-top: 14px;
}

.result-box {
    background: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 16px 18px;
    margin: 8px 0;
}

.gauge-bg {
    background: #222;
    border-radius: 6px;
    height: 16px;
    overflow: hidden;
    margin: 4px 0 10px 0;
}
.gauge-bar { height: 100%; border-radius: 6px; }

hr { border-color: #222 !important; }

[data-testid="stCameraInput"] > div {
    border: 2px solid #8B0000 !important;
    border-radius: 12px !important;
    box-shadow: 0 0 20px rgba(139,0,0,0.35) !important;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# 영역전개 오버레이
# ──────────────────────────────────────────
OVERLAY_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:transparent; overflow:hidden; }
#ov {
    display:none; position:fixed;
    top:0;left:0;right:0;bottom:0;
    z-index:99999; pointer-events:none; overflow:hidden;
}
#ov.on { display:block; }
.bg { position:absolute; inset:0; animation:pulse 2s ease-in-out infinite alternate; }
@keyframes pulse { from{opacity:.85} to{opacity:1} }
.crack {
    position:absolute; height:2px; width:100%;
    animation:flicker .3s infinite;
}
@keyframes flicker { 0%,100%{opacity:1} 50%{opacity:.15} }
.ring {
    position:absolute; top:50%; left:50%;
    border-radius:50%; animation:spin linear infinite;
}
@keyframes spin {
    from{transform:translate(-50%,-50%) rotate(0deg)}
    to{transform:translate(-50%,-50%) rotate(360deg)}
}
.mt {
    position:absolute; top:43%; left:50%;
    font-family:'Noto Serif JP',serif;
    font-size:clamp(2.8rem,8vw,6rem); font-weight:900;
    color:#FFD700; white-space:nowrap; letter-spacing:.4em;
    animation:appear .7s ease-out forwards,
              glow 2s ease-in-out infinite alternate .7s;
    opacity:0;
}
.st {
    position:absolute; top:62%; left:50%;
    font-family:'Noto Serif JP',serif;
    font-size:clamp(1.2rem,4vw,2.4rem);
    color:rgba(255,215,0,.9); letter-spacing:.3em;
    animation:fadein 1s ease-out .5s forwards; opacity:0;
}
@keyframes appear {
    from{opacity:0;transform:translate(-50%,-50%) scale(.3)}
    to{opacity:1;transform:translate(-50%,-50%) scale(1)}
}
@keyframes fadein {
    from{opacity:0;transform:translateX(-50%) translateY(10px)}
    to{opacity:1;transform:translateX(-50%) translateY(0)}
}
@keyframes glow {
    from{text-shadow:0 0 15px #FF4500,0 0 40px #FF4500}
    to{text-shadow:0 0 30px #FFD700,0 0 80px #FF4500,0 0 140px #FF0000}
}
.xbtn {
    position:absolute; top:20px; right:32px;
    font-size:2.5rem; color:rgba(255,215,0,.65);
    cursor:pointer; pointer-events:all;
    z-index:100001; user-select:none;
    transition:color .2s,transform .2s;
}
.xbtn:hover { color:#FFD700; transform:scale(1.15); }
.ptcl {
    position:absolute; border-radius:50%;
    animation:rise linear infinite; pointer-events:none;
}
@keyframes rise {
    from{transform:translateY(108vh) scale(1);opacity:.9}
    to{transform:translateY(-10vh) scale(0);opacity:0}
}
</style>
</head>
<body>
<div id="ov">
  <div class="bg" id="dyn-bg"></div>
  <div class="crack" id="c1"></div>
  <div class="crack" id="c2"></div>
  <div class="crack" id="c3"></div>
  <div class="crack" id="c4"></div>
  <div class="ring" id="r1"></div>
  <div class="ring" id="r2"></div>
  <div class="ring" id="r3"></div>
  <div class="ring" id="r4"></div>
  <div class="mt" id="mt">領域展開</div>
  <div class="st" id="st">無量空処</div>
  <div id="ptcls"></div>
  <span class="xbtn" onclick="closeOv()">&#10005;</span>
</div>
<script>
var TH = {
  blue:   {bg:'rgba(0,50,120,0.96)',   ck:'#00BFFF', rg:'rgba(0,191,255,0.5)'},
  dark:   {bg:'rgba(10,0,30,0.97)',    ck:'#7B2FBE', rg:'rgba(123,47,190,0.5)'},
  red:    {bg:'rgba(139,0,0,0.96)',    ck:'#FF4500', rg:'rgba(255,69,0,0.55)'},
  crimson:{bg:'rgba(100,0,0,0.97)',    ck:'#DC143C', rg:'rgba(220,20,60,0.5)'},
  purple: {bg:'rgba(40,0,80,0.97)',    ck:'#9B59B6', rg:'rgba(155,89,182,0.5)'}
};
function hexToRgb(h) {
  h = h.replace('#','');
  return parseInt(h.substring(0,2),16)+','+
         parseInt(h.substring(2,4),16)+','+
         parseInt(h.substring(4,6),16);
}
function applyTheme(t) {
  var th = TH[t] || TH.red;
  var bg = document.getElementById('dyn-bg');
  if (bg) bg.style.background =
    'radial-gradient(ellipse at center,'+th.bg+' 0%,rgba(0,0,0,0.99) 100%)';
  var cd = [
    {id:'c1',top:'17%',rot:'-14deg',op:'1'},
    {id:'c2',top:'34%',rot:'8deg',  op:'.5'},
    {id:'c3',top:'63%',rot:'-5deg', op:'.65'},
    {id:'c4',top:'83%',rot:'12deg', op:'.4'}
  ];
  cd.forEach(function(c){
    var el=document.getElementById(c.id); if(!el) return;
    el.style.top=c.top; el.style.opacity=c.op;
    el.style.transform='rotate('+c.rot+')';
    el.style.background='linear-gradient(90deg,transparent,'+th.ck+',transparent)';
  });
  var rg = [
    {id:'r1',sz:'280px',dur:'5s', dir:'normal', st:'solid'},
    {id:'r2',sz:'500px',dur:'9s', dir:'reverse',st:'solid'},
    {id:'r3',sz:'720px',dur:'13s',dir:'normal', st:'dashed'},
    {id:'r4',sz:'940px',dur:'17s',dir:'reverse',st:'dotted'}
  ];
  rg.forEach(function(r){
    var el=document.getElementById(r.id); if(!el) return;
    el.style.width=r.sz; el.style.height=r.sz;
    el.style.border='2px '+r.st+' '+th.rg;
    el.style.animationDuration=r.dur;
    el.style.animationDirection=r.dir;
  });
}
function mkParticles(rgb) {
  var c=document.getElementById('ptcls'); if(!c) return;
  c.innerHTML='';
  for(var i=0;i<60;i++){
    var p=document.createElement('div'); p.className='ptcl';
    var s=Math.random()*8+2;
    var useGold=Math.random()>.5;
    p.style.cssText=
      'width:'+s+'px;height:'+s+'px;'+
      'left:'+(Math.random()*100)+'%;'+
      'animation-duration:'+(Math.random()*5+3)+'s;'+
      'animation-delay:'+(Math.random()*4)+'s;'+
      'background:rgba('+(useGold?'255,215,0':rgb)+',0.85);';
    c.appendChild(p);
  }
}
function openOv(main,sub,theme) {
  var o=document.getElementById('ov');
  var mt=document.getElementById('mt');
  var st=document.getElementById('st');
  if(!o) return;
  if(mt){mt.textContent=main||'領域展開';
    mt.style.animation='none'; mt.offsetHeight; mt.style.animation='';}
  if(st){st.textContent=sub||'';
    st.style.animation='none'; st.offsetHeight; st.style.animation='';}
  var t=theme||'red';
  applyTheme(t);
  var rgb=hexToRgb((TH[t]||TH.red).ck);
  mkParticles(rgb);
  o.classList.add('on');
  try{playSound();}catch(e){}
  clearTimeout(window._ac);
  window._ac=setTimeout(closeOv,12000);
}
function closeOv() {
  var o=document.getElementById('ov'); if(o) o.classList.remove('on');
}
function playSound() {
  var ctx=new(window.AudioContext||window.webkitAudioContext)();
  var o1=ctx.createOscillator(),g1=ctx.createGain();
  o1.type='sawtooth';
  o1.frequency.setValueAtTime(65,ctx.currentTime);
  o1.frequency.exponentialRampToValueAtTime(18,ctx.currentTime+2);
  g1.gain.setValueAtTime(0.5,ctx.currentTime);
  g1.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+2);
  o1.connect(g1); g1.connect(ctx.destination);
  o1.start(); o1.stop(ctx.currentTime+2);
  var o2=ctx.createOscillator(),g2=ctx.createGain();
  o2.type='square';
  o2.frequency.setValueAtTime(1000,ctx.currentTime);
  o2.frequency.exponentialRampToValueAtTime(150,ctx.currentTime+0.7);
  g2.gain.setValueAtTime(0.25,ctx.currentTime);
  g2.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+0.7);
  o2.connect(g2); g2.connect(ctx.destination);
  o2.start(); o2.stop(ctx.currentTime+0.7);
}
window.addEventListener('message',function(e){
  if(!e.data) return;
  if(e.data.type==='ACTIVATE') openOv(e.data.main,e.data.sub,e.data.theme);
  if(e.data.type==='CLOSE')    closeOv();
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
        "sub":      "私が最強ですので",
        "char":     "고죠 사토루",
        "color":    "#00BFFF",
        "theme":    "blue",
        "pose":     "양손 손가락을 서로 교차해 맞잡기",
        "keywords": ["양손 교차", "interlocked", "clasp"],
        "emoji":    "🔵",
    },
    "폐옥염정": {
        "main":     "嵌合暗翳庭",
        "sub":      "十種影法術",
        "char":     "후시구로 메구미",
        "color":    "#7B2FBE",
        "theme":    "dark",
        "pose":     "검지+중지만 펴고 나머지 접기 (인/印)",
        "keywords": ["검지 중지", "peace sign", "victory"],
        "emoji":    "🌑",
    },
    "흉흉욕식": {
        "main":     "凶凶呪胎",
        "sub":      "特級呪霊",
        "char":     "조로",
        "color":    "#FF4500",
        "theme":    "red",
        "pose":     "양손 모든 손가락 활짝 펴기",
        "keywords": ["양손 활짝", "spread fingers", "open hands"],
        "emoji":    "🔥",
    },
    "자충玫": {
        "main":     "蝶蛆嵐",
        "sub":      "共鳴り",
        "char":     "쿠기사키 노바라",
        "color":    "#DC143C",
        "theme":    "crimson",
        "pose":     "한 손 주먹 + 다른 손 검지만 펴서 가리키기",
        "keywords": ["주먹 검지", "fist pointing"],
        "emoji":    "🔴",
    },
    "자수밀원": {
        "main":     "自閉円頓裹",
        "sub":      "無為転変",
        "char":     "마히토",
        "color":    "#9B59B6",
        "theme":    "purple",
        "pose":     "한 손 주먹 쥐기 (모든 손가락 접기)",
        "keywords": ["주먹", "fist", "closed hand"],
        "emoji":    "🟣",
    },
}

# ──────────────────────────────────────────
# JS 헬퍼 함수
# ──────────────────────────────────────────
def fire_domain_js(main_txt, sub_txt, theme_name):
    safe_main  = main_txt.replace("\\", "").replace("'", "").replace('"', "")
    safe_sub   = sub_txt.replace("\\", "").replace("'", "").replace('"', "")
    safe_theme = theme_name.replace("'", "").replace('"', "")
    js = "<script>"
    js += "(function(){"
    js += "var m={"
    js += "type:'ACTIVATE',"
    js += "main:'" + safe_main + "',"
    js += "sub:'" + safe_sub + "',"
    js += "theme:'" + safe_theme + "'"
    js += "};"
    js += "if(window.parent&&window.parent!==window)"
    js += "window.parent.postMessage(m,'*');"
    js += "})();"
    js += "</script>"
    st.components.v1.html(js, height=0, scrolling=False)


def close_domain_js():
    js = "<script>"
    js += "(function(){"
    js += "if(window.parent&&window.parent!==window)"
    js += "window.parent.postMessage({type:'CLOSE'},'*');"
    js += "})();"
    js += "</script>"
    st.components.v1.html(js, height=0, scrolling=False)


# ──────────────────────────────────────────
# Claude Vision 분석
# ──────────────────────────────────────────
def pil_to_base64(img):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def analyze_gesture(api_key, img):
    client = anthropic.Anthropic(api_key=api_key)

    lines = []
    for name, data in DOMAINS.items():
        kw = ", ".join(data["keywords"])
        lines.append("- " + name + " (" + data["char"] + "): " + data["pose"] + " / 키워드: " + kw)
    domain_str = "\n".join(lines)

    prompt = (
        "이미지의 손동작을 분석해 아래 목록 중 하나와 매칭하세요.\n\n"
        "목록:\n" + domain_str + "\n\n"
        "아래 JSON 형식으로만 응답 (다른 텍스트 금지):\n"
        "{\"hand_detected\":true or false,"
        "\"hand_description\":\"손동작 설명\","
        "\"matched_domain\":\"매칭 이름 또는 null\","
        "\"confidence\":0.0~1.0,"
        "\"reason\":\"이유\"}\n\n"
        "손이 없으면 hand_detected=false. 신뢰도 0.7 미만이면 matched_domain=null."
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

        # JSON 블록 추출
        if "
