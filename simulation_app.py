import streamlit as st
import anthropic
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re

# ── 페이지 기본 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="물리 선생님 챗봇 🎢",
    page_icon="🎢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS 스타일 ────────────────────────────────────────────────
st.markdown("""
<style>
  /* 전체 배경 */
  .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); }

  /* 사이드바 */
  [data-testid="stSidebar"] {
      background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
      border-right: 2px solid #e94560;
  }

  /* 채팅 말풍선 - 사용자 */
  .user-bubble {
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      padding: 12px 18px;
      border-radius: 18px 18px 4px 18px;
      margin: 8px 0 8px 20%;
      box-shadow: 0 4px 15px rgba(102,126,234,0.4);
      font-size: 15px;
      line-height: 1.6;
  }

  /* 채팅 말풍선 - AI */
  .ai-bubble {
      background: linear-gradient(135deg, #1e3c72, #2a5298);
      color: #e0e8ff;
      padding: 12px 18px;
      border-radius: 18px 18px 18px 4px;
      margin: 8px 20% 8px 0;
      box-shadow: 0 4px 15px rgba(30,60,114,0.5);
      font-size: 15px;
      line-height: 1.8;
      border-left: 3px solid #4fc3f7;
  }

  /* 카드 */
  .info-card {
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 12px;
      padding: 16px;
      margin: 8px 0;
      backdrop-filter: blur(10px);
  }

  /* 에너지 뱃지 */
  .energy-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: bold;
      margin: 3px;
  }
  .ke-badge  { background: #ff6b6b; color: white; }
  .pe-badge  { background: #4ecdc4; color: white; }
  .tot-badge { background: #ffd93d; color: #333; }

  /* 타이틀 */
  .main-title {
      text-align: center;
      font-size: 2.2em;
      font-weight: 800;
      background: linear-gradient(90deg, #f093fb, #f5576c, #4facfe);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 4px;
  }
  .sub-title {
      text-align: center;
      color: #a0aec0;
      font-size: 1em;
      margin-bottom: 20px;
  }

  /* Streamlit 기본 요소 색상 보정 */
  .stMarkdown p { color: #e0e8ff; }
  label         { color: #a0c4ff !important; }
  h1,h2,h3      { color: #f0f4ff; }
</style>
""", unsafe_allow_html=True)

# ── 상수 ──────────────────────────────────────────────────────
G = 9.8   # 중력가속도 (m/s²)

SYSTEM_PROMPT = """당신은 친절하고 열정적인 중학교 물리 선생님입니다. 
이름은 '에너지쌤'이며, 특히 역학적 에너지(위치에너지, 운동에너지)를 
롤러코스터를 예시로 설명하는 것을 좋아합니다.

## 핵심 교육 철학
- 어려운 개념을 일상 속 예시(롤러코스터, 그네, 미끄럼틀 등)로 쉽게 설명합니다.
- 수식을 쓸 때는 반드시 말로도 풀어서 설명합니다.
- 학생이 틀려도 격려하며, 정답으로 유도합니다.
- 이모지를 적절히 사용해 친근한 분위기를 만듭니다.

## 주요 물리 개념 (반드시 정확하게)
- 위치에너지(PE) = mgh  → 높이가 높을수록, 질량이 클수록 크다
- 운동에너지(KE) = ½mv² → 속력이 빠를수록, 질량이 클수록 크다
- 역학적 에너지 보존 법칙: PE + KE = 일정 (마찰 무시 시)
- 롤러코스터: 높은 곳(PE↑, KE↓) → 낮은 곳(PE↓, KE↑)

## 답변 스타일
- 중학생 수준에 맞는 쉬운 언어를 사용합니다.
- 계산 문제는 단계별로 풀어줍니다.
- 답변 끝에 관련 질문을 하나씩 던져 호기심을 자극합니다.
- 시뮬레이션 관련 질문 시 왼쪽 사이드바의 설정을 활용하도록 안내합니다.
"""

# ── 롤러코스터 트랙 생성 ──────────────────────────────────────
def make_track(heights: list[float], n_points: int = 400) -> tuple:
    """높이 리스트로 부드러운 롤러코스터 트랙을 생성합니다."""
    n_ctrl = len(heights)
    x_ctrl = np.linspace(0, 100, n_ctrl)
    x_fine = np.linspace(0, 100, n_points)
    # 3차 스플라인 보간 (numpy poly로 간단 구현)
    coeffs = np.polyfit(x_ctrl, heights, min(n_ctrl - 1, 5))
    y_fine = np.polyval(coeffs, x_fine)
    # 음수 방지
    y_fine = np.clip(y_fine, 0.5, None)
    return x_fine, y_fine


