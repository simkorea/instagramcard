# 입력 데이터 전처리 — PDF·HTML → Markdown 변환 지침

> 부동산 분양 공고문(PDF), 뉴스 웹페이지(HTML) 등 외부 데이터를 입력받을 때  
> **분석 전에 반드시 Markdown으로 변환**합니다. 변환 없이 바로 분석 금지.

---

## 원칙

```
입력(PDF / HTML / URL)
        ↓
  Markdown 변환 (.md 저장)
        ↓
  변환 결과 검토 (표·수치·날짜 누락 여부 확인)
        ↓
  분석·스크립트 작성 시작
```

- 변환 파일 저장 경로: `output/data/raw/원본파일명.md`
- 변환 완료 전까지 스크립트·요약·분석 작업 시작 금지
- 변환 후 수치·표·날짜가 정상 추출됐는지 육안 확인 필수

---

## 도구 선택 기준

| 입력 형식 | 1순위 도구 | 2순위 도구 | 비고 |
|---------|----------|----------|------|
| PDF (분양공고, 정책문서) | `marker` | `markitdown` | marker가 표·레이아웃 보존 우수 |
| HTML (뉴스, 블로그) | `markitdown` | `html2text` | markitdown이 노이즈 제거 우수 |
| URL (웹페이지 직접) | `markitdown` | `trafilatura` | URL 직접 입력 지원 |
| DOCX / PPTX | `markitdown` | `pandoc` | Office 계열 통합 지원 |

---

## 도구별 설치 및 사용법

### 1. marker (PDF 전용 — 최우선)

레이아웃·표·컬럼 구조를 가장 잘 보존하는 PDF → Markdown 변환기.

```bash
# 설치
pip install marker-pdf

# 사용 (단일 파일)
marker_single input.pdf --output_dir output/data/raw/

# 사용 (폴더 전체)
marker input_folder/ --output_dir output/data/raw/ --workers 4
```

출력: `output/data/raw/input/input.md`

---

### 2. markitdown (PDF·HTML·URL·Office 통합)

Microsoft 오픈소스. PDF·HTML·DOCX·PPTX·URL 모두 지원.

```bash
# 설치
pip install markitdown

# PDF 변환
markitdown input.pdf -o output/data/raw/input.md

# HTML 파일 변환
markitdown input.html -o output/data/raw/input.md

# URL 직접 변환 (뉴스 페이지)
markitdown "https://news.example.com/article" -o output/data/raw/article.md
```

Python에서 직접 호출:
```python
from markitdown import MarkItDown

md = MarkItDown()

# PDF
result = md.convert("분양공고문.pdf")

# URL
result = md.convert("https://news.example.com/article")

output_path = "output/data/raw/분양공고문.md"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(result.text_content)
print(f"변환 완료: {output_path}")
```

---

### 3. html2text (HTML 전용 — 경량)

```bash
# 설치
pip install html2text

# CLI
html2text input.html > output/data/raw/input.md

# URL에서 직접
html2text "https://news.example.com/article" > output/data/raw/article.md
```

Python:
```python
import html2text, requests

h = html2text.HTML2Text()
h.ignore_links = False
h.ignore_images = True

# URL에서 HTML 가져와 변환
html = requests.get("https://news.example.com/article").text
md_text = h.handle(html)

with open("output/data/raw/article.md", "w", encoding="utf-8") as f:
    f.write(md_text)
```

---

### 4. trafilatura (뉴스·블로그 URL 특화)

광고·메뉴·사이드바 등 노이즈 제거에 특화. 뉴스 본문 추출 최적화.

```bash
# 설치
pip install trafilatura

# URL에서 본문만 추출 → Markdown
trafilatura --url "https://news.example.com/article" --output-format markdown \
  > output/data/raw/article.md
```

Python:
```python
import trafilatura

downloaded = trafilatura.fetch_url("https://news.example.com/article")
md_text = trafilatura.extract(downloaded, output_format="markdown", include_tables=True)

with open("output/data/raw/article.md", "w", encoding="utf-8") as f:
    f.write(md_text)
```

---

## 변환 후 품질 검토 체크리스트

변환된 `.md` 파일을 열어 아래 항목을 확인합니다.

| 항목 | 확인 내용 |
|------|---------|
| **수치** | 금리 %, LTV %, 가격, 면적(㎡) 등 숫자가 정상 추출됐는가 |
| **표** | 분양가·공급 세대수 표가 Markdown 표로 변환됐는가 |
| **날짜** | 공급 일정, 시행일, 접수 기간이 누락 없이 포함됐는가 |
| **단위** | 만 원·억 원·㎡ 등 단위가 숫자와 분리되지 않았는가 |
| **노이즈** | 광고·메뉴·푸터 텍스트가 본문에 섞이지 않았는가 |

검토 실패 시: 다른 도구로 재변환 또는 수동 보정 후 분석 진행.

---

## 전처리 완료 후 저장 규칙

```bash
# 변환 완료 파일 저장 위치
output/data/raw/원본파일명.md

# state.json에 입력 데이터 기록 (선택)
"inputFiles": ["output/data/raw/분양공고문.md"]
```

변환된 파일 경로를 리서처에게 전달하면 이후 분석·스크립트 작성을 시작합니다.
