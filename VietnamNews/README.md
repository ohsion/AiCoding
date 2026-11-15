# 🇻🇳 Vietnam Today News Dashboard (AI Vibe Coding)

Visual Studio Code와 **Google Gemini MCP (`@houtini/gemini-mcp`)**를 연동하여 베트남 주요 언론사의 오늘자 최신 뉴스를 실시간 수집하고, 한국어 번역·요약 및 AI 핵심 브리핑을 웹 페이지 형태로 제공하는 대시보드 프로젝트입니다.

---

## 📌 주요 작업 및 구현 내용

### 1. 개발 환경 및 Gemini MCP 연동 설정
- **Visual Studio Code 연동**: `AiCoding` 워크스페이스 내 MCP 서버 설정 구성
- **Gemini MCP 서버 구축**: `@houtini/gemini-mcp` (v2.10.1) 글로벌 설치 및 JSON-RPC 2.0 (stdio) 프로토콜 연동 완료 (14개 Gemini MCP 도구 활성화)

### 2. 백엔드 시스템 구현 (`VietnamNews/app.py`, `VietnamNews/mcp_client.py`)
- **실시간 베트남 뉴스 RSS 수집**:
  - 주요 언론사: **VnExpress**, **Tuổi Trẻ**
  - 수집 분야: 속보·종합(`latest`), 경제·비즈니스(`economy`), 하노이·로컬(`hanoi`), 사회(`society`), IT·과학(`tech`), 문화·라이프(`culture`)
- **Gemini MCP 브리핑 및 한국어 번역 연동**:
  - `GeminiMCPClient`를 통해 MCP 서버 상태 확인(`initialize`, `tools/list`) 및 `gemini_chat` 도구 호출을 통한 오늘자 핵심 이슈 요약 브리핑 생성
  - 베트남어 원문 제목/요약과 한국어 번역 제목/요약을 함께 제공하며 빠른 응답을 위한 로컬 캐시(`news_cache.json`) 지원
- **REST API 엔드포인트**:
  - `GET /` : 메인 웹 대시보드 페이지 제공
  - `GET /api/news` : 수집된 뉴스 목록, AI 브리핑, MCP 상태 JSON 반환 (`?refresh=1` 파라미터로 실시간 재수집 지원)
  - `POST /api/refresh` : 뉴스 피드 및 브리핑 강제 갱신
  - `GET /api/mcp-status` : Gemini MCP 서버 실시간 연결 상태 반환

### 3. 프론트엔드 웹 대시보드 구현 (`templates/index.html`, `static/style.css`, `static/app.js`)
- **상단 상태 바**: Gemini MCP 실시간 연결 배지 및 `실시간 뉴스 새로고침` 버튼
- **AI 핵심 브리핑 섹션**: 오늘의 베트남 핵심 뉴스 요약 및 주요 하이라이트 배너
- **카테고리 탭 및 실시간 검색**: 분야별 즉시 필터링 및 한국어/베트남어 키워드 실시간 검색
- **반응형 뉴스 카드 그리드**: 썸네일 이미지, 언론사/카테고리 태그, 발행 시간, 한국어 제목·요약 및 베트남어 원문 병기, 원문 기사 바로가기 링크 제공
- **커스텀 푸터 적용**: `ZEROHS.COM / Made by AI Vibe Coding`

---

## 📂 디렉토리 구조

```text
AiCoding/
├── README.md
└── VietnamNews/
    ├── README.md
    ├── app.py                 # Python HTTP 대시보드 서버 (Port: 8088)
    ├── mcp_client.py          # Gemini MCP 클라이언트 및 베트남 RSS 수집/번역 모듈
    ├── news_cache.json        # 수집 및 번역된 최신 뉴스 캐시 데이터
    ├── templates/
    │   └── index.html         # 대시보드 웹 페이지 템플릿
    └── static/
        ├── style.css          # 모던 다크 테마 반응형 스타일시트
        └── app.js             # 프론트엔드 동적 렌더링 및 필터/검색 스크립트
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
