"""Content Mate - Streamlit UI Application."""

import time

import httpx
import streamlit as st

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="콘텐츠 메이트",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-top: 0;
    }
    .content-box {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .status-pending { color: #FFA500; }
    .status-completed { color: #28A745; }
    .status-failed { color: #DC3545; }
    .phase-box {
        padding: 12px 16px;
        border-radius: 8px;
        margin: 4px 0;
        transition: all 0.3s ease;
    }
    .phase-active {
        background: linear-gradient(90deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 4px solid #1976D2;
    }
    .phase-complete {
        background: linear-gradient(90deg, #e8f5e9 0%, #c8e6c9 100%);
        border-left: 4px solid #388E3C;
    }
    .phase-pending {
        background-color: #f5f5f5;
        opacity: 0.7;
    }
    .phase-failed {
        background: linear-gradient(90deg, #ffebee 0%, #ffcdd2 100%);
        border-left: 4px solid #D32F2F;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Initialize session state
if "generation_in_progress" not in st.session_state:
    st.session_state.generation_in_progress = False
if "current_content_id" not in st.session_state:
    st.session_state.current_content_id = None
if "generated_result" not in st.session_state:
    st.session_state.generated_result = None

STATUS_LABELS = {
    "completed": "완료",
    "pending": "대기 중",
    "researching": "리서치 중",
    "planning": "기획 중",
    "writing": "작성 중",
    "editing": "편집 중",
    "failed": "실패",
}

CONTENT_TYPE_LABELS = {
    "blog_post": "블로그 글",
    "article": "기사",
    "social_media": "소셜 미디어",
    "email": "이메일",
    "landing_page": "랜딩 페이지",
}


def main():
    """Main application entry point."""
    # Header
    st.markdown('<p class="main-header">🚀 콘텐츠 메이트</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">멀티 에이전트 AI 콘텐츠 제작 플랫폼</p>',
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:
        st.header("⚙️ 생성 설정")

        content_type = st.selectbox(
            "콘텐츠 유형",
            ["blog_post", "article", "social_media", "email", "landing_page"],
            index=0,
            format_func=lambda x: {
                "blog_post": "📝 블로그 글",
                "article": "📰 기사",
                "social_media": "📱 소셜 미디어",
                "email": "✉️ 이메일",
                "landing_page": "🌐 랜딩 페이지",
            }.get(x, x),
        )

        tone = st.selectbox(
            "톤",
            ["professional", "casual", "educational", "persuasive", "entertaining"],
            index=0,
            format_func=lambda x: {
                "professional": "전문적",
                "casual": "캐주얼",
                "educational": "교육적",
                "persuasive": "설득적",
                "entertaining": "재미있는",
            }.get(x, x),
        )

        word_count = st.slider("목표 단어 수", 100, 5000, 1500, step=100)

        language = st.selectbox(
            "언어",
            ["en", "ko", "ja", "zh", "es", "fr", "de"],
            index=1,
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

        st.divider()
        st.markdown("### 🤖 에이전트 파이프라인")
        st.markdown("""
        1. 🔍 **리서처** - 자료 수집
        2. 📋 **플래너** - 개요 작성
        3. ✍️ **라이터** - 초안 작성
        4. ✨ **에디터** - 콘텐츠 다듬기
        """)

        st.divider()
        st.markdown("### 📚 문서")
        st.markdown("[API 문서](/docs) | [GitHub](https://github.com)")

    # Main content area
    tab1, tab2, tab3 = st.tabs(["✨ 생성", "📚 기록", "📊 대시보드"])

    with tab1:
        create_content_tab(content_type, tone, word_count, language)

    with tab2:
        history_tab()

    with tab3:
        dashboard_tab()


def create_content_tab(content_type: str, tone: str, word_count: int, language: str):
    """Content creation tab with real-time progress."""
    st.header("새 콘텐츠 생성")

    # Show result if available
    if st.session_state.generated_result:
        display_generated_content(st.session_state.generated_result)
        return

    # Input form
    col1, col2 = st.columns([2, 1])

    with col1:
        topic = st.text_area(
            "📝 주제 / 아이디어",
            placeholder="콘텐츠 주제 또는 아이디어를 입력하세요...\n\n예시: 2025년 콘텐츠 마케팅을 바꾸는 AI",
            height=100,
        )

        target_audience = st.text_input(
            "🎯 대상 독자(선택)",
            placeholder="예: 마케팅 전문가, 스타트업 창업자",
        )

        keywords = st.text_input(
            "🔑 SEO 키워드(선택, 쉼표로 구분)",
            placeholder="예: AI 콘텐츠, 콘텐츠 마케팅, 자동화",
        )

        additional_instructions = st.text_area(
            "📋 추가 지시사항(선택)",
            placeholder="특별히 반영할 요구사항이나 선호도를 입력하세요...",
            height=80,
        )

    with col2:
        st.info("""
        **좋은 결과를 얻는 팁:**
        - 주제를 구체적으로 작성하세요
        - 대상 독자 정보를 포함하세요
        - 관련 키워드를 추가하세요
        - 반드시 포함할 요소를 적어주세요
        """)

        # API Status indicator
        api_status = check_api_status()
        if api_status:
            st.success("🟢 API 서버 온라인")
        else:
            st.error("🔴 API 서버 오프라인")
            st.caption("다음 명령으로 시작하세요: `uv run uvicorn src.api.main:app --reload`")

    # Generate button
    if st.button(
        "🚀 콘텐츠 생성",
        type="primary",
        use_container_width=True,
        disabled=not api_status,
    ):
        if not topic or len(topic.strip()) < 5:
            st.error("주제를 입력해 주세요 (최소 5자)!")
            return

        # Prepare request
        request_data = {
            "topic": topic,
            "content_type": content_type,
            "tone": tone,
            "word_count": word_count,
            "language": language,
            "target_audience": target_audience or None,
            "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
            "additional_instructions": additional_instructions or None,
        }

        # Generate with progress
        generate_content_with_progress(request_data)


def check_api_status() -> bool:
    """Check if API server is running."""
    try:
        with httpx.Client(timeout=2.0) as client:
            response = client.get(f"{API_BASE_URL.replace('/api/v1', '')}/health")
            return response.status_code == 200
    except Exception:
        return False


def generate_content_with_progress(request_data: dict):
    """Generate content with real-time progress visualization."""

    # Progress phases configuration
    phases = [
        ("pending", "⏳", "초기화", "콘텐츠 생성을 시작합니다..."),
        ("researching", "🔍", "리서치", "주제에 대한 정보를 수집합니다..."),
        ("planning", "📋", "기획", "콘텐츠 개요를 작성합니다..."),
        ("writing", "✍️", "작성", "초안을 작성합니다..."),
        ("editing", "✨", "편집", "콘텐츠를 다듬고 개선합니다..."),
        ("completed", "✅", "완료", "콘텐츠 생성이 완료되었습니다!"),
    ]

    phase_order = ["pending", "researching", "planning", "writing", "editing", "completed"]

    try:
        # Start async generation
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{API_BASE_URL}/content/generate/async",
                json=request_data,
            )
            response.raise_for_status()
            data = response.json()
            content_id = data["content_id"]

        st.session_state.current_content_id = content_id

        # Create progress UI
        st.markdown("### 🤖 AI 에이전트 작업 중...")
        st.markdown(f"콘텐츠 ID: `{content_id[:8]}...`")

        progress_bar = st.progress(0)
        phase_container = st.container()

        # Phase status display
        with phase_container:
            phase_cols = st.columns(len(phases))
            phase_placeholders = []
            for i, (_, icon, name, _) in enumerate(phases):
                with phase_cols[i]:
                    phase_placeholders.append(st.empty())
                    phase_placeholders[i].markdown(
                        f'<div class="phase-box phase-pending">{icon} {name}</div>',
                        unsafe_allow_html=True,
                    )

        status_text = st.empty()
        time_text = st.empty()

        # Poll for status
        start_time = time.time()
        max_wait_time = 600  # 10 minutes
        poll_interval = 2  # 2 seconds

        while True:
            elapsed = time.time() - start_time

            if elapsed > max_wait_time:
                st.error("⏰ 생성 시간이 초과되었습니다. 다시 시도해 주세요.")
                return

            # Get current status
            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(f"{API_BASE_URL}/content/{content_id}")

                    if response.status_code == 200:
                        result = response.json()
                        status = result.get("status", "pending")

                        # Update progress
                        if status in phase_order:
                            new_phase_idx = phase_order.index(status)

                            # Update phase display
                            for i, (_phase_status, icon, name, desc) in enumerate(phases):
                                if i < new_phase_idx:
                                    # Completed phase
                                    phase_placeholders[i].markdown(
                                        f'<div class="phase-box phase-complete">✅ {name}</div>',
                                        unsafe_allow_html=True,
                                    )
                                elif i == new_phase_idx:
                                    # Active phase
                                    phase_placeholders[i].markdown(
                                        f'<div class="phase-box phase-active">{icon} {name}</div>',
                                        unsafe_allow_html=True,
                                    )
                                    status_text.info(f"**{name}:** {desc}")
                                else:
                                    # Pending phase
                                    phase_placeholders[i].markdown(
                                        f'<div class="phase-box phase-pending">{icon} {name}</div>',
                                        unsafe_allow_html=True,
                                    )

                            # Update progress bar
                            progress = int((new_phase_idx / (len(phases) - 1)) * 100)
                            progress_bar.progress(progress)

                        # Update time display
                        time_text.caption(f"⏱️ 경과 시간: {elapsed:.0f}초")

                        # Check if completed
                        if status == "completed":
                            progress_bar.progress(100)
                            status_text.success("✅ 콘텐츠 생성 완료!")

                            # Store result and refresh
                            st.session_state.generated_result = result
                            st.session_state.generation_in_progress = False
                            time.sleep(1)
                            st.rerun()
                            return

                        # Check if failed
                        if status == "failed":
                            progress_bar.progress(0)
                            status_text.error("❌ 콘텐츠 생성 실패")
                            st.error(result.get("error", "알 수 없는 오류"))
                            return

            except Exception as e:
                st.warning(f"상태 확인 오류 (재시도 중): {e}")

            time.sleep(poll_interval)

    except httpx.ConnectError:
        st.error("❌ API 서버에 연결할 수 없습니다")
        st.info("서버가 실행 중인지 확인하세요: `uv run uvicorn src.api.main:app --reload`")
    except Exception as e:
        st.error(f"오류: {str(e)}")


def display_generated_content(result: dict):
    """Display generated content result."""
    st.success("✅ 콘텐츠가 성공적으로 생성되었습니다!")

    # Metadata summary
    st.subheader("📊 생성 요약")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("상태", STATUS_LABELS.get(result.get("status"), "알 수 없음"))
    with col2:
        processing_time = result.get("processing_time_seconds")
        st.metric("시간", f"{processing_time:.1f}초" if processing_time else "없음")
    with col3:
        content = result.get("content", "")
        st.metric("단어 수", len(content.split()) if content else 0)
    with col4:
        content_type = result.get("request", {}).get("content_type") or "없음"
        st.metric("유형", CONTENT_TYPE_LABELS.get(content_type, content_type))

    # Outline
    outline = result.get("outline")
    if outline:
        with st.expander("📋 콘텐츠 개요", expanded=False):
            st.markdown(f"**제목:** {outline.get('title', '없음')}")
            st.markdown(f"**후킹 문구:** {outline.get('hook', '없음')}")

            sections = outline.get("sections", [])
            if sections:
                st.markdown("**섹션:**")
                for i, section in enumerate(sections, 1):
                    st.markdown(f"{i}. {section.get('header', '섹션')}")

            if outline.get("cta"):
                st.markdown(f"**CTA:** {outline.get('cta')}")

    # Main content
    st.subheader("📝 생성된 콘텐츠")
    content = result.get("content")
    if content:
        st.markdown(content)

        # Export section
        st.divider()
        st.markdown("### 📥 내보내기 옵션")

        content_id = result.get("id")
        export_cols = st.columns(5)

        formats = [
            ("markdown", "📄 마크다운"),
            ("html", "🌐 HTML"),
            ("pdf", "📑 PDF"),
            ("json", "📦 JSON"),
            ("txt", "📝 텍스트"),
        ]

        for i, (fmt, label) in enumerate(formats):
            with export_cols[i]:
                try:
                    with httpx.Client(timeout=10.0) as client:
                        response = client.get(
                            f"{API_BASE_URL}/content/{content_id}/export",
                            params={"format": fmt},
                        )
                        if response.status_code == 200:
                            ext = {
                                "markdown": "md",
                                "html": "html",
                                "pdf": "html",
                                "json": "json",
                                "txt": "txt",
                            }[fmt]
                            st.download_button(
                                label=label,
                                data=response.content,
                                file_name=f"content.{ext}",
                                mime=response.headers.get("content-type"),
                                key=f"download_{fmt}",
                            )
                except Exception:
                    st.button(label, disabled=True, key=f"btn_{fmt}")
    else:
        st.warning("생성된 콘텐츠가 없습니다")

    # Research findings
    research = result.get("research")
    if research:
        with st.expander("📚 조사 결과", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                if research.get("key_facts"):
                    st.markdown("**핵심 사실:**")
                    for fact in research["key_facts"]:
                        st.markdown(f"- {fact}")

                if research.get("statistics"):
                    st.markdown("**통계:**")
                    for stat in research["statistics"]:
                        st.markdown(f"- {stat}")

            with col2:
                if research.get("quotes"):
                    st.markdown("**인용문:**")
                    for quote in research["quotes"]:
                        st.markdown(f"> {quote}")

                if research.get("competitor_insights"):
                    st.markdown("**경쟁사 인사이트:**")
                    for insight in research["competitor_insights"]:
                        st.markdown(f"- {insight}")

    # Action buttons
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 새 콘텐츠 만들기", type="primary", use_container_width=True):
            st.session_state.generated_result = None
            st.session_state.current_content_id = None
            st.rerun()

    with col2:
        if st.button("📋 클립보드에 복사", use_container_width=True):
            st.code(content, language=None)
            st.info("위 텍스트를 선택해 복사하세요!")


def history_tab():
    """Content history tab."""
    st.header("📚 콘텐츠 기록")

    # Refresh button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🔄 새로고침"):
            st.rerun()

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{API_BASE_URL}/content")
            if response.status_code == 200:
                items = response.json()

                if not items:
                    st.info("📝 아직 생성된 콘텐츠가 없습니다. 첫 콘텐츠를 만들어 보세요!")
                    return

                # Summary stats
                completed = sum(1 for i in items if i["status"] == "completed")
                failed = sum(1 for i in items if i["status"] == "failed")

                stat_cols = st.columns(3)
                with stat_cols[0]:
                    st.metric("전체", len(items))
                with stat_cols[1]:
                    st.metric("✅ 완료", completed)
                with stat_cols[2]:
                    st.metric("❌ 실패", failed)

                st.divider()

                # Content list
                for item in items:
                    topic = item["request"]["topic"][:60]
                    status = item["status"]
                    status_label = STATUS_LABELS.get(status, status)
                    content_type_label = CONTENT_TYPE_LABELS.get(
                        item["request"]["content_type"],
                        item["request"]["content_type"],
                    )
                    status_emoji = {
                        "completed": "✅",
                        "failed": "❌",
                        "pending": "⏳",
                        "researching": "🔍",
                        "planning": "📋",
                        "writing": "✍️",
                        "editing": "✨",
                    }.get(status, "❓")

                    with st.expander(f"{status_emoji} {topic}..."):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**유형:** {content_type_label}")
                            st.markdown(f"**상태:** {status_label}")
                            st.markdown(f"**ID:** `{item['id'][:8]}...`")
                        with col2:
                            if item.get("processing_time_seconds"):
                                st.metric("시간", f"{item['processing_time_seconds']:.1f}초")

                        if item.get("content"):
                            st.markdown("---")
                            preview = item["content"][:500]
                            st.markdown(preview + ("..." if len(item["content"]) > 500 else ""))

                            # Actions
                            action_cols = st.columns([1, 1, 2])
                            with action_cols[0]:
                                # Export button
                                try:
                                    with httpx.Client(timeout=10.0) as exp_client:
                                        exp_response = exp_client.get(
                                            f"{API_BASE_URL}/content/{item['id']}/export",
                                            params={"format": "markdown"},
                                        )
                                        if exp_response.status_code == 200:
                                            st.download_button(
                                                "📥 내보내기",
                                                data=exp_response.content,
                                                file_name="content.md",
                                                key=f"export_{item['id']}",
                                            )
                                except Exception:
                                    pass

                            with action_cols[1]:
                                if st.button("🗑️ 삭제", key=f"delete_{item['id']}"):
                                    delete_content(item["id"])
            else:
                st.warning("기록을 불러올 수 없습니다")
    except httpx.ConnectError:
        st.info("🔌 API 서버를 사용할 수 없습니다. 서버를 실행한 뒤 기록을 확인하세요.")
    except Exception as e:
        st.error(f"기록 로딩 오류: {e}")


def delete_content(content_id: str):
    """Delete content by ID."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.delete(f"{API_BASE_URL}/content/{content_id}")
            if response.status_code == 200:
                st.success("✅ 콘텐츠가 삭제되었습니다!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("콘텐츠 삭제에 실패했습니다")
    except Exception as e:
        st.error(f"삭제 오류: {e}")


def dashboard_tab():
    """Dashboard/analytics tab."""
    st.header("📊 대시보드")

    # Fetch data
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE_URL}/content")
            items = response.json() if response.status_code == 200 else []
    except Exception:
        items = []

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    total = len(items)
    completed = sum(1 for i in items if i["status"] == "completed")
    avg_time = sum(
        i.get("processing_time_seconds", 0) for i in items if i.get("processing_time_seconds")
    ) / max(completed, 1)
    success_rate = (completed / total * 100) if total > 0 else 0

    with col1:
        st.metric("📄 전체 콘텐츠", total)
    with col2:
        st.metric("✅ 완료", completed)
    with col3:
        st.metric("⏱️ 평균 시간", f"{avg_time:.1f}초")
    with col4:
        st.metric("📈 성공률", f"{success_rate:.0f}%")

    if not items:
        st.info("📝 콘텐츠 생성을 시작하면 대시보드 지표가 표시됩니다.")
        return

    st.divider()

    # Content type distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 콘텐츠 유형별")
        type_counts = {}
        for item in items:
            ct = item["request"]["content_type"]
            ct_label = CONTENT_TYPE_LABELS.get(ct, ct)
            type_counts[ct_label] = type_counts.get(ct_label, 0) + 1

        if type_counts:
            import pandas as pd

            df = pd.DataFrame(list(type_counts.items()), columns=["유형", "건수"])
            st.bar_chart(df.set_index("유형"))

    with col2:
        st.subheader("📊 상태 분포")
        status_counts = {}
        for item in items:
            s = item["status"]
            status_label = STATUS_LABELS.get(s, s)
            status_counts[status_label] = status_counts.get(status_label, 0) + 1

        if status_counts:
            import pandas as pd

            df = pd.DataFrame(list(status_counts.items()), columns=["상태", "건수"])
            st.bar_chart(df.set_index("상태"))

    # Recent activity
    st.divider()
    st.subheader("📅 최근 활동")

    recent = items[:5]
    for item in recent:
        status_emoji = (
            "✅"
            if item["status"] == "completed"
            else ("❌" if item["status"] == "failed" else "⏳")
        )
        topic = item["request"]["topic"][:50]
        time_str = item.get("processing_time_seconds")
        time_display = f" ({time_str:.1f}초)" if time_str else ""

        st.markdown(f"- {status_emoji} **{topic}...**{time_display}")


if __name__ == "__main__":
    main()
