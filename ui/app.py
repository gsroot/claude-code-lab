"""Content Mate - Streamlit UI Application."""

import time

import httpx
import streamlit as st

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="Content Mate",
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


def main():
    """Main application entry point."""
    # Header
    st.markdown('<p class="main-header">🚀 Content Mate</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Multi-Agent AI Content Creation Platform</p>',
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Generation Settings")

        content_type = st.selectbox(
            "Content Type",
            ["blog_post", "article", "social_media", "email", "landing_page"],
            index=0,
            format_func=lambda x: {
                "blog_post": "📝 Blog Post",
                "article": "📰 Article",
                "social_media": "📱 Social Media",
                "email": "✉️ Email",
                "landing_page": "🌐 Landing Page",
            }.get(x, x),
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
            format_func=lambda x: {
                "en": "🇺🇸 English",
                "ko": "🇰🇷 한국어",
                "ja": "🇯🇵 日本語",
                "zh": "🇨🇳 中文",
                "es": "🇪🇸 Español",
                "fr": "🇫🇷 Français",
                "de": "🇩🇪 Deutsch",
            }.get(x, x),
        )

        st.divider()
        st.markdown("### 🤖 Agent Pipeline")
        st.markdown("""
        1. 🔍 **Researcher** - Gathers facts
        2. 📋 **Planner** - Creates outline
        3. ✍️ **Writer** - Creates draft
        4. ✨ **Editor** - Polishes content
        """)

        st.divider()
        st.markdown("### 📚 Documentation")
        st.markdown("[API Docs](/docs) | [GitHub](https://github.com)")

    # Main content area
    tab1, tab2, tab3 = st.tabs(["✨ Create", "📚 History", "📊 Dashboard"])

    with tab1:
        create_content_tab(content_type, tone, word_count, language)

    with tab2:
        history_tab()

    with tab3:
        dashboard_tab()


def create_content_tab(content_type: str, tone: str, word_count: int, language: str):
    """Content creation tab with real-time progress."""
    st.header("Create New Content")

    # Show result if available
    if st.session_state.generated_result:
        display_generated_content(st.session_state.generated_result)
        return

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

        # API Status indicator
        api_status = check_api_status()
        if api_status:
            st.success("🟢 API Server Online")
        else:
            st.error("🔴 API Server Offline")
            st.caption("Start with: `uv run uvicorn src.api.main:app --reload`")

    # Generate button
    if st.button(
        "🚀 Generate Content",
        type="primary",
        use_container_width=True,
        disabled=not api_status,
    ):
        if not topic or len(topic.strip()) < 5:
            st.error("Please enter a topic (at least 5 characters)!")
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
        ("pending", "⏳", "Initializing", "Starting content generation..."),
        ("researching", "🔍", "Researching", "Gathering information about the topic..."),
        ("planning", "📋", "Planning", "Creating content outline..."),
        ("writing", "✍️", "Writing", "Writing the initial draft..."),
        ("editing", "✨", "Editing", "Polishing and improving content..."),
        ("completed", "✅", "Complete", "Content generation finished!"),
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
        st.markdown("### 🤖 AI Agents Working...")
        st.markdown(f"Content ID: `{content_id[:8]}...`")

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
                st.error("⏰ Generation timed out. Please try again.")
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
                        time_text.caption(f"⏱️ Elapsed: {elapsed:.0f}s")

                        # Check if completed
                        if status == "completed":
                            progress_bar.progress(100)
                            status_text.success("✅ Content generation complete!")

                            # Store result and refresh
                            st.session_state.generated_result = result
                            st.session_state.generation_in_progress = False
                            time.sleep(1)
                            st.rerun()
                            return

                        # Check if failed
                        if status == "failed":
                            progress_bar.progress(0)
                            status_text.error("❌ Content generation failed")
                            st.error(result.get("error", "Unknown error"))
                            return

            except Exception as e:
                st.warning(f"Polling error (retrying): {e}")

            time.sleep(poll_interval)

    except httpx.ConnectError:
        st.error("❌ Cannot connect to API server")
        st.info("Make sure the server is running: `uv run uvicorn src.api.main:app --reload`")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def display_generated_content(result: dict):
    """Display generated content result."""
    st.success("✅ Content generated successfully!")

    # Metadata summary
    st.subheader("📊 Generation Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Status", result.get("status", "Unknown").title())
    with col2:
        processing_time = result.get("processing_time_seconds")
        st.metric("Time", f"{processing_time:.1f}s" if processing_time else "N/A")
    with col3:
        content = result.get("content", "")
        st.metric("Words", len(content.split()) if content else 0)
    with col4:
        st.metric("Type", result.get("request", {}).get("content_type", "N/A"))

    # Outline
    outline = result.get("outline")
    if outline:
        with st.expander("📋 Content Outline", expanded=False):
            st.markdown(f"**Title:** {outline.get('title', 'N/A')}")
            st.markdown(f"**Hook:** {outline.get('hook', 'N/A')}")

            sections = outline.get("sections", [])
            if sections:
                st.markdown("**Sections:**")
                for i, section in enumerate(sections, 1):
                    st.markdown(f"{i}. {section.get('header', 'Section')}")

            if outline.get("cta"):
                st.markdown(f"**CTA:** {outline.get('cta')}")

    # Main content
    st.subheader("📝 Generated Content")
    content = result.get("content")
    if content:
        st.markdown(content)

        # Export section
        st.divider()
        st.markdown("### 📥 Export Options")

        content_id = result.get("id")
        export_cols = st.columns(5)

        formats = [
            ("markdown", "📄 Markdown"),
            ("html", "🌐 HTML"),
            ("pdf", "📑 PDF"),
            ("json", "📦 JSON"),
            ("txt", "📝 Text"),
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
        st.warning("No content was generated")

    # Research findings
    research = result.get("research")
    if research:
        with st.expander("📚 Research Findings", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                if research.get("key_facts"):
                    st.markdown("**Key Facts:**")
                    for fact in research["key_facts"]:
                        st.markdown(f"- {fact}")

                if research.get("statistics"):
                    st.markdown("**Statistics:**")
                    for stat in research["statistics"]:
                        st.markdown(f"- {stat}")

            with col2:
                if research.get("quotes"):
                    st.markdown("**Quotes:**")
                    for quote in research["quotes"]:
                        st.markdown(f"> {quote}")

                if research.get("competitor_insights"):
                    st.markdown("**Competitor Insights:**")
                    for insight in research["competitor_insights"]:
                        st.markdown(f"- {insight}")

    # Action buttons
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Create New Content", type="primary", use_container_width=True):
            st.session_state.generated_result = None
            st.session_state.current_content_id = None
            st.rerun()

    with col2:
        if st.button("📋 Copy to Clipboard", use_container_width=True):
            st.code(content, language=None)
            st.info("Select the text above and copy it!")


def history_tab():
    """Content history tab."""
    st.header("📚 Content History")

    # Refresh button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{API_BASE_URL}/content")
            if response.status_code == 200:
                items = response.json()

                if not items:
                    st.info("📝 No content generated yet. Create your first content!")
                    return

                # Summary stats
                completed = sum(1 for i in items if i["status"] == "completed")
                failed = sum(1 for i in items if i["status"] == "failed")

                stat_cols = st.columns(3)
                with stat_cols[0]:
                    st.metric("Total", len(items))
                with stat_cols[1]:
                    st.metric("✅ Completed", completed)
                with stat_cols[2]:
                    st.metric("❌ Failed", failed)

                st.divider()

                # Content list
                for item in items:
                    topic = item["request"]["topic"][:60]
                    status = item["status"]
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
                            st.markdown(f"**Type:** {item['request']['content_type']}")
                            st.markdown(f"**Status:** {status}")
                            st.markdown(f"**ID:** `{item['id'][:8]}...`")
                        with col2:
                            if item.get("processing_time_seconds"):
                                st.metric("Time", f"{item['processing_time_seconds']:.1f}s")

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
                                                "📥 Export",
                                                data=exp_response.content,
                                                file_name="content.md",
                                                key=f"export_{item['id']}",
                                            )
                                except Exception:
                                    pass

                            with action_cols[1]:
                                if st.button("🗑️ Delete", key=f"delete_{item['id']}"):
                                    delete_content(item["id"])
            else:
                st.warning("Could not load history")
    except httpx.ConnectError:
        st.info("🔌 API server not available. Start the server to view history.")
    except Exception as e:
        st.error(f"Error loading history: {e}")


def delete_content(content_id: str):
    """Delete content by ID."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.delete(f"{API_BASE_URL}/content/{content_id}")
            if response.status_code == 200:
                st.success("✅ Content deleted!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Failed to delete content")
    except Exception as e:
        st.error(f"Delete error: {e}")


def dashboard_tab():
    """Dashboard/analytics tab."""
    st.header("📊 Dashboard")

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
        st.metric("📄 Total Content", total)
    with col2:
        st.metric("✅ Completed", completed)
    with col3:
        st.metric("⏱️ Avg. Time", f"{avg_time:.1f}s")
    with col4:
        st.metric("📈 Success Rate", f"{success_rate:.0f}%")

    if not items:
        st.info("📝 Dashboard metrics will populate once you start generating content.")
        return

    st.divider()

    # Content type distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Content by Type")
        type_counts = {}
        for item in items:
            ct = item["request"]["content_type"]
            type_counts[ct] = type_counts.get(ct, 0) + 1

        if type_counts:
            import pandas as pd

            df = pd.DataFrame(list(type_counts.items()), columns=["Type", "Count"])
            st.bar_chart(df.set_index("Type"))

    with col2:
        st.subheader("📊 Status Distribution")
        status_counts = {}
        for item in items:
            s = item["status"]
            status_counts[s] = status_counts.get(s, 0) + 1

        if status_counts:
            import pandas as pd

            df = pd.DataFrame(list(status_counts.items()), columns=["Status", "Count"])
            st.bar_chart(df.set_index("Status"))

    # Recent activity
    st.divider()
    st.subheader("📅 Recent Activity")

    recent = items[:5]
    for item in recent:
        status_emoji = (
            "✅"
            if item["status"] == "completed"
            else ("❌" if item["status"] == "failed" else "⏳")
        )
        topic = item["request"]["topic"][:50]
        time_str = item.get("processing_time_seconds")
        time_display = f" ({time_str:.1f}s)" if time_str else ""

        st.markdown(f"- {status_emoji} **{topic}...**{time_display}")


if __name__ == "__main__":
    main()
