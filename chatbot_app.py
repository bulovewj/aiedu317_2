import streamlit as st
import anthropic

# ── 페이지 기본 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="6학년 수업 활동 추천 챗봇",
    page_icon="🏫",
    layout="centered",
)

# ── 시스템 프롬프트 ───────────────────────────────────────────
SYSTEM_PROMPT = """
당신은 초등학교 베테랑 6학년 담임교사입니다.
교사가 수업 주제와 내용을 알려주면, 그에 맞는 다양한 학습 활동을 추천해 주세요.

[활동 유형]
- 개별 활동: 학생 혼자서 수행하는 활동
- 짝 활동: 두 명이 함께 수행하는 활동
- 모둠 활동: 소그룹(4~6명)이 함께 수행하는 활동
- 전체 활동: 학급 전체가 함께 수행하는 활동

[답변 형식]
1. 수업 주제와 학습 목표를 한 줄로 요약합니다.
2. 위 네 가지 유형별로 각각 2~3가지 구체적인 활동을 추천합니다.
3. 각 활동마다 다음 정보를 포함하세요:
   - 활동명
   - 활동 방법 (단계별로 간략하게)
   - 예상 소요 시간
   - 기대 효과
4. 마지막에 교사를 위한 수업 운영 팁을 1~2가지 제안합니다.

항상 한국어로 답변하며, 6학년 학생의 발달 수준과 교육과정에 적합한 활동을 추천하세요.
친절하고 열정적인 베테랑 교사의 말투를 사용하세요.
"""

# ── 사이드바: API 키 입력 & 앱 소개 ─────────────────────────
with st.sidebar:
    st.title("⚙️ 설정")
    api_key = st.text_input(
        "Anthropic API 키를 입력하세요",
        type="password",
        placeholder="sk-ant-...",
        help="https://console.anthropic.com 에서 발급받을 수 있습니다.",
    )
    st.divider()

    st.markdown("### 📖 사용 방법")
    st.markdown(
        """
        1. **API 키**를 입력하세요.
        2. 채팅창에 **수업 주제와 내용**을 입력하세요.
        3. 개별·짝·모둠·전체 활동을 **추천**받으세요!
        """
    )
    st.divider()

    st.markdown("### 💡 입력 예시")
    examples = [
        "수학 | 분수의 나눗셈 개념 학습",
        "국어 | 논설문 쓰기 - 주장과 근거",
        "사회 | 조선 시대 신분 제도",
        "과학 | 식물의 광합성 원리",
        "도덕 | 공정한 생활과 책임감",
    ]
    for ex in examples:
        st.markdown(f"- {ex}")

    st.divider()
    # 대화 초기화 버튼
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("🤖 Powered by Claude claude-sonnet-4-6")

# ── 메인 화면 타이틀 ─────────────────────────────────────────
st.title("🏫 6학년 수업 활동 추천 챗봇")
st.markdown(
    "수업 **주제와 내용**을 알려주시면, "
    "**개별 / 짝 / 모둠 / 전체** 활동을 맞춤 추천해 드립니다! 😊"
)
st.divider()

# ── 세션 상태 초기화 ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── 대화 기록 출력 ───────────────────────────────────────────
for msg in st.session_state.messages:
    role = msg["role"]
    avatar = "🧑‍🏫" if role == "assistant" else "👩‍💻"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])

# ── 첫 방문 안내 메시지 ───────────────────────────────────────
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="🧑‍🏫"):
        st.markdown(
            """
            안녕하세요! 저는 초등학교 6학년 베테랑 담임교사 AI입니다. 👋

            **수업 주제와 내용**을 입력해 주시면,  
            학생들이 즐겁고 효과적으로 참여할 수 있는  
            **개별 / 짝 / 모둠 / 전체 활동**을 추천해 드릴게요!

            예) `수학 | 분수의 나눗셈 개념 학습`  
            예) `국어 | 논설문 쓰기 - 주장과 근거 찾기`

            어떤 수업을 준비 중이신가요? 😊
            """
        )

# ── 사용자 입력 처리 ─────────────────────────────────────────
user_input = st.chat_input("수업 주제와 내용을 입력하세요. 예) 과학 | 식물의 광합성 원리")

if user_input:
    # API 키 확인
    if not api_key:
        st.warning("⚠️ 사이드바에서 Anthropic API 키를 먼저 입력해 주세요.")
        st.stop()

    # 사용자 메시지 저장 및 출력
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👩‍💻"):
        st.markdown(user_input)

    # ── Claude API 호출 (스트리밍) ────────────────────────────
    with st.chat_message("assistant", avatar="🧑‍🏫"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            client = anthropic.Anthropic(api_key=api_key)

            # 대화 히스토리 구성 (system 제외, user/assistant만)
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]

            with client.messages.stream(
                model="claude-sonnet-4-5",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=history,
            ) as stream:
                for text_chunk in stream.text_stream:
                    full_response += text_chunk
                    response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)

        except anthropic.AuthenticationError:
            full_response = "❌ API 키가 유효하지 않습니다. 사이드바에서 올바른 API 키를 입력해 주세요."
            response_placeholder.error(full_response)

        except anthropic.RateLimitError:
            full_response = "⏳ API 요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요."
            response_placeholder.warning(full_response)

        except anthropic.APIConnectionError:
            full_response = "🌐 네트워크 연결 오류가 발생했습니다. 인터넷 연결을 확인해 주세요."
            response_placeholder.error(full_response)

        except Exception as e:
            full_response = f"⚠️ 예기치 않은 오류가 발생했습니다: {str(e)}"
            response_placeholder.error(full_response)

    # 어시스턴트 응답 저장
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )