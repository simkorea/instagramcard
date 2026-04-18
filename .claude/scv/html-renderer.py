"""html-renderer.py

SCV 스크립트: `/output/drafts/script-final.md`를 읽고
카드뉴스 HTML 파일을 생성합니다.

디자인은 1080x1350px 미니멀 레이아웃을 목표로 합니다.
"""

import sys
from pathlib import Path
from datetime import datetime

INPUT_FILE = Path("output/drafts/script-final.md")
OUTPUT_DIR = Path("output/html")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = Path("output/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def parse_script(md_path: Path) -> list[dict]:
    """Markdown 스크립트를 슬라이드 단위로 파싱합니다."""
    content = md_path.read_text(encoding="utf-8")
    slides = []
    current = {}

    for line in content.splitlines():
        line = line.strip()
        if line == "---":
            if current:
                slides.append(current)
                current = {}
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = value.strip()
    if current:
        slides.append(current)
    return slides


def render_cover_slide(slide: dict, index: int) -> str:
    """커버 슬라이드 HTML을 생성합니다."""
    title = slide.get("title", "")
    subtitle = slide.get("subtitle", "")
    
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>Slide {index:02d} - Cover</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      width: 1080px;
      height: 1350px;
      background: #ffffff;
      font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      color: #1a1a1a;
    }}
    .container {{
      width: 100%;
      height: 100%;
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 40px;
      padding: 80px;
      align-items: center;
    }}
    .hero {{
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}
    .title {{
      font-size: 88px;
      font-weight: 800;
      line-height: 1.05;
      word-break: keep-all;
      letter-spacing: -1px;
    }}
    .subtitle {{
      font-size: 38px;
      font-weight: 500;
      line-height: 1.5;
      color: #4d5260;
      word-break: keep-all;
    }}
    .hero-tag {{
      display: inline-block;
      padding: 14px 24px;
      border-radius: 999px;
      background: #0f5be0;
      color: white;
      font-size: 22px;
      font-weight: 700;
      letter-spacing: -0.2px;
      width: fit-content;
    }}
    .visual-card {{
      width: 100%;
      min-height: 680px;
      border-radius: 40px;
      background: linear-gradient(180deg, #eaf1ff 0%, #ffffff 100%);
      padding: 40px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-shadow: 0 30px 70px rgba(20, 40, 90, 0.08);
    }}
    .photo-box {{
      height: 360px;
      border-radius: 32px;
      background: rgba(255, 255, 255, 0.75);
      border: 2px dashed rgba(15, 91, 224, 0.35);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #23357d;
      font-size: 34px;
      font-weight: 700;
      text-align: center;
      padding: 20px;
    }}
    .info-box {{
      display: grid;
      gap: 18px;
      margin-top: 20px;
    }}
    .stat-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      font-size: 28px;
      font-weight: 600;
      color: #1a1a1a;
    }}
    .stat-graph {{
      flex: 1;
      height: 18px;
      background: #d9e5ff;
      border-radius: 999px;
      overflow: hidden;
    }}
    .stat-fill {{
      height: 100%;
      border-radius: 999px;
      background: #0f5be0;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="hero">
      <span class="hero-tag">AI 도구로 수익 만들기</span>
      <h1 class="title">{title}</h1>
      <p class="subtitle">{subtitle}</p>
    </div>
    <div class="visual-card">
      <div class="photo-box">사진 또는 인포그래픽 영역</div>
      <div class="info-box">
        <div class="stat-row"><span>아이디어 검증</span><span>78%</span></div>
        <div class="stat-graph"><div class="stat-fill" style="width: 78%;"></div></div>
        <div class="stat-row"><span>초기 수익</span><span>63%</span></div>
        <div class="stat-graph"><div class="stat-fill" style="width: 63%;"></div></div>
        <div class="stat-row"><span>실행력</span><span>85%</span></div>
        <div class="stat-graph"><div class="stat-fill" style="width: 85%;"></div></div>
      </div>
    </div>
  </div>
</body>
</html>"""


def render_body_slide(slide: dict, index: int) -> str:
    """본문 슬라이드 HTML을 생성합니다."""
    subtitle = slide.get("subtitle", "")
    body = slide.get("body", "")
    emphasis = slide.get("emphasis", "")
    
    emphasis_html = f'<p class="emphasis">{emphasis}</p>' if emphasis else ""
    
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>Slide {index:02d}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      width: 1080px;
      height: 1350px;
      background: #ffffff;
      font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      color: #1a1a1a;
    }}
    .container {{
      width: 100%;
      height: 100%;
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 40px;
      padding: 80px;
      align-items: center;
    }}
    .text-area {{
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}
    .subtitle {{
      font-size: 64px;
      font-weight: 800;
      line-height: 1.05;
      word-break: keep-all;
      color: #1a1a1a;
    }}
    .body {{
      font-size: 40px;
      font-weight: 400;
      line-height: 1.7;
      color: #333333;
      word-break: keep-all;
    }}
    .visual-card {{
      width: 100%;
      border-radius: 38px;
      background: #f7f9ff;
      padding: 36px;
      display: grid;
      gap: 26px;
      box-shadow: 0 26px 60px rgba(18, 44, 90, 0.08);
    }}
    .photo-box {{
      height: 360px;
      border-radius: 32px;
      background: rgba(255, 255, 255, 0.9);
      border: 2px dashed #b7c4f4;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #1f3f83;
      font-size: 30px;
      font-weight: 700;
      text-align: center;
      padding: 20px;
    }}
    .infographic {{
      display: grid;
      gap: 18px;
    }}
    .bar-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      font-size: 28px;
      color: #2a3568;
      font-weight: 700;
    }}
    .chart-track {{
      flex: 1;
      height: 18px;
      background: #d8e1ff;
      border-radius: 999px;
      overflow: hidden;
    }}
    .chart-fill {{
      height: 100%;
      border-radius: 999px;
      background: #0f5be0;
    }}
    .emphasis {{
      font-size: 36px;
      font-weight: 700;
      color: #0f4fbf;
      background: #e9efff;
      padding: 24px 28px;
      border-radius: 26px;
      line-height: 1.4;
      word-break: keep-all;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="text-area">
      <h2 class="subtitle">{subtitle}</h2>
      <p class="body">{body}</p>
      {emphasis_html}
    </div>
    <div class="visual-card">
      <div class="photo-box">실제 사례를 담은 사진 또는 딥러닝 인포그래픽</div>
      <div class="infographic">
        <div class="bar-row"><span>아이디어</span><span>78%</span></div>
        <div class="chart-track"><div class="chart-fill" style="width: 78%;"></div></div>
        <div class="bar-row"><span>실행</span><span>64%</span></div>
        <div class="chart-track"><div class="chart-fill" style="width: 64%;"></div></div>
        <div class="bar-row"><span>수익화</span><span>52%</span></div>
        <div class="chart-track"><div class="chart-fill" style="width: 52%;"></div></div>
      </div>
    </div>
  </div>
</body>
</html>"""


def render_closing_slide(slide: dict, index: int) -> str:
    """마무리 슬라이드 HTML을 생성합니다."""
    summary = slide.get("summary", "")
    cta = slide.get("cta", "")
    
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>Slide {index:02d} - Closing</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      width: 1080px;
      height: 1350px;
      background: #ffffff;
      font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      color: #1a1a1a;
    }}
    .container {{
      width: 100%;
      height: 100%;
      display: grid;
      grid-template-columns: 1fr 0.95fr;
      gap: 40px;
      padding: 80px;
      align-items: center;
    }}
    .summary-box {{
      display: flex;
      flex-direction: column;
      gap: 32px;
    }}
    .summary {{
      font-size: 64px;
      font-weight: 800;
      line-height: 1.05;
      word-break: keep-all;
      color: #1a1a1a;
    }}
    .cta-box {{
      align-self: start;
      background: #0f5be0;
      color: white;
      border-radius: 40px;
      padding: 40px 48px;
      box-shadow: 0 22px 50px rgba(15, 91, 224, 0.24);
    }}
    .cta {{
      font-size: 38px;
      font-weight: 800;
      line-height: 1.3;
      word-break: keep-all;
    }}
    .visual-card {{
      width: 100%;
      min-height: 600px;
      border-radius: 42px;
      background: linear-gradient(180deg, #eef4ff 0%, #ffffff 100%);
      padding: 36px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      box-shadow: 0 28px 68px rgba(26, 51, 103, 0.09);
    }}
    .photo-box {{
      height: 100%;
      border-radius: 32px;
      background: rgba(255, 255, 255, 0.95);
      border: 2px dashed #adc8ff;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #284481;
      font-size: 34px;
      font-weight: 700;
      text-align: center;
      padding: 30px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="summary-box">
      <div class="summary">{summary}</div>
      <div class="cta-box"><p class="cta">{cta}</p></div>
    </div>
    <div class="visual-card">
      <div class="photo-box">완성된 카드뉴스 미리보기 이미지 또는 인포그래픽</div>
    </div>
  </div>
</body>
</html>"""


def render_slide_html(slide: dict, index: int) -> str:
    """슬라이드 역할에 따라 적절한 HTML을 생성합니다."""
    role = slide.get("role", "body").lower()
    
    if role == "cover":
        return render_cover_slide(slide, index)
    elif role == "closing":
        return render_closing_slide(slide, index)
    else:  # body
        return render_body_slide(slide, index)


def log_error(message: str) -> None:
    """에러 메시지를 로그 파일에 기록합니다."""
    log_file = LOG_DIR / "error.log"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")


def main() -> bool:
    """HTML 슬라이드 생성 메인 함수."""
    try:
        if not INPUT_FILE.exists():
            raise FileNotFoundError(f"입력 파일 없음: {INPUT_FILE}")

        print(f"HTML 슬라이드 생성 시작...")
        
        # 1단계: 스크립트 파싱
        slides = parse_script(INPUT_FILE)
        if not slides:
            raise ValueError("슬라이드를 파싱할 수 없습니다")
        
        print(f"파싱됨: {len(slides)}개 슬라이드")
        
        # 2단계: 각 슬라이드 HTML 생성
        for idx, slide in enumerate(slides, start=1):
            try:
                html_content = render_slide_html(slide, idx)
                html_path = OUTPUT_DIR / f"slide-{idx:02d}.html"
                html_path.write_text(html_content, encoding="utf-8")
                print(f"✅ {html_path.name} 생성")
            except Exception as e:
                error_msg = f"슬라이드 {idx} 생성 실패: {str(e)}"
                print(f"❌ {error_msg}")
                log_error(error_msg)
                raise
        
        print(f"\n✅ 완료: {len(slides)}개 HTML 파일 생성 완료")
        print(f"저장 경로: {OUTPUT_DIR}")
        
        return True
    
    except Exception as e:
        print(f"❌ 오류: {str(e)}")
        log_error(f"[main] {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