def compute_energies(mass: float, heights: np.ndarray) -> tuple:
    """각 지점의 위치에너지·운동에너지·역학적 에너지를 계산합니다."""
    h0   = heights[0]          # 출발 높이
    pe   = mass * G * heights  # 위치에너지
    te   = mass * G * h0       # 역학적 에너지 보존 (총합 = 출발 PE)
    ke   = np.clip(te - pe, 0, None)  # 운동에너지 (음수 방지)
    v    = np.sqrt(2 * ke / mass)     # 속도
    return pe, ke, np.full_like(pe, te), v


# ── 롤러코스터 시각화 ─────────────────────────────────────────
def draw_simulation(mass: float, heights: list[float], car_pos_pct: float):
    """Plotly로 롤러코스터 + 에너지 그래프를 그립니다."""
    x, y = make_track(heights)
    pe, ke, te, v = compute_energies(mass, y)

    # 카트 위치 인덱스
    idx = int(car_pos_pct / 100 * (len(x) - 1))
    idx = np.clip(idx, 0, len(x) - 1)
    car_x, car_y = float(x[idx]), float(y[idx])
    cur_pe, cur_ke, cur_te, cur_v = (
        float(pe[idx]), float(ke[idx]), float(te[idx]), float(v[idx])
    )

    # ── 서브플롯 레이아웃 ──
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "🎢 롤러코스터 트랙",
            "⚡ 에너지 막대 그래프",
            "📈 위치별 에너지 변화",
            "🚀 위치별 속도 변화",
        ),
        row_heights=[0.55, 0.45],
        column_widths=[0.6, 0.4],
        vertical_spacing=0.12,
        horizontal_spacing=0.1,
    )

    # ── (1,1) 트랙 ──
    # 트랙 아래 채우기
    fig.add_trace(go.Scatter(
        x=np.append(x, [x[-1], x[0]]),
        y=np.append(y, [0, 0]),
        fill="toself",
        fillcolor="rgba(100,80,60,0.3)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False, hoverinfo="skip",
    ), row=1, col=1)

    # 트랙 선
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="lines",
        line=dict(color="#a0c4ff", width=4),
        name="트랙",
        hovertemplate="x=%{x:.1f}m<br>높이=%{y:.1f}m",
    ), row=1, col=1)

    # 카트
    fig.add_trace(go.Scatter(
        x=[car_x], y=[car_y + 0.8],
        mode="markers+text",
        marker=dict(size=28, color="#ff6b6b",
                    symbol="square", line=dict(color="white", width=2)),
        text=["🎠"],
        textfont=dict(size=18),
        name="카트",
        hovertemplate=(
            f"높이: {car_y:.1f}m<br>"
            f"속도: {cur_v:.2f}m/s<br>"
            f"PE: {cur_pe:.1f}J<br>"
            f"KE: {cur_ke:.1f}J"
        ),
    ), row=1, col=1)

    # 높이 점선
    fig.add_trace(go.Scatter(
        x=[car_x, car_x], y=[0, car_y],
        mode="lines",
        line=dict(color="#ffd93d", width=1.5, dash="dot"),
        showlegend=False, hoverinfo="skip",
    ), row=1, col=1)

    # 높이 텍스트
    fig.add_annotation(
        x=car_x, y=car_y / 2,
        text=f"h={car_y:.1f}m",
        font=dict(color="#ffd93d", size=11),
        showarrow=False,
        xshift=18,
        row=1, col=1,
    )

    # ── (1,2) 에너지 막대 ──
    bar_labels = ["위치에너지(PE)", "운동에너지(KE)", "역학적에너지(TE)"]
    bar_values = [cur_pe, cur_ke, cur_te]
    bar_colors = ["#4ecdc4", "#ff6b6b", "#ffd93d"]

    fig.add_trace(go.Bar(
        x=bar_labels,
        y=bar_values,
        marker_color=bar_colors,
        text=[f"{v:.1f}J" for v in bar_values],
        textposition="outside",
        textfont=dict(color="white", size=12),
        showlegend=False,
        hovertemplate="%{x}: %{y:.2f}J<extra></extra>",
    ), row=1, col=2)

    # ── (2,1) 에너지 변화 곡선 ──
    fig.add_trace(go.Scatter(
        x=x, y=pe,
        mode="lines", name="위치에너지",
        line=dict(color="#4ecdc4", width=2.5),
        fill="tozeroy", fillcolor="rgba(78,205,196,0.15)",
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=x, y=ke,
        mode="lines", name="운동에너지",
        line=dict(color="#ff6b6b", width=2.5),
        fill="tozeroy", fillcolor="rgba(255,107,107,0.15)",
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=x, y=te,
        mode="lines", name="역학적에너지",
        line=dict(color="#ffd93d", width=2, dash="dash"),
    ), row=2, col=1)

    # 현재 위치 수직선
    fig.add_vline(
        x=car_x, line_dash="dot",
        line_color="white", line_width=1.5,
        row=2, col=1,
    )

    # ── (2,2) 속도 곡선 ──
    fig.add_trace(go.Scatter(
        x=x, y=v,
        mode="lines", name="속도",
        line=dict(color="#a29bfe", width=2.5),
        fill="tozeroy", fillcolor="rgba(162,155,254,0.2)",
        showlegend=False,
        hovertemplate="x=%{x:.1f}m<br>속도=%{y:.2f}m/s<extra></extra>",
    ), row=2, col=2)

    fig.add_vline(
        x=car_x, line_dash="dot",
        line_color="white", line_width=1.5,
        row=2, col=2,
    )

    # ── 레이아웃 공통 설정 ──
    fig.update_layout(
        height=680,
        paper_bgcolor="rgba(15,12,41,0.95)",
        plot_bgcolor="rgba(255,255,255,0.04)",
        font=dict(color="#e0e8ff", size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.08,
            xanchor="center", x=0.25,
            bgcolor="rgba(0,0,0,0.4)",
            bordercolor="rgba(255,255,255,0.2)",
            borderwidth=1,
        ),
        margin=dict(t=50, b=30, l=40, r=20),
    )

    # 축 스타일 공통 함수
    axis_style = dict(
        gridcolor="rgba(255,255,255,0.08)",
        zerolinecolor="rgba(255,255,255,0.2)",
        tickfont=dict(color="#a0aec0"),
    )
    fig.update_xaxes(**axis_style)
    fig.update_yaxes(**axis_style)

    # 개별 축 레이블
    fig.update_xaxes(title_text="위치 (m)", row=1, col=1)
    fig.update_yaxes(title_text="높이 (m)", row=1, col=1)
    fig.update_yaxes(title_text="에너지 (J)", row=1, col=2)
    fig.update_xaxes(title_text="위치 (m)", row=2, col=1)
    fig.update_yaxes(title_text="에너지 (J)", row=2, col=1)
    fig.update_xaxes(title_text="위치 (m)", row=2, col=2)
    fig.update_yaxes(title_text="속도 (m/s)", row=2, col=2)

    # 막대 y축 범위 여유
    fig.update_yaxes(range=[0, cur_te * 1.3 + 10], row=1, col=2)

    return fig, {
        "height": round(car_y, 2),
        "speed":  round(cur_v, 2),
        "pe":     round(cur_pe, 1),
        "ke":     round(cur_ke, 1),
        "te":     round(cur_te, 1),
        "pos_pct": round(car_pos_pct, 1),
    }


