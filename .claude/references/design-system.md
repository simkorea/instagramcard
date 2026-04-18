# 디자인 시스템 — 단일 진실 공급원 (SSOT)

> 이 파일이 색상, 폰트, 레이아웃의 유일한 기준입니다.
> 브랜드 변경 시 이 파일만 수정하면 전체 슬라이드에 반영됩니다.

---

## 캔버스 규격

| 항목 | 값 |
|------|-----|
| 너비 | 1080px |
| 높이 | 1350px |
| 비율 | 4:5 (인스타그램 세로형) |
| 포맷 | PNG |

---

## 색상 팔레트

### Primary (주요 색상)
| 이름 | HEX | 용도 |
|------|-----|------|
| Primary Blue | `#1A56DB` | 버튼, 강조 태그, 핵심 포인트 |
| Primary Light | `#EBF1FF` | 배경 강조, 카드 배경 |
| Primary Dark | `#1E3A8A` | 텍스트 강조, 진한 포인트 |

### Neutral (중립 색상)
| 이름 | HEX | 용도 |
|------|-----|------|
| Background | `#FFFFFF` | 슬라이드 기본 배경 |
| Surface | `#F8FAFC` | 카드/박스 배경 |
| Border | `#E2E8F0` | 구분선, 테두리 |
| Text Primary | `#1E2330` | 본문 주요 텍스트 |
| Text Secondary | `#4A5568` | 부가 설명, 서브 텍스트 |
| Text Muted | `#94A3B8` | 보조 텍스트 |

### Semantic (의미 색상)
| 이름 | HEX | 용도 |
|------|-----|------|
| Emphasis BG | `#EBF1FF` | 강조 문구 배경 |
| Emphasis Text | `#1A56DB` | 강조 문구 텍스트 |

---

## 타이포그래피

### 폰트 패밀리
```css
/* Google Fonts CDN */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif;
```

### 폰트 스케일

> 모바일 가독성 기준 (인스타그램 피드 실사용 환경 최적화)

| 역할 | 크기 | 두께 | 용도 |
|------|------|------|------|
| Display | 120–144px | 900 | 커버 메인 제목 |
| Heading 1 | 88–100px | 900 | 본문 슬라이드 소제목 |
| Heading 2 | 60–72px | 700 | 서브 제목, 커버 서브타이틀 |
| Body Large | 48–56px | 500 | 본문 주요 내용 (최소 기준) |
| Body | 40–46px | 400 | 일반 본문 |
| Caption | 32–36px | 500 | 보조 텍스트, 태그, 레이블 |
| Stat Display | 140–180px | 900 | 인포그래픽 핵심 숫자 |

### 줄 간격
| 텍스트 유형 | line-height |
|------------|-------------|
| 헤딩 (대형 제목) | 1.05–1.15 |
| 본문 | 1.55–1.70 |
| 강조 박스 | 1.35 |

### letter-spacing
- 대형 제목: `-1px` ~ `-2px`
- 일반 텍스트: 기본값 (0)

---

## 여백 시스템

```
슬라이드 외부 여백 (padding)
  상하: 80px
  좌우: 80px

요소 간 간격 (gap)
  섹션 간: 32–48px
  텍스트 간: 16–24px
  소요소 간: 8–12px
```

---

## 인포그래픽 컴포넌트

> 사진/그래픽 요소가 없는 텍스트 전용 슬라이드 금지. 모든 본문 슬라이드에 아래 중 1개 이상 포함.

### 유형별 사용 기준

| 유형 | 컴포넌트 | 적합한 콘텐츠 |
|------|---------|-------------|
| 수치 강조 | Stat Hero | 퍼센트, 배수, 기간 등 핵심 숫자 |
| 순서 목록 | Numbered List | 단계별 항목, 체크리스트 |
| 비교/변환 | Arrow Flow | A → B 변환, Before/After |
| 공식/계산 | Formula Block | 수식, 결과 계산 |
| 트렌드 | Bar Chart (CSS) | 증감률, 비율 시각화 |
| 도넛 차트 | Ring Chart (SVG) | 비율/퍼센트 시각화 |
| 정의 카드 | Definition Card | 용어 설명, 개념 소개 |

