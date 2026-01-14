"""History page - View and manage generated content."""

from datetime import datetime
from typing import Any

import requests
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="기록 - 콘텐츠 메이트",
    page_icon="📚",
    layout="wide",
)

# Initialize session state
if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"

if "selected_content_id" not in st.session_state:
    st.session_state.selected_content_id = None

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
    "product_description": "제품 설명",
}

TONE_LABELS = {
    "professional": "전문적",
    "casual": "캐주얼",
    "educational": "교육적",
    "persuasive": "설득적",
    "entertaining": "재미있는",
}

LANGUAGE_LABELS = {
    "en": "영어",
    "ko": "한국어",
    "ja": "일본어",
    "zh": "중국어",
    "es": "스페인어",
    "fr": "프랑스어",
    "de": "독일어",
}


def get_api_url() -> str:
    """Get the API URL from session state."""
    return st.session_state.get("api_url", "http://localhost:8000")


def fetch_content_list(
    limit: int = 20,
    offset: int = 0,
    status_filter: str | None = None,
) -> dict[str, Any] | None:
    """Fetch content list from API.

    Args:
        limit: Number of items to fetch
        offset: Pagination offset
        status_filter: Optional status filter

    Returns:
        Content list response or None on error
    """
    try:
        params = {"limit": limit, "offset": offset}
        if status_filter and status_filter != "all":
            params["status"] = status_filter

        response = requests.get(
            f"{get_api_url()}/api/v1/content",
            params=params,
            timeout=10,
        )

        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"콘텐츠를 불러오지 못했습니다: {e}")
        return None


def fetch_content_detail(content_id: str) -> dict[str, Any] | None:
    """Fetch content detail from API.

    Args:
        content_id: Content ID

    Returns:
        Content detail or None on error
    """
    try:
        response = requests.get(
            f"{get_api_url()}/api/v1/content/{content_id}",
            timeout=10,
        )

        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"콘텐츠 상세 정보를 불러오지 못했습니다: {e}")
        return None


def delete_content(content_id: str) -> bool:
    """Delete content by ID.

    Args:
        content_id: Content ID

    Returns:
        True if deleted successfully
    """
    try:
        response = requests.delete(
            f"{get_api_url()}/api/v1/content/{content_id}",
            timeout=10,
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"콘텐츠 삭제에 실패했습니다: {e}")
        return False


def export_content(content_id: str, format: str) -> bytes | None:
    """Export content to specified format.

    Args:
        content_id: Content ID
        format: Export format

    Returns:
        Exported content bytes or None
    """
    try:
        response = requests.get(
            f"{get_api_url()}/api/v1/content/{content_id}/export",
            params={"format": format},
            timeout=30,
        )

        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        st.error(f"내보내기에 실패했습니다: {e}")
        return None


def format_date(date_str: str | None) -> str:
    """Format ISO date string for display.

    Args:
        date_str: ISO format date string

    Returns:
        Formatted date string
    """
    if not date_str:
        return "-"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return date_str


def get_status_color(status: str) -> str:
    """Get color for status badge.

    Args:
        status: Content status

    Returns:
        Color code
    """
    colors = {
        "completed": "green",
        "pending": "orange",
        "researching": "blue",
        "planning": "blue",
        "writing": "blue",
        "editing": "blue",
        "failed": "red",
    }
    return colors.get(status, "gray")


def get_content_type_emoji(content_type: str) -> str:
    """Get emoji for content type.

    Args:
        content_type: Content type

    Returns:
        Emoji string
    """
    emojis = {
        "blog_post": "📝",
        "article": "📰",
        "social_media": "📱",
        "email": "✉️",
        "landing_page": "🌐",
        "product_description": "🏷️",
    }
    return emojis.get(content_type, "📄")


