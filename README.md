# 🇻🇳 Vietnam Today News Dashboard (AI Vibe Coding)

Visual Studio Code와 **Google Gemini MCP (`@houtini/gemini-mcp`)**를 연동하여 베트남 주요 언론사의 오늘자 최신 뉴스를 실시간 수집하고, **전체 뉴스 내용을 100% 한글로 번역·요약**하며 **AI 모델 및 뉴스 수집 사이트를 웹에서 직접 설정**할 수 있는 대시보드 프로젝트입니다.

---

## 📌 주요 작업 및 업데이트 내역

### 1. 우측 상단 `⚙️ 설정` 기능 추가 (AI 모델 & 뉴스 수집 사이트 관리)
- **버튼 배치**: 대시보드 우측 상단 `실시간 뉴스 새로고침` 버튼 왼쪽에 `⚙️ 설정` 버튼 배치
- **AI 모델 설정**:
  - `gemini-4-argon`, `gemini-3.8-flash`, `gemini-3.1-pro-preview`, `gemini-3-flash-preview`, `gemini-3.5-flash` 선택 또는 사용자 정의 모델명 직접 입력 지원
  - 선택한 AI 모델이 Gemini MCP 브리핑 및 상태 배지에 실시간 반영
- **뉴스 수집 인터넷 사이트 주소 설정**:
  - 사이트 이름, 카테고리(속보·종합 / 경제·비즈니스 / 하노이·로컬 / 사회·로컬 / IT·과학 / 문화·라이프), 인터넷 주소(RSS 피드 URL 또는 일반 웹 페이지 URL) 추가·수정·삭제 지원
  - 설정 저장 시 `VietnamNews/config.json`에 영구 반영되며 즉시 뉴스 재수집 및 한글 번역 수행

### 2. 대시보드 표시 뉴스 전체 한글화 (100% 한국어 번역 및 정제)
- **일괄 자동 한글 번역 파이프라인**: 수집된 모든 베트남 뉴스 제목과 요약문을 일괄 한국어로 번역
- **베트남 고유명사 및 용어 한글 정제 (`polish_korean_text`)**:
  - 언론사명(`VN익스프레스`, `뚜오이째`, `탄니엔`), 주요 지역명(`하노이`, `껀터`, `달랏`, `람동`, `꽝찌` 등) 및 영문 병기 문구를 자연스러운 한글 표현으로 정제
  - 뉴스 카드에서 외국어 원문 노출을 제거하고 제목·요약·언론사·브리핑 전 영역을 한글로만 깔끔하게 표시

### 3. 백엔드 및 REST API (`VietnamNews/app.py`, `VietnamNews/mcp_client.py`)
- `GET /` : 메인 웹 대시보드 페이지 렌더링
- `GET /api/news` : 한글 번역된 최신 뉴스 목록, AI 브리핑, MCP 상태, 현재 설정 정보 반환 (`?refresh=1`로 강제 갱신 지원)
- `GET /api/config` : 현재 설정된 AI 모델 및 뉴스 수집 사이트 목록(`config.json`) 조회
- `POST /api/config` : AI 모델 및 뉴스 수집 사이트 설정 저장 후 즉시 뉴스 재수집·한글 번역 수행
- `POST /api/refresh` : 뉴스 피드 및 브리핑 강제 갱신
- `GET /api/mcp-status` : Gemini MCP 서버 실시간 연결 상태 및 활성 모델 정보 반환

### 4. 프론트엔드 웹 대시보드 (`templates/index.html`, `static/style.css`, `static/app.js`)
- **상단 헤더**: Gemini MCP 실시간 연결 상태 배지 + `⚙️ 설정` 버튼 + `↻ 실시간 뉴스 새로고침` 버튼
- **AI 핵심 브리핑 배너**: 현재 설정된 AI 모델 표시 및 오늘의 베트남 핵심 뉴스 브리핑 제공
- **카테고리 탭 및 실시간 한글 검색**: 분야별 즉시 필터링 및 한글 키워드 검색
- **하단 푸터**: `ZEROHS.COM / Made by AI Vibe Coding`

---

## 📂 디렉토리 구조

```text
AiCoding/
├── README.md
└── VietnamNews/
    ├── README.md
    ├── app.py                 # Python HTTP 대시보드 서버 및 설정/뉴스 API (Port: 8088)
    ├── mcp_client.py          # Gemini MCP 클라이언트, 사이트 수집기 및 한글 번역/정제 모듈
    ├── config.json            # 사용자 설정 파일 (AI 모델 및 뉴스 수집 사이트 URL 목록)
    ├── news_cache.json        # 한글 번역 완료된 최신 뉴스 캐시 데이터
    ├── templates/
    │   └── index.html         # 대시보드 메인 웹 페이지 및 설정 모달 UI
    └── static/
        ├── style.css          # 모던 다크 테마 반응형 스타일시트 및 모달 스타일
        └── app.js             # 프론트엔드 렌더링, 필터/검색, 설정 모달 제어 스크립트
```

---

## 🚀 실행 방법

```bash
cd /home/zerohs/GitHub/AiCoding/VietnamNews
python3 app.py
```

웹 브라우저에서 **`http://127.0.0.1:8088`** 접속

---

**ZEROHS.COM / Made by AI Vibe Coding**