# ── 세션 초기화 ───────────────────────────────────────────────
def init_session():
    defaults = {
        "messages":    [],
        "api_key":     "",
        "mass":        50.0,
        "car_pos":     0.0,
        "heights":     [20.0, 15.0, 25.0, 5.0, 18.0, 3.0],
        "track_preset":"기본 트랙",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ── 사이드바 ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔑 API 설정")
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=st.session_state["api_key"],
        placeholder="sk-ant-...",
        help="Anthropic Console에서 발급받은 키를 입력하세요.",
    )
    if api_key:
        st.session_state["api_key"] = api_key
        st.success("✅ API 키 등록됨", icon="🔓")
    else:
        st.warning("API 키를 입력해주세요.", icon="⚠️")

    st.divider()
    st.markdown("## 🎢 시뮬레이션 설정")

    # 프리셋 트랙
    preset = st.selectbox(
        "트랙 프리셋",
        ["기본 트랙", "빅 드롭", "파도 트랙", "완만한 트랙", "직접 설정"],
        index=0,
    )
    preset_map = {
        "기본 트랙":   [20.0, 15.0, 25.0, 5.0, 18.0, 3.0],
        "빅 드롭":     [40.0, 38.0, 2.0,  8.0, 15.0, 2.0],
        "파도 트랙":   [15.0, 5.0,  20.0, 5.0, 15.0, 5.0],
        "완만한 트랙": [10.0, 8.0,  12.0, 6.0, 9.0,  3.0],
        "직접 설정":   st.session_state["heights"],
    }
    if preset != "직접 설정":
        st.session_state["heights"] = preset_map[preset]

    # 직접 높이 조정
    if preset == "직접 설정":
        st.markdown("**각 지점 높이 (m)**")
        new_heights = []
        cols_h = st.columns(2)
        labels = ["출발", "지점2", "정상", "지점4", "지점5", "도착"]
        for i, label in enumerate(labels):
            with cols_h[i % 2]:
                h = st.number_input(
                    label, min_value=1.0, max_value=60.0,
                    value=float(st.session_state["heights"][i]),
                    step=1.0, key=f"h_{i}",
                )
                new_heights.append(h)
        st.session_state["heights"] = new_heights

    # 질량 설정
    st.session_state["mass"] = st.slider(
        "🏋️ 카트 질량 (kg)", 10, 200,
        int(st.session_state["mass"]), 5,
    )

    # 카트 위치
    st.session_state["car_pos"] = st.slider(
        "📍 카트 위치 (%)", 0.0, 100.0,
        float(st.session_state["car_pos"]), 0.5,
    )

    st.divider()

    # 에너지 공식 참조
    st.markdown("## 📚 공식 참조")
    st.markdown("""
<div class="info-card">
  <b>위치에너지</b><br>
  <span class="energy-badge pe-badge">PE = mgh</span><br><br>
  <b>운동에너지</b><br>
  <span class="energy-badge ke-badge">KE = ½mv²</span><br><br>
  <b>에너지 보존</b><br>
  <span class="energy-badge tot-badge">PE + KE = 일정</span>
</div>
""", unsafe_allow_html=True)

    st.divider()
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

