# 영상 엔지니어 - 릴스(Short-form) 제작 로직

> CLAUDE.md에서 분리된 세부 지침. 릴스 제작 시 이 파일을 참조합니다.

---

## ⚠️ 기본 원칙 — 릴스/쇼츠/동영상 제작 시 필수

> **카드뉴스 PNG를 영상 배경으로 사용하지 않는다.**
> 
> 릴스, 쇼츠, 동영상 제작 요청이 들어오면 반드시 아래 순서로 진행:
> 1. Leonardo AI로 **영상 전용 배경 이미지 5장** 생성 (720×1280, Lucid Realism)
> 2. `output/assets/video-bg/video-{N}.png` 저장
> 3. `output/final/YYYYMMDD_주제명_videobg/` 복사
> 4. `video_maker.py`를 해당 폴더로 실행
>
> 기존 카드뉴스 슬라이드(`output/final/YYYYMMDD_주제명/`)를 그대로 쓰지 말 것.

### Leonardo 영상 배경 생성 규칙

| 항목 | 값 |
|------|-----|
| 모델 | Lucid Realism (`05ce0082-2d80-4a2d-8653-4d1c85e2418e`) |
| 해상도 | **720×1280** (세로 쇼츠 비율) |
| 장 수 | **5장** |
| 저장 경로 | `output/assets/video-bg/video-{N}.png` |
| 복사 경로 | `output/final/YYYYMMDD_주제명_videobg/slide-{N}.png` |

**프롬프트 방향**: 주제를 상징하는 cinematic, 분위기 있는 배경. 텍스트 없음. 인물 없음.

---

## 기능 11: 릴스 자동 전환 — 필수 퀄리티 규칙

모든 릴스 제작 시 예외 없이 적용합니다.

### 규칙 1 — 대본 분리 (카드뉴스 텍스트 ≠ 나레이션)

| 구분 | 파일 | 스타일 |
|------|------|--------|
| 카드뉴스 텍스트 | `output/drafts/script.md` | 정보 전달형, 명사 중심, 20~80자 |
| 릴스 나레이션 | `output/drafts/narration.txt` | 구어체, 도파민 자극, 손실 회피 본능 |

나레이션 상세 원칙 → `.claude/experts/copywriter.md` 참조

---

### 규칙 2 — 비주얼 믹스 (Leonardo 70% + B-Roll 30%)

| 소재 | 비율 | 용도 |
|------|------|------|
| Leonardo AI 생성 이미지 (슬라이드) | **70%** | 슬라이드별 메인 비주얼 |
| 실사 B-Roll 영상 (Pexels/Pixabay) | **30%** | 슬라이드 전환 사이 2~3초 삽입 |

**B-Roll 키워드 매핑**:

| 주제 | 검색어 |
|------|--------|
| 부동산·아파트 | `apartment drone aerial`, `real estate building` |
| 주식·투자 | `stock market graph`, `financial trading screen` |
| 금리·경제 | `bank building exterior`, `currency coins` |
| 재건축·개발 | `construction crane city`, `urban development` |

- B-Roll 삽입 위치: 슬라이드 3→4, 5→6 전환 구간 우선
- API 없을 때: Leonardo 100%로 진행 (중단 금지)

---

### 규칙 3 — 사운드 강화 (BGM + 나레이션 덕킹)

**BGM 기준**: Lo-fi hip-hop / Cinematic trap / Motivational beat, BPM 90~120
**파일 위치**: `output/assets/bgm.mp3`

| 구간 | BGM 볼륨 |
|------|---------|
| 나레이션 없는 구간 | 40% |
| 나레이션 시작 0.3초 전 | 40% → 12% 페이드다운 |
| 나레이션 진행 중 | **12%** (`bgm_volume = 0.12`) |
| 나레이션 끝 0.5초 후 | 12% → 40% 페이드업 |

```bash
python .claude/scv/video_maker.py --images-dir "output/final/YYYYMMDD_주제명" \
  --tts --narration output/drafts/narration.txt \
  --bgm output/assets/bgm.mp3 --broll --topic "주제키워드"
```

---

