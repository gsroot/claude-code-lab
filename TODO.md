# 📋 ContentForge AI - TODO List

> 마지막 업데이트: 2025-12-10

---

## 📊 현재 프로젝트 상태

### ✅ 완료된 항목

| 카테고리 | 항목 | 파일 |
|----------|------|------|
| 프로젝트 설정 | pyproject.toml (uv) | `pyproject.toml` |
| 프로젝트 설정 | 환경 변수 템플릿 | `.env.example` |
| 프로젝트 설정 | 설정 관리 | `src/utils/config.py` |
| 에이전트 | BaseAgent 클래스 | `src/agents/base.py` |
| 에이전트 | ResearcherAgent | `src/agents/researcher.py` |
| 에이전트 | WriterAgent | `src/agents/writer.py` |
| 에이전트 | EditorAgent | `src/agents/editor.py` |
| 워크플로우 | ContentPipeline (LangGraph) | `src/workflows/content_pipeline.py` |
| MCP | MCPToolManager 클라이언트 | `src/mcp/client.py` |
| API | FastAPI 앱 | `src/api/main.py` |
| API | 콘텐츠 생성 라우트 | `src/api/routes/content.py` |
| 모델 | Content Pydantic 모델 | `src/models/content.py` |
| UI | Streamlit 기본 앱 | `ui/app.py` |
| 테스트 | 기본 테스트 구조 | `tests/` |
| 문서 | README.md (한국어) | `README.md` |
| 문서 | 서비스 기획서 | `SERVICE_PLAN.md` |

### 📈 진행률: **Phase 1 MVP - 약 60% 완료**

---

## 🚀 Phase 1: MVP (목표: 4주)

### Week 1-2: 핵심 인프라 (현재 단계)

#### 에이전트 구현
- [x] BaseAgent 클래스 구현
- [x] ResearcherAgent 구현
- [x] WriterAgent 구현
- [x] EditorAgent 구현
- [ ] **PlannerAgent 구현** - 콘텐츠 아웃라인 생성
  - 파일: `src/agents/planner.py`
  - 기능: 리서치 결과를 바탕으로 콘텐츠 구조 설계

#### MCP 연동
- [x] MCP 클라이언트 기본 구조
- [ ] **Fetch MCP 서버 실제 연동 테스트**
- [ ] **Memory MCP 서버 연동**
- [ ] **에이전트에 MCP 도구 주입**
  - ResearcherAgent에 Fetch 도구 연결
  - 웹 검색 기능 활성화

#### 워크플로우 개선
- [x] 기본 파이프라인 (Research → Write → Edit)
- [ ] **Planner 노드 추가** (Research → Plan → Write → Edit)
- [ ] **에러 처리 강화**
- [ ] **재시도 로직 추가**

### Week 3-4: MVP 기능

#### API 확장
- [x] 콘텐츠 생성 엔드포인트
- [x] 비동기 생성 엔드포인트
- [ ] **WebSocket 실시간 진행 상황 전송**
  - 파일: `src/api/routes/websocket.py`
- [ ] **콘텐츠 내보내기 (Markdown, HTML, PDF)**

#### 데이터베이스 연동
- [ ] **PostgreSQL 연동**
  - 파일: `src/db/database.py`
  - SQLAlchemy 모델 정의
- [ ] **Redis 캐시 연동**
  - 생성 결과 캐싱
  - Rate limiting
- [ ] **콘텐츠 영구 저장**
  - 현재: 인메모리 → 변경: DB 저장

#### 사용자 인증
- [ ] **JWT 인증 구현**
  - 파일: `src/api/routes/auth.py`
- [ ] **사용자 모델**
  - 파일: `src/models/user.py`
- [ ] **Supabase 또는 자체 인증**

#### UI 개선
- [x] Streamlit 기본 UI
- [ ] **실시간 생성 진행 표시**
- [ ] **콘텐츠 편집 기능**
- [ ] **히스토리 페이지 개선**
- [ ] **설정 페이지**
  - 파일: `ui/pages/settings.py`

#### 테스트
- [x] 기본 테스트 구조
- [ ] **에이전트 단위 테스트 확장**
- [ ] **워크플로우 통합 테스트**
- [ ] **API 엔드투엔드 테스트**
- [ ] **테스트 커버리지 80% 이상**

---

## 🔧 Phase 2: Beta (목표: 8주)

### Week 5-8: 전체 에이전트 구현

#### 추가 에이전트
- [ ] **TrendAnalystAgent**
  - 파일: `src/agents/trend_analyst.py`
  - 기능: 실시간 트렌드 분석, 인기 키워드 추출
  - MCP: 웹 검색, 소셜 미디어 API

- [ ] **SEOOptimizerAgent**
  - 파일: `src/agents/seo_optimizer.py`
  - 기능: 키워드 밀도 최적화, 메타 태그 생성
  - 출력: SEOMetadata 모델

- [ ] **VisualCreatorAgent**
  - 파일: `src/agents/visual_creator.py`
  - 기능: 이미지 프롬프트 생성, 썸네일 제안
  - 연동: DALL-E, Stable Diffusion API