def main():
    """Main function for history page."""
    st.title("📚 콘텐츠 기록")
    st.markdown("생성된 콘텐츠를 확인하고 관리하세요")

    # Sidebar filters
    with st.sidebar:
        st.header("필터")

        # Status filter
        status_options = ["all", "completed", "pending", "failed"]
        selected_status = st.selectbox(
            "상태",
            options=status_options,
            format_func=lambda x: {"all": "전체", **STATUS_LABELS}.get(x, x),
        )

        # Items per page
        items_per_page = st.selectbox(
            "페이지당 항목 수",
            options=[10, 20, 50],
            index=1,
        )

        # Search
        search_query = st.text_input("주제 검색", placeholder="키워드를 입력하세요...")

        # Refresh button
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()

    # Main content area
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("콘텐츠 목록")

        # Pagination state
        if "page" not in st.session_state:
            st.session_state.page = 0

        offset = st.session_state.page * items_per_page

        # Fetch content list
        content_list = fetch_content_list(
            limit=items_per_page,
            offset=offset,
            status_filter=selected_status,
        )

        if content_list and "items" in content_list:
            items = content_list["items"]

            # Filter by search query
            if search_query:
                items = [
                    item
                    for item in items
                    if search_query.lower() in item.get("request", {}).get("topic", "").lower()
                ]

            if not items:
                st.info("콘텐츠가 없습니다")
            else:
                # Display content cards
                for item in items:
                    request = item.get("request", {})
                    topic = request.get("topic", "제목 없음")
                    status = item.get("status", "unknown")
                    content_type = request.get("content_type", "blog_post")
                    created_at = format_date(item.get("created_at"))

                    # Content card
                    with st.container():
                        card_col1, card_col2 = st.columns([4, 1])

                        with card_col1:
                            emoji = get_content_type_emoji(content_type)
                            if st.button(
                                f"{emoji} {topic[:50]}...",
                                key=f"btn_{item['id']}",
                                use_container_width=True,
                            ):
                                st.session_state.selected_content_id = item["id"]
                                st.rerun()

                        with card_col2:
                            color = get_status_color(status)
                            st.markdown(
                                f"<span style='color:{color};font-size:0.8em;'>●</span>",
                                unsafe_allow_html=True,
                            )

                        st.caption(f"생성: {created_at}")
                        st.divider()

            # Pagination controls
            total = content_list.get("total", 0)
            total_pages = (total + items_per_page - 1) // items_per_page

            if total_pages > 1:
                page_col1, page_col2, page_col3 = st.columns([1, 2, 1])

                with page_col1:
                    if st.button("◀", disabled=st.session_state.page == 0):
                        st.session_state.page -= 1
                        st.rerun()

                with page_col2:
                    st.markdown(
                        f"<center>페이지 {st.session_state.page + 1} / {total_pages}</center>",
                        unsafe_allow_html=True,
                    )

                with page_col3:
                    if st.button("▶", disabled=st.session_state.page >= total_pages - 1):
                        st.session_state.page += 1
                        st.rerun()

        else:
            st.warning("콘텐츠 목록을 불러올 수 없습니다. API 연결을 확인하세요.")

    with col2:
        st.subheader("콘텐츠 상세")

        if st.session_state.selected_content_id:
            content = fetch_content_detail(st.session_state.selected_content_id)

            if content:
                request = content.get("request", {})
                status = content.get("status", "unknown")
                status_label = STATUS_LABELS.get(status, status)

                # Status badge
                color = get_status_color(status)
                st.markdown(
                    f"**상태:** <span style='color:{color};'>{status_label}</span>",
                    unsafe_allow_html=True,
                )

                # Content info
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    content_type = request.get("content_type", "없음")
                    tone = request.get("tone", "없음")
                    language = request.get("language", "없음")
                    st.markdown(
                        f"**유형:** {CONTENT_TYPE_LABELS.get(content_type, content_type)}"
                    )
                    st.markdown(f"**톤:** {TONE_LABELS.get(tone, tone)}")
                    st.markdown(f"**언어:** {LANGUAGE_LABELS.get(language, language)}")

                with info_col2:
                    st.markdown(f"**단어 수:** {request.get('word_count', '없음')}")
                    st.markdown(f"**생성:** {format_date(content.get('created_at'))}")
                    if content.get("processing_time_seconds"):
                        st.markdown(
                            f"**처리 시간:** {content['processing_time_seconds']:.1f}초"
                        )

                # Topic
                st.markdown("---")
                st.markdown(f"**주제:** {request.get('topic', '없음')}")

                # Keywords
                keywords = request.get("keywords", [])
                if keywords:
                    st.markdown(f"**키워드:** {', '.join(keywords)}")

                # Tabs for different sections
                tabs = st.tabs(["📝 콘텐츠", "📋 개요", "🔍 조사", "⚙️ 작업"])

                with tabs[0]:  # Content tab
                    generated_content = content.get("content")
                    if generated_content:
                        st.markdown(generated_content)
                    else:
                        st.info("아직 콘텐츠가 생성되지 않았습니다")

                with tabs[1]:  # Outline tab
                    outline = content.get("outline")
                    if outline:
                        st.markdown(f"### {outline.get('title', '제목 없음')}")
                        st.markdown(f"**후킹 문구:** {outline.get('hook', '없음')}")

                        sections = outline.get("sections", [])
                        if sections:
                            st.markdown("**섹션:**")
                            for i, section in enumerate(sections, 1):
                                with st.expander(f"{i}. {section.get('header', '섹션')}"):
                                    st.markdown(f"*목적:* {section.get('purpose', '없음')}")
                                    points = section.get("points", [])
                                    for point in points:
                                        st.markdown(f"- {point}")

                        conclusion = outline.get("conclusion_points", [])
                        if conclusion:
                            st.markdown("**결론 포인트:**")
                            for point in conclusion:
                                st.markdown(f"- {point}")

                        if outline.get("cta"):
                            st.markdown(f"**행동 유도 문구:** {outline['cta']}")
                    else:
                        st.info("개요를 사용할 수 없습니다")

                with tabs[2]:  # Research tab
                    research = content.get("research")
                    if research:
                        key_facts = research.get("key_facts", [])
                        if key_facts:
                            st.markdown("**핵심 사실:**")
                            for fact in key_facts:
                                st.markdown(f"- {fact}")

                        statistics = research.get("statistics", [])
                        if statistics:
                            st.markdown("**통계:**")
                            for stat in statistics:
                                st.markdown(f"- {stat}")

                        quotes = research.get("quotes", [])
                        if quotes:
                            st.markdown("**인용문:**")
                            for quote in quotes:
                                st.markdown(f"> {quote}")

                        sources = research.get("sources", [])
                        if sources:
                            st.markdown("**출처:**")
                            for source in sources:
                                if isinstance(source, dict):
                                    st.markdown(
                                        f"- [{source.get('title', '출처')}]({source.get('url', '#')})"
                                    )
                                else:
                                    st.markdown(f"- {source}")
                    else:
                        st.info("조사 데이터를 사용할 수 없습니다")

                with tabs[3]:  # Actions tab
                    st.markdown("### 내보내기")
                    export_col1, export_col2 = st.columns(2)

                    with export_col1:
                        export_format = st.selectbox(
                            "형식",
                            options=["markdown", "html", "txt", "json"],
                        )

                    with export_col2:
                        if st.button("📥 다운로드", use_container_width=True):
                            exported = export_content(
                                st.session_state.selected_content_id,
                                export_format,
                            )
                            if exported:
                                ext_map = {
                                    "markdown": "md",
                                    "html": "html",
                                    "txt": "txt",
                                    "json": "json",
                                }
                                st.download_button(
                                    label="💾 파일 저장",
                                    data=exported,
                                    file_name=f"content.{ext_map.get(export_format, 'txt')}",
                                    mime="application/octet-stream",
                                )

                    st.markdown("---")
                    st.markdown("### 위험 구역")

                    if st.button("🗑️ 콘텐츠 삭제", type="secondary", use_container_width=True):
                        if st.session_state.get("confirm_delete"):
                            if delete_content(st.session_state.selected_content_id):
                                st.success("콘텐츠가 삭제되었습니다!")
                                st.session_state.selected_content_id = None
                                st.session_state.confirm_delete = False
                                st.rerun()
                        else:
                            st.session_state.confirm_delete = True
                            st.warning("다시 클릭하면 삭제가 확정됩니다")

            else:
                st.error("콘텐츠 상세 정보를 불러오지 못했습니다")
        else:
            st.info("상세 내용을 보려면 목록에서 콘텐츠를 선택하세요")

    # Footer
    st.markdown("---")
    st.markdown(
        "<center style='color:gray;'>콘텐츠 메이트 - 콘텐츠 기록</center>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