### Stat Hero (핵심 숫자 강조)
```css
.stat-hero {
  font-size: 160px;
  font-weight: 900;
  color: #1A56DB;
  letter-spacing: -4px;
  line-height: 1;
}
.stat-hero-label {
  font-size: 44px;
  font-weight: 500;
  color: #4A5568;
}
```

### Ring Chart (SVG 도넛 차트)
```html
<!-- 78% 예시 -->
<svg width="220" height="220" viewBox="0 0 220 220">
  <circle cx="110" cy="110" r="90" fill="none" stroke="#EBF1FF" stroke-width="20"/>
  <circle cx="110" cy="110" r="90" fill="none" stroke="#1A56DB" stroke-width="20"
    stroke-dasharray="440" stroke-dashoffset="97" <!-- (1-0.78)*440 -->
    stroke-linecap="round" transform="rotate(-90 110 110)"/>
</svg>
```

### Bar Chart (CSS 막대그래프)
```css
.bar-track { background: #EBF1FF; border-radius: 12px; height: 24px; }
.bar-fill  { background: #1A56DB; border-radius: 12px; height: 24px; }
```

### Photo Hero (사진 배경 + 오버레이)

> **커버·마무리 슬라이드**에 적용. 배경 이미지 위에 어두운 그라디언트 오버레이를 씌워 텍스트 가독성을 확보.

**사진 소스**: Unsplash 고정 URL (CDN 캐시, 안정적)
```
https://images.unsplash.com/photo-{photo-id}?w=1080&h=1350&fit=crop&crop=center
```

**⚠️ ID 형식 주의**: 구형 긴 숫자 ID만 사용 가능. 신형 단문 영숫자 ID(`zIObZEoSQ1w` 형태)는 404 오류.

### 검증된 Unsplash Photo ID 목록 (직접 테스트 완료)

| 카테고리 | photo-id | 설명 | 용도 |
|---------|---------|------|------|
| **도시/야경** | `1477959858617-67f85cf4f1df` | 시카고 야경 스카이라인 | 커버/CTA (Photo Hero) |
| **아파트 외관** | `1545324418-cc1a3fa10c00` | 아파트 단지 외관 | 시장현황/공급 (Photo Banner) |
| **계약/서류** | `1450101499163-c8848c66ca85` | 계약서 서명 장면 | 경고/주의사항 (Photo Banner, 적색 오버레이) |
| **세금/문서** | `1554224155-6726b3ff858f` | 세무 서류/체크리스트 | 체크리스트/점검 (Photo Banner) |
| **도시 고층** | `1486325212027-8081e485255e` | 도시 고층빌딩 야경 | 커버 대안 (Photo Hero) |
| **집/열쇠** | `1560518883-ce09059eeffa` | 집 열쇠 / 내집마련 | CTA / 마무리 |
| **투자/차트** | `1611974789855-9c2a0a7236a3` | 주식/투자 차트 | 기회/상승 슬라이드 |
| **건물 인테리어** | `1502672260266-1c1ef2d93688` | 아파트 거실 인테리어 | 실거주 / 라이프스타일 |

**사용 예시:**
```html
<!-- Photo Hero (커버) -->
<div class="photo-bg" style="background-image:url('https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=1080&h=1350&fit=crop&crop=top')"></div>

<!-- Photo Banner (본문) -->
<img src="https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=1080&h=230&fit=crop&crop=center" alt="">
```

- `source.unsplash.com` 대신 `images.unsplash.com` 사용 (source API 지원 종료)
- 새 ID 필요 시: HEAD 요청으로 200 확인 후 사용 (`output/assets/images/`에 썸네일 저장)

**⚠️ 주의**: 외부 이미지 미로드 대비 `background-color` 폴백 필수
```css
.photo-bg {
  background-image: url('https://images.unsplash.com/...');
  background-size: cover;
  background-color: #0d1b3e; /* 이미지 로드 실패 시 폴백 */
}
```

