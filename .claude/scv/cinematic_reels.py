#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cinematic_reels.py — 대본 기반 시네마틱 릴스 완전 자동 제작

사용법:
  python .claude/scv/cinematic_reels.py \
    --narration output/drafts/narration.txt \
    --bgm output/assets/bgm.mp3 \
    --output output/video/final_reels.mp4

script_data 포맷 (코드에서 직접 지정하거나 --script-json 파일로 전달):
  [
    {"visual_prompt": "cinematic Seoul skyline...", "narration": "첫 문장"},
    ...
  ]
"""

import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os, time, argparse, json, asyncio, re, tempfile
from pathlib import Path

import numpy as np
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("LEONARDO_API_KEY")

# ──────────────────────────────────────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────────────────────────────────────
MODEL_ID     = "5c232a9e-9061-4777-980a-ddc8e65647c6"  # Leonardo Vision XL (검증된 모델)
REELS_W      = 864
REELS_H      = 1536   # 9:16 (864/1536 = 0.5625) — API 지원 최대 세로 규격
IMAGE_DIR    = Path("output/assets/images/cinematic")
OUTPUT_DIR   = Path("output/reels")
POLL_INTERVAL = 5
POLL_TIMEOUT  = 120   # 초

NEGATIVE_PROMPT = (
    "text, letters, words, numbers, captions, watermark, logo, signature, "
    "typography, subtitles, labels, banners, signs, writing, inscriptions, "
    "distortion, deformed, warped, stretched, skewed, fisheye, lens distortion, "
    "bad proportions, unrealistic perspective, cropped, out of frame, "
    "blurry, low quality, jpeg artifacts, noise, grain, overexposed, underexposed, "
    "cartoon, illustration, painting, drawing, anime, 3d render, cgi, "
    "people, faces, persons, crowd, human figures"
)

# ──────────────────────────────────────────────────────────────────────────────
# [Step 2] wait_and_download — 폴링 완료 후 이미지 저장
# ──────────────────────────────────────────────────────────────────────────────
def wait_and_download(gen_id: str, slide_idx: int, headers: dict) -> Path | None:
    """
    Leonardo 생성 완료를 폴링하고, 완료 시 이미지를 로컬에 저장합니다.

    Args:
        gen_id:     Leonardo generationId
        slide_idx:  슬라이드 번호 (파일명에 사용)
        headers:    인증 헤더 (API Key 포함)

    Returns:
        저장된 이미지 Path, 실패 시 None
    """
    check_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{gen_id}"
    deadline  = time.time() + POLL_TIMEOUT

    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        try:
            res  = requests.get(check_url, headers=headers, timeout=15)
            data = res.json().get("generations_by_pk", {})
        except Exception as e:
            print(f"    폴링 오류: {e}", flush=True)
            continue

        status = data.get("status", "")
        if status == "COMPLETE":
            images = data.get("generated_images", [])
            if not images:
                print(f"    [{slide_idx}] 완료됐지만 이미지 없음")
                return None

            img_url  = images[0]["url"]
            IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            out_path = IMAGE_DIR / f"slide-{slide_idx}.png"

            img_bytes = requests.get(img_url, timeout=30).content
            out_path.write_bytes(img_bytes)
            print(f"    [{slide_idx}] 저장: {out_path} ({len(img_bytes)//1024} KB)")
            return out_path

        elif status == "FAILED":
            print(f"    [{slide_idx}] 생성 실패 (status=FAILED)")
            return None

        print(f"    [{slide_idx}] 생성 중... ({status})", flush=True)

    print(f"    [{slide_idx}] 타임아웃 ({POLL_TIMEOUT}초)")
    return None


# ──────────────────────────────────────────────────────────────────────────────
# [Step 3] assemble_v5_video — v5 고퀄리티 영상 조립
# ──────────────────────────────────────────────────────────────────────────────
def assemble_v5_video(
    image_paths: list,
    narration_path: str,
    bgm_path: str | None = None,
    tts_voice: str = "ko-KR-HyunsuMultilingualNeural",
    fps: int = 30,
    transition: float = 0.5,
    output_path: str = "output/reels/final_reels.mp4",
):
    """
    v5 고퀄리티 로직으로 영상 조립:
      - Ken Burns 줌인/아웃
      - Zoom-In ↔ Zoom-Out 교대 슬라이드 전환
      - 누적 리듬 자막 (현재 + 직전 세그먼트)
      - 숫자 골드 강조 (#FFD860)
      - BGM 덕킹 (나레이션 중 12%, 무음 40%)
      - SFX Pop 14회 자동 삽입
    """
    # video_maker.py의 검증된 함수 재사용
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from video_maker import (
        generate_tts, make_slide_clip_tts, build_video,
        mix_tts_bgm, _make_sfx_clip,
        AudioFileClip, concatenate_audioclips,
        _trim_and_loop, _clip_set_audio,
        CompositeAudioClip, _clip_set_start, _clip_volume,
        MOVIEPY_V2, BGM_VOL_SPEECH, BGM_VOL_SILENCE,
        DEFAULT_TRANSITION,
    )

    slides = [Path(p) for p in image_paths if p and Path(p).exists()]
    if not slides:
        print("❌ 유효한 이미지 없음")
        return None

    n_slides = len(slides)
    print(f"\n🎬 v5 어셈블리 시작 — 슬라이드 {n_slides}장")

    # ── TTS 생성 ──────────────────────────────────────────────────────────────
    narration_text = Path(narration_path).read_text(encoding='utf-8').strip()
    tts_cache      = Path("output/video/tts_cache")
    tts_audio_path, srt_segments = generate_tts(
        narration_text, tts_voice, tts_cache, use_ssml=False,
    )

    tts_dur   = AudioFileClip(str(tts_audio_path)).duration
    per_slide = tts_dur / n_slides
    print(f"  ⏱️  TTS {tts_dur:.1f}초 → 슬라이드당 {per_slide:.1f}초")

    # ── 슬라이드 클립 생성 (Zoom In-Out 교대) ────────────────────────────────
    clips    = []
    t_offset = 0.0
    for idx, slide_path in enumerate(slides, 1):
        z_type = 'in' if idx % 2 == 1 else 'out'
        print(f"  [{idx}/{n_slides}] {slide_path.name} [zoom-{z_type}]", flush=True)
        clip = make_slide_clip_tts(
            img_path        = slide_path,
            duration        = per_slide,
            fps             = fps,
            srt_segments    = srt_segments,
            t_offset        = t_offset,
            canvas_w        = REELS_W,
            canvas_h        = REELS_H,
            enable_ken_burns= True,
            zoom_type       = z_type,
            trans_dur       = transition,
        )
        clips.append(clip)
        t_offset += per_slide - (transition if idx < n_slides else 0.0)

    # ── 크로스페이드 연결 ────────────────────────────────────────────────────
    print(f"\n🔗 크로스페이드 {transition}s 연결...")
    video = build_video(clips, per_slide, transition, REELS_W, REELS_H)

    # ── TTS + BGM 덕킹 + SFX 믹싱 ────────────────────────────────────────────
    sfx_wav      = _make_sfx_clip(None)   # 자동 합성 Pop 음
    dur          = video.duration
    tts_clip     = _trim_and_loop(AudioFileClip(str(tts_audio_path)), dur)
    if MOVIEPY_V2:
        from moviepy.audio.fx import AudioFadeIn, AudioFadeOut
        tts_clip = tts_clip.with_effects([AudioFadeIn(0.3), AudioFadeOut(0.8)])
    else:
        tts_clip = tts_clip.audio_fadein(0.3).audio_fadeout(0.8)

    audio_tracks = [tts_clip]

    # BGM 덕킹
    if bgm_path and Path(bgm_path).exists():
        from video_maker import build_ducked_bgm
        print(f"  🎚️  BGM 덕킹: 나레이션 {BGM_VOL_SPEECH*100:.0f}% / 무음 {BGM_VOL_SILENCE*100:.0f}%")
        ducked = build_ducked_bgm(bgm_path, srt_segments, dur)
        audio_tracks.append(ducked)

    # SFX Pop
    sfx_count = 0
    for seg in srt_segments:
        t_sfx = seg['start']
        if t_sfx >= dur:
            continue
        sfx_raw = _clip_volume(AudioFileClip(sfx_wav), 0.30)
        sfx_raw = _clip_set_start(sfx_raw, t_sfx)
        audio_tracks.append(sfx_raw)
        sfx_count += 1
    if sfx_count:
        print(f"  🔔 SFX Pop: {sfx_count}회 삽입")

    mixed = CompositeAudioClip(audio_tracks)
    video = _clip_set_audio(video, mixed)

    # ── 렌더링 ────────────────────────────────────────────────────────────────
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cpu = max(4, min(os.cpu_count() or 4, 8))
    print(f"\n🎥 렌더링 → {out}  ({dur:.1f}초 | {fps}fps | threads={cpu})")
    video.write_videofile(
        str(out),
        fps           = fps,
        codec         = "libx264",
        audio_codec   = "aac",
        threads       = cpu,
        preset        = "fast",
        ffmpeg_params = ["-pix_fmt", "yuv420p"],
        logger        = "bar",
    )
    mb = out.stat().st_size / (1024 * 1024)
    print(f"\n✅ 완료! {out}  ({mb:.1f} MB)")
    return str(out)


# ──────────────────────────────────────────────────────────────────────────────
# [Main] generate_cinematic_reels — 전체 파이프라인 오케스트레이터
# ──────────────────────────────────────────────────────────────────────────────
def generate_cinematic_reels(
    script_data: list,
    narration_path: str,
    bgm_path: str | None = None,
    output_path: str = "output/reels/final_reels.mp4",
    skip_existing: bool = True,
):
    """
    대본 기반 시네마틱 릴스 완전 자동 제작.

    Args:
        script_data:    [{"visual_prompt": "...", ...}, ...]
        narration_path: 나레이션 텍스트 파일 경로
        bgm_path:       BGM mp3 경로 (없으면 생략)
        output_path:    최종 영상 출력 경로
        skip_existing:  이미 생성된 이미지가 있으면 재사용

    Returns:
        최종 영상 경로 문자열
    """
    if not API_KEY:
        print("❌ LEONARDO_API_KEY 환경변수 없음")
        return None

    headers = {
        "authorization": f"Bearer {API_KEY}",
        "content-type":  "application/json",
    }

    print(f"🎨 시네마틱 릴스 제작 시작")
    print(f"   슬라이드: {len(script_data)}장 | 규격: {REELS_W}×{REELS_H} (9:16)")
    print(f"   모델: Leonardo Vision XL ({MODEL_ID[:8]}...)\n")

    image_paths = []

    for i, item in enumerate(script_data, 1):
        out_path = IMAGE_DIR / f"slide-{i}.png"

        # 기존 이미지 재사용
        if skip_existing and out_path.exists():
            print(f"  [{i}] 기존 이미지 재사용: {out_path}")
            image_paths.append(out_path)
            continue

        prompt = item.get("visual_prompt", "")
        if not prompt:
            print(f"  [{i}] visual_prompt 없음 — 스킵")
            image_paths.append(None)
            continue

        # [Step 1] 이미지 생성 요청
        payload = {
            "height":          REELS_H,
            "width":           REELS_W,
            "modelId":         MODEL_ID,
            "prompt":          prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "num_images":      1,
            "promptMagic":     True,
        }
        print(f"  [{i}] 생성 요청...", flush=True)
        try:
            res    = requests.post(
                "https://cloud.leonardo.ai/api/rest/v1/generations",
                json=payload, headers=headers, timeout=30,
            )
            if not res.ok:
                print(f"  [{i}] API 거부: {res.status_code} — {res.text[:200]}")
                image_paths.append(None)
                continue
            gen_id = res.json()["sdGenerationJob"]["generationId"]
            print(f"  [{i}] ID: {gen_id}")
        except Exception as e:
            print(f"  [{i}] 요청 실패: {e}")
            image_paths.append(None)
            continue

        # [Step 2] 완료 대기 + 다운로드
        path = wait_and_download(gen_id, i, headers)
        image_paths.append(path)

    ok = sum(1 for p in image_paths if p)
    print(f"\n📦 이미지 {ok}/{len(script_data)}장 준비 완료\n")

    if ok == 0:
        print("❌ 생성된 이미지 없음 — 중단")
        return None

    # [Step 3] v5 영상 조립
    result = assemble_v5_video(
        image_paths    = [str(p) for p in image_paths if p],
        narration_path = narration_path,
        bgm_path       = bgm_path,
        output_path    = output_path,
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# CLI 진입점
# ──────────────────────────────────────────────────────────────────────────────
def _default_script_data() -> list:
    """코스피 6400 / 부동산 릴스 기본 script_data"""
    return [
        {"visual_prompt": "Dramatic Seoul night skyline from below, luxury apartment towers glowing golden against deep indigo sky, stock ticker LED bokeh foreground, cinematic vertical 9:16, 8k photorealistic, wide angle upward shot, no people"},
        {"visual_prompt": "Massive LED display showing soaring green stock market chart, Seoul financial skyscrapers at night, bullish energy neon lighting, cinematic vertical 9:16, 8k photorealistic, dynamic composition, no people"},
        {"visual_prompt": "Aerial drone bird-eye view of dense Seoul apartment complex at golden hour, geometric rooftop pattern, warm amber sunlight, premium residential district, vertical 9:16, 8k photorealistic, no people"},
        {"visual_prompt": "Luxury Seoul apartment tower exterior at sunset, dramatic orange-purple cinematic sky, modern glass facade, upward street-level perspective, 9:16 vertical, 8k photorealistic, golden hour, no people"},
        {"visual_prompt": "Minimalist luxury bank interior, soaring marble columns, dramatic spotlights, empty grand hall, warm gold accents, cinematic architectural photography, vertical 9:16, 8k photorealistic, no people"},
        {"visual_prompt": "Cinematic Seoul urban landscape at dusk, outer district apartments glowing warm vs shadowed city-center, dramatic light-shadow contrast, documentary style, vertical 9:16, 8k photorealistic, no people"},
        {"visual_prompt": "Elegant Seoul apartment living room, floor-to-ceiling panoramic windows, city night skyline, luxury interior warm ambient lighting, aspirational lifestyle, vertical 9:16, 8k photorealistic, no people"},
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="시네마틱 릴스 완전 자동 제작")
    parser.add_argument("--narration",    default="output/drafts/narration.txt")
    parser.add_argument("--bgm",          default="output/assets/bgm.mp3")
    parser.add_argument("--output",       default="output/reels/final_reels.mp4")
    parser.add_argument("--script-json",  default=None,
                        help="script_data JSON 파일 경로 (없으면 기본값 사용)")
    parser.add_argument("--no-skip",      action="store_true",
                        help="기존 이미지가 있어도 새로 생성")
    args = parser.parse_args()

    if args.script_json:
        with open(args.script_json, encoding="utf-8") as f:
            script_data = json.load(f)
    else:
        script_data = _default_script_data()

    result = generate_cinematic_reels(
        script_data    = script_data,
        narration_path = args.narration,
        bgm_path       = args.bgm if Path(args.bgm).exists() else None,
        output_path    = args.output,
        skip_existing  = not args.no_skip,
    )

    if result:
        print(f"\n🎬 시네마틱 릴스 제작 완료! → {result}")
    else:
        print("\n❌ 제작 실패")
        sys.exit(1)