#### 커스텀 MCP 서버
- [ ] **Trend MCP 서버**
  - 파일: `src/mcp/servers/trend_server.py`
  - 기능: Google Trends, Twitter API 래핑

- [ ] **SEO MCP 서버**
  - 파일: `src/mcp/servers/seo_server.py`
  - 기능: 키워드 분석, 경쟁사 분석

#### 에이전트 협업 로직
- [ ] **병렬 실행 구현**
  - Research + Trend Analysis 동시 실행
- [ ] **조건부 분기**
  - SEO 필요 여부에 따른 분기
- [ ] **Human-in-the-Loop**
  - 각 단계에서 사용자 승인/수정

### Week 9-12: 제품 완성도

#### 결제 시스템
- [ ] **Stripe 연동**
  - 파일: `src/api/routes/billing.py`
  - 파일: `src/services/billing_service.py`
- [ ] **구독 플랜 관리**
- [ ] **사용량 추적**
- [ ] **인보이스 생성**

#### 대시보드 & 분석
- [ ] **사용 통계 대시보드**
- [ ] **콘텐츠 성과 분석**
- [ ] **비용 추적**

#### 템플릿 시스템
- [ ] **템플릿 모델**
  - 파일: `src/models/template.py`
- [ ] **업종별 템플릿**
- [ ] **사용자 커스텀 템플릿**

#### 팀 협업
- [ ] **팀/워크스페이스 모델**
- [ ] **멤버 초대/권한 관리**
- [ ] **공유 콘텐츠 라이브러리**

---

## 🚢 Phase 3: Launch (목표: 4주)

### Week 13-14: 런칭 준비

#### 인프라
- [ ] **Docker 설정**
  - 파일: `docker/Dockerfile`
  - 파일: `docker/docker-compose.yml`
- [ ] **CI/CD 파이프라인**
  - GitHub Actions 설정
- [ ] **프로덕션 배포**
  - AWS/GCP/Vercel

#### 성능 최적화
- [ ] **응답 시간 최적화**
- [ ] **동시 요청 처리**
- [ ] **LLM 비용 최적화**

#### 보안
- [ ] **보안 감사**
- [ ] **Rate Limiting 강화**
- [ ] **입력 검증 강화**
- [ ] **OWASP Top 10 점검**

#### 문서화
- [ ] **API 문서 완성**
- [ ] **사용자 가이드**
- [ ] **개발자 문서**

### Week 15-16: 퍼블릭 런칭

#### 마케팅
- [ ] **랜딩 페이지**
- [ ] **ProductHunt 런칭**
- [ ] **프레스 릴리스**

#### 운영
- [ ] **모니터링 설정**
  - Sentry, DataDog 등
- [ ] **알림 시스템**
- [ ] **백업 시스템**

---

## 📁 생성 필요 파일 목록

### 에이전트
```
src/agents/
├── planner.py          # Week 1-2
├── trend_analyst.py    # Week 5-8
├── seo_optimizer.py    # Week 5-8
└── visual_creator.py   # Week 5-8
```

### API
```
src/api/routes/
├── auth.py             # Week 3-4
├── billing.py          # Week 9-12
└── websocket.py        # Week 3-4
```

### 모델
```
src/models/
├── user.py             # Week 3-4
├── workflow.py         # Week 3-4
└── template.py         # Week 9-12
```

### 서비스
```
src/services/
├── content_service.py  # Week 3-4
├── user_service.py     # Week 3-4
└── billing_service.py  # Week 9-12
```

### MCP 서버
```
src/mcp/servers/
├── trend_server.py     # Week 5-8
└── seo_server.py       # Week 5-8
```

### 데이터베이스
```
src/db/
├── database.py         # Week 3-4
├── models.py           # Week 3-4
└── migrations/         # Week 3-4
```

### 인프라
```
docker/
├── Dockerfile          # Week 13-14
└── docker-compose.yml  # Week 13-14

.github/workflows/
└── ci.yml              # Week 13-14
```

### UI 페이지
```
ui/pages/
├── settings.py         # Week 3-4
└── analytics.py        # Week 9-12
```

---

## 🎯 이번 주 우선순위 (즉시 실행)

### 높음 (High)
1. [ ] PlannerAgent 구현
2. [ ] MCP Fetch 서버 실제 연동 테스트
3. [ ] 워크플로우에 Planner 노드 추가
4. [ ] 에이전트 테스트 확장

### 중간 (Medium)
5. [ ] WebSocket 실시간 진행 상황
6. [ ] PostgreSQL 연동 시작
7. [ ] UI 실시간 진행 표시

### 낮음 (Low)
8. [ ] 문서 개선
9. [ ] 코드 리팩토링
10. [ ] 로깅 시스템 개선

---

## 📝 메모

### 기술적 고려사항
- LangGraph 버전 호환성 확인 필요
- MCP 어댑터 최신 버전 확인
- Anthropic API 비용 모니터링 설정

### 비즈니스 고려사항
- Beta 테스터 10명 모집 계획
- 초기 가격 정책 확정
- 경쟁사 모니터링

---

*이 문서는 프로젝트 진행에 따라 지속적으로 업데이트됩니다.*