**오버레이 스펙**
```css
/* 방식 1 — 그라디언트 오버레이 (하단 강조) */
.photo-overlay {
  background: linear-gradient(
    to bottom,
    rgba(10, 20, 50, 0.35) 0%,
    rgba(10, 20, 50, 0.75) 60%,
    rgba(10, 20, 50, 0.92) 100%
  );
}

/* 방식 2 — 균일 다크 오버레이 */
.photo-overlay-flat {
  background: rgba(15, 25, 60, 0.68);
}
```

**사진 캡션 (Photo Credit)**
```css
.photo-credit {
  font-size: 24px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.45);
  position: absolute;
  bottom: 28px;
  right: 40px;
  letter-spacing: 0;
}
```
- 표기 형식: `Photo by [이름] on Unsplash`
- 위치: 슬라이드 우측 하단 고정
- 텍스트 색상은 배경 방해 없는 반투명 흰색 사용

### Photo Banner (본문 슬라이드 상단 사진 띠)

> **본문 슬라이드(2~6장)**에 적용. 슬라이드 상단에 가로 전폭 사진 띠를 배치해 시각적 몰입감 제공.

**규격**: 너비 100%, 높이 200~240px, `border-radius: 24~28px`

**오버레이 방향**: 주제에 따라 선택
- 정보성(청색 계열): `to right` — 좌측 텍스트 위 어둡게
- 경고성(적색 계열): `to bottom` — 하단 텍스트 위 어둡게

```html
<div class="photo-banner">
  <img src="https://images.unsplash.com/photo-{id}?w=1080&h=240&fit=crop" alt="">
  <div class="ban-overlay">
    <span class="ban-tag">📌 슬라이드 핵심 태그</span>
  </div>
</div>
```
```css
.photo-banner { width: 100%; height: 220px; border-radius: 28px; overflow: hidden; position: relative; }
.photo-banner img { width: 100%; height: 100%; object-fit: cover; }
.ban-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(to right, rgba(13,27,62,0.82) 0%, rgba(13,27,62,0.2) 100%);
  display: flex; align-items: flex-end; padding: 0 40px 24px;
}
.ban-tag { background: #1A56DB; color: #fff; font-size: 28px; font-weight: 700; padding: 10px 28px; border-radius: 999px; }
```

**슬라이드별 추천 Unsplash 키워드**

| 슬라이드 내용 | 추천 사진 키워드 | 오버레이 |
|-------------|--------------|---------|
| 시장/뉴스 분석 | apartment, cityscape | to right (청색) |
| 경고/함정 | office, contract, stress | to bottom (적색, `filter: brightness(0.55)`) |
| 기회/상승 | growth, chart, investment | to right (청색) |
| 체크리스트 | checklist, document, plan | to bottom (청색) |

---

### Timeline (단계별 타임라인 인포그래픽)

> 날짜·단계 흐름이 있는 슬라이드에 사용. 점(dot) + 연결선 + 라벨 구조.

```html
<div class="tl-row">
  <div class="tl-step active">
    <div class="tl-dot"></div>
    <div class="tl-connector"></div>
    <div class="tl-content">
      <div class="tc-date">날짜</div>
      <div class="tc-label">단계명</div>
    </div>
  </div>
  <!-- 반복 -->
</div>
```
```css
.tl-row { display: flex; align-items: flex-start; }
.tl-step { flex: 1; position: relative; display: flex; flex-direction: column; align-items: center; }
.tl-dot { width: 20px; height: 20px; background: #1A56DB; border-radius: 50%; border: 3px solid #5B9BFF; z-index: 2; }
.tl-connector { position: absolute; top: 9px; left: 50%; right: -50%; height: 3px; background: rgba(91,141,239,0.3); z-index: 1; }
.tl-step:last-child .tl-connector { display: none; }
.tl-step.active .tl-dot { background: #FF9F43; border-color: #FFD070; box-shadow: 0 0 16px rgba(255,159,67,0.6); }
.tl-step.done .tl-dot { background: #22C55E; border-color: #4ADE80; }
.tc-date { font-size: 26px; font-weight: 700; color: rgba(255,255,255,0.6); }
.tc-label { font-size: 28px; font-weight: 700; color: rgba(255,255,255,0.9); }
.tl-step.active .tc-label { color: #FFD070; }
```

