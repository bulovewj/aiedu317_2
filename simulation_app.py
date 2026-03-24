import streamlit as st
import anthropic
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

st.set_page_config(
    page_title="롤러코스터 에너지 탐험 🎢",
    page_icon="🎢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); }
  [data-testid="stSidebar"] {
      background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
      border-right: 2px solid #e94560;
  }
  .user-bubble {
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white; padding: 12px 18px;
      border-radius: 18px 18px 4px 18px;
      margin: 8px 0 8px 20%;
      box-shadow: 0 4px 15px rgba(102,126,234,0.4);
      font-size: 15px; line-height: 1.6;
  }
  .ai-bubble {
      background: linear-gradient(135deg, #1e3c72, #2a5298);
      color: #e0e8ff; padding: 12px 18px;
      border-radius: 18px 18px 18px 4px;
      margin: 8px 20% 8px 0;
      box-shadow: 0 4px 15px rgba(30,60,114,0.5);
      font-size: 15px; line-height: 1.8;
      border-left: 3px solid #4fc3f7;
  }
  .stat-card {
      background: rgba(255,255,255,0.06);
      border-radius: 12px; padding: 14px 10px;
      text-align: center;
      border: 1px solid rgba(255,255,255,0.1);
  }
  .stat-value { font-size: 1.5em; font-weight: 800; line-height: 1.2; }
  .stat-label { font-size: 0.75em; color: #a0aec0; margin-top: 4px; }
  .energy-bar-wrap {
      background: rgba(255,255,255,0.07);
      border-radius: 10px; overflow: hidden;
      height: 26px; display: flex; margin: 4px 0;
  }
  .pe-fill {
      background: linear-gradient(90deg,#4ecdc4,#44a08d);
      display:flex; align-items:center; justify-content:center;
      color:white; font-size:11px; font-weight:bold; min-width:0;
  }
  .ke-fill {
      background: linear-gradient(90deg,#f7971e,#ff6b6b);
      display:flex; align-items:center; justify-content:center;
      color:white; font-size:11px; font-weight:bold; min-width:0;
  }
  .status-running {
      background: linear-gradient(90deg,#11998e,#38ef7d);
      color:white; padding:6px 16px; border-radius:20px;
      font-size:13px; font-weight:bold; display:inline-block;
  }
  .status-stopped {
      background: linear-gradient(90deg,#636e72,#b2bec3);
      color:white; padding:6px 16px; border-radius:20px;
      font-size:13px; font-weight:bold; display:inline-block;
  }
  .status-finished {
      background: linear-gradient(90deg,#f7971e,#ffd200);
      color:#333; padding:6px 16px; border-radius:20px;
      font-size:13px; font-weight:bold; display:inline-block;
  }
  .info-card {
      background:rgba(255,255,255,0.05);
      border:1px solid rgba(255,255,255,0.1);
      border-radius:12px; padding:14px; margin:6px 0;
  }
  .energy-badge {
      display:inline-block; padding:3px 10px;
      border-radius:20px; font-size:12px; font-weight:bold; margin:2px;
  }
  .ke-badge  { background:#ff6b6b; color:white; }
  .pe-badge  { background:#4ecdc4; color:white; }
  .tot-badge { background:#ffd93d; color:#333; }
  .main-title {
      text-align:center; font-size:2.2em; font-weight:800;
      background:linear-gradient(90deg,#f093fb,#f5576c,#4facfe);
      -webkit-background-clip:text; -webkit-text-fill-color:transparent;
      margin-bottom:2px;
  }
  .sub-title {
      text-align:center; color:#a0aec0;
      font-size:0.95em; margin-bottom:16px;
  }
  .hint-box { border-radius:8px; padding:12px 16px; margin-top:8px; }
  label { color:#a0c4ff !important; }
  h1,h2,h3 { color:#f0f4ff; }
  .stMarkdown p { color:#e0e8ff; }
</style>
""", unsafe_allow_html=True)

# ── 상수 ──────────────────────────────────────────────────────
G            = 9.8
TOTAL_FRAMES = 300

SYSTEM_PROMPT = """당신은 친절하고 열정적인 중학교 물리 선생님입니다.
이름은 '에너지쌤'이며, 특히 역학적 에너지(위치에너지, 운동에너지)를
롤러코스터를 예시로 설명하는 것을 좋아합니다.

핵심 교육 철학
- 어려운 개념을 일상 속 예시로 쉽게 설명합니다.
- 수식을 쓸 때는 반드시 말로도 풀어서 설명합니다.
- 학생이 틀려도 격려하며 정답으로 유도합니다.
- 이모지를 적절히 사용해 친근한 분위기를 만듭니다.

주요 물리 개념
- 위치에너지(PE) = mgh
- 운동에너지(KE) = 1/2 mv²
- 역학적 에너지 보존 법칙: PE + KE = 일정 (마찰 무시 시)
- 롤러코스터: 높은 곳(PE↑, KE↓) → 낮은 곳(PE↓, KE↑)

답변 스타일
- 중학생 수준에 맞는 쉬운 언어를 사용합니다.
- 계산 문제는 단계별로 풀어줍니다.
- 답변 끝에 관련 질문을 하나씩 던져 호기심을 자극합니다.
"""


# ── 캐시된 계산 함수 ──────────────────────────────────────────
@st.cache_data
def make_track(heights_tuple, n_points=TOTAL_FRAMES):
    heights = list(heights_tuple)
    n_ctrl  = len(heights)
    x_ctrl  = np.linspace(0, 100, n_ctrl)
    x_fine  = np.linspace(0, 100, n_points)
    deg     = min(n_ctrl - 1, 5)
    coeffs  = np.polyfit(x_ctrl, heights, deg)
    y_fine  = np.polyval(coeffs, x_fine)
    y_fine  = np.clip(y_fine, 0.5, None)
    return x_fine, y_fine


@st.cache_data
def compute_energies(mass, heights_tuple):
    _, y = make_track(heights_tuple)
    h0   = y[0]
    pe   = mass * G * y
    te   = mass * G * h0
    ke   = np.clip(te - pe, 0, None)
    v    = np.sqrt(2 * ke / mass)
    return pe, ke, np.full_like(pe, te), v, y


# ── 그래프 생성 ───────────────────────────────────────────────
def build_figure(mass, heights, frame_idx):
    h_tuple          = tuple(heights)
    x, y             = make_track(h_tuple)
    pe, ke, te, v, _ = compute_energies(mass, h_tuple)

    idx    = int(np.clip(frame_idx, 0, TOTAL_FRAMES - 1))
    car_x  = float(x[idx])
    car_y  = float(y[idx])
    cur_pe = float(pe[idx])
    cur_ke = float(ke[idx])
    cur_te = float(te[idx])
    cur_v  = float(v[idx])

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "🎢 롤러코스터 트랙",
            "⚡ 에너지 막대 그래프",
            "📈 위치별 에너지 변화",
            "🚀 위치별 속도 변화",
        ),
        row_heights=[0.55, 0.45],
        column_widths=[0.62, 0.38],
        vertical_spacing=0.13,
        horizontal_spacing=0.10,
    )

    # (1,1) 트랙
    fig.add_trace(go.Scatter(
        x=np.append(x, [x[-1], x[0]]),
        y=np.append(y, [0, 0]),
        fill="toself",
        fillcolor="rgba(80,60,40,0.25)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False, hoverinfo="skip",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines",
        line=dict(color="#4fc3f7", width=5),
        showlegend=False, hoverinfo="skip",
    ), row=1, col=1)

    if idx > 1:
        fig.add_trace(go.Scatter(
            x=x[:idx+1], y=y[:idx+1], mode="lines",
            line=dict(color="rgba(255,255,255,0.30)", width=7),
            showlegend=False, hoverinfo="skip",
        ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=[car_x, car_x], y=[0, car_y], mode="lines",
        line=dict(color="rgba(255,217,61,0.55)", width=1.5, dash="dot"),
        showlegend=False, hoverinfo="skip",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=[car_x], y=[car_y + 1.2],
        mode="markers+text",
        marker=dict(
            size=26, color="#ff6b6b", symbol="square",
            line=dict(color="white", width=2.5),
        ),
        text=["🎠"], textfont=dict(size=20),
        textposition="middle center",
        name="카트",
        hovertemplate=(
            "높이: " + str(round(car_y,2)) + " m<br>"
            "속도: " + str(round(cur_v,2)) + " m/s<br>"
            "PE: "  + str(round(cur_pe,1)) + " J<br>"
            "KE: "  + str(round(cur_ke,1)) + " J<extra></extra>"
        ),
    ), row=1, col=1)

    if cur_v > 0.5 and idx < TOTAL_FRAMES - 6:
        look = min(idx + 7, TOTAL_FRAMES - 1)
        dx   = float(x[look] - x[idx])
        dya  = float(y[look] - y[idx])
        nm   = np.sqrt(dx**2 + dya**2) + 1e-9
        sc   = min(cur_v * 0.5, 7.0)
        fig.add_annotation(
            x=car_x + dx/nm*sc,
            y=car_y + dya/nm*sc + 1.2,
            ax=car_x, ay=car_y + 1.2,
            xref="x", yref="y", axref="x", ayref="y",
            arrowhead=3, arrowsize=1.2,
            arrowwidth=2.5, arrowcolor="#ffd93d",
            row=1, col=1,
        )

    fig.add_annotation(
        x=car_x, y=car_y / 2,
        text="h=" + str(round(car_y,1)) + "m",
        font=dict(color="#ffd93d", size=11),
        showarrow=False, xshift=22, row=1, col=1,
    )
    fig.add_annotation(
        x=car_x, y=car_y + 3.8,
        text="v=" + str(round(cur_v,1)) + "m/s",
        font=dict(color="#ff9f9f", size=11, family="monospace"),
        showarrow=False, row=1, col=1,
    )

    # (1,2) 에너지 막대
    fig.add_trace(go.Bar(
        x=["위치에너지\n(PE)", "운동에너지\n(KE)", "역학적에너지\n(TE)"],
        y=[cur_pe, cur_ke, cur_te],
        marker=dict(
            color=["#4ecdc4", "#ff6b6b", "#ffd93d"],
            line=dict(color="rgba(255,255,255,0.3)", width=1.5),
        ),
        text=[
            str(round(cur_pe,0))+"J",
            str(round(cur_ke,0))+"J",
            str(round(cur_te,0))+"J",
        ],
        textposition="outside",
        textfont=dict(color="white", size=13, family="monospace"),
        showlegend=False, width=0.55,
        hovertemplate="%{x}: %{y:.1f}J<extra></extra>",
    ), row=1, col=2)

    # (2,1) 에너지 변화 곡선
    fig.add_trace(go.Scatter(
        x=x, y=te, mode="lines", name="역학적에너지 (TE)",
        line=dict(color="#ffd93d", width=2, dash="dash"),
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=x, y=pe, mode="lines", name="위치에너지 (PE)",
        line=dict(color="#4ecdc4", width=2.5),
        fill="tozeroy", fillcolor="rgba(78,205,196,0.12)",
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=x, y=ke, mode="lines", name="운동에너지 (KE)",
        line=dict(color="#ff6b6b", width=2.5),
        fill="tozeroy", fillcolor="rgba(255,107,107,0.12)",
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=[car_x, car_x, car_x],
        y=[cur_pe, cur_ke, cur_te],
        mode="markers",
        marker=dict(
            size=[13, 13, 11],
            color=["#4ecdc4", "#ff6b6b", "#ffd93d"],
            symbol=["circle", "circle", "diamond"],
            line=dict(color="white", width=1.5),
        ),
        showlegend=False,
        hovertemplate="현재: %{y:.1f}J<extra></extra>",
    ), row=2, col=1)
    fig.add_vline(
        x=car_x, line_dash="dot",
        line_color="rgba(255,255,255,0.45)", line_width=1.5,
        row=2, col=1,
    )

    # (2,2) 속도 곡선
    fig.add_trace(go.Scatter(
        x=x, y=v, mode="lines",
        line=dict(color="#a29bfe", width=2.5),
        fill="tozeroy", fillcolor="rgba(162,155,254,0.15)",
        showlegend=False, name="속도",
        hovertemplate="위치=%{x:.1f}m<br>속도=%{y:.2f}m/s<extra></extra>",
    ), row=2, col=2)
    fig.add_trace(go.Scatter(
        x=[car_x], y=[cur_v], mode="markers",
        marker=dict(
            size=14, color="#ffd93d",
            line=dict(color="white", width=2),
        ),
        showlegend=False,
    ), row=2, col=2)
    fig.add_vline(
        x=car_x, line_dash="dot",
        line_color="rgba(255,255,255,0.45)", line_width=1.5,
        row=2, col=2,
    )

    max_v_idx = int(np.argmax(v))
    fig.add_annotation(
        x=float(x[max_v_idx]), y=float(v[max_v_idx]),
        text="최대 " + str(round(float(v[max_v_idx]),1)) + "m/s",
        font=dict(color="#ffd93d", size=10),
        showarrow=True, arrowhead=2,
        arrowcolor="#ffd93d", arrowsize=0.8,
        ax=0, ay=-26, row=2, col=2,
    )

    fig.update_layout(
        height=700,
        paper_bgcolor="rgba(15,12,41,0.97)",
        plot_bgcolor="rgba(255,255,255,0.03)",
        font=dict(color="#e0e8ff", size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.07,
            xanchor="center", x=0.25,
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="rgba(255,255,255,0.15)",
            borderwidth=1, font=dict(size=11),
        ),
        margin=dict(t=55, b=20, l=45, r=20),
        bargap=0.35,
        uirevision="rollercoaster_fixed",
    )

    axis_kw = dict(
        gridcolor="rgba(255,255,255,0.07)",
        zerolinecolor="rgba(255,255,255,0.2)",
        tickfont=dict(color="#a0aec0", size=11),
    )
    fig.update_xaxes(**axis_kw)
    fig.update_yaxes(**axis_kw)
    fig.update_xaxes(title_text="위치 (m)",   row=1, col=1)
    fig.update_yaxes(title_text="높이 (m)",   row=1, col=1)
    fig.update_yaxes(title_text="에너지 (J)", row=1, col=2,
                     range=[0, cur_te * 1.4 + 5])
    fig.update_xaxes(title_text="위치 (m)",   row=2, col=1)
    fig.update_yaxes(title_text="에너지 (J)", row=2, col=1)
    fig.update_xaxes(title_text="위치 (m)",   row=2, col=2)
    fig.update_yaxes(title_text="속도 (m/s)", row=2, col=2)

    for ann in fig.layout.annotations:
        if ann.text:
            ann.font = dict(color="#c5cfe8", size=13)

    stats = dict(
        height=round(car_y, 2),
        speed =round(cur_v, 2),
        pe    =round(cur_pe, 1),
        ke    =round(cur_ke, 1),
        te    =round(cur_te, 1),
    )
    return fig, stats


# ── 세션 초기화 ───────────────────────────────────────────────
def init_session():
    defaults = {
        "messages":       [],
        "api_key":        "",
        "mass":           50.0,
        "frame":          0,
        "is_running":     False,
        "is_finished":    False,
        "anim_speed":     2,
        "heights":        [20.0, 15.0, 25.0, 5.0, 18.0, 3.0],
        "lap_count":      0,
        "max_speed_seen": 0.0,
        "quick_question": "",
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
    )
    if api_key:
        st.session_state["api_key"] = api_key
        st.success("✅ API 키 등록됨", icon="🔓")
    else:
        st.warning("API 키를 입력해주세요.", icon="⚠️")

    st.divider()
    st.markdown("## 🎢 트랙 설정")

    preset = st.selectbox(
        "트랙 프리셋",
        ["기본 트랙", "빅 드롭", "파도 트랙", "완만한 트랙", "직접 설정"],
    )
    preset_map = {
        "기본 트랙":   [20.0, 15.0, 25.0,  5.0, 18.0, 3.0],
        "빅 드롭":     [40.0, 38.0,  2.0,  8.0, 15.0, 2.0],
        "파도 트랙":   [15.0,  5.0, 20.0,  5.0, 15.0, 5.0],
        "완만한 트랙": [10.0,  8.0, 12.0,  6.0,  9.0, 3.0],
        "직접 설정":   st.session_state["heights"],
    }
    if preset != "직접 설정":
        new_h = preset_map[preset]
        if new_h != st.session_state["heights"]:
            st.session_state.update({
                "heights": new_h, "frame": 0,
                "is_running": False, "is_finished": False,
                "max_speed_seen": 0.0,
            })

    if preset == "직접 설정":
        st.markdown("**각 지점 높이 (m)**")
        new_heights = []
        cols_h = st.columns(2)
        labels_h = ["출발점", "지점2", "최고점", "지점4", "지점5", "도착점"]
        for i, lbl in enumerate(labels_h):
            with cols_h[i % 2]:
                h = st.number_input(
                    lbl, min_value=1.0, max_value=60.0,
                    value=float(st.session_state["heights"][i]),
                    step=1.0, key="h_" + str(i),
                )
                new_heights.append(h)
        st.session_state["heights"] = new_heights

    new_mass = st.slider(
        "🏋️ 카트 질량 (kg)", 10, 200,
        int(st.session_state["mass"]), 5,
    )
    if new_mass != int(st.session_state["mass"]):
        st.session_state.update({
            "mass": float(new_mass), "frame": 0,
            "is_running": False, "is_finished": False,
        })

    speed_labels = {
        1: "🐢 느리게",
        2: "🚶 보통",
        3: "🏃 빠르게",
        5: "🚀 매우 빠르게",
        8: "⚡ 초고속",
    }
    st.session_state["anim_speed"] = st.select_slider(
        "⚡ 애니메이션 속도",
        options=[1, 2, 3, 5, 8],
        value=st.session_state["anim_speed"],
        format_func=lambda x: speed_labels[x],
    )

    st.divider()
    st.markdown("## 📚 공식 참조")
    st.markdown("""
<div class="info-card">
  <b>위치에너지</b><br>
  <span class="energy-badge pe-badge">PE = mgh</span><br><br>
  <b>운동에너지</b><br>
  <span class="energy-badge ke-badge">KE = 1/2 mv²</span><br><br>
  <b>에너지 보존</b><br>
  <span class="energy-badge tot-badge">PE + KE = 일정</span>
</div>
""", unsafe_allow_html=True)

    st.divider()
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()


# ── 메인 타이틀 ───────────────────────────────────────────────
st.markdown(
    '<div class="main-title">🎢 롤러코스터 에너지 탐험</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-title">위치에너지 ↔ 운동에너지 실시간 전환 시뮬레이션</div>',
    unsafe_allow_html=True,
)

tab_sim, tab_chat = st.tabs(["⚡ 에너지 시뮬레이션", "💬 에너지쌤과 대화"])

# ════════════════════════════════════════════════════════════
#  시뮬레이션 탭
# ════════════════════════════════════════════════════════════
with tab_sim:

    # ── 플롯 (key 고정 → 깜빡임 방지) ────────────────────────
    fig, stats = build_figure(
        st.session_state["mass"],
        st.session_state["heights"],
        st.session_state["frame"],
    )
    st.plotly_chart(fig, use_container_width=True, key="main_chart")

    # ── 컨트롤 패널 ───────────────────────────────────────────
    with st.container(border=True):
        col_ctrl, col_status, col_energy = st.columns([3, 3, 4])

        with col_ctrl:
            st.markdown("#### 🎮 컨트롤")
            bc1, bc2, bc3 = st.columns(3)

            with bc1:
                if st.session_state["is_finished"]:
                    btn_label = "🔄 다시"
                elif st.session_state["is_running"]:
                    btn_label = "⏸ 정지"
                else:
                    btn_label = "▶ 출발"

                if st.button(btn_label, use_container_width=True,
                             type="primary", key="btn_start"):
                    if st.session_state["is_finished"]:
                        st.session_state.update({
                            "frame": 0,
                            "is_running": True,
                            "is_finished": False,
                            "max_speed_seen": 0.0,
                        })
                        st.session_state["lap_count"] += 1
                    else:
                        st.session_state["is_running"] = (
                            not st.session_state["is_running"]
                        )
                    st.rerun()

            with bc2:
                if st.button("⏹ 리셋", use_container_width=True,
                             key="btn_stop"):
                    st.session_state.update({
                        "is_running": False,
                        "frame": 0,
                        "is_finished": False,
                        "max_speed_seen": 0.0,
                    })
                    st.rerun()

            with bc3:
                if st.button("⏭ 끝", use_container_width=True,
                             key="btn_end"):
                    st.session_state.update({
                        "is_running": False,
                        "frame": TOTAL_FRAMES - 1,
                        "is_finished": True,
                    })
                    st.rerun()

            if not st.session_state["is_running"]:
                new_manual = st.slider(
                    "📍 수동 위치 조정",
                    0, TOTAL_FRAMES - 1,
                    st.session_state["frame"],
                    key="manual_slider",
                )
                if new_manual != st.session_state["frame"]:
                    st.session_state["frame"] = new_manual
                    st.rerun()

        with col_status:
            st.markdown("#### 📊 현재 상태")

            if st.session_state["is_running"]:
                badge_html = '<span class="status-running">🟢 주행 중</span>'
            elif st.session_state["is_finished"]:
                badge_html = '<span class="status-finished">🏁 도착!</span>'
            else:
                badge_html = '<span class="status-stopped">⚪ 정지</span>'

            st.markdown(badge_html, unsafe_allow_html=True)

            prog = st.session_state["frame"] / (TOTAL_FRAMES - 1)
            st.progress(prog)
            st.caption(
                "진행률: " + str(round(prog*100,1)) + "%  |  "
                "프레임: " + str(st.session_state["frame"]) +
                "/" + str(TOTAL_FRAMES-1) + "  |  "
                "누적 주행: " + str(st.session_state["lap_count"]) + "회"
            )

        with col_energy:
            st.markdown("#### ⚡ 에너지 실시간 비율")

            cur_te_d = stats["te"]
            cur_pe_d = stats["pe"]
            cur_ke_d = stats["ke"]

            if cur_te_d > 0:
                pe_pct = cur_pe_d / cur_te_d * 100
                ke_pct = cur_ke_d / cur_te_d * 100
            else:
                pe_pct = 0.0
                ke_pct = 0.0

            pe_label = ("PE " + str(round(pe_pct,0)) + "%") if pe_pct > 15 else ""
            ke_label = ("KE " + str(round(ke_pct,0)) + "%") if ke_pct > 15 else ""

            st.markdown(
                "🌿 **위치에너지 (PE)** — " + str(round(cur_pe_d,0)) + " J"
            )
            bar_html = (
                '<div class="energy-bar-wrap">'
                '<div class="pe-fill" style="width:' + str(round(pe_pct,1)) + '%">'
                + pe_label +
                '</div>'
                '<div class="ke-fill" style="width:' + str(round(ke_pct,1)) + '%">'
                + ke_label +
                '</div>'
                '</div>'
            )
            st.markdown(bar_html, unsafe_allow_html=True)
            st.markdown(
                "⚡ **운동에너지 (KE)** — " + str(round(cur_ke_d,0)) + " J"
            )
            st.caption(
                "역학적에너지 (TE): " + str(round(cur_te_d,0)) +
                " J  |  현재 속도: " + str(stats["speed"]) + " m/s"
            )

    # ── 수치 대시보드 ─────────────────────────────────────────
    if stats["speed"] > st.session_state["max_speed_seen"]:
        st.session_state["max_speed_seen"] = stats["speed"]

    st.markdown("### 📊 실시간 수치 대시보드")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    dash_data = [
        (m1, "🏔️ 현재 높이",    str(stats["height"]) + " m",   "#4ecdc4"),
        (m2, "🚀 현재 속도",    str(stats["speed"])  + " m/s", "#ff6b6b"),
        (m3, "🌿 위치에너지",   str(stats["pe"])     + " J",   "#4ecdc4"),
        (m4, "⚡ 운동에너지",   str(stats["ke"])     + " J",   "#f7971e"),
        (m5, "🔋 역학적에너지", str(stats["te"])     + " J",   "#ffd93d"),
        (m6, "🏆 최고 속도",
             str(round(st.session_state["max_speed_seen"], 2)) + " m/s",
             "#a29bfe"),
    ]
    for col, label, value, color in dash_data:
        with col:
            st.markdown(
                '<div class="stat-card">'
                '<div class="stat-value" style="color:' + color + ';">'
                + value +
                '</div>'
                '<div class="stat-label">' + label + '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

    # ── 물리 힌트 ─────────────────────────────────────────────
    max_h   = max(st.session_state["heights"])
    h_ratio = stats["height"] / (max_h + 1e-9)

    if h_ratio > 0.80:
        hint_msg   = "🏔️ 높은 곳! 위치에너지(PE)가 최대입니다. 속도가 느리죠? — PE↑  KE↓"
        hint_color = "#4ecdc4"
    elif h_ratio < 0.15:
        hint_msg   = "⚡ 낮은 곳! 위치에너지가 운동에너지로 전환! 속도 최대! — PE↓  KE↑"
        hint_color = "#ff6b6b"
    elif stats["ke"] > stats["pe"]:
        hint_msg   = "🚀 가속 구간! 높이가 낮아지며 운동에너지가 증가하고 있어요."
        hint_color = "#f7971e"
    else:
        hint_msg   = "⚖️ 에너지 전환 중! PE + KE = 일정 — 역학적 에너지 보존 법칙!"
        hint_color = "#a29bfe"

    st.markdown(
        '<div class="hint-box" style="background:rgba(255,255,255,0.04);'
        'border-left:4px solid ' + hint_color + ';">'
        '<span style="color:' + hint_color + '; font-size:15px;">'
        + hint_msg +
        '</span></div>',
        unsafe_allow_html=True,
    )

    # ── 애니메이션 루프 ───────────────────────────────────────
    if st.session_state["is_running"]:
        delay_map  = {1: 0.12, 2: 0.07, 3: 0.045, 5: 0.025, 8: 0.01}
        delay      = delay_map.get(st.session_state["anim_speed"], 0.07)
        next_frame = st.session_state["frame"] + st.session_state["anim_speed"]

        if next_frame >= TOTAL_FRAMES:
            st.session_state.update({
                "frame": TOTAL_FRAMES - 1,
                "is_running": False,
                "is_finished": True,
            })
        else:
            st.session_state["frame"] = next_frame

        time.sleep(delay)
        st.rerun()


# ════════════════════════════════════════════════════════════
#  챗봇 탭
# ════════════════════════════════════════════════════════════
with tab_chat:
    st.markdown("### 💬 에너지쌤과 대화하기")

    st.markdown("**💡 빠른 질문:**")
    quick_qs = [
        "위치에너지란 무엇인가요?",
        "운동에너지 공식 알려줘",
        "에너지 보존 법칙이 뭐예요?",
        "롤러코스터 가장 빠른 지점은?",
    ]
    qc = st.columns(4)
    for i, q in enumerate(quick_qs):
        with qc[i]:
            if st.button(q, key="qbtn_" + str(i), use_container_width=True):
                st.session_state["quick_question"] = q

    if st.session_state["quick_question"]:
        st.session_state["messages"].append(
            {"role": "user", "content": st.session_state["quick_question"]}
        )
        st.session_state["quick_question"] = ""

    st.divider()

    # 대화 기록
    if not st.session_state["messages"]:
        st.markdown(
            '<div class="ai-bubble">'
            "안녕하세요! 저는 <b>에너지쌤</b>이에요 🎢<br>"
            "롤러코스터로 배우는 물리, 정말 재미있죠?<br><br>"
            "<b>⚡ 에너지 시뮬레이션</b> 탭에서 <b>▶ 출발</b> 버튼을 눌러<br>"
            "롤러코스터가 달리는 동안 에너지가 어떻게 바뀌는지 확인해보세요!<br><br>"
            "궁금한 것이 있으면 뭐든 물어보세요 ⚡"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        for msg in st.session_state["messages"]:
            if msg["role"] == "user":
                st.markdown(
                    '<div class="user-bubble">🧑‍🎓 ' + msg["content"] + '</div>',
                    unsafe_allow_html=True,
                )
            else:
                content_html = msg["content"].replace("\n", "<br>")
                st.markdown(
                    '<div class="ai-bubble">👨‍🏫 ' + content_html + '</div>',
                    unsafe_allow_html=True,
                )

    # 입력 폼
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "질문 입력",
            placeholder="예) 높이가 2배가 되면 위치에너지는 몇 배가 되나요?",
            height=80,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("📨 전송", use_container_width=True)

    if submitted and user_input.strip():
        st.session_state["messages"].append(
            {"role": "user", "content": user_input.strip()}
        )
        st.rerun()

    # API 호출
    need_response = (
        len(st.session_state["messages"]) > 0
        and st.session_state["messages"][-1]["role"] == "user"
    )

    if need_response:
        if not st.session_state["api_key"]:
            st.error("❌ 사이드바에서 API 키를 먼저 입력해주세요!")
        else:
            h_tuple          = tuple(st.session_state["heights"])
            _, y_c           = make_track(h_tuple)
            pe_c, ke_c, te_c, v_c, _ = compute_energies(
                st.session_state["mass"], h_tuple
            )
            f_c = st.session_state["frame"]

            context = (
                " [현재 시뮬레이션: 질량=" +
                str(st.session_state["mass"]) + "kg, 높이=" +
                str(round(float(y_c[f_c]), 1)) + "m, 속도=" +
                str(round(float(v_c[f_c]), 2)) + "m/s, PE=" +
                str(round(float(pe_c[f_c]), 1)) + "J, KE=" +
                str(round(float(ke_c[f_c]), 1)) + "J, TE=" +
                str(round(float(te_c[f_c]), 1)) + "J]"
            )

            last_user_msg = st.session_state["messages"][-1]["content"]

            api_messages = []
            for m in st.session_state["messages"][:-1]:
                api_messages.append(
                    {"role": m["role"], "content": m["content"]}
                )
            api_messages.append(
                {"role": "user", "content": last_user_msg + context}
            )

            with st.spinner("에너지쌤이 답변을 작성 중이에요... ✏️"):
                try:
                    client = anthropic.Anthropic(
                        api_key=st.session_state["api_key"]
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
                    st.error("❌ API 키가 올바르지 않습니다.")
                except anthropic.RateLimitError:
                    st.error("⏳ 요청이 너무 많습니다. 잠시 후 다시 시도해주세요.")
                except Exception as e:
                    st.error("오류 발생: " + str(e))

# ── 푸터 ──────────────────────────────────────────────────────
st.divider()
st.caption("🎢 롤러코스터 에너지 탐험 | 중학교 물리 학습 도우미 | Powered by Claude")
