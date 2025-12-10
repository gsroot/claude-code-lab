"""Settings page for ContentForge AI."""

import httpx
import streamlit as st

st.set_page_config(
    page_title="Settings - ContentForge AI",
    page_icon="⚙️",
    layout="wide",
)

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"


def main():
    """Settings page main function."""
    st.title("⚙️ Settings")
    st.markdown("Configure your ContentForge AI experience")

    # Tabs for different settings sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔌 API Connection",
        "🤖 Generation Defaults",
        "🎨 Appearance",
        "ℹ️ About",
    ])

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
    st.header("🔌 API Connection")

    # Current API URL
    st.subheader("API Server")

    col1, col2 = st.columns([3, 1])

    with col1:
        api_url = st.text_input(
            "API Base URL",
            value=API_BASE_URL.replace("/api/v1", ""),
            help="The base URL of your ContentForge API server",
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Test Connection"):
            test_api_connection(api_url)

    # Connection status
    st.subheader("Connection Status")

    try:
        with httpx.Client(timeout=5.0) as client:
            # Health check
            health_response = client.get(f"{api_url}/health")
            if health_response.status_code == 200:
                st.success("✅ API Server: Connected")

                # Get API info
                root_response = client.get(f"{api_url}/")
                if root_response.status_code == 200:
                    info = root_response.json()
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("API Name", info.get("name", "N/A"))
                    with col2:
                        st.metric("Version", info.get("version", "N/A"))
                    with col3:
                        st.metric("Status", info.get("status", "N/A").title())
            else:
                st.error("❌ API Server: Not responding correctly")
    except httpx.ConnectError:
        st.error("❌ API Server: Cannot connect")
        st.info("""
        **To start the API server:**
        ```bash
        uv run uvicorn src.api.main:app --reload
        ```
        """)
    except Exception as e:
        st.error(f"❌ Connection error: {e}")

    # WebSocket settings
    st.subheader("WebSocket Connection")
    ws_url = st.text_input(
        "WebSocket URL",
        value=f"ws://localhost:8000/api/v1",
        help="WebSocket URL for real-time progress updates",
    )
    st.info("WebSocket connection is used for real-time generation progress updates.")


def test_api_connection(api_url: str):
    """Test API connection."""
    with st.spinner("Testing connection..."):
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{api_url}/health")
                if response.status_code == 200:
                    st.success("✅ Connection successful!")
                else:
                    st.error(f"❌ Server returned status {response.status_code}")
        except httpx.ConnectError:
            st.error("❌ Cannot connect to server")
        except Exception as e:
            st.error(f"❌ Error: {e}")


def generation_defaults():
    """Default generation settings."""
    st.header("🤖 Generation Defaults")
    st.markdown("Set default values for content generation")

    # Initialize session state for defaults
    if "default_content_type" not in st.session_state:
        st.session_state.default_content_type = "blog_post"
    if "default_tone" not in st.session_state:
        st.session_state.default_tone = "professional"
    if "default_word_count" not in st.session_state:
        st.session_state.default_word_count = 1500
    if "default_language" not in st.session_state:
        st.session_state.default_language = "en"

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Content Settings")

        default_type = st.selectbox(
            "Default Content Type",
            ["blog_post", "article", "social_media", "email", "landing_page"],
            index=["blog_post", "article", "social_media", "email", "landing_page"].index(
                st.session_state.default_content_type
            ),
            format_func=lambda x: {
                "blog_post": "📝 Blog Post",
                "article": "📰 Article",
                "social_media": "📱 Social Media",
                "email": "✉️ Email",
                "landing_page": "🌐 Landing Page",
            }.get(x, x),
        )

        default_tone = st.selectbox(
            "Default Tone",
            ["professional", "casual", "educational", "persuasive", "entertaining"],
            index=["professional", "casual", "educational", "persuasive", "entertaining"].index(
                st.session_state.default_tone
            ),
        )

        default_word_count = st.slider(
            "Default Word Count",
            min_value=100,
            max_value=5000,
            value=st.session_state.default_word_count,
            step=100,
        )

    with col2:
        st.subheader("Language & Localization")

        default_language = st.selectbox(
            "Default Language",
            ["en", "ko", "ja", "zh", "es", "fr", "de"],
            index=["en", "ko", "ja", "zh", "es", "fr", "de"].index(
                st.session_state.default_language
            ),
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

        st.markdown("---")
        st.subheader("Generation Options")

        include_research = st.checkbox("Include research findings in output", value=True)
        include_outline = st.checkbox("Show content outline", value=True)
        auto_export = st.checkbox("Auto-download after generation", value=False)

    # Save button
    st.divider()
    if st.button("💾 Save Defaults", type="primary"):
        st.session_state.default_content_type = default_type
        st.session_state.default_tone = default_tone
        st.session_state.default_word_count = default_word_count
        st.session_state.default_language = default_language
        st.success("✅ Settings saved!")


def appearance_settings():
    """Appearance settings."""
    st.header("🎨 Appearance")

    st.subheader("Theme")
    theme = st.selectbox(
        "Color Theme",
        ["System Default", "Light", "Dark"],
        help="Note: Theme changes may require app restart",
    )

    st.info("""
    **To change Streamlit theme:**

    Create or edit `.streamlit/config.toml`:
    ```toml
    [theme]
    primaryColor = "#1E88E5"
    backgroundColor = "#FFFFFF"
    secondaryBackgroundColor = "#F0F2F6"
    textColor = "#262730"
    ```
    """)

    st.subheader("Display Options")

    col1, col2 = st.columns(2)

    with col1:
        show_api_status = st.checkbox("Show API status indicator", value=True)
        show_word_count = st.checkbox("Show word count in results", value=True)
        show_processing_time = st.checkbox("Show processing time", value=True)

    with col2:
        expand_outline = st.checkbox("Auto-expand outline section", value=False)
        expand_research = st.checkbox("Auto-expand research section", value=False)
        compact_history = st.checkbox("Compact history view", value=False)


def about_section():
    """About section."""
    st.header("ℹ️ About ContentForge AI")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### 🚀 ContentForge AI

        **Multi-Agent AI Content Creation Platform**

        ContentForge AI uses a pipeline of specialized AI agents to create
        high-quality content:

        1. **🔍 Researcher Agent** - Gathers facts and information
        2. **📋 Planner Agent** - Creates structured outlines
        3. **✍️ Writer Agent** - Writes engaging content
        4. **✨ Editor Agent** - Polishes and refines

        Built with:
        - **LangGraph** - Multi-agent orchestration
        - **MCP** - Model Context Protocol for tools
        - **FastAPI** - High-performance API
        - **Streamlit** - Interactive UI
        """)

    with col2:
        st.markdown("### 📊 System Info")

        # Try to get API version
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{API_BASE_URL.replace('/api/v1', '')}/")
                if response.status_code == 200:
                    info = response.json()
                    st.metric("API Version", info.get("version", "N/A"))
        except Exception:
            st.metric("API Version", "N/A")

        st.metric("UI Version", "0.1.0")
        st.metric("Python", "3.11+")

    st.divider()

    st.markdown("### 📚 Documentation")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **API Documentation**
        - [OpenAPI Docs](/docs)
        - [ReDoc](/redoc)
        """)

    with col2:
        st.markdown("""
        **Resources**
        - [GitHub Repository](https://github.com)
        - [Issue Tracker](https://github.com)
        """)

    with col3:
        st.markdown("""
        **Support**
        - [Discord Community](#)
        - [Email Support](#)
        """)

    st.divider()

    st.markdown("### 📄 License")
    st.markdown("""
    ContentForge AI is released under the **MIT License**.

    Copyright © 2025 ContentForge Team
    """)


if __name__ == "__main__":
    main()
