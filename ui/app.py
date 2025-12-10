"""ContentForge AI - Streamlit UI Application."""

import asyncio
from datetime import datetime

import httpx
import streamlit as st

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="ContentForge AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
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
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""
    # Header
    st.markdown('<p class="main-header">🚀 ContentForge AI</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Multi-Agent AI Content Creation Platform</p>',
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        content_type = st.selectbox(
            "Content Type",
            ["blog_post", "article", "social_media", "email", "landing_page"],
            index=0,
        )

        tone = st.selectbox(
            "Tone",
            ["professional", "casual", "educational", "persuasive", "entertaining"],
            index=0,
        )

        word_count = st.slider("Target Word Count", 100, 5000, 1500, step=100)

        language = st.selectbox(
            "Language",
            ["en", "ko", "ja", "zh", "es", "fr", "de"],
            index=0,
        )

        st.divider()
        st.markdown("### 🤖 Agent Pipeline")
        st.markdown("""
        1. 🔍 **Researcher** - Gathers facts
        2. ✍️ **Writer** - Creates draft
        3. ✨ **Editor** - Polishes content
        """)

    # Main content area
    tab1, tab2, tab3 = st.tabs(["✨ Create", "📚 History", "📊 Dashboard"])

    with tab1:
        create_content_tab(content_type, tone, word_count, language)

    with tab2:
        history_tab()

    with tab3:
        dashboard_tab()


def create_content_tab(content_type: str, tone: str, word_count: int, language: str):
    """Content creation tab."""
    st.header("Create New Content")

    # Input form
    col1, col2 = st.columns([2, 1])

    with col1:
        topic = st.text_area(
            "📝 Topic / Idea",
            placeholder="Enter your content topic or idea...\n\nExample: How AI is transforming content marketing in 2025",
            height=100,
        )

        target_audience = st.text_input(
            "🎯 Target Audience (optional)",
            placeholder="e.g., Marketing professionals, startup founders",
        )

        keywords = st.text_input(
            "🔑 SEO Keywords (optional, comma-separated)",
            placeholder="e.g., AI content, content marketing, automation",
        )

        additional_instructions = st.text_area(
            "📋 Additional Instructions (optional)",
            placeholder="Any specific requirements or preferences...",
            height=80,
        )

    with col2:
        st.info("""
        **Tips for best results:**
        - Be specific about your topic
        - Include target audience info
        - Add relevant keywords
        - Specify any must-include points
        """)

    # Generate button
    if st.button("🚀 Generate Content", type="primary", use_container_width=True):
        if not topic:
            st.error("Please enter a topic first!")
            return

        with st.spinner("🤖 AI agents are working on your content..."):
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

            try:
                # Make API request
                result = generate_content_sync(request_data)

                if result:
                    st.success("✅ Content generated successfully!")

                    # Display result
                    st.subheader("Generated Content")

                    # Metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Status", result.get("status", "Unknown"))
                    with col2:
                        processing_time = result.get("processing_time_seconds")
                        st.metric(
                            "Processing Time",
                            f"{processing_time:.1f}s" if processing_time else "N/A",
                        )
                    with col3:
                        word_count_actual = len(result.get("content", "").split())
                        st.metric("Word Count", word_count_actual)

                    # Content
                    st.markdown("---")
                    st.markdown(result.get("content", "No content generated"))

                    # Research findings
                    research = result.get("research")
                    if research:
                        with st.expander("📚 Research Findings"):
                            if research.get("key_facts"):
                                st.markdown("**Key Facts:**")
                                for fact in research["key_facts"]:
                                    st.markdown(f"- {fact}")

                            if research.get("statistics"):
                                st.markdown("**Statistics:**")
                                for stat in research["statistics"]:
                                    st.markdown(f"- {stat}")
                else:
                    st.error("Content generation failed. Please try again.")

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("Make sure the API server is running: `uv run uvicorn src.api.main:app --reload`")


def generate_content_sync(request_data: dict) -> dict | None:
    """Generate content via API (sync wrapper).

    Args:
        request_data: Content request data

    Returns:
        API response or None if failed
    """
    try:
        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                f"{API_BASE_URL}/content/generate",
                json=request_data,
            )
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        st.error("Cannot connect to API server. Is it running?")
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def history_tab():
    """Content history tab."""
    st.header("Content History")

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{API_BASE_URL}/content")
            if response.status_code == 200:
                items = response.json()

                if not items:
                    st.info("No content generated yet. Create your first content!")
                    return

                for item in items:
                    with st.expander(f"📄 {item['request']['topic'][:50]}..."):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**Type:** {item['request']['content_type']}")
                            st.markdown(f"**Status:** {item['status']}")
                        with col2:
                            if item.get("processing_time_seconds"):
                                st.metric("Time", f"{item['processing_time_seconds']:.1f}s")

                        if item.get("content"):
                            st.markdown("---")
                            st.markdown(item["content"][:500] + "...")
            else:
                st.warning("Could not load history")
    except httpx.ConnectError:
        st.info("API server not available. History will be shown when server is running.")
    except Exception as e:
        st.error(f"Error loading history: {e}")


def dashboard_tab():
    """Dashboard/analytics tab."""
    st.header("Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    # Demo metrics (replace with real data in production)
    with col1:
        st.metric("Total Content", "0", delta=None)
    with col2:
        st.metric("This Week", "0", delta=None)
    with col3:
        st.metric("Avg. Time", "0s", delta=None)
    with col4:
        st.metric("Success Rate", "0%", delta=None)

    st.info("Dashboard metrics will be available once you start generating content.")


if __name__ == "__main__":
    main()
