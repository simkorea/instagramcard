# 카드뉴스 자동화 에이전트 워크스페이스

이 워크스페이스는 **카드뉴스 자동화 시스템**입니다.

## 빠른 시작

사용자가 다음 중 하나를 입력할 때 시작합니다:
1. 키워드: "퇴사 후 프리랜서 전환", "1인 비즈니스", 등
2. 자유 명령: "이번 주 트렌드 찾아줘", "카드뉴스 만들어줘", 등

## 워크플로우

```
사용자 입력
  ↓
1️⃣ SCV: 트렌드 수집 → /output/data/trends.json
  ↓
2️⃣ 리서처: 주제 후보 도출 → /output/data/topic-candidates.md
  ↓
3️⃣ 사용자: 주제 선택 ⛔
  ↓
4️⃣ 콘텐츠 기획자: 슬라이드 기획 → /output/drafts/slide-plan.md
  ↓
5️⃣ 카피라이터: 스크립트 작성 → /output/drafts/script-final.md
  ↓
6️⃣ SCV: HTML 생성 → /output/html/slide-*.html
  ↓
7️⃣ SCV: PNG 변환 → /output/YYYYMMDD_주제명/*.png
  ↓
8️⃣ CEO: 최종 검토 ✅
```

## 주요 파일

### 설정 & 프롬프트
- `CLAUDE.md`: CEO 오케스트레이션 프롬프트
- `.claude/agents/ceo.agent.md`: 에이전트 정의 (Claude Code)
- `.claude/staff/experts/researcher.md`: 리서처 프롬프트
- `.claude/staff/experts/content-planner.md`: 콘텐츠 기획자 프롬프트
- `.claude/staff/experts/copywriter.md`: 카피라이터 프롬프트

### 참조 자료
- `.claude/references/target-audience.md`: 타겟 오디언스
- `.claude/references/tone-of-voice.md`: 톤앤매너
- `.claude/references/slide-template.md`: 슬라이드 템플릿

### 실행 & SCV
- `run_agent.py`: 전체 파이프라인 실행기 (예제)
- `.claude/scv/trend-collector.py`: 트렌드 수집
- `.claude/scv/html-renderer.py`: HTML 슬라이드 생성
- `.claude/scv/image-exporter.py`: PNG 변환

### 설계 문서
- `카드뉴스_자동화_에이전트_설계서.md`: 전체 설계서
- `README.md`: 프로젝트 개요

## 출력 구조

생성된 카드뉴스와 중간 산출물은 아래 위치에 저장됩니다:

```
/output
├── /data
│   ├── trends.json              # 트렌드 데이터
│   ├── topic-candidates.md      # 주제 후보
│   └── selected-topic.json      # 선택된 주제
├── /drafts
│   ├── slide-plan.md           # 슬라이드 기획안
│   └── script-final.md         # 최종 스크립트
├── /html
│   └── slide-01.html ~ ...     # HTML 슬라이드
├── /logs
│   └── error.log               # 에러/재시도 로그
└── /YYYYMMDD_주제명/           # 최종 PNG 카드뉴스
    ├── slide-01.png
    ├── slide-02.png
    └── ...
```

## 사용 방법

### Claude Code에서:
1. "카드뉴스 만들어줘" 또는 "퇴사 후 프리랜서 전환 관련 카드뉴스 만들어" 입력
2. CEO 에이전트가 8단계 워크플로우 실행
3. 최종적으로 `/output/YYYYMMDD_주제명/` 폴더에 PNG 파일 생성

### 직접 실행:
```bash
# 전체 파이프라인 (예제)
python run_agent.py

# 개별 SCV 실행
python .claude/scv/trend-collector.py
python .claude/scv/html-renderer.py
python .claude/scv/image-exporter.py "주제명"
```

## 참고

- 현재 설계는 Claude Code 어시스턴트가 각 단계를 오케스트레이션하는 방식입니다.
- SCV 스크립트는 기본 구현이며, 실제 트렌드 수집 및 이미지 렌더링은 추가 개발이 필요합니다.
- 모든 중간 산출물은 파일 기반으로 저장되므로, 각 단계의 진행 상황을 폴더에서 확인할 수 있습니다.
