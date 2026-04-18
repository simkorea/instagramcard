"""image-exporter.py

SCV 스크립트: `/output/html/*.html`을 PNG로 변환하여
`/output/YYYYMMDD_주제명/` 폴더에 저장합니다.

요구사항: pip install playwright
"""

import sys
import struct
import zlib
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

HTML_DIR = Path("output/html")
BASE_OUTPUT_DIR = Path("output")
LOG_DIR = Path("output/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_error(message: str) -> None:
    """에러 메시지를 로그 파일에 기록합니다."""
    log_file = LOG_DIR / "error.log"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")


def create_fallback_png(path: Path, width: int = 1080, height: int = 1350,
                       color: Tuple[int, int, int] = (255, 255, 255)) -> None:
    """Playwright가 없을 때 대체용 흰색 PNG를 생성합니다."""
    row = b"\x00" + bytes(color) * width
    raw_data = row * height
    compressed = zlib.compress(raw_data)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png_data = b"\x89PNG\r\n\x1a\n"

    length = struct.pack(">I", len(ihdr))
    crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF)
    png_data += length + b"IHDR" + ihdr + crc

    length = struct.pack(">I", len(compressed))
    crc = struct.pack(">I", zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF)
    png_data += length + b"IDAT" + compressed + crc

    crc = struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    png_data += b"\x00\x00\x00\x00IEND" + crc

    with path.open("wb") as f:
        f.write(png_data)


async def render_with_playwright(html_files: List[Path], target_dir: Path) -> Tuple[int, int]:
    """Playwright를 사용하여 여러 HTML 파일을 PNG로 변환합니다."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        log_error("Playwright not installed")
        raise

    conversion_count = 0
    fallback_count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1080, "height": 1350})
        page = await context.new_page()

        for html_path in html_files:
            png_path = target_dir / html_path.with_suffix(".png").name
            try:
                await page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
                await page.set_viewport_size({"width": 1080, "height": 1350})
                await page.screenshot(path=str(png_path), clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
                print(f"✅ {png_path.name}")
                conversion_count += 1
            except Exception as e:
                error_msg = f"Playwright rendering failed ({html_path.name}): {str(e)}"
                print(f"❌ {error_msg}")
                log_error(error_msg)
                create_fallback_png(png_path)
                print(f"⚠️ {png_path.name} created as fallback")
                fallback_count += 1

        await browser.close()

    return conversion_count, fallback_count


def export_images(topic_name: str) -> Path:
    """출력 폴더를 생성합니다."""
    sanitized = topic_name.replace(" ", "_").replace("/", "-")
    today = datetime.now().strftime("%Y%m%d")
    target_dir = BASE_OUTPUT_DIR / f"{today}_{sanitized}"
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def main() -> bool:
    """이미지 내보내기 메인 함수."""
    try:
        topic_name = sys.argv[1] if len(sys.argv) > 1 else "card-news"
        target_dir = export_images(topic_name)

        print(f"PNG 변환 시작...")
        print(f"출력 폴더: {target_dir}")

        if not HTML_DIR.exists():
            raise FileNotFoundError(f"HTML 폴더 없음: {HTML_DIR}")

        html_files = sorted(HTML_DIR.glob("slide-*.html"))
        if not html_files:
            raise FileNotFoundError(f"HTML 파일 없음: {HTML_DIR}")

        print(f"발견: {len(html_files)}개 HTML 파일\n")

        try:
            conversion_count, fallback_count = asyncio.run(render_with_playwright(html_files, target_dir))
        except ImportError:
            print("⚠️ Playwright 미설치. 대체 PNG로 전환합니다.")
            conversion_count = 0
            fallback_count = 0
            for html_path in html_files:
                png_path = target_dir / html_path.with_suffix(".png").name
                create_fallback_png(png_path)
                print(f"⚠️ {png_path.name} (대체용)")
                fallback_count += 1

        print(f"\n✅ 완료: {conversion_count}개 PNG 변환, {fallback_count}개 대체 생성")
        print(f"저장 경로: {target_dir}")
        return True

    except Exception as e:
        error_msg = f"[main] {str(e)}"
        print(f"❌ 오류: {error_msg}")
        log_error(error_msg)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
