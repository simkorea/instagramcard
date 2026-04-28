"""run_agent.py

카드뉴스 자동화 파이프라인의 기본 실행기입니다.
이 스크립트는 설계 단계에서 전체 플로우를 연결하고,
중간 결과물을 `/output/`에 저장합니다.
"""

import json
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("output")
DATA_DIR = OUTPUT_DIR / "data"
DRAFTS_DIR = OUTPUT_DIR / "drafts"
HTML_DIR = OUTPUT_DIR / "html"
LOG_DIR = OUTPUT_DIR / "logs"

for path in (DATA_DIR, DRAFTS_DIR, HTML_DIR, LOG_DIR):
    path.mkdir(parents=True, exist_ok=True)


def collect_trends(keyword: str | None = None) -> dict:
    """트렌드 수집 결과를 생성합니다."""
    return {
        "keyword": keyword or "auto",
        "channels": {
            "instagram": [
                {"title": "퇴사 준비 체크리스트", "source": "instagram", "url": None, "summary": "퇴사 준비 시점에 확인해야 할 필수 항목입니다."},
                {"title": "프리랜서 첫 수입 만들기", "source": "instagram", "url": None, "summary": "초보 프리랜서를 위한 첫 수익 확보 팁입니다."},
            ],
            "youtube": [
                {"title": "1인 비즈니스 성장 전략", "source": "youtube", "url": None, "summary": "소규모 사업 성장에 필요한 핵심 전략을 다룹니다."},
                {"title": "퇴사 후 월 200만원 만드는 방법", "source": "youtube", "url": None, "summary": "퇴사 후에도 수입을 만드는 실전 방법을 설명합니다."},
            ],
            "naver": [
                {"title": "부업으로 안정적 수익 내는 법", "source": "naver", "url": None, "summary": "안정적인 부업 구조를 만드는 방법을 정리합니다."},
                {"title": "창업 아이템 검증 체크포인트", "source": "naver", "url": None, "summary": "초기 아이템 검증 시 확인해야 할 사항을 안내합니다."},
            ],
        },
    }


def save_json(data: dict, path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log_error(message: str) -> None:
    log_path = LOG_DIR / "error.log"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(message + "\n")


def generate_topic_candidates(trends: dict) -> list[dict]:
    """리서처가 주제 후보를 도출합니다."""
    return [
        {
            "title": "퇴사 후 첫 달, 안정적으로 시작하는 체크리스트",
            "insight": "퇴사 전후에 반드시 준비해야 할 5가지 실무 요소를 정리합니다.",
        },
        {
            "title": "프리랜서 초보가 첫 수익을 만드는 3단계",
            "insight": "신뢰도 높은 포트폴리오 대신 할 수 있는 실전 행동을 제시합니다.",
        },
        {
            "title": "1인 비즈니스로 월 100만원 만드는 기본 구조",
            "insight": "작은 시도부터 수익으로 연결하는 단계별 로드맵을 보여줍니다.",
        },
    ]


def save_topic_candidates(candidates: list[dict], path: Path) -> None:
    lines = ["# 주제 후보 목록\n"]
    for index, item in enumerate(candidates, start=1):
        lines.append(f"## {index}. {item['title']}\n")
        lines.append(f"- 인사이트: {item['insight']}\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def select_topic(candidates: list[dict]) -> dict:
    print("주제 후보:")
    for index, item in enumerate(candidates, start=1):
        print(f"{index}. {item['title']}")
        print(f"   인사이트: {item['insight']}\n")

    while True:
        choice = input("원하는 주제 번호를 입력하세요 [1-{}]: ".format(len(candidates)))
        if choice.isdigit() and 1 <= int(choice) <= len(candidates):
            return candidates[int(choice) - 1]
        print("유효한 번호를 입력해 주세요.")


def plan_slides(topic: dict) -> list[dict]:
    return [
        {
            "role": "cover",
            "title": topic["title"],
            "subtitle": topic["insight"],
            "body": "퇴사 직후에도 흔들리지 않는 준비 전략을 카드뉴스로 정리합니다.",
        },
        {
            "role": "body",
            "title": "1. 핵심 준비 항목",
            "subtitle": "무엇을 먼저 점검해야 할까?",
            "body": "자금, 업무 정리, 시장 조사, 플랫폼 준비, 일정 설계 순으로 확인하세요.",
        },
        {
            "role": "body",
            "title": "2. 첫 수익 연결 포인트",
            "subtitle": "작은 시작이 큰 차이를 만듭니다.",
            "body": "클라이언트 제안서, 콘텐츠 테스트, 소셜 프로필 검증이 중요합니다.",
        },
        {
            "role": "body",
            "title": "3. 실패 리스크 줄이는 방법",
            "subtitle": "불확실성을 관리하는 실전 팁",
            "body": "고정 지출 최소화, 초기 고객 확보, 반복 가능한 작업 구조를 만드세요.",
        },
        {
            "role": "body",
            "title": "4. 다음 행동",
            "subtitle": "오늘 당장 할 수 있는 실천",
            "body": "현 상황 점검표 작성, 첫 고객 리스트 만들기, 1주일 목표 설정하기.",
        },
        {
            "role": "closing",
            "title": "정리와 다음 단계",
            "subtitle": "작은 준비가 큰 변화를 만듭니다.",
            "body": "이제 핵심 항목을 하나씩 체크하고, 카드뉴스 내용을 실제 행동으로 연결하세요.",
        },
    ]


def save_slide_plan(slide_plan: list[dict], path: Path) -> None:
    lines = ["# 슬라이드 구성안\n"]
    for index, slide in enumerate(slide_plan, start=1):
        lines.append(f"## 슬라이드 {index}\n")
        lines.append(f"- 역할: {slide['role']}\n")
        lines.append(f"- 제목: {slide['title']}\n")
        lines.append(f"- 서브타이틀: {slide['subtitle']}\n")
        lines.append(f"- 요약: {slide['body']}\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def save_script_final(slide_plan: list[dict], path: Path) -> None:
    lines = []
    for index, slide in enumerate(slide_plan, start=1):
        lines.append("---")
        lines.append(f"title: {slide['title']}")
        lines.append(f"subtitle: {slide['subtitle']}")
        lines.append(f"body: {slide['body']}")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main() -> None:
    print("카드뉴스 자동화 에이전트를 실행합니다.")
    keyword = input("키워드를 입력하세요 (비워두면 자동 트렌드 수집): ").strip() or None

    trends = collect_trends(keyword)
    save_json(trends, DATA_DIR / "trends.json")
    print("트렌드 데이터를 저장했습니다: output/data/trends.json")

    candidates = generate_topic_candidates(trends)
    save_topic_candidates(candidates, DATA_DIR / "topic-candidates.md")
    print("주제 후보를 저장했습니다: output/data/topic-candidates.md")

    selected_topic = select_topic(candidates)
    save_json(selected_topic, DATA_DIR / "selected-topic.json")
    print("선택된 주제를 저장했습니다: output/data/selected-topic.json")
    print(f"선택된 주제: {selected_topic['title']}\n")

    slide_plan = plan_slides(selected_topic)
    save_slide_plan(slide_plan, DRAFTS_DIR / "slide-plan.md")
    print("슬라이드 구성안을 저장했습니다: output/drafts/slide-plan.md")

    save_script_final(slide_plan, DRAFTS_DIR / "script-final.md")
    print("최종 스크립트를 저장했습니다: output/drafts/script-final.md")

    print("HTML 렌더링 및 PNG 변환은 `.claude/scv/` 스크립트를 실행하세요.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log_error(f"[run_agent] {exc}")
        raise
