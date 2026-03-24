import streamlit as st
import anthropic

# ── 페이지 기본 설정 ──────────────────────────────────────────────────
st.set_page_config(
    page_title="롤러코스터 물리 선생님 🎢",
    page_icon="🎢",
    layout="centered",
)

# ── CSS 스타일 ────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: #ffffff;
    }

    /* 헤더 카드 */
    .header-card {
        background: linear-gradient(90deg, #f7971e, #ffd200);
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(247,151,30,0.35);
    }
    .header-card h1 {
        color: #1a1a2e;
        margin: 0;
        font-size: 1.9rem;
    }
    .header-card p {
        color: #2d2d2d;
        margin: 4px 0 0 0;
        font-size: 0.95rem;
    }

    /* 정보 박스 */
    .info-box {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,210,0,0.35);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 18px;
        font-size: 0.88rem;
        line-height: 1.7;
    }
    .info-box b { color: #ffd200; }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background: rgba(15,12,41,0.95);
        border-right: 1px solid rgba(255,210,0,0.2);
    }

    /* 채팅 메시지 공통 */
    .chat-message {
        padding: 14px 18px;
        border-radius: 14px;
        margin: 10px 0;
        line-height: 1.7;
        font-size: 0.95rem;
        max-width: 88%;
    }

    /* 사용자 메시지 */
    .user-message {
        background: linear-gradient(135deg, #667eea, #764ba2);
        margin-left: auto;
        border-bottom-right-radius: 4px;
        box-shadow: 0 4px 15px rgba(102,126,234,0.4);
    }

    /* 어시스턴트 메시지 */
    .assistant-message {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,210,0,0.25);
        border-bottom-left-radius: 4px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    /* 메시지 레이블 */
    .msg-label {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
        opacity: 0.85;
    }
    .user-label { color: #e0d7ff; }
    .assistant-label { color: #ffd200; }

    /* 롤러코스터 에너지 바 */
    .energy-bar-container {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 14px 18px;
        margin: 10px 0;
        border: 1px solid rgba(255,210,0,0.2);
    }
    .energy-label {
        font-size: 0.8rem;
        margin-bottom: 6px;
        color: #ccc;
    }
    .bar-wrap {
        height: 14px;
        background: rgba(255,255,255,0.08);
        border-radius: 99px;
        overflow: hidden;
        margin-bottom: 8px;
    }
    .bar-pe {
        height: 100%;
        border-radius: 99px;
        background: linear-gradient(90deg, #f7971e, #ffd200);
        transition: width 0.5s ease;
    }
    .bar-ke {
        height: 100%;
        border-radius: 99px;
        background: linear-gradient(90deg, #56ccf2, #2f80ed);
        transition: width 0.5s ease;
    }

    /* 입력창 래퍼 */
    .stChatInput textarea {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,210,0,0.4) !important;
        color: #fff !important;
        border-radius: 12px !important;
    }

    /* 버튼 */
    .stButton > button {
        background: linear-gradient(90deg, #f7971e, #ffd200);
        color: #1a1a2e;
        font-weight: 700;
        border: none;
        border-radius: 10px;
        padding: 8px 20px;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.85; }
</style>
""", unsafe_allow_html=True)

# ── 시스템 프롬프트 ───────────────────────────────────────────────────
SYSTEM_PROMPT = """
당신은 대한민국 중학교 물리 선생님입니다. 이름은 '에너지 선생님'이고, 학생들이 어렵게 느끼는 
물리 개념을 쉽고 재미있게 설명하는 것이 특기입니다.

【전문 분야】
- 위치에너지(퍼텐셜 에너지)와 운동에너지의 개념 및 공식
- 롤러코스터를 활용한 역학적 에너지 보존 법칙 설명
- 에너지 전환 과정의 시각적·직관적 설명

【설명 원칙】
1. 롤러코스터를 주된 비유 도구로 사용합니다.
   - 높은 곳(꼭대기) = 위치에너지 최대, 운동에너지 최소(속도 ≈ 0)
   - 낮은 곳(바닥) = 운동에너지 최대, 위치에너지 최소
   - 중간 지점 = 두 에너지가 나뉘어 공존
2. 중학교 수준에 맞는 언어를 씁니다 (지나친 수식 자제, 꼭 필요하면 설명과 함께).
3. 공식은 필요할 때만, 이해를 돕는 방향으로 제시합니다.
   - 위치에너지: Ep = mgh  (m=질량, g=9.8 m/s², h=높이)
   - 운동에너지: Ek = ½mv²  (v=속도)
   - 역학적 에너지 보존: Ep + Ek = 일정
4. 구체적인 숫자 예시를 자주 활용합니다.
5. 학생이 틀린 개념을 말하면, 부드럽게 바로잡아 줍니다.
6. 답변 끝에 관련 퀴즈나 생각해볼 질문을 1개씩 던져 학습 참여를 유도합니다.
7. 이모지를 적절히 사용하여 친근한 분위기를 만듭니다.
8. 한국어로만 답변합니다.

【금지 사항】
- 물리와 무관한 주제에는 "저는 물리 에너지 전환 전문 선생님이라 그 질문은 도움드리기 어렵네요 😊 
  에너지나 롤러코스터 관련 질문을 해 주세요!" 라고 안내합니다.
- 욕설, 비하 표현 사용 금지.
"""

# ── 롤러코스터 위치별 에너지 비율 ─────────────────────────────────────
POSITIONS = {
    "🏔️ 꼭대기 (출발)": (100, 0),
    "🔽 내리막 중간": (65, 35),
    "⬇️ 바닥 (최저점)": (5, 95),
    "📈 오르막 중간": (55, 45),
    "🏁 두 번째 봉우리": (80, 20),
}

# ── 세션 상태 초기화 ─────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key" in st.session_state and st.session_state.api_key:
    pass

# ── 사이드바 ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 설정")

    api_key = st.text_input(
        "🔑 Anthropic API 키",
        type="password",
        placeholder="sk-ant-...",
        help="Anthropic Console에서 발급받은 API 키를 입력하세요.",
        key="api_key_input"
    )

    st.markdown("---")

    # 롤러코스터 에너지 시각화
    st.markdown("### 🎢 롤러코스터 에너지 뷰어")
    st.markdown("<div style='font-size:0.8rem;color:#aaa;margin-bottom:8px;'>위치를 선택하면 에너지 비율을 확인할 수 있어요!</div>", unsafe_allow_html=True)

    selected_pos = st.selectbox("위치 선택", list(POSITIONS.keys()))
    pe_ratio, ke_ratio = POSITIONS[selected_pos]

    st.markdown(f"""
    <div class="energy-bar-container">
        <div class="energy-label">🟡 위치에너지 (Ep) — {pe_ratio}%</div>
        <div class="bar-wrap"><div class="bar-pe" style="width:{pe_ratio}%"></div></div>
        <div class="energy-label">🔵 운동에너지 (Ek) — {ke_ratio}%</div>
        <div class="bar-wrap"><div class="bar-ke" style="width:{ke_ratio}%"></div></div>
        <div style="font-size:0.78rem;color:#ffd200;margin-top:8px;">
            ⚖️ Ep + Ek = 역학적 에너지 보존!
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 빠른 질문 버튼
    st.markdown("### 💡 추천 질문")
    quick_questions = [
        "위치에너지가 뭐예요?",
        "운동에너지 공식 알려주세요",
        "롤러코스터 바닥에서 왜 빠른가요?",
        "역학적 에너지 보존이란?",
        "마찰이 있으면 어떻게 되나요?",
    ]

    for q in quick_questions:
        if st.button(q, key=f"quick_{q}", use_container_width=True):
            st.session_state["quick_input"] = q

    st.markdown("---")

    # 대화 초기화
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("""
    <div style='font-size:0.78rem;color:#888;margin-top:10px;line-height:1.6;'>
        📌 Model: claude-sonnet-4-6<br>
        🏫 중학교 물리 에너지 전환 챗봇<br>
        🎢 롤러코스터로 배우는 물리!
    </div>
    """, unsafe_allow_html=True)

# ── 메인 영역 ─────────────────────────────────────────────────────────

# 헤더
st.markdown("""
<div class="header-card">
    <h1>🎢 롤러코스터 물리 선생님</h1>
    <p>위치에너지 ↔ 운동에너지 전환을 롤러코스터로 쉽게 배워요! | 중학교 물리</p>
</div>
""", unsafe_allow_html=True)

# API 키 미입력 안내
if not api_key:
    st.markdown("""
    <div class="info-box">
        👋 안녕하세요! <b>롤러코스터 물리 선생님</b>입니다.<br><br>
        ▶ <b>왼쪽 사이드바</b>에 <b>Anthropic API 키</b>를 입력하면 대화를 시작할 수 있어요!<br>
        ▶ API 키는 <a href="https://console.anthropic.com" target="_blank" style="color:#ffd200;">console.anthropic.com</a>에서 발급받을 수 있습니다.<br>
        ▶ 사이드바의 <b>에너지 뷰어</b>로 롤러코스터 각 위치의 에너지를 미리 확인해보세요! 🎢
    </div>
    """, unsafe_allow_html=True)

    # 미리보기 예시 카드
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="info-box" style="text-align:center;">
            <div style="font-size:2rem;">🏔️</div>
            <b>꼭대기</b><br>
            <span style="color:#ffd200;">위치에너지 최대</span><br>
            운동에너지 최소<br>
            <small>(속도 ≈ 0)</small>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="info-box" style="text-align:center;">
            <div style="font-size:2rem;">🔄</div>
            <b>중간 지점</b><br>
            <span style="color:#ffd200;">위치에너지 ↕</span><br>
            운동에너지 ↕<br>
            <small>(서로 전환 중)</small>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="info-box" style="text-align:center;">
            <div style="font-size:2rem;">⚡</div>
            <b>바닥(최저점)</b><br>
            <span style="color:#56ccf2;">운동에너지 최대</span><br>
            위치에너지 최소<br>
            <small>(속도 최대)</small>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ── 채팅 기록 출력 ────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <div class="msg-label user-label">🙋 학생</div>
            {msg["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <div class="msg-label assistant-label">🎢 에너지 선생님</div>
            {msg["content"]}
        </div>
        """, unsafe_allow_html=True)

# ── 빠른 질문 처리 ────────────────────────────────────────────────────
quick_input = st.session_state.pop("quick_input", None)

# ── 사용자 입력 ───────────────────────────────────────────────────────
user_input = st.chat_input("궁금한 점을 질문해 보세요! (예: 롤러코스터 꼭대기에서 왜 느린가요?)")

# 빠른 질문 우선 처리
if quick_input:
    user_input = quick_input

# ── API 호출 및 응답 ──────────────────────────────────────────────────
if user_input:
    # 사용자 메시지 저장 및 표시
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.markdown(f"""
    <div class="chat-message user-message">
        <div class="msg-label user-label">🙋 학생</div>
        {user_input}
    </div>
    """, unsafe_allow_html=True)

    # 응답 생성
    with st.spinner("선생님이 설명을 준비하고 있어요... 🎢"):
        try:
            client = anthropic.Anthropic(api_key=api_key)

            # 메시지 리스트 구성 (system은 별도 파라미터)
            api_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]

            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=api_messages,
            )

            assistant_reply = response.content[0].text

            # 응답 저장 및 표시
            st.session_state.messages.append(
                {"role": "assistant", "content": assistant_reply}
            )
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <div class="msg-label assistant-label">🎢 에너지 선생님</div>
                {assistant_reply}
            </div>
            """, unsafe_allow_html=True)

        except anthropic.AuthenticationError:
            st.error("❌ API 키가 올바르지 않습니다. 사이드바에서 키를 다시 확인해 주세요.")
        except anthropic.RateLimitError:
            st.error("⏳ 요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.")
        except anthropic.APIError as e:
            st.error(f"🚨 API 오류가 발생했습니다: {str(e)}")
        except Exception as e:
            st.error(f"🚨 오류가 발생했습니다: {str(e)}")

# ── 하단 안내 ─────────────────────────────────────────────────────────
if st.session_state.messages:
    st.markdown("""
    <div style="text-align:center;font-size:0.78rem;color:#666;margin-top:20px;">
        🎢 롤러코스터 물리 선생님 | 역학적 에너지 보존 법칙 Ep + Ek = 일정
    </div>
    """, unsafe_allow_html=True)