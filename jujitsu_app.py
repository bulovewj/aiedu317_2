import streamlit as st
import anthropic
import base64
from PIL import Image
import io
import time

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="웹캠 카메라 앱",
    page_icon="📷",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── 커스텀 CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
        color: #e0e0e0;
    }

    /* 타이틀 영역 */
    .title-container {
        text-align: center;
        padding: 20px 0 10px 0;
    }
    .title-container h1 {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00d2ff, #7b2ff7, #00d2ff);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 3s linear infinite;
    }
    @keyframes shine {
        to { background-position: 200% center; }
    }
    .title-container p {
        color: #888;
        font-size: 0.95rem;
        margin-top: -8px;
    }

    /* 카메라 컨테이너 */
    .camera-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 10px auto;
        max-width: 680px;
    }

    /* 상태 배지 */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 18px;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0 auto 8px auto;
        text-align: center;
    }
    .status-on {
        background: rgba(0,255,128,0.15);
        border: 1px solid rgba(0,255,128,0.4);
        color: #00ff80;
    }
    .status-off {
        background: rgba(255,80,80,0.15);
        border: 1px solid rgba(255,80,80,0.4);
        color: #ff5050;
    }
    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-on  { background: #00ff80; box-shadow: 0 0 6px #00ff80; animation: blink 1.2s infinite; }
    .dot-off { background: #ff5050; }
    @keyframes blink {
        0%,100% { opacity:1; } 50% { opacity:0.3; }
    }

    /* 버튼 공통 */
    div.stButton > button {
        border-radius: 12px;
        font-weight: 700;
        font-size: 1rem;
        padding: 0.55rem 0;
        width: 100%;
        border: none;
        transition: all 0.25s ease;
        letter-spacing: 0.5px;
    }

    /* ON 버튼 */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00c853, #69f0ae);
        color: #000;
        box-shadow: 0 4px 18px rgba(0,200,83,0.4);
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(0,200,83,0.6);
    }

    /* OFF / 분석 버튼 */
    div.stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #e53935, #ff5252);
        color: #fff;
        box-shadow: 0 4px 18px rgba(229,57,53,0.4);
    }
    div.stButton > button[kind="secondary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(229,57,53,0.6);
    }

    /* 분석 결과 박스 */
    .analysis-box {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(123,47,247,0.4);
        border-radius: 14px;
        padding: 18px 22px;
        margin-top: 12px;
        line-height: 1.7;
        color: #d0d0e8;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(255,255,255,0.03);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    section[data-testid="stSidebar"] .stTextInput input {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.15);
        color: #e0e0e0;
        border-radius: 8px;
    }

    /* 구분선 */
    hr { border-color: rgba(255,255,255,0.08); }

    /* 카메라 캡처 버튼 숨김 처리 & 스타일 */
    div[data-testid="stCameraInput"] > div > button {
        background: linear-gradient(135deg, #7b2ff7, #00d2ff) !important;
        color: #fff !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
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
</style>
""", unsafe_allow_html=True)

# ── Session State 초기화 ──────────────────────────────────────
if "camera_on" not in st.session_state:
    st.session_state.camera_on = False
if "captured_image" not in st.session_state:
    st.session_state.captured_image = None
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── 사이드바 ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 설정")
    st.markdown("---")
    api_key = st.text_input(
        "🔑 Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="https://console.anthropic.com 에서 발급받으세요.",
    )
    st.markdown("---")
    st.markdown("### 📋 사용 방법")
    st.markdown("""
1. **API Key** 입력
2. **카메라 ON** 버튼 클릭
3. 브라우저 카메라 권한 허용
4. 📸 **사진 찍기** 버튼으로 캡처
5. **🔍 AI 이미지 분석** 버튼 클릭
6. 채팅으로 추가 질문 가능
""")
    st.markdown("---")
    st.markdown("### 🤖 모델 정보")
    st.info("claude-sonnet-4-5")
    st.markdown("---")
    if st.button("🗑️ 대화 기록 초기화"):
        st.session_state.chat_history = []
        st.session_state.analysis_result = ""
        st.session_state.captured_image = None
        st.rerun()

# ── 타이틀 ────────────────────────────────────────────────────
st.markdown("""
<div class="title-container">
    <h1>📷 웹캠 카메라 앱</h1>
    <p>실시간 카메라 & Claude AI 이미지 분석</p>
</div>
""", unsafe_allow_html=True)

# ── 상태 배지 ─────────────────────────────────────────────────
col_badge = st.columns([1, 2, 1])[1]
with col_badge:
    if st.session_state.camera_on:
        st.markdown("""
        <div style="text-align:center">
            <span class="status-badge status-on">
                <span class="dot dot-on"></span> LIVE · 카메라 활성화
            </span>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center">
            <span class="status-badge status-off">
                <span class="dot dot-off"></span> OFF · 카메라 비활성
            </span>
        </div>""", unsafe_allow_html=True)

# ── ON / OFF 버튼 ─────────────────────────────────────────────
col1, col_space, col2 = st.columns([1, 0.15, 1])
with col1:
    if not st.session_state.camera_on:
        if st.button("🟢  카메라 ON", type="primary", use_container_width=True):
            st.session_state.camera_on = True
            st.session_state.captured_image = None
            st.session_state.analysis_result = ""
            st.rerun()
    else:
        st.button("🟢  카메라 ON", type="primary", use_container_width=True, disabled=True)

with col2:
    if st.session_state.camera_on:
        if st.button("🔴  카메라 OFF", type="secondary", use_container_width=True):
            st.session_state.camera_on = False
            st.session_state.captured_image = None
            st.session_state.analysis_result = ""
            st.rerun()
    else:
        st.button("🔴  카메라 OFF", type="secondary", use_container_width=True, disabled=True)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ── 카메라 영역 ───────────────────────────────────────────────
if st.session_state.camera_on:
    st.markdown("<div class='camera-wrapper'>", unsafe_allow_html=True)
    camera_image = st.camera_input(
        label="",
        key="webcam",
        help="📸 사진 찍기 버튼을 눌러 캡처하세요",
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if camera_image is not None:
        st.session_state.captured_image = camera_image
        st.success("✅ 사진이 캡처되었습니다! 아래에서 AI 분석을 실행해보세요.")
else:
    # 카메라 OFF 상태 플레이스홀더
    st.markdown("""
    <div style="
        width: 100%;
        max-width: 640px;
        height: 360px;
        margin: 0 auto;
        background: rgba(255,255,255,0.03);
        border: 2px dashed rgba(255,255,255,0.12);
        border-radius: 16px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 12px;
        color: #555;
    ">
        <div style="font-size: 3.5rem">📷</div>
        <div style="font-size: 1.1rem; font-weight: 600;">카메라가 꺼져 있습니다</div>
        <div style="font-size: 0.85rem;">카메라 ON 버튼을 눌러 시작하세요</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── AI 이미지 분석 섹션 ───────────────────────────────────────
st.markdown("### 🔍 AI 이미지 분석")

analyze_col1, analyze_col2 = st.columns([3, 1])
with analyze_col1:
    analyze_prompt = st.text_input(
        "분석 질문",
        value="이 이미지에서 무엇이 보이나요? 자세히 설명해주세요.",
        label_visibility="collapsed",
        placeholder="이미지에 대해 질문을 입력하세요...",
    )

with analyze_col2:
    analyze_btn = st.button(
        "🔍 분석 실행",
        type="primary",
        use_container_width=True,
        disabled=(st.session_state.captured_image is None),
    )

# ── 분석 실행 로직 ────────────────────────────────────────────
def encode_image_to_base64(image_file) -> str:
    """업로드된 이미지를 base64로 인코딩"""
    img_bytes = image_file.getvalue()
    return base64.standard_b64encode(img_bytes).decode("utf-8")

def analyze_image_with_claude(api_key: str, image_b64: str, prompt: str) -> str:
    """Claude claude-sonnet-4-5으로 이미지 분석"""
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
        system="당신은 이미지를 분석하는 전문 AI 어시스턴트입니다. 이미지의 내용을 한국어로 상세하고 정확하게 설명해주세요.",
    )
    return message.content[0].text

if analyze_btn:
    if not api_key:
        st.warning("⚠️ 사이드바에서 Anthropic API Key를 먼저 입력해주세요.")
    elif st.session_state.captured_image is None:
        st.warning("⚠️ 먼저 카메라로 사진을 촬영해주세요.")
    else:
        with st.spinner("🤖 Claude AI가 이미지를 분석 중입니다..."):
            try:
                img_b64 = encode_image_to_base64(st.session_state.captured_image)
                result = analyze_image_with_claude(api_key, img_b64, analyze_prompt)
                st.session_state.analysis_result = result
                # 채팅 기록에 추가
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": f"[이미지 분석 요청] {analyze_prompt}",
                })
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": result,
                })
            except anthropic.AuthenticationError:
                st.error("❌ API Key가 유효하지 않습니다. 다시 확인해주세요.")
            except anthropic.RateLimitError:
                st.error("❌ API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")
            except Exception as e:
                st.error(f"❌ 오류 발생: {str(e)}")