# ── 메인 화면 ─────────────────────────────────────────────────
st.markdown('<div class="main-title">🎢 에너지 탐험 – 롤러코스터 물리</div>',
            unsafe_allow_html=True)
st.markdown('<div class="sub-title">위치에너지 ↔ 운동에너지 전환을 눈으로 확인해보세요!</div>',
            unsafe_allow_html=True)

# 탭 구성
tab_sim, tab_chat = st.tabs(["⚡ 에너지 시뮬레이션", "💬 에너지쌤과 대화"])

# ────────────── 시뮬레이션 탭 ────────────────────────────────
with tab_sim:
    fig, stats = draw_simulation(
        st.session_state["mass"],
        st.session_state["heights"],
        st.session_state["car_pos"],
    )
    st.plotly_chart(fig, use_container_width=True)

    # 현재 상태 지표
    st.markdown("### 📊 현재 카트 상태")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("🏔️ 높이",    f"{stats['height']} m")
    with c2:
        st.metric("🚀 속도",    f"{stats['speed']} m/s")
    with c3:
        st.metric("🌿 위치에너지", f"{stats['pe']} J",
                  delta=None, help="PE = mgh")
    with c4:
        st.metric("⚡ 운동에너지", f"{stats['ke']} J",
                  delta=None, help="KE = ½mv²")
    with c5:
        st.metric("🔋 역학적에너지", f"{stats['te']} J",
                  delta=None, help="PE + KE")

    # 에너지 비율 시각화
    if stats["te"] > 0:
        pe_pct = stats["pe"] / stats["te"] * 100
        ke_pct = stats["ke"] / stats["te"] * 100
        st.markdown("### ⚖️ 에너지 비율")
        st.markdown(f"""
<div style="background:rgba(255,255,255,0.05); border-radius:12px;
            overflow:hidden; height:28px; display:flex;">
  <div style="width:{pe_pct:.1f}%; background:linear-gradient(90deg,#4ecdc4,#44a08d);
              display:flex; align-items:center; justify-content:center;
              color:white; font-size:12px; font-weight:bold; min-width:40px;">
    PE {pe_pct:.0f}%
  </div>
  <div style="width:{ke_pct:.1f}%; background:linear-gradient(90deg,#ff6b6b,#ee0979);
              display:flex; align-items:center; justify-content:center;
              color:white; font-size:12px; font-weight:bold; min-width:40px;">
    KE {ke_pct:.0f}%
  </div>
</div>
""", unsafe_allow_html=True)

    st.info(
        "💡 **사이드바**에서 카트 위치 슬라이더를 움직여 에너지 전환을 실시간으로 확인하세요! "
        "트랙 프리셋도 바꿔보세요.",
        icon="🎯",
    )

