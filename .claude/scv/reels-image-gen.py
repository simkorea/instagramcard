#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reels-image-gen.py — 릴스 전용 시네마틱 이미지 자동 생성 (9:16 세로)

나레이션 텍스트를 분석해 슬라이드별 Leonardo Vision XL 프롬프트를 생성하고
output/assets/images/reels/ 폴더에 slide-{N}.png 로 저장합니다.

사용법:
  python .claude/scv/reels-image-gen.py
  python .claude/scv/reels-image-gen.py --slides 1 3 5   # 특정 슬라이드만
"""

import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os, time, argparse, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("LEONARDO_API_KEY")

# ─── 9:16 릴스 규격 ───────────────────────────────────────────────────────────
REELS_W = 864    # 9:16 (864/1536 = 0.5625)
REELS_H = 1536

MODEL_ID = "5c232a9e-9061-4777-980a-ddc8e65647c6"   # Leonardo Vision XL (실사 특화)

OUTPUT_DIR = Path("output/assets/images/reels")

# ─── 네거티브 프롬프트 (고정) ─────────────────────────────────────────────────
NEGATIVE_PROMPT = (
    "text, letters, words, numbers, captions, watermark, logo, signature, "
    "typography, subtitles, labels, banners, signs, writing, inscriptions, "
    "distortion, deformed, warped, stretched, skewed, fisheye, lens distortion, "
    "bad proportions, unrealistic perspective, cropped, out of frame, "
    "blurry, low quality, jpeg artifacts, noise, grain, overexposed, underexposed, "
    "cartoon, illustration, painting, drawing, anime, 3d render, cgi, "
    "people, faces, persons, crowd, human figures"
)

# ─── 슬라이드별 시네마틱 프롬프트 ────────────────────────────────────────────
# 나레이션 매핑:
#  1: 코스피 6400 / 부동산 기차 (Hook)
#  2: 코스피 최고가 경신 (주식 불장 비주얼)
#  3: 주식-부동산 상관계수 0.86 (데이터/연결)
#  4: 부동산 상승 예고 (상승 무드)
#  5: 입주물량 30% 급감 + 금리 동결 (공급 부족)
#  6: 외곽 강세 vs 강남 조정 (지역 대비)
#  7: CTA — 균형 포트폴리오 (마무리 클로징)

PROMPTS = {
    1: (
        "Dramatic Seoul night skyline viewed from below looking upward, "
        "luxury high-rise apartment towers illuminated with warm golden lights "
        "against deep indigo sky, stock market LED ticker glowing green in "
        "foreground bokeh, cinematic vertical composition 9:16, "
        "architectural photography, ultra-wide angle upward shot, "
        "city lights reflecting off glass facades, depth of field, "
        "8k resolution, photorealistic, cinematic lighting, no people"
    ),
    2: (
        "Massive digital stock market display showing soaring bullish chart "
        "with bright green upward arrow, Seoul financial district glass towers "
        "at night in background, dramatic neon and LED lighting, "
        "dynamic energy atmosphere, vertical 9:16 composition, "
        "cinematic ultra-wide shot, 8k resolution, photorealistic, "
        "high fidelity, dramatic shadows, no people"
    ),
    3: (
        "Aerial drone shot looking straight down on a dense Seoul apartment "
        "complex neighborhood at golden hour, geometric pattern of rooftops "
        "and streets, warm amber sunlight casting long shadows, "
        "premium residential district, vertical 9:16 bird-eye composition, "
        "8k resolution, photorealistic, cinematic lighting, architectural photography, "
        "depth and scale, no people"
    ),
    4: (
        "Luxury Seoul apartment tower exterior at sunset with dramatic "
        "orange and purple cinematic sky, modern glass facade reflecting "
        "clouds and city, upward perspective shot from street level, "
        "premium real estate atmosphere, golden hour lighting, "
        "9:16 vertical composition looking skyward, "
        "8k resolution, photorealistic, ultra-detailed, no people"
    ),
    5: (
        "Minimalist luxury bank interior with soaring marble columns "
        "and dramatic spotlights, empty grand hall suggesting exclusivity "
        "and scarcity, warm gold accent lighting, polished floors reflecting "
        "ceiling lights, cinematic architectural photography, "
        "9:16 vertical composition, 8k resolution, photorealistic, "
        "premium financial institution atmosphere, no people"
    ),
    6: (
        "Cinematic split-view Seoul urban landscape at dusk, outer district "
        "mid-rise apartments glowing warmly in foreground sharply contrasted "
        "against shadowed Gangnam high-rises in distance, "
        "dramatic golden light vs cool blue shadow, "
        "urban documentary photography style, 9:16 vertical composition, "
        "8k resolution, photorealistic, cinematic depth of field, no people"
    ),
    7: (
        "Elegant modern Seoul apartment living room with floor-to-ceiling "
        "panoramic windows overlooking glittering city night skyline, "
        "sophisticated luxury interior with warm ambient lighting, "
        "premium real estate lifestyle, aspirational home atmosphere, "
        "9:16 vertical composition, 8k resolution, photorealistic, "
        "cinematic lighting, ultra-detailed interior, no people"
    ),
}


def generate_image(prompt: str, slide_num: int, retry: int = 2) -> Path | None:
    """Leonardo API로 이미지 생성 후 저장. 실패 시 retry회 재시도."""
    url     = "https://cloud.leonardo.ai/api/rest/v1/generations"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "height":          REELS_H,
        "width":           REELS_W,
        "modelId":         MODEL_ID,
        "prompt":          prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "num_images":      1,
        "promptMagic":     True,
    }

    for attempt in range(1, retry + 2):
        try:
            print(f"  [{slide_num}] 생성 요청 (시도 {attempt})...", flush=True)
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            gen_id = resp.json()["sdGenerationJob"]["generationId"]
            print(f"  [{slide_num}] ID: {gen_id}")

            # 폴링 (최대 120초)
            for _ in range(24):
                time.sleep(5)
                check = requests.get(
                    f"https://cloud.leonardo.ai/api/rest/v1/generations/{gen_id}",
                    headers=headers, timeout=15,
                )
                data = check.json()["generations_by_pk"]
                if data["status"] == "COMPLETE":
                    img_url = data["generated_images"][0]["url"]
                    break
                print("    ...생성 중...", flush=True)
            else:
                print(f"  [{slide_num}] 타임아웃 — 재시도")
                continue

            # 저장
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            out_path = OUTPUT_DIR / f"slide-{slide_num}.png"
            img_data = requests.get(img_url, timeout=30).content
            out_path.write_bytes(img_data)
            print(f"  [{slide_num}] 저장 완료: {out_path}  ({len(img_data)//1024} KB)")
            return out_path

        except Exception as e:
            print(f"  [{slide_num}] 오류: {e}")
            if attempt <= retry:
                time.sleep(3)

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slides", type=int, nargs="*",
                        help="생성할 슬라이드 번호 (미지정 시 전체 1~7)")
    args = parser.parse_args()

    if not API_KEY:
        print("❌ LEONARDO_API_KEY 환경변수 없음 (.env 확인)")
        sys.exit(1)

    targets = args.slides if args.slides else list(PROMPTS.keys())
    print(f"🎨 릴스 전용 이미지 생성 시작 — 슬라이드 {targets}")
    print(f"   규격: {REELS_W}×{REELS_H} (9:16) | 모델: Leonardo Vision XL")
    print(f"   저장 경로: {OUTPUT_DIR}\n")

    results = {}
    for num in targets:
        if num not in PROMPTS:
            print(f"  [{num}] 프롬프트 없음 — 스킵")
            continue
        path = generate_image(PROMPTS[num], num)
        results[num] = path
        print()

    ok    = sum(1 for p in results.values() if p)
    fail  = len(results) - ok
    print(f"\n✅ 생성 완료: {ok}/{len(results)}장 성공" + (f" | ❌ 실패: {fail}장" if fail else ""))

    if ok == len(targets):
        print(f"\n▶ 다음 명령으로 릴스 영상 제작:")
        print(f'  python .claude/scv/video_maker.py \\')
        print(f'    --images-dir "{OUTPUT_DIR}" \\')
        print(f'    --tts --narration output/drafts/narration.txt \\')
        print(f'    --bgm output/assets/bgm.mp3 --sfx \\')
        print(f'    --output output/video/릴스전용_코스피6400.mp4')


if __name__ == "__main__":
    main()