---

### SVG Check Icon (체크리스트 아이콘)

> 체크리스트 슬라이드에서 텍스트 앞 아이콘으로 사용. PNG 대신 인라인 SVG로 렌더링 보장.

```html
<!-- 기본 (파란 배경, 흰 체크) -->
<svg width="52" height="52" viewBox="0 0 52 52">
  <circle cx="26" cy="26" r="26" fill="#1A56DB"/>
  <polyline points="14,27 22,35 38,18" stroke="#fff" stroke-width="4.5"
    fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>

<!-- 강조 (다크 배경, 황금 체크) -->
<svg width="52" height="52" viewBox="0 0 52 52">
  <circle cx="26" cy="26" r="26" fill="#1A3A8A"/>
  <polyline points="14,27 22,35 38,18" stroke="#FFD060" stroke-width="4.5"
    fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

---

### Progress Bar (진행 표시 바)

> 체크리스트·단계별 슬라이드에서 독자에게 진행 상태를 시각화.

```html
<div class="progress-outer">
  <div class="progress-inner" style="width: 100%"></div>
</div>
<div class="progress-steps">
  <span>1</span><span>2</span><span>3</span><span>4</span><span>5 ✓</span>
</div>
```
```css
.progress-outer { background: #EBF1FF; border-radius: 10px; height: 14px; }
.progress-inner { background: #1A56DB; border-radius: 10px; height: 14px; }
.progress-steps { display: flex; justify-content: space-between; margin-top: 8px; font-size: 24px; font-weight: 600; color: #1A56DB; }
```

---

### Summary Card Row (요약 카드 행)

> 마무리 슬라이드 상단 또는 커버 하단에 핵심 인사이트 4개를 카드로 요약 표시.

```html
<div class="summary-row">
  <div class="summary-card">
    <div class="sc-icon">📅</div>
    <div class="sc-text">D-25<br>마감일</div>
  </div>
  <!-- 3~4개 반복 -->
</div>
```
```css
.summary-row { display: flex; gap: 14px; }
.summary-card {
  flex: 1; background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.14);
  border-radius: 18px; padding: 18px 14px; text-align: center;
}
.sc-icon { font-size: 32px; margin-bottom: 6px; }
.sc-text { font-size: 24px; font-weight: 600; color: rgba(255,255,255,0.8); line-height: 1.35; }
```

---

### Warning Icon Row (경고 아이콘 3종)

> 함정·주의 슬라이드에서 경고 항목을 한눈에 요약하는 아이콘 카드 행.

```html
<div class="warn-icons">
  <div class="warn-icon-box">
    <div class="wi-icon">🏠</div>
    <div class="wi-label">항목명</div>
  </div>
  <!-- 3개 반복 -->
</div>
```
```css
.warn-icons { display: flex; gap: 20px; }
.warn-icon-box {
  flex: 1; background: #FFF5F5; border-radius: 20px; padding: 24px 16px; text-align: center;
  border: 1.5px solid rgba(255,107,107,0.25);
}
.wi-icon { font-size: 52px; margin-bottom: 8px; }
.wi-label { font-size: 26px; font-weight: 700; color: #E53E3E; line-height: 1.35; }
```

---

### D-Day Badge (청약·마감일 강조 배지)

> 청약일·마감일 등 날짜 긴박감 슬라이드에 사용. 날짜와 서브 설명을 한 줄로 묶은 pill 형태.

```html
<div class="dday-badge">
  <span class="dday-text">📅 청약일 4월 28일</span>
  <span class="dday-sub">입주자모집공고 4월 17일</span>
</div>
```
```css
.dday-badge {
  display: inline-flex; align-items: center; gap: 12px;
  background: rgba(255,107,107,0.15); border: 1.5px solid rgba(255,107,107,0.5);
  border-radius: 16px; padding: 14px 28px;
}
.dday-text { font-size: 30px; font-weight: 900; color: #FF6B6B; }
.dday-sub  { font-size: 26px; font-weight: 500; color: rgba(255,255,255,0.7); }
```

---

### Spec Grid (단지·상품 스펙 2×2 그리드)

> 단지 분석, 상품 소개 슬라이드에서 규모·가격·교통 등 핵심 스펙 4개를 2×2 그리드로 배치.

```html
<div class="spec-grid">
  <div class="spec-card">
    <div class="sc-label">규모</div>
    <div class="sc-value blue">178가구</div>
  </div>
  <!-- 3개 더 반복 -->
</div>
```
```css
.spec-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.spec-card { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); border-radius: 18px; padding: 22px 24px; }
.sc-label  { font-size: 24px; font-weight: 600; color: rgba(255,255,255,0.5); margin-bottom: 8px; }
.sc-value  { font-size: 32px; font-weight: 900; color: #fff; line-height: 1.2; }
.sc-value.blue   { color: #5B9BFF; }
.sc-value.green  { color: #34D399; }
.sc-value.orange { color: #FB923C; }
```
- 다크 배경 슬라이드에 적합 (투명 카드)
- 밝은 배경 슬라이드에서는 `background: #F8FAFC`, `border: 1.5px solid #E2E8F0`으로 교체

---

### Category Badge Row (노선·분류 뱃지 행)

> 지하철 노선, 카테고리 태그 등 색상으로 구분되는 항목을 pill 형태로 나열.

```html
<div class="badge-row">
  <div class="cat-badge l5">5호선</div>
  <div class="cat-badge l6">6호선</div>
  <div class="cat-badge gyeong">경의중앙선</div>
  <div class="cat-badge airport">공항철도</div>
</div>
```
```css
.badge-row { display: flex; gap: 12px; flex-wrap: wrap; }
.cat-badge { border-radius: 12px; padding: 10px 20px; font-size: 26px; font-weight: 700; }
/* 지하철 노선 색상 예시 */
.cat-badge.l5      { background: rgba(147,51,234,0.25); border: 1.5px solid rgba(167,81,254,0.5); color: #C084FC; }
.cat-badge.l6      { background: rgba(234,88,12,0.2);  border: 1.5px solid rgba(251,146,60,0.5); color: #FB923C; }
.cat-badge.gyeong  { background: rgba(22,163,74,0.2);  border: 1.5px solid rgba(52,211,153,0.5); color: #34D399; }
.cat-badge.airport { background: rgba(59,130,246,0.2); border: 1.5px solid rgba(96,165,250,0.5); color: #60A5FA; }
```

---

### Ratio Bar (비율 2분할 가로 바)

> 추첨/가점, A/B 두 항목의 비율을 단일 가로 바로 표현.

```html
<div class="ratio-bar">
  <div class="rb-part green" style="flex:60">추첨제 60%</div>
  <div class="rb-part gray"  style="flex:40">가점제 40%</div>
</div>
```
```css
.ratio-bar { display: flex; height: 36px; border-radius: 18px; overflow: hidden; }
.rb-part { display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: 900; }
.rb-part.green { background: linear-gradient(90deg, #22C55E, #4ADE80); color: #fff; }
.rb-part.blue  { background: linear-gradient(90deg, #1A56DB, #3B82F6); color: #fff; }
.rb-part.gray  { background: rgba(255,255,255,0.15); color: rgba(255,255,255,0.5); }
```

---

### Compare Column Table (두 항목 비교 표)

> 추첨제 vs 가점제, A안 vs B안 등 두 옵션을 head+body 2열로 나란히 비교.

```html
<div class="compare-table">
  <div class="ct-col">
    <div class="ct-head green"><div class="ct-head-title">추첨제</div><div class="ct-head-pct">60%</div></div>
    <div class="ct-body">
      <div class="ct-row"><div class="dot green"></div><span>항목1</span></div>
      <!-- 반복 -->
    </div>
  </div>
  <div class="ct-col">
    <div class="ct-head gray">...</div>
    <div class="ct-body">...</div>
  </div>
</div>
```
```css
.compare-table { display: flex; gap: 20px; }
.ct-col { flex: 1; border-radius: 22px; overflow: hidden; }
.ct-head { padding: 22px 24px; text-align: center; }
.ct-head.green { background: #22C55E; }
.ct-head.gray  { background: #94A3B8; }
.ct-head-title { font-size: 32px; font-weight: 900; color: #fff; margin-bottom: 4px; }
.ct-head-pct   { font-size: 48px; font-weight: 900; color: #fff; }
.ct-body { background: #fff; padding: 20px 24px; display: flex; flex-direction: column; gap: 12px; }
.ct-row  { display: flex; align-items: center; gap: 12px; font-size: 26px; }
.dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.dot.green { background: #22C55E; }
.dot.gray  { background: #94A3B8; }
```

---

### Date Schedule Row (청약 일정 3열 카드)

> 특공·1순위·2순위 등 연속 날짜 일정을 3개 카드로 나란히 표시.

```html
<div class="date-row">
  <div class="date-card green">
    <div class="dc-label">특별공급</div>
    <div class="dc-date">4월 20일</div>
  </div>
  <div class="date-card green">
    <div class="dc-label">1순위</div>
    <div class="dc-date">4월 21일</div>
  </div>
  <div class="date-card green">
    <div class="dc-label">2순위</div>
    <div class="dc-date">4월 22일</div>
  </div>
</div>
```
```css
.date-row { display: flex; gap: 16px; }
.date-card { flex: 1; border-radius: 16px; padding: 16px 20px; text-align: center; }
.date-card.green  { background: #F0FDF4; border: 1.5px solid #86EFAC; }
.date-card.blue   { background: #EFF6FF; border: 1.5px solid #93C5FD; }
.dc-label { font-size: 22px; font-weight: 600; color: #16A34A; margin-bottom: 4px; }
.dc-date  { font-size: 30px; font-weight: 900; color: #1E2330; }
```

---

### Checklist ok/warn (두 가지 상태 체크리스트)

> 체크리스트 슬라이드에서 통과 항목(ok·초록)과 주의 항목(warn·빨강)을 색상으로 구분.

```html
<div class="check-item ok">
  <div class="ci-num ok">1</div>
  <div class="ci-body">
    <div class="ci-title">세대원 전원 무주택 여부</div>
    <div class="ci-desc">본인 + 배우자 + 세대원 모두 확인 필수</div>
    <span class="ci-badge ok">✓ 확인 필수</span>
  </div>
</div>
<div class="check-item warn">
  <div class="ci-num warn">2</div>
  <!-- ... -->
</div>
```
```css
.check-item     { display: flex; align-items: flex-start; gap: 20px; border-radius: 20px; padding: 28px 28px; }
.check-item.ok  { background: #F0FDF4; border: 1.5px solid #86EFAC; }
.check-item.warn{ background: #FFF1F2; border: 1.5px solid #FECDD3; }
.ci-num { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: 900; color: #fff; flex-shrink: 0; }
.ci-num.ok   { background: #22C55E; }
.ci-num.warn { background: #DC2626; }
.ci-title { font-size: 32px; font-weight: 700; color: #1E2330; margin-bottom: 6px; }
.ci-desc  { font-size: 26px; font-weight: 500; color: #64748B; line-height: 1.4; }
.ci-badge { display: inline-block; margin-top: 8px; font-size: 22px; font-weight: 700; padding: 4px 14px; border-radius: 20px; }
.ci-badge.ok   { background: #DCFCE7; color: #16A34A; }
.ci-badge.warn { background: #FEE2E2; color: #DC2626; }
```

---

### Profile CTA (프로필 유도 버튼)

> 마무리 슬라이드(7장)에만 적용. 팔로우/프로필 방문을 유도하는 전용 버튼 컴포넌트.

```css
.profile-cta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  background: #FFFFFF;
  color: #1A56DB;
  border: 4px solid #1A56DB;
  border-radius: 999px;
  padding: 36px 52px;
  font-size: 46px;
  font-weight: 800;
  letter-spacing: -0.5px;
}
.profile-cta .arrow {
  font-size: 44px;
}
```
- 표기 형식: `프로필 보러가기 →`
- 위치: 저장 유도 버튼 아래, 계정명 위
- 흰 배경 + 블루 텍스트로 저장 CTA(파란 배경)와 시각적 구분

---

## 컴포넌트 패턴

### 강조 박스 (Emphasis Block)
```css
.emphasis {
  background: #EBF1FF;
  color: #1A56DB;
  border-radius: 20px;
  padding: 20px 28px;
  font-size: 34px;
  font-weight: 700;
  line-height: 1.4;
}
```

### 태그 / 뱃지
```css
.tag {
  display: inline-block;
  background: #1A56DB;
  color: #FFFFFF;
  border-radius: 999px;
  padding: 10px 22px;
  font-size: 22px;
  font-weight: 700;
}
```

### 카드 / 패널
```css
.card {
  background: #F8FAFC;
  border-radius: 32px;
  padding: 36px;
  box-shadow: 0 20px 50px rgba(30, 50, 100, 0.07);
}
```

### CTA 버튼 (마무리 슬라이드)
```css
.cta-button {
  background: #1A56DB;
  color: #FFFFFF;
  border-radius: 36px;
  padding: 36px 44px;
  font-size: 36px;
  font-weight: 800;
  line-height: 1.3;
  box-shadow: 0 18px 42px rgba(26, 86, 219, 0.28);
}
```

---

## 슬라이드 레이아웃 템플릿

> **필수 규칙**: 텍스트만 있는 슬라이드 금지. 모든 슬라이드에 사진 또는 인포그래픽 중 1개 이상 반드시 포함.

### 슬라이드 유형별 사진·인포그래픽 매핑

| 슬라이드 | 사진 | 인포그래픽 |
|---------|------|----------|
| 커버 | Photo Hero (full bleed) | Summary Card Row + Arrow Flow |
| 본문 — 데이터/현황 | Photo Banner (상단 띠) | Bar Chart 또는 Stat Hero |
| 본문 — 타임라인/절차 | (선택) | Timeline 인포그래픽 필수 |
| 본문 — 경고/함정 | Photo Banner (경고 분위기) | Warning Icon Row 필수 |
| 본문 — 비교/기회 | (선택) | Bar Chart + Ring Chart |
| 본문 — 체크리스트 | Photo Banner (상단 띠) | SVG Check Icon + Progress Bar |
| 본문 — 단지/상품분석 | Photo Banner 또는 다크bg | Spec Grid + Category Badge Row + Ratio Bar |
| 본문 — 일정/날짜비교 | Photo Banner (상단 띠) | Date Schedule Row + Bar Chart |
| 마무리 CTA | Photo Hero (full bleed) | Summary Card Row (상단) |

---

### 커버 슬라이드 (Photo Hero + 인포그래픽)
```
+------------------------------------------+
|  [Unsplash 배경 사진 — full bleed]        |
|  [다크 그라디언트 오버레이]                 |
|                                          |
|  [상단] 뱃지 태그 + 날짜                   |
|                                          |
|  [중앙] 대형 제목 Display/900/#FFFFFF     |
|         서브카피 Heading2/500/rgba(w,0.8) |
|                                          |
|  [하단] Stat Card Row (3~4개)            |
|         Arrow Flow 인포그래픽              |
|                                          |
|  [번호]              [Photo by Unsplash]  |
+------------------------------------------+
```

### 본문 슬라이드 — 데이터/현황형
```
+------------------------------------------+
|  [Photo Banner — 상단 220px]              |
|  (Unsplash 사진 + 오버레이 + 태그)         |
|                                          |
|  [슬라이드 번호]                           |
|  [소제목] Heading1/900/#1E2330           |
|                                          |
|  [Bar Chart 또는 Stat Hero 인포그래픽]    |
|                                          |
|  [정보 리스트 카드들]                      |
|  (border-left: 5px solid #1A56DB)       |
|                                          |
|  [강조 박스 Emphasis Block]               |
+------------------------------------------+
```

### 본문 슬라이드 — 타임라인/절차형
```
+------------------------------------------+
|  [슬라이드 번호]                           |
|  [소제목]                                 |
|                                          |
|  [D-day 카운트다운 박스]                   |
|  (배경: rgba(26,86,219,0.15), 다크 배경)  |
|                                          |
|  [Timeline 인포그래픽]                    |
|  dot → connector → dot → ... → done     |
|                                          |
|  [조건 카드 리스트]                        |
|                                          |
|  [강조 박스]                              |
+------------------------------------------+
```

### 본문 슬라이드 — 경고/함정형
```
+------------------------------------------+
|  [Photo Banner — 상단 200~220px]          |
|  (filter: brightness(0.55) + 적색 오버레이)|
|  (하단 경고 태그 — 빨간 뱃지)              |
|                                          |
|  [슬라이드 번호]                           |
|  [소제목] + 부연 설명                      |
|                                          |
|  [Warning Icon Row — 3종 아이콘]          |
|                                          |
|  [번호 배지 + 함정 카드 리스트]             |
|  (border-left: 6px solid #FF6B6B)       |
|  (background: #FFF5F5)                  |
|                                          |
|  [경고 강조 박스 — 적색]                   |
+------------------------------------------+
```

### 본문 슬라이드 — 비교/기회형
```
+------------------------------------------+
|  [슬라이드 번호]                           |
|  [소제목]                                 |
|  [구분선 divider]                         |
|                                          |
|  [Bar Chart 박스 — 비교 데이터]            |
|  (white 배경, border: 1.5px #E2E8F0)    |
|                                          |
|  [Ring Chart + 핵심 수치 설명]             |
|  (Primary Blue 배경 패널)                 |
|                                          |
|  [기회 리스트 카드들]                      |
|                                          |
|  [강조 박스 Emphasis Block]               |
+------------------------------------------+
```

### 본문 슬라이드 — 체크리스트형
```
+------------------------------------------+
|  [Photo Banner — 상단 200px]              |
|  (서류/계획 관련 사진 + 청색 오버레이)       |
|  (하단 체크리스트 제목)                     |
|                                          |
|  [슬라이드 번호]                           |
|  [소제목] + 판단 기준 설명                  |
|                                          |
|  [Progress Bar — 단계 표시]               |
|                                          |
|  [SVG Check Icon + 체크 항목 리스트]       |
|  (5개 항목, 마지막 항목 highlighted)       |
|                                          |
|  [결과 박스 — Primary Blue 배경]           |
+------------------------------------------+
```

### 마무리 슬라이드 (Photo Hero + 요약 인포그래픽)
```
+------------------------------------------+
|  [Unsplash 배경 사진 — full bleed]        |
|  [다크 그라디언트 오버레이]                 |
|                                          |
|  [상단 고정] Summary Card Row (4개)       |
|  "오늘 배운 핵심 요약" 라벨                 |
|                                          |
|  [날짜/주제 태그]                          |
|  [메인 CTA 문구] Display/900/#FFFFFF     |
|  [부연 메시지]                            |
|                                          |
|  [저장 유도 버튼 — Primary Blue]          |
|  [공유 버튼 — 반투명 테두리]               |
|  [프로필 버튼 — 흰 배경 + 블루 테두리]     |
|  [계정명]                                |
|                                          |
|  [번호]              [Photo by Unsplash]  |
+------------------------------------------+
```

---

## 사용 금지

- 이 파일에 없는 색상 임의 사용 금지
- 폰트 종류 임의 변경 금지
- 캔버스 크기(1080×1350) 변경 금지
- 브랜드 변경 필요 시 이 파일만 수정