# ────────────── 챗봇 탭 ──────────────────────────────────────
with tab_chat:
    st.markdown("### 💬 에너지쌤과 대화하기")

    # 빠른 질문 버튼
    st.markdown("**💡 빠른 질문:**")
    q_cols = st.columns(4)
    quick_qs = [
        "위치에너지란 무엇인가요?",
        "운동에너지 공식 알려줘",
        "에너지 보존 법칙이 뭐예요?",
        "롤러코스터 가장 빠른 지점은?",
    ]
    for i, q in enumerate(quick_qs):
        with q_cols[i]:
            if st.button(q, key=f"qbtn_{i}", use_container_width=True):
                st.session_state["messages"].append(
                    {"role": "user", "content": q}
                )
                st.rerun()

    st.divider()

    # 대화 기록 출력
    chat_container = st.container()
    with chat_container:
        if not st.session_state["messages"]:
            st.markdown("""
<div class="ai-bubble">
안녕하세요! 저는 <b>에너지쌤</b>이에요 🎢<br>
롤러코스터로 배우는 물리, 정말 재미있죠?<br><br>
위치에너지와 운동에너지에 대해 궁금한 것이 있으면 뭐든 물어보세요!<br>
왼쪽 시뮬레이션 탭에서 카트를 움직이며 에너지 변화도 직접 확인해보세요 ⚡
</div>
""", unsafe_allow_html=True)
        else:
            for msg in st.session_state["messages"]:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div class="user-bubble">🧑‍🎓 {msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    safe_content = msg["content"].replace("\n", "<br>")
                    st.markdown(
                        f'<div class="ai-bubble">👨‍🏫 {safe_content}</div>',
                        unsafe_allow_html=True,
                    )

    # 입력창
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "질문을 입력하세요",
            placeholder="예) 높이가 2배가 되면 위치에너지는 몇 배가 되나요?",
            height=80,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("📨 전송", use_container_width=True)

    # API 호출 & 응답
    if submitted and user_input.strip():
        if not st.session_state["api_key"]:
            st.error("❌ 사이드바에서 API 키를 먼저 입력해주세요!")
        else:
            # 시뮬레이션 컨텍스트를 질문에 자동 첨부
            _, cur_stats = draw_simulation(
                st.session_state["mass"],
                st.session_state["heights"],
                st.session_state["car_pos"],
            )
            context = (
                f"\n\n[현재 시뮬레이션 상태: 질량={st.session_state['mass']}kg, "
                f"높이={cur_stats['height']}m, 속도={cur_stats['speed']}m/s, "
                f"PE={cur_stats['pe']}J, KE={cur_stats['ke']}J, "
                f"TE={cur_stats['te']}J]"
            )
            full_input = user_input.strip() + context

            st.session_state["messages"].append(
                {"role": "user", "content": user_input.strip()}
            )

            # 스트리밍 응답
            with st.spinner("에너지쌤이 답변을 작성 중이에요... ✏️"):
                try:
                    client = anthropic.Anthropic(
                        api_key=st.session_state["api_key"]
                    )
                    api_messages = []
                    for m in st.session_state["messages"][:-1]:
                        api_messages.append(
                            {"role": m["role"], "content": m["content"]}
                        )
                    api_messages.append(
                        {"role": "user", "content": full_input}
                    )

                    full_response = ""
                    with client.messages.stream(
                        model="claude-sonnet-4-5",
                        max_tokens=1024,
                        system=SYSTEM_PROMPT,
                        messages=api_messages,
                    ) as stream:
                        for text in stream.text_stream:
                            full_response += text

                    st.session_state["messages"].append(
                        {"role": "assistant", "content": full_response}
                    )
                    st.rerun()

                except anthropic.AuthenticationError:
                    st.error("❌ API 키가 올바르지 않습니다. 다시 확인해주세요.")
                except anthropic.RateLimitError:
                    st.error("⏳ 요청이 너무 많습니다. 잠시 후 다시 시도해주세요.")
                except Exception as e:
                    st.error(f"오류 발생: {e}")

# ── 푸터 ──────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center; color:#718096; font-size:13px; padding:10px 0;">
  🎢 롤러코스터 에너지 탐험 | 중학교 물리 학습 도우미<br>
  <span style="color:#4a5568;">Powered by Claude claude-sonnet-4-5 & Streamlit</span>
</div>
""", unsafe_allow_html=True)