# 🚀 ContentForge AI

> **Multi-Agent AI Content Creation Platform** powered by LangGraph and MCP

ContentForge AI is a next-generation content creation platform that leverages multiple specialized AI agents to automate the entire content production workflow - from research to publication-ready content.

## ✨ Key Features

- **🤖 Multi-Agent Pipeline**: 7 specialized AI agents collaborating to produce high-quality content
- **🔗 MCP Integration**: Connect to 250+ tools via Model Context Protocol
- **⚡ Fast Generation**: Create publication-ready content in minutes
- **🎨 Multiple Content Types**: Blog posts, articles, social media, emails, and more
- **🌍 Multilingual**: Support for English, Korean, Japanese, Chinese, and more
- **📊 SEO Optimization**: Built-in keyword optimization and metadata generation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Input                        │
│           "Write about AI marketing"                │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│                 LangGraph Pipeline                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │Researcher│→ │  Writer  │→ │     Editor       │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│           MCP Tool Layer (External Tools)            │
│  [Fetch] [Memory] [Browser] [Notion] [Slack] ...    │
└─────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Anthropic API key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourorg/contentforge-ai.git
cd contentforge-ai

# Install dependencies with uv
uv sync

# Copy environment template
cp .env.example .env

# Add your API keys to .env
# ANTHROPIC_API_KEY=your_key_here
```

### Running the API Server

```bash
# Start the FastAPI server
uv run uvicorn src.api.main:app --reload

# API will be available at http://localhost:8000
# Documentation at http://localhost:8000/docs
```

### Running the Streamlit UI

```bash
# In a new terminal
uv run streamlit run ui/app.py

# UI will be available at http://localhost:8501
```

## 📖 API Usage

### Generate Content

```bash
curl -X POST "http://localhost:8000/api/v1/content/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "How AI is transforming content marketing in 2025",
    "content_type": "blog_post",
    "tone": "professional",
    "word_count": 1500,
    "keywords": ["AI content", "marketing automation"]
  }'
```

### Python Client

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/v1/content/generate",
    json={
        "topic": "AI content marketing trends",
        "content_type": "blog_post",
        "tone": "professional",
    },
    timeout=300.0,
)

content = response.json()
print(content["content"])
```

## 🤖 Agent Pipeline

| Agent | Role |
|-------|------|
| 🔍 **Researcher** | Gathers facts, statistics, and insights about the topic |
| 📋 **Planner** | Creates content outline and structure |
| ✍️ **Writer** | Writes the initial draft with storytelling |
| ✨ **Editor** | Polishes grammar, flow, and clarity |
| 🔎 **SEO Optimizer** | Optimizes keywords and metadata |
| 🎨 **Visual Creator** | Generates images and graphics |
| 📊 **Trend Analyst** | Analyzes current trends and competition |

## 🛠️ Development

### Project Structure

```
contentforge-ai/
├── src/
│   ├── agents/          # LangGraph agents
│   ├── workflows/       # LangGraph pipelines
│   ├── mcp/            # MCP server integration
│   ├── api/            # FastAPI application
│   └── models/         # Pydantic models
├── ui/                 # Streamlit UI
├── tests/              # Test suite
└── pyproject.toml      # Project configuration
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy src
```

## 📊 Market Opportunity

- **2025 Market Size**: $6.14B
- **2034 Projection**: $63.25B
- **CAGR**: 29.57%

## 🗺️ Roadmap

- [x] MVP with core 3 agents (Researcher, Writer, Editor)
- [ ] Full 7-agent pipeline
- [ ] MCP server integrations
- [ ] User authentication
- [ ] Team collaboration
- [ ] API billing system
- [ ] Chrome extension

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

---

Built with ❤️ using [LangGraph](https://langchain-ai.github.io/langgraph/) and [MCP](https://modelcontextprotocol.io/)
