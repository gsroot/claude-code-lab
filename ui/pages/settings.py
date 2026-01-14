"""Settings page for Content Mate."""

import httpx
import streamlit as st

st.set_page_config(
    page_title="설정 - 콘텐츠 메이트",
    page_icon="⚙️",
    layout="wide",
)

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"


def main():
    """Settings page main function."""
    st.title("⚙️ 설정")
    st.markdown("콘텐츠 메이트 환경을 설정하세요")

    # Tabs for different settings sections
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "🔌 API 연결",
            "🤖 생성 기본값",
            "🎨 외관",
            "ℹ️ 소개",
        ]
    )

    with tab1:
        api_settings()

    with tab2:
        generation_defaults()

    with tab3:
        appearance_settings()

    with tab4:
        about_section()


def api_settings():
    """API connection settings."""
    st.header("🔌 API 연결")

    # Current API URL
    st.subheader("API 서버")

    col1, col2 = st.columns([3, 1])

    with col1:
        api_url = st.text_input(
            "API 기본 URL",
            value=API_BASE_URL.replace("/api/v1", ""),
            help="Content Mate API 서버의 기본 URL입니다",
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 연결 테스트"):
            test_api_connection(api_url)

    # Connection status
    st.subheader("연결 상태")

    try:
        with httpx.Client(timeout=5.0) as client:
            # Health check
            health_response = client.get(f"{api_url}/health")
            if health_response.status_code == 200:
                st.success("✅ API 서버: 연결됨")

                # Get API info
                root_response = client.get(f"{api_url}/")
                if root_response.status_code == 200:
                    info = root_response.json()
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("API 이름", info.get("name", "없음"))
                    with col2:
                        st.metric("버전", info.get("version", "없음"))
                    with col3:
                        st.metric("상태", info.get("status", "없음").title())
            else:
                st.error("❌ API 서버: 응답이 올바르지 않습니다")
    except httpx.ConnectError:
        st.error("❌ API 서버: 연결할 수 없습니다")
        st.info("""
        **API 서버 시작 방법:**
        ```bash
        uv run uvicorn src.api.main:app --reload
        ```
        """)
    except Exception as e:
        st.error(f"❌ 연결 오류: {e}")

    # WebSocket settings
    st.subheader("WebSocket 연결")
    _ws_url = st.text_input(
        "WebSocket URL",
        value="ws://localhost:8000/api/v1",
        help="실시간 진행 상황 업데이트용 WebSocket URL",
    )
    st.info("WebSocket 연결은 실시간 생성 진행 상황 업데이트에 사용됩니다.")


def test_api_connection(api_url: str):
    """Test API connection."""
    with st.spinner("연결을 테스트 중..."):
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{api_url}/health")
                if response.status_code == 200:
                    st.success("✅ 연결 성공!")
                else:
                    st.error(f"❌ 서버가 상태 코드 {response.status_code}을 반환했습니다")
        except httpx.ConnectError:
            st.error("❌ 서버에 연결할 수 없습니다")
        except Exception as e:
            st.error(f"❌ 오류: {e}")


def generation_defaults():
    """Default generation settings."""
    st.header("🤖 생성 기본값")
    st.markdown("콘텐츠 생성 기본값을 설정하세요")

    # Initialize session state for defaults
    if "default_content_type" not in st.session_state:
        st.session_state.default_content_type = "blog_post"
    if "default_tone" not in st.session_state:
        st.session_state.default_tone = "professional"
    if "default_word_count" not in st.session_state:
        st.session_state.default_word_count = 1500
    if "default_language" not in st.session_state:
        st.session_state.default_language = "ko"

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("콘텐츠 설정")

        default_type = st.selectbox(
            "기본 콘텐츠 유형",
            ["blog_post", "article", "social_media", "email", "landing_page"],
            index=["blog_post", "article", "social_media", "email", "landing_page"].index(
                st.session_state.default_content_type
            ),
            format_func=lambda x: {
                "blog_post": "📝 블로그 글",
                "article": "📰 기사",
                "social_media": "📱 소셜 미디어",
                "email": "✉️ 이메일",
                "landing_page": "🌐 랜딩 페이지",
            }.get(x, x),
        )

        default_tone = st.selectbox(
            "기본 톤",
            ["professional", "casual", "educational", "persuasive", "entertaining"],
            index=["professional", "casual", "educational", "persuasive", "entertaining"].index(
                st.session_state.default_tone
            ),
            format_func=lambda x: {
                "professional": "전문적",
                "casual": "캐주얼",
                "educational": "교육적",
                "persuasive": "설득적",
                "entertaining": "재미있는",
            }.get(x, x),
        )

        default_word_count = st.slider(
            "기본 단어 수",
            min_value=100,
            max_value=5000,
            value=st.session_state.default_word_count,
            step=100,
        )

    with col2:
        st.subheader("언어 및 지역화")

        default_language = st.selectbox(
            "기본 언어",
            ["en", "ko", "ja", "zh", "es", "fr", "de"],
            index=["en", "ko", "ja", "zh", "es", "fr", "de"].index(
                st.session_state.default_language
            ),
            format_func=lambda x: {
                "en": "🇺🇸 영어",
                "ko": "🇰🇷 한국어",
                "ja": "🇯🇵 일본어",
                "zh": "🇨🇳 중국어",
                "es": "🇪🇸 스페인어",
                "fr": "🇫🇷 프랑스어",
                "de": "🇩🇪 독일어",
            }.get(x, x),
        )

        st.markdown("---")
        st.subheader("생성 옵션")

        _include_research = st.checkbox("조사 결과를 출력에 포함", value=True)
        _include_outline = st.checkbox("콘텐츠 개요 표시", value=True)
        _auto_export = st.checkbox("생성 후 자동 다운로드", value=False)

    # Save button
    st.divider()
    if st.button("💾 기본값 저장", type="primary"):
        st.session_state.default_content_type = default_type
        st.session_state.default_tone = default_tone
        st.session_state.default_word_count = default_word_count
        st.session_state.default_language = default_language
        st.success("✅ 설정이 저장되었습니다!")


def appearance_settings():
    """Appearance settings."""
    st.header("🎨 외관")

    st.subheader("테마")
    _theme = st.selectbox(
        "색상 테마",
        ["시스템 기본값", "라이트", "다크"],
        help="참고: 테마 변경은 앱 재시작이 필요할 수 있습니다",
    )

    st.info("""
    **Streamlit 테마 변경 방법:**

    `.streamlit/config.toml`을 생성하거나 수정하세요:
    ```toml
    [theme]
    primaryColor = "#1E88E5"
    backgroundColor = "#FFFFFF"
    secondaryBackgroundColor = "#F0F2F6"
    textColor = "#262730"
    ```
    """)

    st.subheader("표시 옵션")

    col1, col2 = st.columns(2)

    with col1:
        _show_api_status = st.checkbox("API 상태 표시기 표시", value=True)
        _show_word_count = st.checkbox("결과에 단어 수 표시", value=True)
        _show_processing_time = st.checkbox("처리 시간 표시", value=True)

    with col2:
        _expand_outline = st.checkbox("개요 섹션 자동 펼치기", value=False)
        _expand_research = st.checkbox("조사 섹션 자동 펼치기", value=False)
        _compact_history = st.checkbox("기록 보기 간소화", value=False)


def about_section():
    """About section."""
    st.header("ℹ️ 콘텐츠 메이트 소개")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### 🚀 콘텐츠 메이트

        **멀티 에이전트 AI 콘텐츠 제작 플랫폼**

        콘텐츠 메이트는 전문화된 AI 에이전트 파이프라인으로
        고품질 콘텐츠를 생성합니다:

        1. **🔍 리서처 에이전트** - 사실 및 정보 수집
        2. **📋 플래너 에이전트** - 구조화된 개요 작성
        3. **✍️ 라이터 에이전트** - 매력적인 콘텐츠 작성
        4. **✨ 에디터 에이전트** - 다듬기와 개선

        사용 기술:
        - **LangGraph** - 멀티 에이전트 오케스트레이션
        - **MCP** - 도구를 위한 Model Context Protocol
        - **FastAPI** - 고성능 API
        - **Streamlit** - 인터랙티브 UI
        """)

    with col2:
        st.markdown("### 📊 시스템 정보")

        # Try to get API version
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{API_BASE_URL.replace('/api/v1', '')}/")
                if response.status_code == 200:
                    info = response.json()
                    st.metric("API 버전", info.get("version", "없음"))
        except Exception:
            st.metric("API 버전", "없음")

        st.metric("UI 버전", "0.1.0")
        st.metric("Python", "3.11+")

    st.divider()

    st.markdown("### 📚 문서")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **API 문서**
        - [OpenAPI 문서](/docs)
        - [ReDoc](/redoc)
        """)

    with col2:
        st.markdown("""
        **리소스**
        - [GitHub 저장소](https://github.com)
        - [이슈 트래커](https://github.com)
        """)

    with col3:
        st.markdown("""
        **지원**
        - [Discord 커뮤니티](#)
        - [이메일 지원](#)
        """)

    st.divider()

    st.markdown("### 📄 라이선스")
    st.markdown("""
    콘텐츠 메이트는 **MIT 라이선스**로 제공됩니다.

    Copyright © 2025 ContentMate Team
    """)


if __name__ == "__main__":
    main()
