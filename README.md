# 카드뉴스 자동화 에이전트

## 개요

이 저장소는 퇴사 희망자 및 1인 비즈니스 예비 창업가를 위한 카드뉴스 자동화 시스템 설계를 담고 있습니다.

- 입력: 키워드 또는 자유 명령
- 출력: 1080×1350 PNG 카드뉴스 6~8장 + 슬라이드 스크립트 `.md`
- 구성: CEO 오케스트레이션 + 전문가 역할 + SCV 스크립트

## 주요 파일

- `CLAUDE.md`: 전체 에이전트 오케스트레이션 및 조직도
- `.claude/staff/experts/*`: 리서처, 콘텐츠 기획자, 카피라이터 역할 정의
- `.claude/references/*`: 타겟 오디언스, 톤앤매너, 슬라이드 템플릿
- `.claude/scv/trend-collector.py`: 트렌드 수집
- `.claude/scv/html-renderer.py`: Markdown → HTML 변환
- `.claude/scv/image-exporter.py`: HTML → PNG 변환
- `run_agent.py`: 파이프라인 연결 실행기
- `run-pipeline.ps1`: Windows PowerShell 전체 파이프라인 시뮬레이션

## 요구 사항

- Windows 10/11 환경
- Python 3.x
- PowerShell
- Playwright는 선택 사항이며, 실제 HTML→PNG 변환이 필요할 때 설치합니다.

## 설치

1. Python 설치 확인

```powershell
python --version
```

2. 필요 시 Python 설치

- Python.org 또는 Windows Store에서 Python 3.11 이상 설치

3. Playwright 설치 (선택)

```powershell
python -m pip install playwright
python -m playwright install
```

## 실행 방법

### 1) 전체 파이프라인 실행 (Windows PowerShell)

```powershell
cd "c:\다운로드\ai등 공부 자료 및 잡동\instagramcard"
PowerShell -NoProfile -ExecutionPolicy Bypass -File .\run-pipeline.ps1
```

이 스크립트는 다음을 자동으로 생성합니다.

- `output/data/trends.json`
- `output/data/topic-candidates.md`
- `output/data/selected-topic.json`
- `output/drafts/slide-plan.md`
- `output/drafts/script-final.md`
- `output/html/slide-01.html` ~ `slide-07.html`
- `output/20260411_Freelancer/slide-01.png` ~ `slide-07.png`

### 2) 개별 스크립트 실행

```powershell
cd "c:\다운로드\ai등 공부 자료 및 잡동\instagramcard"
python .claude\scv\trend-collector.py
python .claude\scv\html-renderer.py
python .claude\scv\image-exporter.py "Freelancer"
```

`image-exporter.py`는 Playwright가 설치되어 있지 않으면 대체 PNG를 생성합니다.

## 출력 구조

- `output/data/trends.json`
- `output/data/topic-candidates.md`
- `output/data/selected-topic.json`
- `output/drafts/slide-plan.md`
- `output/drafts/script-final.md`
- `output/html/slide-01.html` ~ `slide-07.html`
- `output/20260411_Freelancer/slide-01.png` ~ `slide-07.png`
- `output/logs/error.log`

## 주의 사항

- 현재 `run-pipeline.ps1`는 Windows 환경을 기준으로 전체 플로우를 시뮬레이션합니다.
- `trend-collector.py`는 현재 실제 API 호출 대신 샘플 데이터를 생성합니다.
- 고품질 PNG 렌더링은 `playwright` 기반 설정이 필요합니다.

## 다음 단계

- `trend-collector.py`에 Google Trends / YouTube / Naver API 연동
- `image-exporter.py`를 실제 Playwright 렌더링으로 전환
- `CLAUDE.md` 기반 Claude Code 에이전트 실행 환경 구성
