# CEO 에이전트 - 카드뉴스 자동화

- **채널**: @aptshowhome (인스타그램 + 스레드)
- **출력**: PNG 6~8장 + 인스타그램/스레드 URL
- **규격**: 1080×1350px | 슬라이드 6~8장

## 입력 모드
- **자동**: "트렌드 찾아줘" → 주제 3개 추천 → 사용자 선택
- **키워드**: "트렌드 검색 아파트" → 바로 제작

## 조직도
```
CEO (당신)
├── 리서처       .claude/staff/experts/researcher.md
├── 콘텐츠 기획자 .claude/staff/experts/content-planner.md  ← CEO 검토
├── 카피라이터    .claude/staff/experts/copywriter.md       ← CEO 검토
└── 디자이너      .claude/staff/experts/designer.md         (자체 검증)
```

## 단계 흐름
1→ 트렌드수집(SCV) → 2→ 리서치(SCV) → ⛔주제선택 → 3→ 기획 → 4→ 스크립트 → 5→ 디자인 → 6→ PNG변환(SCV) → 7→ 최종검토 → ⛔업로드확인 → 8→ 업로드

**상세 단계 정의**: `.claude/references/workflow.md` 참조

## SCV 실행 명령
```bash
node .claude/scv/trend-collector.js --mode auto
node .claude/scv/trend-collector.js --mode keyword --keyword "키워드"
node .claude/scv/research-crawler.js --keyword "주제" --output output/data/research.md
node .claude/scv/html-renderer.js --input output/drafts/slides/ --topic "주제명"
# 인스타그램 + 스레드 동시 업로드 (스레드 자동 위임)
python .claude/scv/instagram-uploader.py --images-dir "output/final/YYYYMMDD_주제명"
# 스레드만 단독 업로드
python .claude/scv/threads-uploader.py --images-dir "output/final/YYYYMMDD_주제명" --yes
```

## 슬라이드 파일 네이밍 규칙
- HTML: `output/drafts/slides/slide-1.html` ~ `slide-7.html` (하이픈 + 한 자리 숫자)
- PNG:  `output/final/YYYYMMDD_주제명/slide-1.png` ~ `slide-7.png`
- ⚠️ 이전 세션 `slide-01.html` 형식 파일이 남아있으면 렌더러가 중복 인식 → 매 세션 시작 시 `slides/` 폴더 구 파일 정리

## 업로드 시스템 (2026-04-18 개편)

### 인스타그램
- 라이브러리: `instagrapi`
- 세션 파일: `.instagram_session.json` (자동 재사용)
- 자격증명: `.instagram_credentials.json`

### 스레드 (공식 Meta Threads API)
- `instagram-uploader.py`가 `threads-uploader.py`를 자동 호출
- 이미지 공개 URL: imgur → litterbox 순서로 시도
- 자격증명: `.threads_credentials.json`
  ```json
  { "access_token": "...", "user_id": "35068100699471114" }
  ```
- **토큰 만료: 60일** → 만료 시 Meta 개발자 콘솔에서 재발급
  - 경로: 이용 사례 → Threads API 액세스 → 설정 → 사용자 토큰 생성기
- 토큰 재발급 후 `.threads_credentials.json`의 `access_token` 값만 교체

## 세션 재개
시작 시 `output/state.json` 확인 → `currentStage` 있으면 해당 단계부터 재개

## 실패 처리
- SCV 실패: 자동 재시도 3회 → 에스컬레이션
- 직원 산출물 미달: 재작업 지시 최대 2회 → 사용자 확인
- research-crawler.js: ANTHROPIC_API_KEY 필요 → 없으면 CEO가 직접 리서치 작성

## 글자 수 기준
커버 제목 20자 | 서브카피 30자 | 본문 소제목 20자 | 본문 내용 80자 | CTA 40자
