"""History page - View and manage generated content."""

from datetime import datetime
from typing import Any

import requests
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="History - Content Mate",
    page_icon="📚",
    layout="wide",
)

# Initialize session state
if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"

if "selected_content_id" not in st.session_state:
    st.session_state.selected_content_id = None


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
        st.error(f"Failed to fetch content: {e}")
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
        st.error(f"Failed to fetch content detail: {e}")
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
        st.error(f"Failed to delete content: {e}")
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
        st.error(f"Export failed: {e}")
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
    st.title("📚 Content History")
    st.markdown("View and manage your generated content")

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")

        # Status filter
        status_options = ["all", "completed", "pending", "failed"]
        selected_status = st.selectbox(
            "Status",
            options=status_options,
            format_func=lambda x: x.capitalize(),
        )

        # Items per page
        items_per_page = st.selectbox(
            "Items per page",
            options=[10, 20, 50],
            index=1,
        )

        # Search
        search_query = st.text_input("Search topic", placeholder="Enter keyword...")

        # Refresh button
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    # Main content area
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Content List")

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
                st.info("No content found")
            else:
                # Display content cards
                for item in items:
                    request = item.get("request", {})
                    topic = request.get("topic", "Untitled")
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

                        st.caption(f"Created: {created_at}")
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
                        f"<center>Page {st.session_state.page + 1} of {total_pages}</center>",
                        unsafe_allow_html=True,
                    )

                with page_col3:
                    if st.button("▶", disabled=st.session_state.page >= total_pages - 1):
                        st.session_state.page += 1
                        st.rerun()

        else:
            st.warning("Unable to load content list. Check API connection.")

    with col2:
        st.subheader("Content Detail")

        if st.session_state.selected_content_id:
            content = fetch_content_detail(st.session_state.selected_content_id)

            if content:
                request = content.get("request", {})
                status = content.get("status", "unknown")

                # Status badge
                color = get_status_color(status)
                st.markdown(
                    f"**Status:** <span style='color:{color};'>{status.upper()}</span>",
                    unsafe_allow_html=True,
                )

                # Content info
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.markdown(f"**Type:** {request.get('content_type', 'N/A')}")
                    st.markdown(f"**Tone:** {request.get('tone', 'N/A')}")
                    st.markdown(f"**Language:** {request.get('language', 'N/A')}")

                with info_col2:
                    st.markdown(f"**Word Count:** {request.get('word_count', 'N/A')}")
                    st.markdown(f"**Created:** {format_date(content.get('created_at'))}")
                    if content.get("processing_time_seconds"):
                        st.markdown(
                            f"**Processing Time:** {content['processing_time_seconds']:.1f}s"
                        )

                # Topic
                st.markdown("---")
                st.markdown(f"**Topic:** {request.get('topic', 'N/A')}")

                # Keywords
                keywords = request.get("keywords", [])
                if keywords:
                    st.markdown(f"**Keywords:** {', '.join(keywords)}")

                # Tabs for different sections
                tabs = st.tabs(["📝 Content", "📋 Outline", "🔍 Research", "⚙️ Actions"])

                with tabs[0]:  # Content tab
                    generated_content = content.get("content")
                    if generated_content:
                        st.markdown(generated_content)
                    else:
                        st.info("Content not yet generated")

                with tabs[1]:  # Outline tab
                    outline = content.get("outline")
                    if outline:
                        st.markdown(f"### {outline.get('title', 'Untitled')}")
                        st.markdown(f"**Hook:** {outline.get('hook', 'N/A')}")

                        sections = outline.get("sections", [])
                        if sections:
                            st.markdown("**Sections:**")
                            for i, section in enumerate(sections, 1):
                                with st.expander(f"{i}. {section.get('header', 'Section')}"):
                                    st.markdown(f"*Purpose:* {section.get('purpose', 'N/A')}")
                                    points = section.get("points", [])
                                    for point in points:
                                        st.markdown(f"- {point}")

                        conclusion = outline.get("conclusion_points", [])
                        if conclusion:
                            st.markdown("**Conclusion Points:**")
                            for point in conclusion:
                                st.markdown(f"- {point}")

                        if outline.get("cta"):
                            st.markdown(f"**Call to Action:** {outline['cta']}")
                    else:
                        st.info("Outline not available")

                with tabs[2]:  # Research tab
                    research = content.get("research")
                    if research:
                        key_facts = research.get("key_facts", [])
                        if key_facts:
                            st.markdown("**Key Facts:**")
                            for fact in key_facts:
                                st.markdown(f"- {fact}")

                        statistics = research.get("statistics", [])
                        if statistics:
                            st.markdown("**Statistics:**")
                            for stat in statistics:
                                st.markdown(f"- {stat}")

                        quotes = research.get("quotes", [])
                        if quotes:
                            st.markdown("**Quotes:**")
                            for quote in quotes:
                                st.markdown(f"> {quote}")

                        sources = research.get("sources", [])
                        if sources:
                            st.markdown("**Sources:**")
                            for source in sources:
                                if isinstance(source, dict):
                                    st.markdown(
                                        f"- [{source.get('title', 'Source')}]({source.get('url', '#')})"
                                    )
                                else:
                                    st.markdown(f"- {source}")
                    else:
                        st.info("Research data not available")

                with tabs[3]:  # Actions tab
                    st.markdown("### Export")
                    export_col1, export_col2 = st.columns(2)

                    with export_col1:
                        export_format = st.selectbox(
                            "Format",
                            options=["markdown", "html", "txt", "json"],
                        )

                    with export_col2:
                        if st.button("📥 Download", use_container_width=True):
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
                                    label="💾 Save File",
                                    data=exported,
                                    file_name=f"content.{ext_map.get(export_format, 'txt')}",
                                    mime="application/octet-stream",
                                )

                    st.markdown("---")
                    st.markdown("### Danger Zone")

                    if st.button("🗑️ Delete Content", type="secondary", use_container_width=True):
                        if st.session_state.get("confirm_delete"):
                            if delete_content(st.session_state.selected_content_id):
                                st.success("Content deleted!")
                                st.session_state.selected_content_id = None
                                st.session_state.confirm_delete = False
                                st.rerun()
                        else:
                            st.session_state.confirm_delete = True
                            st.warning("Click again to confirm deletion")

            else:
                st.error("Failed to load content details")
        else:
            st.info("Select a content item from the list to view details")

    # Footer
    st.markdown("---")
    st.markdown(
        "<center style='color:gray;'>Content Mate - Content History</center>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
