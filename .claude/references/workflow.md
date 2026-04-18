# 워크플로우 상세 — 단계별 정의

> CLAUDE.md 요약에서 참조. CEO가 각 단계 진행 전 이 파일을 읽어 확인합니다.

---

## 1단계: 트렌드 수집 (리서처 + SCV)

| 항목 | 내용 |
|------|------|
| 담당 | 리서처 + SCV(trend-collector.js) |
| 출력 | `output/data/trend-data.json` |
| 성공 | 채널별 트렌드 3개 이상. 자동 모드 시 추천 주제 3개 포함 |
| 실패 | SCV 재시도 3회 → 에스컬레이션 |

```
node .claude/scv/trend-collector.js --mode [auto/keyword] --keyword "..."
```

⛔ **자동 모드 분기**: 추천 주제 3개 제시 → 사용자 선택 → state.json 저장 → 2단계

---

## 2단계: 자료 리서치 (리서처 + SCV)

| 항목 | 내용 |
|------|------|
| 담당 | 리서처 + SCV(research-crawler.js) |
| 출력 | `output/data/research.md` |
| 성공 | 인사이트 3건 이상 |
| 실패 | 키워드 변경 후 재시도 2회 |

```
node .claude/scv/research-crawler.js --keyword "주제" --output output/data/research.md
```

---

## 3단계: 슬라이드 기획 (콘텐츠 기획자) ← CEO 검토

| 항목 | 내용 |
|------|------|
| 담당 | 콘텐츠 기획자 |
| 입력 | `output/data/trend-data.json`, `output/data/research.md` |
| 참조 | `.claude/references/brand-guide.md`, `.claude/references/slide-templates.md` |
| 출력 | `output/drafts/content-plan.md` |
| 성공 | 6~8장 구조, 각 슬라이드 핵심 메시지 명확 |

---

## 4단계: 스크립트 작성 (카피라이터) ← CEO 검토

| 항목 | 내용 |
|------|------|
| 담당 | 카피라이터 |
| 입력 | `output/drafts/content-plan.md` |
| 참조 | `.claude/references/brand-guide.md`, `.claude/references/tone-guide.md` |
| 출력 | `output/drafts/script.md`, `output/drafts/hashtags.md` |
| 성공 | 글자 수 충족, 톤 일관, 해시태그 15~30개 |

**글자 수**: 커버제목 20 | 서브카피 30 | 본문소제목 20 | 본문 80 | CTA 40

---

## 5단계: 디자인 (디자이너) — CEO 게이트 없음

| 항목 | 내용 |
|------|------|
| 담당 | 디자이너 |
| 입력 | `output/drafts/script.md` |
| 참조 | `.claude/references/design-system.md` (SSOT) |
| 출력 | `output/drafts/slides/slide-*.html` |
| 성공 | design-system.md 준수, 가독성, 슬라이드 간 통일감 |

---

## 6단계: PNG 변환 (SCV)

| 항목 | 내용 |
|------|------|
| 담당 | SCV(html-renderer.js / Puppeteer) |
| 출력 | `output/final/YYYYMMDD_주제명/slide-*.png` |
| 성공 | 1080×1350px, 100KB 이상 |
| 실패 | 자동 재시도 3회 |

```
node .claude/scv/html-renderer.js --input output/drafts/slides/ --topic "주제명"
```

---

## 7단계: 최종 검토 (CEO) ← CEO 검토

검토 항목: 슬라이드 장수(6~8) | 텍스트 가독성 | 브랜드 일관성 | 타겟 적합성

통과 → 사용자에게 보고 후 업로드 여부 확인
반려 → 문제 단계 재작업 지시 (최대 2회)

⛔ **업로드 분기**: 사용자 승인 시 8단계 진행

---

## 8단계: 업로드 (Python)

**인스타그램 + 스레드 동시:**
```bash
python .claude/scv/instagram-uploader.py --images-dir "output/final/YYYYMMDD_주제명"
```

**스레드만 (인스타그램 이미 업로드한 경우):**
```bash
python .claude/scv/threads-uploader.py --images-dir "output/final/YYYYMMDD_주제명"
```

| 항목 | 내용 |
|------|------|
| 인스타그램 | instagrapi, PNG→JPEG 자동 변환 |
| 스레드 | 공식 Threads API + catbox.moe 이미지 호스팅 |
| 자격증명 | `.instagram_credentials.json`, `.threads_credentials.json` |
| 세션캐시 | `.instagram_session.json` (재로그인 방지) |

---

## 품질 게이트 요약

| 단계 | CEO 검토 |
|------|---------|
| 3단계: 기획 | O |
| 4단계: 스크립트 | O |
| 5단계: 디자인 | X |
| 7단계: 최종 | O |
| 8단계: 업로드 | O (사용자 확인) |

---

## 진행 상태 파일 체크

```
output/data/trend-data.json     → 1단계 완료
output/data/research.md         → 2단계 완료
output/drafts/content-plan.md   → 3단계 완료
output/drafts/script.md         → 4단계 완료
output/drafts/slides/           → 5단계 완료
output/final/YYYYMMDD_주제명/   → 6단계 완료
```
