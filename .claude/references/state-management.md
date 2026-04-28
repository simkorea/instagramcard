# state.json 상태 관리 레퍼런스

> CLAUDE.md 세션 재개 섹션의 세부 스펙. 구현 시 이 파일을 참조합니다.

---

## state.json 전체 스키마

```json
{
  "currentStage": 3,
  "completedStages": [1, 2],
  "mode": "keyword",
  "selectedTopic": "주제명",
  "outputFolder": "output/final/YYYYMMDD_주제명",
  "startedAt": "2026-04-23T10:00:00+09:00",
  "updatedAt": "2026-04-23T10:30:00+09:00",
  "instagramUrl": null,
  "threadsUrl": null,
  "decisions": {
    "stage2_research": {
      "keyFacts": ["핵심 사실 1", "핵심 사실 2"],
      "numbers": ["LTV 70%", "최대 6억"],
      "sources": ["출처1", "출처2"],
      "verifiedAt": "2026-04-23T10:05:00+09:00"
    },
    "stage3_plan": {
      "slideCount": 7,
      "slides": [
        {"num": 1, "role": "cover",   "title": "커버 제목"},
        {"num": 2, "role": "body",    "title": "슬라이드 2 소제목"},
        {"num": 7, "role": "closing", "title": "CTA 제목"}
      ]
    },
    "stage4_script": {
      "coverTitle": "커버 제목 (20자 이내)",
      "emphasis": ["강조 문구 1", "강조 문구 2"],
      "ctaText": "CTA 문구",
      "narrationFile": "output/drafts/narration.txt"
    },
    "stage5_design": {
      "imagesGenerated": ["output/assets/images/leonardo-slide-1.png"],
      "htmlFiles": ["output/drafts/slides/slide-1.html"]
    },
    "stage6_png": {
      "pngFiles": ["output/final/YYYYMMDD_주제명/slide-1.png"],
      "allConverted": true
    },
    "stage7_review": {
      "approved": true,
      "issues": []
    }
  }
}
```

---

## save_state 헬퍼 함수

```python
import json, datetime
from pathlib import Path

def save_state(updates: dict):
    """state.json에 부분 업데이트. decisions는 딥머지."""
    path = Path("output/state.json")
    path.parent.mkdir(exist_ok=True)
    state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    # decisions 딥머지 (기존 키 보존)
    if "decisions" in updates:
        state.setdefault("decisions", {}).update(updates.pop("decisions"))

    state.update(updates)
    state["updatedAt"] = datetime.datetime.now().astimezone().isoformat()
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[state] stage {state.get('currentStage')} 저장 완료")
```

---

## 단계별 저장 예시

### 2단계 리서치 완료

```python
save_state({
    "currentStage": 3,
    "completedStages": [1, 2],
    "decisions": {
        "stage2_research": {
            "keyFacts": ["생애최초 LTV 70% (2025.6.27 시행)", "수도권 한도 최대 6억"],
            "numbers": ["LTV 70%", "6억", "DSR 40%"],
            "sources": ["국토교통부 보도자료", "금융위원회 공지"],
            "verifiedAt": datetime.datetime.now().astimezone().isoformat()
        }
    }
})
```

### 3단계 기획 완료

```python
save_state({
    "currentStage": 4,
    "completedStages": [1, 2, 3],
    "decisions": {
        "stage3_plan": {
            "slideCount": 7,
            "slides": [
                {"num": 1, "role": "cover",   "title": "생애최초 6억 대출 가능해졌다"},
                {"num": 2, "role": "body",    "title": "뭐가 달라졌나?"},
                {"num": 7, "role": "closing", "title": "지금이 기회입니다"}
            ]
        }
    }
})
```

### 8단계 업로드 완료

```python
save_state({
    "currentStage": 9,
    "completedStages": [1,2,3,4,5,6,7,8],
    "instagramUrl": "https://www.instagram.com/p/XXXXXXX/",
    "threadsUrl":   "https://www.threads.com/@aptshowhome/post/XXXXXXX"
})
```

---

## /clear 후 복구 대화 예시

```
[세션 시작]
CEO → output/state.json 읽기
    → currentStage: 4, selectedTopic: "생애최초 대출 6억"

출력:
"생애최초 대출 6억 작업을 4단계(스크립트 작성)부터 재개합니다.

이전 결정 요약:
- 슬라이드: 7장 (커버 1 + 본문 5 + CTA 1)
- 커버 제목: '생애최초 6억 대출 가능해졌다'
- 핵심 수치: LTV 70%, 최대 6억, DSR 40%
- 출처: 국토교통부, 금융위원회 (2025.6.27 확인)

카피라이터에게 스크립트 작성을 지시하겠습니다."
```
