# 🚀 Content Mate

> LangGraph와 MCP 기반의 **멀티 에이전트 AI 콘텐츠 제작 플랫폼**

Content Mate는 여러 전문화된 AI 에이전트를 활용하여 리서치부터 발행 가능한 콘텐츠까지 전체 제작 워크플로우를 자동화하는 차세대 콘텐츠 제작 플랫폼입니다.

## ✨ 주요 기능

- **🤖 멀티 에이전트 파이프라인**: 7개의 전문 AI 에이전트가 협업하여 고품질 콘텐츠 생산
- **🔗 MCP 통합**: Model Context Protocol을 통해 250개 이상의 도구와 연동
- **⚡ 빠른 생성**: 몇 분 만에 발행 가능한 콘텐츠 생성
- **🎨 다양한 콘텐츠 유형**: 블로그 포스트, 아티클, 소셜 미디어, 이메일 등 지원
- **🌍 다국어 지원**: 한국어, 영어, 일본어, 중국어 등 지원
- **📊 SEO 최적화**: 키워드 최적화 및 메타데이터 자동 생성

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                    사용자 입력                        │
│           "AI 마케팅에 대한 글 작성해줘"               │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│                 LangGraph 파이프라인                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ 리서처   │→ │  작성자  │→ │      편집자      │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│            MCP 도구 레이어 (외부 도구 연동)            │
│  [Fetch] [Memory] [Browser] [Notion] [Slack] ...    │
└─────────────────────────────────────────────────────┘
```

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 패키지 관리자
- Anthropic API 키

### 설치

```bash
# 저장소 클론
git clone https://github.com/yourorg/content-mate.git
cd content-mate

# uv로 의존성 설치
uv sync

# 환경 변수 템플릿 복사
cp .env.example .env

# .env 파일에 API 키 입력
# ANTHROPIC_API_KEY=your_key_here
```

### API 서버 실행

```bash
# FastAPI 서버 시작
uv run uvicorn src.api.main:app --reload

# API 주소: http://localhost:8000
# API 문서: http://localhost:8000/docs
```

### Streamlit UI 실행

```bash
# 새 터미널에서 실행
uv run streamlit run ui/app.py

# UI 주소: http://localhost:8501
```

## 📖 API 사용법

### 콘텐츠 생성

```bash
curl -X POST "http://localhost:8000/api/v1/content/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "2025년 AI가 콘텐츠 마케팅을 혁신하는 방법",
    "content_type": "blog_post",
    "tone": "professional",
    "word_count": 1500,
    "language": "ko",
    "keywords": ["AI 콘텐츠", "마케팅 자동화"]
  }'
```

### Python 클라이언트

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/v1/content/generate",
    json={
        "topic": "AI 콘텐츠 마케팅 트렌드",
        "content_type": "blog_post",
        "tone": "professional",
        "language": "ko",
    },
    timeout=300.0,
)

content = response.json()
print(content["content"])
```

## 🤖 에이전트 파이프라인

| 에이전트                 | 역할                                  |
| ------------------------ | ------------------------------------- |
| 🔍 **리서처**            | 주제에 대한 사실, 통계, 인사이트 수집 |
| 📋 **플래너**            | 콘텐츠 아웃라인 및 구조 설계          |
| ✍️ **라이터**            | 스토리텔링을 적용한 초안 작성         |
| ✨ **에디터**            | 문법, 흐름, 명확성 교정               |
| 🔎 **SEO 옵티마이저**    | 키워드 및 메타데이터 최적화           |
| 🎨 **비주얼 크리에이터** | 이미지 및 그래픽 생성                 |
| 📊 **트렌드 분석가**     | 현재 트렌드 및 경쟁사 분석            |

## 🛠️ 개발 가이드

### 프로젝트 구조

```
content-mate/
├── src/
│   ├── agents/          # LangGraph 에이전트
│   ├── workflows/       # LangGraph 파이프라인
│   ├── mcp/            # MCP 서버 연동
│   ├── api/            # FastAPI 애플리케이션
│   └── models/         # Pydantic 모델
├── ui/                 # Streamlit UI
├── tests/              # 테스트
└── pyproject.toml      # 프로젝트 설정
```

### 테스트 실행

```bash
# 전체 테스트 실행
uv run pytest

# 커버리지 포함 테스트
uv run pytest --cov=src --cov-report=html
```

### 코드 품질

```bash
# 코드 포맷팅
uv run ruff format .

# 린트 검사
uv run ruff check .

# 타입 체크
uv run mypy src
```

## 📊 시장 기회

| 지표                 | 수치                    |
| -------------------- | ----------------------- |
| 2025년 시장 규모     | **$6.14B** (약 8조원)   |
| 2034년 예상 규모     | **$63.25B** (약 84조원) |
| 연평균 성장률 (CAGR) | **29.57%**              |

## 🗺️ 로드맵

- [x] 핵심 3개 에이전트 MVP (리서처, 라이터, 에디터)
- [ ] 전체 7개 에이전트 파이프라인
- [ ] MCP 서버 연동 확장
- [ ] 사용자 인증 시스템
- [ ] 팀 협업 기능
- [ ] API 과금 시스템
- [ ] Chrome 확장 프로그램

## 📄 라이선스

MIT 라이선스 - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🤝 기여하기

기여를 환영합니다! 먼저 [Contributing Guide](CONTRIBUTING.md)를 읽어주세요.

---

[LangGraph](https://langchain-ai.github.io/langgraph/)와 [MCP](https://modelcontextprotocol.io/)를 사용하여 ❤️로 만들었습니다
