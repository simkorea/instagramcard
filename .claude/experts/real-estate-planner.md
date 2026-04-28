# 부동산 리서처·기획자 - 리서치 및 기획 세부 지침

> CLAUDE.md에서 분리된 세부 지침. 주제 선정·리서치·슬라이드 기획 시 이 파일을 참조합니다.

---

## 타겟 오디언스

- **연령**: 20~50대
- **관심사**: 아파트 매매·전세·청약·투자·대출·정책
- **콘텐츠 방향**: 즉시 쓸 수 있는 실용 정보, 정책 변화 임팩트, 수치 기반 인사이트

---

## 주제 선정 기준

자동 모드(트렌드 탐색) 또는 키워드 모드 중 선택.

**좋은 주제 조건**:
- 최근 1~2주 내 발표된 정책·규제 변화
- 수치로 설명 가능한 내용 (LTV %, 금리, 가격)
- 타겟의 즉각적 행동을 유도할 수 있는 인사이트
- 7장 슬라이드로 분해 가능한 분량

**피해야 할 주제**:
- 너무 광범위한 주제 ("부동산 전망")
- 수치·날짜 없는 추상적 내용
- 이미 다뤘던 주제 (output/final 폴더 확인)

---

## 콘텐츠 정확성 원칙 (필수)

| 규칙 | 내용 |
|------|------|
| 사전 검증 필수 | 스크립트 작성 전 WebSearch로 최신 정보 확인 |
| 교차검증 2건 이상 | 수치·날짜·정책명은 출처 2개 이상에서 동일 내용 확인 |
| 최신 정보 우선 | 정책·규제 변경 여부 반드시 확인, 개정일 명시 |
| 구버전 혼재 금지 | 이전 정책과 현재 정책이 섞이지 않도록 타임라인 확인 |

**실패 사례**: 생애최초 LTV 80%(2022.8)와 LTV 70%(2025.6.27 강화) 혼재 → 전면 재작업 필요.
수치는 반드시 시행일 기준으로 최신 값 확인.

---

## 입력 데이터 전처리 (PDF·HTML → Markdown 변환 필수)

PDF 공고문이나 HTML 뉴스를 받으면 **분석 전에 반드시 Markdown으로 변환**합니다.
변환 없이 바로 분석 시작 금지. 상세 도구 사용법 → `.claude/references/input-preprocessing.md`

### 도구 선택

| 입력 | 1순위 | 2순위 |
|------|-------|-------|
| PDF (분양공고·정책문서) | `marker` | `markitdown` |
| HTML·URL (뉴스·블로그) | `markitdown` | `trafilatura` |

### 빠른 실행

```bash
# PDF → Markdown (marker)
marker_single 분양공고문.pdf --output_dir output/data/raw/

# URL → Markdown (markitdown)
markitdown "https://뉴스URL" -o output/data/raw/article.md

# 뉴스 본문만 추출 (trafilatura — 광고·메뉴 제거)
trafilatura --url "https://뉴스URL" --output-format markdown > output/data/raw/article.md
```

### 변환 후 필수 확인
- 수치(%, 억 원, ㎡), 표, 날짜가 정상 추출됐는지 육안 검토
- 검토 통과 후 `output/data/raw/파일명.md` 저장 → 이후 분석 시작

---

## 리서치 절차

### SCV 사용 (research-crawler.js)
```bash
node .claude/scv/research-crawler.js --keyword "주제명" --output output/data/research.md
```
- `ANTHROPIC_API_KEY` 필요
- 실패 시: CEO가 WebSearch로 직접 리서치 작성

### 직접 리서치 (WebSearch)
1. 주제 키워드로 WebSearch 2~3회
2. 정부 공식 발표, 주요 언론 기사 최소 2건 확인
3. 수치·날짜 교차검증 후 `output/data/research.md`에 저장

---

## 슬라이드 구성 기획

### 고정 구조
```
slide-1: 커버 (제목 + 훅 문구 + 요약 카드)
slide-2~N-1: 본문 (각 슬라이드 하나의 핵심 메시지)
slide-N: 마무리 CTA (요약 + 3단계 액션 + 저장/공유 유도)
```

### 본문 슬라이드 유형
| 유형 | 내용 |
|------|------|
| 비교형 | 이전 vs 현재, A vs B |
| 계산형 | 수치 예시 3개 (소·중·대) |
| 체크리스트형 | 자격 조건·절차 4~5가지 |
| 경고형 | 규제·리스크 강조 |
| 비교표형 | 3열 비교 (최적·차선·일반) |

### 슬라이드별 Leonardo AI 프롬프트 동시 작성
기획 완료 시 각 슬라이드 씬 방향도 함께 정해 디자이너에게 전달.
프롬프트 작성 상세 규칙 → `.claude/staff/experts/designer.md` 참조

---

## 해시태그 조사

리서치 완료 후 주제 관련 인기 해시태그 조사:
- 타겟 검색 키워드 기반 15~30개
- 저장: `output/drafts/hashtags.md`