### 규칙 4 — 강조형 자막 (화면 정중앙)

| 항목 | 값 |
|------|-----|
| 위치 | 화면 세로 **50%** (정중앙) |
| 폰트 크기 | **160px** |
| 배경 | 골드(`#FFD060`) 박스 + 패딩 18px |
| 텍스트 색 | `#1A1A1A` |
| 최대 글자 수 | 한 줄 10자 초과 시 줄바꿈 |

**애니메이션 (3단계)**:
```
0ms       : scale 0.7, opacity 0
0~150ms   : scale 1.08, opacity 1.0  (튀어오름)
150~250ms : scale 1.0               (안착)
```

- 수치·퍼센트·고유명사: 폰트 1.15배 + 자막 배경 흰색(`#FFFFFF`)
- 전환 직전 0.5초: 자막 `opacity 1.0 → 0` 페이드아웃
- 적용 함수: `draw_subtitle_center_impact(frame, text, t_in_segment)`

**시각 효과 (기존 유지)**:
- Ken Burns 줌: 1.0 → 1.15배 (`ZOOM_TO = 1.15`)
- 크로스페이드: 0.6초
- 목소리: `ko-KR-InJoonNeural` (기본) / ElevenLabs 우선 (키 있을 때)

---

## 기능 12: 릴스 고급 퀄리티 옵션

사용자가 "영상으로 만들어줘" 요청 시 아래 4가지를 적용합니다.

### ① Hook-First Scripting

나레이션 상세 → `.claude/experts/copywriter.md` 참조

### ② B-Roll 자동 삽입 (Pexels / Pixabay API)

**API 우선순위**: Pexels (`PEXELS_API_KEY`) → Pixabay (`PIXABAY_API_KEY`) → 건너뜀

**삽입 규칙**:
- 슬라이드 3~4장 간격으로 1클립 (전체 영상의 20~30%)
- 클립 길이: 2~3초, 소리 없이 (muted)
- B-Roll 중에도 자막·나레이션 계속 진행
- 검색 실패 시 기존 이미지 유지 (영상 중단 금지)

```bash
python .claude/scv/video_maker.py --images-dir "output/final/YYYYMMDD_주제명" \
  --tts --narration output/drafts/narration.txt --broll --topic "부동산"
```

`.env` 필요 키: `PEXELS_API_KEY`, `PIXABAY_API_KEY`

---

### ③ ElevenLabs 고품질 TTS

`ELEVENLABS_API_KEY` 있으면 edge-tts 대신 우선 사용.

```
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB   # Adam (기본값)
ELEVENLABS_MODEL=eleven_multilingual_v2
```

```bash
python .claude/scv/video_maker.py --images-dir "output/final/YYYYMMDD_주제명" \
  --tts --narration output/drafts/narration.txt --tts-engine elevenlabs
```

폴백: ElevenLabs 실패 → `ko-KR-InJoonNeural` 자동 전환

---

### ④ 다이내믹 자막 + SFX + 흔들림

- 강조 단어: 골드(`#FFD060`) + 흰색 배경 + 1.1배 스케일업 애니메이션
- SFX: `output/assets/sfx/whoosh.mp3` (전환 시), `impact.mp3` (강조 수치 등장 시) — 없으면 건너뜀
- Shake: 강조 단어 등장 순간 0.1초 ±8px 진동 — 슬라이드당 최대 1회
- 함수: `apply_shake(frame, intensity=8, duration=0.1)`

```bash
python .claude/scv/video_maker.py --images-dir "output/final/YYYYMMDD_주제명" \
  --tts --narration output/drafts/narration.txt --sfx --shake
```

> 기능 ②③④는 API 키·SFX 파일 없으면 자동으로 건너뛰고 기본 모드로 진행.

---

## 표준 업무 순서

1. 카드뉴스 기획 및 Leonardo AI 이미지 생성 (7장)
2. 릴스 나레이션 동시 작성 → `output/drafts/narration.txt` 저장
3. 인스타그램 피드 + 스레드 업로드
4. 릴스 영상 자동 생성 → 업로드 (별도 확인 불필요)