# 분석 결과 표시
if st.session_state.analysis_result:
    st.markdown(f"""
    <div class="analysis-box">
        <strong style="color:#a78bfa">🤖 AI 분석 결과</strong><br><br>
        {st.session_state.analysis_result.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── 채팅 섹션 ────────────────────────────────────────────────
st.markdown("### 💬 AI와 대화하기")

# 채팅 기록 표시
chat_container = st.container()
with chat_container:
    if not st.session_state.chat_history:
        st.markdown("""
        <div style="text-align:center; color:#555; padding: 20px 0; font-size:0.9rem;">
            💡 카메라로 사진을 찍고 분석하거나, 아래에서 직접 질문해보세요.
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"],
                                  avatar="🧑" if msg["role"] == "user" else "🤖"):
                st.write(msg["content"])

# 채팅 입력
if prompt_input := st.chat_input("메시지를 입력하세요... (예: 이미지에 대해 더 자세히 알려줘)"):
    if not api_key:
        st.warning("⚠️ 사이드바에서 Anthropic API Key를 먼저 입력해주세요.")
    else:
        # 사용자 메시지 추가
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt_input,
        })

        # Claude API 호출 (이미지 컨텍스트 포함 가능)
        with st.spinner("🤖 응답 생성 중..."):
            try:
                client = anthropic.Anthropic(api_key=api_key)

                # 메시지 구성 (이미지가 있으면 첫 번째 사용자 메시지에 포함)
                api_messages = []
                has_image = st.session_state.captured_image is not None

                for i, msg in enumerate(st.session_state.chat_history):
                    if msg["role"] == "user" and i == 0 and has_image:
                        img_b64 = encode_image_to_base64(st.session_state.captured_image)
                        api_messages.append({
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
                                {"type": "text", "text": msg["content"]},
                            ],
                        })
                    else:
                        api_messages.append({
                            "role": msg["role"],
                            "content": msg["content"],
                        })

                response = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=1024,
                    system="당신은 웹캠 카메라 앱과 연동된 친절한 AI 어시스턴트입니다. 사용자의 질문에 한국어로 친절하고 정확하게 답변해주세요.",
                    messages=api_messages,
                )
                assistant_reply = response.content[0].text
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": assistant_reply,
                })
                st.rerun()

            except anthropic.AuthenticationError:
                st.error("❌ API Key가 유효하지 않습니다.")
            except Exception as e:
                st.error(f"❌ 오류 발생: {str(e)}")

# ── 푸터 ─────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:#444; font-size:0.78rem; padding: 20px 0 10px 0;">
    📷 Webcam App · Powered by Claude claude-sonnet-4-5 · Built with Streamlit
</div>
""", unsafe_allow_html=True)
