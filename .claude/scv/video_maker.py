#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
video_maker.py — 카드뉴스 PNG → 인스타그램 릴스 MP4 (기능 11/12)

[ 기본 모드 ]
  python .claude/scv/video_maker.py -i output/final/YYYYMMDD_주제명

[ TTS 풀 모드 — 나레이션 + 성우 + 중앙 임팩트 자막 + BGM 덕킹 ]
  python .claude/scv/video_maker.py \\
    -i output/final/YYYYMMDD_주제명 \\
    --tts --narration output/drafts/narration.txt \\
    --bgm output/assets/bgm.mp3

[ B-Roll 포함 (Pexels API) ]
  python .claude/scv/video_maker.py \\
    -i output/final/YYYYMMDD_주제명 \\
    --tts --narration output/drafts/narration.txt \\
    --broll --topic 부동산 --bgm output/assets/bgm.mp3

[ 옵션 ]
  --portrait          4:5 비율(1080×1350) 유지
  --no-ken-burns      줌 효과 비활성화
  --no-subtitles      자막 비활성화
  --duration N        슬라이드당 N초 (TTS 모드에서는 무시)

요구사항: pip install moviepy pillow numpy pyyaml edge-tts anthropic requests
"""

import sys
import io
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
import asyncio
import os
import re
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# ── moviepy v2 / v1 자동 감지 ────────────────────────────────────────────────
try:
    from moviepy import (
        VideoClip, VideoFileClip, CompositeVideoClip, AudioFileClip,
        concatenate_videoclips, concatenate_audioclips,
    )
    from moviepy.audio.AudioClip import CompositeAudioClip
    from moviepy.video.fx import CrossFadeIn
    from moviepy.audio.fx import AudioFadeIn, AudioFadeOut
    MOVIEPY_V2 = True
except ImportError:
    try:
        from moviepy.editor import (
            VideoClip, VideoFileClip, CompositeVideoClip, AudioFileClip,
            concatenate_videoclips,
        )
        from moviepy.audio.AudioClip import (
            CompositeAudioClip, concatenate_audioclips,
        )
        MOVIEPY_V2 = False
    except ImportError:
        print("❌ moviepy 설치 필요: pip install moviepy")
        sys.exit(1)

# ── v1 / v2 API 브릿지 ───────────────────────────────────────────────────────
def _clip_set_fps(clip, fps):
    return clip.with_fps(fps) if MOVIEPY_V2 else clip.set_fps(fps)

def _clip_set_audio(video, audio):
    return video.with_audio(audio) if MOVIEPY_V2 else video.set_audio(audio)

def _clip_subclip(clip, t_start, t_end):
    return clip.subclipped(t_start, t_end) if MOVIEPY_V2 else clip.subclip(t_start, t_end)

def _clip_volume(clip, vol):
    return clip.with_volume_scaled(vol) if MOVIEPY_V2 else clip.volumex(vol)

def _clip_set_start(clip, t):
    return clip.with_start(t) if MOVIEPY_V2 else clip.set_start(t)

# ─────────────────────────────────────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────────────────────────────────────

REELS_W, REELS_H = 1080, 1920
CARD_W,  CARD_H  = 1080, 1350

DEFAULT_DURATION   = 4.0
DEFAULT_TRANSITION = 0.5
DEFAULT_FPS        = 30

BLUR_RADIUS   = 28
BG_BRIGHTNESS = 0.38

ZOOM_FROM = 1.00
ZOOM_TO   = 1.15

# 기본 모드 하단 자막
SUBTITLE_FONT_SIZE  = 38
SUBTITLE_BOTTOM_GAP = 72
SUBTITLE_MAX_CHARS  = 26

# ── 규칙 4: 중앙 임팩트 자막 ─────────────────────────────────────────────────
DYN_FONT_SIZE       = 112     # 2x 확대 (기존 56px → 112px)
DYN_POS_RATIO       = 0.65   # 화면 65% 지점 (중앙보다 아래)
DYN_POS_PREV_RATIO  = 0.52   # 이전 자막: 현재보다 위 (리듬 누적 효과)
IMPACT_ANIM_T1      = 0.15   # 0 ~ 0.15s: 0.7 → 1.08 스케일업
IMPACT_ANIM_T2      = 0.25   # 0.15 ~ 0.25s: 1.08 → 1.0 안착
DYN_BG_COLOR        = (5,   15,  40,  160)  # 통일된 다크 배경 (반투명, 배경 비침)
DYN_TEXT_NORMAL     = (255, 255, 255, 255)   # 기본 흰색 텍스트
DYN_TEXT_NUMBER     = (255, 216,  96, 255)   # 숫자 골드 강조 #FFD860
DYN_TEXT_PREV       = (200, 200, 200, 140)   # 이전 자막 (흐릿하게)

# ── 화면 전환 줌 설정 ─────────────────────────────────────────────────────────
ZOOM_TRANS_SCALE_IN  = 0.88   # Zoom-in 시작 스케일 (88%→100%)
ZOOM_TRANS_SCALE_OUT = 1.12   # Zoom-out 시작 스케일 (112%→100%)
ZOOM_TRANS_DUR       = 0.45   # 줌 전환 적용 시간(초)

# ── 규칙 3: BGM 덕킹 볼륨 ────────────────────────────────────────────────────
BGM_VOL_SPEECH  = 0.12   # TTS 나레이션 중
BGM_VOL_SILENCE = 0.40   # 나레이션 없는 구간
BGM_DUCK_PRE    = 0.30   # 나레이션 시작 0.3초 전부터 낮춤
BGM_DUCK_POST   = 0.50   # 나레이션 끝 0.5초 후 복원

# TTS 기본 음성
DEFAULT_TTS_VOICE = 'ko-KR-InJoonNeural'

# B-Roll 키워드 매핑 (규칙 2)
BROLL_KEYWORD_MAP = {
    '부동산': 'apartment drone aerial real estate building',
    '아파트': 'apartment building exterior luxury',
    '주식':   'stock market graph financial trading screen',
    '코스피': 'stock market financial graph trading',
    '금리':   'bank building exterior currency money',
    '재건축': 'construction crane urban development city',
    '경제':   'city financial district skyline',
    '투자':   'investment finance money growth',
}

# ── 규칙 1: Hook-First 나레이션 프롬프트 ──────────────────────────────────────
NARRATION_PROMPT = """카드뉴스 스크립트를 기반으로 인스타그램 릴스용 나레이션 대본을 작성해주세요.

[필수 규칙 — 반드시 지킬 것]
1. 첫 문장(0~3초): 손실 회피·긴박감 문구로 시작. 절대 "안녕하세요"나 "오늘은 ~에 대해" 금지.
   좋은 예: "지금 이것 모르면 부동산 기차 놓칩니다!"
           "이미 늦은 사람들이 후회하는 딱 한 가지가 있습니다."
           "당신만 모르는 아파트 투자 패턴, 지금 공개합니다."
2. 구어체로 작성. 말하듯이 짧은 문장. 쉼표보다 마침표를 자주 사용.
3. 전체 분량: 읽는 데 55~60초 (분당 약 320자 기준)
4. 숫자·퍼센트·금액은 원본 그대로 유지
5. 문장마다 줄바꿈 (TTS 자막 싱크용)
6. 마지막 2문장: "이 영상 저장하고", "@aptshowhome 팔로우" CTA

[카드뉴스 스크립트]
{script_content}

나레이션 대본만 출력하세요 (제목·설명 없이):"""

# ─────────────────────────────────────────────────────────────────────────────
# script.md 파싱
# ─────────────────────────────────────────────────────────────────────────────

def parse_script_md(script_path: str) -> dict:
    if not HAS_YAML:
        return {}
    path = Path(script_path)
    if not path.exists():
        return {}
    content = path.read_text(encoding='utf-8')
    blocks  = re.findall(r'---\s*\n(.*?)\n---', content, re.DOTALL)
    slides  = {}
    for block in blocks:
        try:
            data = yaml.safe_load(block.strip())
            if not isinstance(data, dict) or 'slide_number' not in data:
                continue
            num  = int(data['slide_number'])
            role = data.get('role', 'body')
            if role == 'cover':
                parts = [data.get('title', ''), data.get('subtitle', '')]
            elif role == 'closing':
                parts = [data.get('summary', ''), data.get('cta', '')]
            else:
                parts = [data.get('subtitle', ''), data.get('body', '')]
            lines = []
            for p in parts:
                if not p:
                    continue
                p = str(p)
                if len(p) > SUBTITLE_MAX_CHARS * 2:
                    p = p[:SUBTITLE_MAX_CHARS * 2 - 1] + '…'
                lines.append(p)
            slides[num] = '\n'.join(lines)
        except Exception:
            continue
    return slides


def read_script_raw(script_path: str) -> str:
    path = Path(script_path)
    if not path.exists():
        return ''
    return path.read_text(encoding='utf-8')

# ─────────────────────────────────────────────────────────────────────────────
# 이미지 합성
# ─────────────────────────────────────────────────────────────────────────────

def _blurred_background(img_pil: Image.Image, canvas_w: int, canvas_h: int) -> Image.Image:
    ratio = max(canvas_w / img_pil.width, canvas_h / img_pil.height)
    bg = img_pil.resize(
        (int(img_pil.width * ratio), int(img_pil.height * ratio)), Image.LANCZOS,
    )
    lx = (bg.width  - canvas_w) // 2
    ty = (bg.height - canvas_h) // 2
    bg = bg.crop((lx, ty, lx + canvas_w, ty + canvas_h))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))
    bg = ImageEnhance.Brightness(bg).enhance(BG_BRIGHTNESS)
    return bg


def composite_frame(
    img_pil: Image.Image,
    canvas_w: int,
    canvas_h: int,
    letterbox: bool = False,
) -> np.ndarray:
    canvas = Image.new('RGB', (canvas_w, canvas_h), (0, 0, 0)) if letterbox \
             else _blurred_background(img_pil, canvas_w, canvas_h)
    slide_ratio = img_pil.height / img_pil.width
    fit_w = canvas_w
    fit_h = int(fit_w * slide_ratio)
    if fit_h > canvas_h:
        fit_h = canvas_h
        fit_w = int(fit_h / slide_ratio)
    slide = img_pil.resize((fit_w, fit_h), Image.LANCZOS)
    canvas.paste(slide, ((canvas_w - fit_w) // 2, (canvas_h - fit_h) // 2))
    return np.array(canvas)

# ─────────────────────────────────────────────────────────────────────────────
# 폰트
# ─────────────────────────────────────────────────────────────────────────────

_font_cache: dict = {}

def _load_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        'C:/Windows/Fonts/malgunbd.ttf',
        'C:/Windows/Fonts/malgun.ttf',
        'C:/Windows/Fonts/NanumGothicBold.ttf',
        '/Library/Fonts/AppleGothic.ttf',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        'output/assets/fonts/NotoSansKR-Regular.ttf',
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _load_font_cached(size: int) -> ImageFont.FreeTypeFont:
    """폰트 캐시 — 동일 크기 반복 로드 제거 (렌더링 속도 핵심 최적화)"""
    if size not in _font_cache:
        _font_cache[size] = _load_font(size)
    return _font_cache[size]

# ─────────────────────────────────────────────────────────────────────────────
# 자막 렌더러 A: 하단 반투명 (기본 모드)
# ─────────────────────────────────────────────────────────────────────────────

def draw_subtitle_bottom(
    frame: np.ndarray,
    text: str,
    canvas_w: int,
    canvas_h: int,
    font_size: int = SUBTITLE_FONT_SIZE,
) -> np.ndarray:
    if not text or not text.strip():
        return frame
    img   = Image.fromarray(frame).convert('RGBA')
    font  = _load_font_cached(font_size)
    dummy = ImageDraw.Draw(img)
    lines = text.split('\n')
    line_h = font_size + 10
    pad_x, pad_y = 44, 18
    widths = []
    for line in lines:
        try:
            bbox = dummy.textbbox((0, 0), line, font=font)
            widths.append(bbox[2] - bbox[0])
        except AttributeError:
            widths.append(int(len(line) * font_size * 0.62))
    max_w  = max(widths) if widths else canvas_w - pad_x * 2
    box_w  = min(max_w + pad_x * 2, canvas_w - 40)
    box_h  = len(lines) * line_h + pad_y * 2
    box_x1 = (canvas_w - box_w) // 2
    box_y1 = canvas_h - SUBTITLE_BOTTOM_GAP - box_h
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle(
        [(box_x1, box_y1), (box_x1 + box_w, box_y1 + box_h)],
        radius=12, fill=(10, 10, 10, 175),
    )
    img  = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
        except AttributeError:
            tw = widths[i]
        tx = (canvas_w - tw) // 2
        ty = box_y1 + pad_y + i * line_h
        draw.text((tx + 2, ty + 2), line, font=font, fill=(0, 0, 0, 180))
        draw.text((tx,     ty    ), line, font=font, fill=(255, 255, 255, 255))
    return np.array(img.convert('RGB'))

# ─────────────────────────────────────────────────────────────────────────────
# 자막 렌더러 B: 중앙 임팩트 (TTS 모드 — 규칙 4)
# ─────────────────────────────────────────────────────────────────────────────

def _wrap_text(text: str, max_chars: int = 12) -> list:
    """한글 기준 max_chars자마다 줄바꿈"""
    words    = text.split()
    lines    = []
    cur_line = ''
    for w in words:
        candidate = (cur_line + ' ' + w).strip()
        if len(candidate) > max_chars:
            if cur_line:
                lines.append(cur_line)
            cur_line = w
        else:
            cur_line = candidate
    if cur_line:
        lines.append(cur_line)
    return lines if lines else [text]


# ── 자막 오버레이 캐시 (속도 최적화 #4) ──────────────────────────────────────
_subtitle_overlay_cache: dict = {}


def _blend_overlay(frame: np.ndarray, overlay_rgba: np.ndarray) -> np.ndarray:
    """PIL alpha_composite 대신 numpy 직접 블렌딩 — 3~5× 빠름"""
    alpha  = overlay_rgba[:, :, 3:4].astype(np.float32) / 255.0
    rgb    = overlay_rgba[:, :, :3].astype(np.float32)
    result = frame.astype(np.float32) * (1.0 - alpha) + rgb * alpha
    return np.clip(result, 0, 255).astype(np.uint8)


def _render_subtitle_rgba(
    text: str,
    eff_size: int,
    canvas_w: int,
    canvas_h: int,
    pos_ratio: float,
    text_color: tuple,
    bg_alpha_override: int = -1,
) -> np.ndarray:
    """
    자막 박스를 RGBA numpy 배열로 렌더링 후 캐시에 저장.
    (text, eff_size, pos_ratio*100, text_color) 키로 캐싱.
    """
    cache_key = (text, eff_size, int(pos_ratio * 100), text_color[:3])
    if cache_key in _subtitle_overlay_cache:
        return _subtitle_overlay_cache[cache_key]

    font   = _load_font_cached(eff_size)
    pad_x  = max(8, int(14 * eff_size / DYN_FONT_SIZE))
    pad_y  = max(6, int(10 * eff_size / DYN_FONT_SIZE))
    radius = max(8, int(12 * eff_size / DYN_FONT_SIZE))
    lines  = _wrap_text(text, max_chars=12)
    line_h = eff_size + max(4, int(10 * eff_size / DYN_FONT_SIZE))

    # 텍스트 폭 계산
    tmp_img = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    tmp_drw = ImageDraw.Draw(tmp_img)
    widths  = []
    for line in lines:
        try:
            bbox = tmp_drw.textbbox((0, 0), line, font=font)
            widths.append(bbox[2] - bbox[0])
        except AttributeError:
            widths.append(int(len(line) * eff_size * 0.6))
    max_w = max(widths) if widths else canvas_w - 80

    box_w  = min(max_w + pad_x * 2, canvas_w - 60)
    box_h  = len(lines) * line_h + pad_y * 2
    box_x1 = (canvas_w - box_w) // 2
    center_y = int(canvas_h * pos_ratio)
    box_y1   = center_y - box_h // 2

    # 박스 렌더링 (다크 반투명 배경 통일)
    bg_a   = bg_alpha_override if bg_alpha_override >= 0 else DYN_BG_COLOR[3]
    bg_col = DYN_BG_COLOR[:3] + (bg_a,)
    overlay = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle(
        [(box_x1, box_y1), (box_x1 + box_w, box_y1 + box_h)],
        radius=radius, fill=bg_col,
    )
    draw = ImageDraw.Draw(overlay)

    # 텍스트 렌더링 — 숫자 단어는 골드, 나머지는 지정 색
    for i, line in enumerate(lines):
        words   = line.split()
        x_cur   = box_x1 + pad_x
        ty      = box_y1 + pad_y + i * line_h
        # 라인 전체 폭으로 x 중앙 계산
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw   = bbox[2] - bbox[0]
        except AttributeError:
            tw = widths[i]
        x_cur = (canvas_w - tw) // 2

        # 단어별 순차 렌더링으로 숫자 골드 적용
        for word in words:
            has_num   = bool(re.search(r'\d', word))
            w_color   = DYN_TEXT_NUMBER if has_num else text_color
            try:
                wb = draw.textbbox((0, 0), word, font=font)
                ww = wb[2] - wb[0]
            except AttributeError:
                ww = int(len(word) * eff_size * 0.6)
            draw.text((x_cur, ty), word, font=font, fill=w_color)
            # 단어 간격 (공백 폭)
            try:
                sb = draw.textbbox((0, 0), ' ', font=font)
                sw = sb[2] - sb[0]
            except AttributeError:
                sw = int(eff_size * 0.3)
            x_cur += ww + sw

    result = np.array(overlay)
    _subtitle_overlay_cache[cache_key] = result
    return result


def draw_subtitle_center_impact(
    frame: np.ndarray,
    text: str,
    t_in_segment: float,
    canvas_w: int,
    canvas_h: int,
    font_size: int = DYN_FONT_SIZE,
    pos_ratio: float = DYN_POS_RATIO,
    text_color: tuple = DYN_TEXT_NORMAL,
) -> np.ndarray:
    """
    임팩트 자막 (규칙 4):
    - 0~0.15s: 스케일 0.70→1.08 (튀어오름)
    - 0.15~0.25s: 스케일 1.08→1.00 (안착)
    - 숫자 단어 자동 골드 강조
    - numpy 블렌딩 + 오버레이 캐시로 빠른 렌더링
    """
    if not text or not text.strip():
        return frame

    if t_in_segment < IMPACT_ANIM_T1:
        p     = t_in_segment / IMPACT_ANIM_T1
        scale = 0.70 + (1.08 - 0.70) * p
    elif t_in_segment < IMPACT_ANIM_T2:
        p     = (t_in_segment - IMPACT_ANIM_T1) / (IMPACT_ANIM_T2 - IMPACT_ANIM_T1)
        scale = 1.08 + (1.00 - 1.08) * p
    else:
        scale = 1.00

    eff_size = max(20, int(font_size * scale))
    overlay  = _render_subtitle_rgba(text, eff_size, canvas_w, canvas_h,
                                     pos_ratio, text_color)
    return _blend_overlay(frame, overlay)


def draw_subtitle_accumulated(
    frame: np.ndarray,
    srt_segments: list,
    global_t: float,
    canvas_w: int,
    canvas_h: int,
) -> np.ndarray:
    """
    리듬감 자막 (기능 1):
    - 현재 세그먼트: 임팩트 애니메이션 (DYN_POS_RATIO)
    - 직전 세그먼트: 위에 흐릿하게 유지 (DYN_POS_PREV_RATIO)
    → 나레이션 싱크에 맞춰 한 줄씩 쌓이는 효과
    """
    current = get_active_segment(srt_segments, global_t)
    if current is None:
        return frame

    t_in_seg = global_t - current['start']

    # 직전 세그먼트 찾기 (현재 시작 0.8초 이내에 끝난 것)
    prev_seg = None
    for seg in srt_segments:
        if seg['end'] <= current['start'] and (current['start'] - seg['end']) < 0.8:
            prev_seg = seg

    # 직전 자막: 흐릿 + 위 위치
    if prev_seg:
        ov_prev = _render_subtitle_rgba(
            prev_seg['text'], int(DYN_FONT_SIZE * 0.78),
            canvas_w, canvas_h, DYN_POS_PREV_RATIO,
            DYN_TEXT_PREV, bg_alpha_override=70,
        )
        frame = _blend_overlay(frame, ov_prev)

    # 현재 자막: 임팩트 애니메이션
    frame = draw_subtitle_center_impact(
        frame, current['text'], t_in_seg, canvas_w, canvas_h,
    )
    return frame

# ─────────────────────────────────────────────────────────────────────────────
# 자막 조회
# ─────────────────────────────────────────────────────────────────────────────

def _scale_frame_center(frame: np.ndarray, scale: float,
                        canvas_w: int, canvas_h: int) -> np.ndarray:
    """줌 전환용: 프레임을 중앙 기준으로 scale 배 확대/축소"""
    if abs(scale - 1.0) < 0.005:
        return frame
    new_w = int(canvas_w * scale)
    new_h = int(canvas_h * scale)
    pil   = Image.fromarray(frame).resize((new_w, new_h), Image.BILINEAR)
    canvas = Image.new('RGB', (canvas_w, canvas_h), (0, 0, 0))
    px     = (canvas_w - new_w) // 2
    py     = (canvas_h - new_h) // 2
    canvas.paste(pil, (px, py))
    return np.array(canvas)


def get_active_segment(segments: list, t: float) -> dict | None:
    """시간 t에 해당하는 SRT 세그먼트 반환 (t_in_segment 계산용)"""
    for seg in segments:
        if seg['start'] <= t <= seg['end']:
            return seg
    return None


def get_active_subtitle(segments: list, t: float) -> str:
    seg = get_active_segment(segments, t)
    return seg['text'] if seg else ''

# ─────────────────────────────────────────────────────────────────────────────
# SRT 파싱 (edge-tts 7.x)
# ─────────────────────────────────────────────────────────────────────────────

def _srt_time_to_sec(t: str) -> float:
    t     = t.strip().replace(',', '.')
    parts = t.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])


def parse_srt(srt_content: str) -> list:
    segments = []
    for block in re.split(r'\n{2,}', srt_content.strip()):
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        for i, line in enumerate(lines):
            m = re.match(r'([\d:,]+)\s*-->\s*([\d:,]+)', line)
            if m:
                text = ' '.join(lines[i + 1:]).strip()
                text = re.sub(r'<[^>]+>', '', text).strip()
                if text:
                    segments.append({
                        'start': _srt_time_to_sec(m.group(1)),
                        'end':   _srt_time_to_sec(m.group(2)),
                        'text':  text,
                    })
                break
    return segments

# ─────────────────────────────────────────────────────────────────────────────
# TTS 생성 (edge-tts 7.x)
# ─────────────────────────────────────────────────────────────────────────────

async def _tts_async(text: str, voice: str, audio_path: str, srt_path: str,
                     use_ssml: bool = False) -> None:
    """항상 plain text만 전달 — edge-tts는 SSML 태그를 그대로 낭독하므로 제거"""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    submaker    = edge_tts.SubMaker()
    with open(audio_path, 'wb') as af:
        async for chunk in communicate.stream():
            if chunk['type'] == 'audio':
                af.write(chunk['data'])
            elif chunk['type'] in ('WordBoundary', 'SentenceBoundary'):
                submaker.feed(chunk)
    Path(srt_path).write_text(submaker.get_srt(), encoding='utf-8')


def _apply_ssml(text: str, lang: str = 'ko-KR') -> str:
    """물음표 후 300ms + 마침표 후 100ms break SSML 삽입.
    Microsoft TTS 필수 namespace 포함 (없으면 NoAudioReceived).
    <emphasis>는 edge-tts에서 거부됨 → break 태그만 사용.
    """
    text = re.sub(r'\?(\s)', r'?<break time="300ms"/>\1', text)
    text = re.sub(r'\?$', r'?<break time="300ms"/>', text, flags=re.MULTILINE)
    text = re.sub(r'\.(\s)', r'.<break time="100ms"/>\1', text)
    return (
        f'<speak version="1.0" '
        f'xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xmlns:mstts="https://www.w3.org/2001/mstts" '
        f'xml:lang="{lang}">'
        f'{text}</speak>'
    )


def _make_sfx_clip(sfx_path: str | None, duration: float = 0.08) -> str:
    """Pop 효과음 WAV 경로 반환 (파일 없으면 numpy로 합성)"""
    if sfx_path and Path(sfx_path).exists():
        return sfx_path
    import wave as wv
    sample_rate = 44100
    n = int(sample_rate * duration)
    t = np.linspace(0, duration, n)
    wave_data = np.sin(2 * np.pi * 880 * t) * np.exp(-t * 60)
    wave_data = (wave_data * 28000).astype(np.int16)
    tmp = tempfile.mktemp(suffix='_pop.wav')
    with wv.open(tmp, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(wave_data.tobytes())
    return tmp


def generate_tts(text: str, voice: str, output_dir: Path, use_ssml: bool = False) -> tuple:
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        print("❌ edge-tts 미설치: pip install edge-tts")
        sys.exit(1)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_path = output_dir / 'narration.mp3'
    srt_path   = output_dir / 'narration.srt'
    ssml_label = ' [SSML+emphasis]' if use_ssml else ''
    print(f"  🎙️  TTS 생성 중... (목소리: {voice}{ssml_label})")
    asyncio.run(_tts_async(text, voice, str(audio_path), str(srt_path), use_ssml))
    srt_content = srt_path.read_text(encoding='utf-8')
    segments    = parse_srt(srt_content)
    print(f"  ✅ TTS 완료: {audio_path.name} | 자막 세그먼트 {len(segments)}개")
    return audio_path, segments

# ─────────────────────────────────────────────────────────────────────────────
# 나레이션 자동 생성 (Claude API)
# ─────────────────────────────────────────────────────────────────────────────

def generate_narration_with_claude(script_path: str) -> str:
    try:
        import anthropic
    except ImportError:
        print("❌ anthropic 미설치: pip install anthropic")
        sys.exit(1)
    script_content = read_script_raw(script_path)
    if not script_content:
        print(f"❌ script.md 없음: {script_path}")
        sys.exit(1)
    print("  🤖 Claude API로 나레이션 대본 생성 중...")
    client  = anthropic.Anthropic()
    message = client.messages.create(
        model      = 'claude-sonnet-4-6',
        max_tokens = 1200,
        messages   = [{'role': 'user', 'content': NARRATION_PROMPT.format(script_content=script_content)}],
    )
    narration = message.content[0].text.strip()
    print(f"  ✅ 나레이션 생성 완료 ({len(narration)}자)")
    return narration

# ─────────────────────────────────────────────────────────────────────────────
# 규칙 3 — BGM 덕킹 (TTS 구간: 12%, 무음 구간: 40%)
# ─────────────────────────────────────────────────────────────────────────────

def build_ducked_bgm(
    bgm_path: str,
    tts_segments: list,
    total_duration: float,
    vol_speech: float = BGM_VOL_SPEECH,
    vol_silence: float = BGM_VOL_SILENCE,
) -> object:
    """
    TTS 타이밍에 맞춰 BGM 볼륨을 동적으로 조절합니다.
    나레이션 전후 0.3s/0.5s 버퍼를 포함해 자연스러운 덕킹을 구현합니다.
    """
    raw = AudioFileClip(bgm_path)
    looped = _trim_and_loop(raw, total_duration + 5)

    # 시간 이벤트 목록 구성: [(시각, 볼륨)]
    events = [(0.0, vol_silence)]
    for seg in sorted(tts_segments, key=lambda s: s['start']):
        t_duck  = max(0.0, seg['start'] - BGM_DUCK_PRE)
        t_raise = min(total_duration, seg['end'] + BGM_DUCK_POST)
        events.append((t_duck,  vol_speech))
        events.append((t_raise, vol_silence))
    events.append((total_duration, vol_silence))

    # 중복 제거·정렬
    seen  = {}
    for t, v in events:
        seen[round(t, 3)] = v
    events = sorted(seen.items())

    # 구간별 오디오 클립 생성 후 연결
    chunks = []
    for i in range(len(events) - 1):
        t_start, vol = events[i]
        t_end        = events[i + 1][0]
        if t_end - t_start < 0.01:
            continue
        chunk = _clip_subclip(looped, t_start, t_end)
        chunk = _clip_volume(chunk, vol)
        chunks.append(chunk)

    if not chunks:
        return _clip_volume(looped, vol_speech)

    ducked = concatenate_audioclips(chunks)
    if MOVIEPY_V2:
        ducked = ducked.with_effects([AudioFadeIn(0.5), AudioFadeOut(1.5)])
    else:
        ducked = ducked.audio_fadein(0.5).audio_fadeout(1.5)
    return ducked

# ─────────────────────────────────────────────────────────────────────────────
# 규칙 2 — B-Roll 클립 (Pexels API)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_broll_clip(
    topic: str,
    duration: float,
    canvas_w: int,
    canvas_h: int,
    fps: int,
    cache_dir: Path,
) -> object | None:
    """
    Pexels API로 주제별 B-Roll 영상을 가져옵니다.
    PEXELS_API_KEY 없으면 None 반환 (영상 중단 없음).
    """
    api_key = os.getenv('PEXELS_API_KEY')
    if not api_key:
        return None

    try:
        import requests
    except ImportError:
        return None

    # 주제 → 검색어 매핑
    query = 'real estate building'
    for k, v in BROLL_KEYWORD_MAP.items():
        if k in (topic or ''):
            query = v
            break

    cache_key  = re.sub(r'\W+', '_', query)[:40]
    cache_path = cache_dir / f'broll_{cache_key}.mp4'

    try:
        # 캐시 우선 사용
        if not cache_path.exists():
            resp = requests.get(
                'https://api.pexels.com/videos/search',
                params={'query': query, 'per_page': 10, 'orientation': 'portrait', 'size': 'medium'},
                headers={'Authorization': api_key},
                timeout=10,
            )
            data   = resp.json()
            videos = data.get('videos', [])
            if not videos:
                return None

            # 적절한 해상도 파일 선택
            video_url = None
            for video in videos:
                for f in sorted(video.get('video_files', []),
                                key=lambda x: x.get('width', 0), reverse=True):
                    if f.get('width', 0) >= 720:
                        video_url = f['link']
                        break
                if video_url:
                    break

            if not video_url:
                return None

            cache_dir.mkdir(parents=True, exist_ok=True)
            r = requests.get(video_url, timeout=30, stream=True)
            with open(cache_path, 'wb') as fh:
                for chunk in r.iter_content(chunk_size=8192):
                    fh.write(chunk)

        # VideoFileClip 로드 후 리사이즈·트림
        raw_clip = VideoFileClip(str(cache_path), audio=False)
        clip_dur = min(duration, raw_clip.duration)

        if MOVIEPY_V2:
            trimmed = raw_clip.subclipped(0, clip_dur)
        else:
            trimmed = raw_clip.subclip(0, clip_dur)

        # 캔버스에 맞게 리사이즈 (블러 배경 합성)
        def make_broll_frame(t: float) -> np.ndarray:
            raw_frame = trimmed.get_frame(t)
            pil_frame = Image.fromarray(raw_frame).convert('RGB')
            return composite_frame(pil_frame, canvas_w, canvas_h)

        broll = _clip_set_fps(VideoClip(make_broll_frame, duration=clip_dur), fps)
        print(f"  🎬 B-Roll: '{query[:30]}' ({clip_dur:.1f}s)")
        return broll

    except Exception as e:
        print(f"  ⚠️  B-Roll 스킵 ({e})")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# 오디오 유틸
# ─────────────────────────────────────────────────────────────────────────────

def _trim_and_loop(clip, duration: float):
    if clip.duration < duration:
        loops = int(duration / clip.duration) + 1
        clip  = concatenate_audioclips([clip] * loops)
    return _clip_subclip(clip, 0, duration)


def mix_tts_bgm(
    video,
    tts_path: Path,
    bgm_path: str | None,
    tts_segments: list,
    bgm_volume_override: float | None = None,
    sfx_path: str | None = None,
) -> object:
    """TTS 음성 + 덕킹 BGM + SFX 믹싱 후 영상에 부착"""
    dur = video.duration

    tts_clip = _trim_and_loop(AudioFileClip(str(tts_path)), dur)
    if MOVIEPY_V2:
        tts_clip = tts_clip.with_effects([AudioFadeIn(0.3), AudioFadeOut(0.8)])
    else:
        tts_clip = tts_clip.audio_fadein(0.3).audio_fadeout(0.8)

    audio_tracks = [tts_clip]

    if bgm_path and Path(bgm_path).exists():
        if tts_segments:
            bgm_vol_sp = bgm_volume_override if bgm_volume_override else BGM_VOL_SPEECH
            bgm_vol_si = BGM_VOL_SILENCE
            print(f"  🎚️  BGM 덕킹 적용: 나레이션 중 {bgm_vol_sp*100:.0f}% / 무음 시 {bgm_vol_si*100:.0f}%")
            ducked = build_ducked_bgm(bgm_path, tts_segments, dur, bgm_vol_sp, bgm_vol_si)
        else:
            bgm_vol = bgm_volume_override or BGM_VOL_SPEECH
            ducked  = _trim_and_loop(AudioFileClip(bgm_path), dur)
            ducked  = _clip_volume(ducked, bgm_vol)
            if MOVIEPY_V2:
                ducked = ducked.with_effects([AudioFadeIn(1.0), AudioFadeOut(2.0)])
            else:
                ducked = ducked.audio_fadein(1.0).audio_fadeout(2.0)
        audio_tracks.append(ducked)

    # 규칙 4: SFX — 자막 등장 시점(+0.25s)에 Pop 효과음 삽입
    if sfx_path and tts_segments:
        try:
            pop_wav = _make_sfx_clip(sfx_path)
            sfx_vol = 0.30  # BGM 볼륨의 30%
            added   = 0
            for seg in tts_segments:
                t_sfx = seg['start']
                if t_sfx >= dur:
                    continue
                sfx_raw = AudioFileClip(pop_wav)
                sfx_raw = _clip_volume(sfx_raw, sfx_vol)
                sfx_raw = _clip_set_start(sfx_raw, t_sfx)
                audio_tracks.append(sfx_raw)
                added += 1
            if added:
                print(f"  🔔 SFX Pop: {added}회 삽입 (볼륨 {sfx_vol*100:.0f}%)")
        except Exception as e:
            print(f"  ⚠️  SFX 스킵 ({e})")

    mixed = CompositeAudioClip(audio_tracks)
    return _clip_set_audio(video, mixed)


def attach_bgm_only(video, bgm_path: str, bgm_volume: float) -> object:
    bgm = _trim_and_loop(AudioFileClip(bgm_path), video.duration)
    bgm = _clip_volume(bgm, bgm_volume)
    if MOVIEPY_V2:
        bgm = bgm.with_effects([AudioFadeIn(1.0), AudioFadeOut(2.0)])
    else:
        bgm = bgm.audio_fadein(1.0).audio_fadeout(2.0)
    return _clip_set_audio(video, bgm)

# ─────────────────────────────────────────────────────────────────────────────
# 슬라이드 → VideoClip (기본 모드)
# ─────────────────────────────────────────────────────────────────────────────

def make_slide_clip(
    img_path: Path,
    duration: float,
    fps: int,
    subtitle_text: str = '',
    canvas_w: int = REELS_W,
    canvas_h: int = REELS_H,
    enable_ken_burns: bool = True,
    enable_subtitles: bool = True,
    letterbox: bool = False,
) -> object:
    img_pil = Image.open(img_path).convert('RGB')

    if enable_ken_burns:
        margin  = int(max(canvas_w, canvas_h) * (ZOOM_TO - 1.0) * 1.3) + 8
        big_w   = canvas_w + margin * 2
        big_h   = canvas_h + margin * 2
        big_pil = Image.fromarray(composite_frame(img_pil, big_w, big_h, letterbox))

        def make_frame(t: float) -> np.ndarray:
            zoom   = ZOOM_FROM + (ZOOM_TO - ZOOM_FROM) * (t / duration if duration > 0 else 0)
            crop_w = int(canvas_w / zoom)
            crop_h = int(canvas_h / zoom)
            lx     = (big_w - crop_w) // 2
            ty     = (big_h - crop_h) // 2
            frame  = np.array(
                big_pil.crop((lx, ty, lx + crop_w, ty + crop_h))
                       .resize((canvas_w, canvas_h), Image.LANCZOS)
            )
            if enable_subtitles and subtitle_text:
                frame = draw_subtitle_bottom(frame, subtitle_text, canvas_w, canvas_h)
            return frame
    else:
        static = composite_frame(img_pil, canvas_w, canvas_h, letterbox)
        if enable_subtitles and subtitle_text:
            static = draw_subtitle_bottom(static, subtitle_text, canvas_w, canvas_h)

        def make_frame(t: float) -> np.ndarray:  # noqa: F811
            return static

    return _clip_set_fps(VideoClip(make_frame, duration=duration), fps)

# ─────────────────────────────────────────────────────────────────────────────
# 슬라이드 → VideoClip (TTS 모드 — 중앙 임팩트 자막)
# ─────────────────────────────────────────────────────────────────────────────

def make_slide_clip_tts(
    img_path: Path,
    duration: float,
    fps: int,
    srt_segments: list,
    t_offset: float,
    canvas_w: int = REELS_W,
    canvas_h: int = REELS_H,
    enable_ken_burns: bool = True,
    letterbox: bool = False,
    zoom_type: str = 'none',   # 'in' | 'out' | 'none'
    trans_dur: float = DEFAULT_TRANSITION,
) -> object:
    """
    규칙 4: draw_subtitle_center_impact 적용 + t_in_segment 전달.
    최적화: 모든 프레임을 사전 계산 후 배열로 저장 → write_videofile 호출 시
    단순 배열 인덱싱만 수행 (PIL/폰트 로드 반복 제거).
    Ken Burns는 BILINEAR 리사이즈 사용 (영상 품질 충분, 3~5× 속도 향상).
    """
    from concurrent.futures import ThreadPoolExecutor
    import threading

    img_pil  = Image.open(img_path).convert('RGB')
    n_frames = max(1, int(duration * fps) + 1)

    if enable_ken_burns:
        margin  = int(max(canvas_w, canvas_h) * (ZOOM_TO - 1.0) * 1.3) + 8
        big_w   = canvas_w + margin * 2
        big_h   = canvas_h + margin * 2
        big_np  = np.array(composite_frame(img_pil, big_w, big_h, letterbox))

        # PIL operations share read from big_np (immutable); each thread owns its output
        _lock = threading.Lock()

        trans_n = int(ZOOM_TRANS_DUR * fps)

        def compute_frame(fi: int) -> tuple[int, np.ndarray]:
            t        = fi / fps
            zoom     = ZOOM_FROM + (ZOOM_TO - ZOOM_FROM) * (t / duration if duration > 0 else 0)
            crop_w   = int(canvas_w / zoom)
            crop_h   = int(canvas_h / zoom)
            lx       = (big_w - crop_w) // 2
            ty       = (big_h - crop_h) // 2
            cropped  = Image.fromarray(big_np[ty:ty + crop_h, lx:lx + crop_w])
            frame    = np.array(cropped.resize((canvas_w, canvas_h), Image.BILINEAR))

            # 줌 전환 (Zoom In-Out, 슬라이드 입장 구간)
            if zoom_type in ('in', 'out') and fi < trans_n:
                p = fi / trans_n
                if zoom_type == 'in':
                    sc = ZOOM_TRANS_SCALE_IN + (1.0 - ZOOM_TRANS_SCALE_IN) * p
                else:
                    sc = ZOOM_TRANS_SCALE_OUT + (1.0 - ZOOM_TRANS_SCALE_OUT) * p
                frame = _scale_frame_center(frame, sc, canvas_w, canvas_h)

            global_t = t + t_offset
            subtitle = get_active_subtitle(srt_segments, global_t)
            if subtitle:
                frame = draw_subtitle_bottom(frame, subtitle, canvas_w, canvas_h)
            return fi, frame

        print(f"    ⚡ 프레임 사전계산: {n_frames}프레임 (ThreadPool)...", flush=True)
        frames_buf: list = [None] * n_frames
        cpu = max(2, min(os.cpu_count() or 4, 8))
        with ThreadPoolExecutor(max_workers=cpu) as pool:
            for fi, frame in pool.map(compute_frame, range(n_frames)):
                frames_buf[fi] = frame
    else:
        static_bg = composite_frame(img_pil, canvas_w, canvas_h, letterbox)

        trans_n = int(ZOOM_TRANS_DUR * fps)

        def compute_frame_static(fi: int) -> tuple[int, np.ndarray]:
            t        = fi / fps
            frame    = static_bg.copy()

            if zoom_type in ('in', 'out') and fi < trans_n:
                p = fi / trans_n
                sc = (ZOOM_TRANS_SCALE_IN + (1.0 - ZOOM_TRANS_SCALE_IN) * p
                      if zoom_type == 'in'
                      else ZOOM_TRANS_SCALE_OUT + (1.0 - ZOOM_TRANS_SCALE_OUT) * p)
                frame = _scale_frame_center(frame, sc, canvas_w, canvas_h)

            global_t = t + t_offset
            subtitle = get_active_subtitle(srt_segments, global_t)
            if subtitle:
                frame = draw_subtitle_bottom(frame, subtitle, canvas_w, canvas_h)
            return fi, frame

        print(f"    ⚡ 프레임 사전계산: {n_frames}프레임...", flush=True)
        frames_buf = [None] * n_frames
        for fi, frame in map(compute_frame_static, range(n_frames)):
            frames_buf[fi] = frame

    def make_frame(t: float) -> np.ndarray:
        idx = min(int(t * fps), len(frames_buf) - 1)
        return frames_buf[idx]

    return _clip_set_fps(VideoClip(make_frame, duration=duration), fps)

# ─────────────────────────────────────────────────────────────────────────────
# 트랜지션 연결
# ─────────────────────────────────────────────────────────────────────────────

def build_video(clips: list, duration_per_clip: float, trans: float,
                canvas_w: int, canvas_h: int) -> object:
    if MOVIEPY_V2:
        positioned = []
        t_start    = 0.0
        for i, clip in enumerate(clips):
            c = clip.with_effects([CrossFadeIn(trans)]) if i > 0 else clip
            positioned.append(c.with_start(t_start))
            t_start += clip.duration - (trans if i < len(clips) - 1 else 0.0)
        total_dur = t_start + (trans if len(clips) > 1 else duration_per_clip)
        return (
            CompositeVideoClip(positioned, size=(canvas_w, canvas_h))
            .with_duration(total_dur)
        )
    else:
        faded = [
            clip.crossfadein(trans) if i > 0 else clip
            for i, clip in enumerate(clips)
        ]
        return concatenate_videoclips(faded, method='compose', padding=-trans)

# ─────────────────────────────────────────────────────────────────────────────
# 슬라이드 수집
# ─────────────────────────────────────────────────────────────────────────────

def collect_slides(images_dir: str) -> list:
    folder = Path(images_dir)
    if not folder.exists():
        print(f"❌ 폴더 없음: {images_dir}")
        sys.exit(1)
    files = []
    for pat in ('slide-*.png', 'slide-*.jpg', 'slide-*.jpeg'):
        files.extend(folder.glob(pat))
    if not files:
        print(f"❌ 슬라이드 파일 없음: {images_dir}")
        sys.exit(1)

    def _key(p: Path) -> int:
        m = re.search(r'slide-0*(\d+)', p.name)
        return int(m.group(1)) if m else 0

    return sorted(files, key=_key)

# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='카드뉴스 PNG → 인스타그램 릴스 MP4',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본
  python .claude/scv/video_maker.py -i output/final/20260423_주제명

  # TTS 풀 모드 (중앙 임팩트 자막 + 덕킹 BGM)
  python .claude/scv/video_maker.py \\
    -i output/final/20260423_주제명 \\
    --tts --narration output/drafts/narration.txt \\
    --bgm output/assets/bgm.mp3

  # B-Roll 포함 (PEXELS_API_KEY 환경변수 필요)
  python .claude/scv/video_maker.py \\
    -i output/final/20260423_주제명 \\
    --tts --narration output/drafts/narration.txt \\
    --broll --topic 부동산 --bgm output/assets/bgm.mp3

한국어 TTS:
  ko-KR-InJoonNeural   남성 (기본)
  ko-KR-SunHiNeural    여성
  ko-KR-HyunsuNeural   남성 (밝은 톤)
        """,
    )
    parser.add_argument('--images-dir', '-i', required=True)
    parser.add_argument('--script',     '-s', default='output/drafts/script.md')
    parser.add_argument('--output',     '-o', default=None)
    parser.add_argument('--duration',   '-d', type=float, default=DEFAULT_DURATION)
    parser.add_argument('--transition', '-t', type=float, default=DEFAULT_TRANSITION)
    parser.add_argument('--fps',              type=int,   default=DEFAULT_FPS)
    parser.add_argument('--portrait',         action='store_true')
    parser.add_argument('--letterbox',        action='store_true')
    parser.add_argument('--no-ken-burns',     action='store_true')
    parser.add_argument('--no-subtitles',     action='store_true')
    parser.add_argument('--bgm',              default=None)
    parser.add_argument('--bgm-volume',       type=float, default=None,
                        help='BGM 볼륨 고정값 (미지정 시 덕킹 자동 적용)')
    parser.add_argument('--tts',              action='store_true')
    parser.add_argument('--tts-voice',        default=DEFAULT_TTS_VOICE)
    parser.add_argument('--narration',        default=None)
    parser.add_argument('--generate-narration', action='store_true')
    # 규칙 2: B-Roll
    parser.add_argument('--broll',            action='store_true',
                        help='B-Roll 삽입 (PEXELS_API_KEY 필요)')
    parser.add_argument('--topic',            default='',
                        help='B-Roll 주제 키워드 (예: 부동산, 주식)')
    # 규칙 4: SFX Pop 효과음
    parser.add_argument('--sfx',             nargs='?', const='auto',
                        help='자막 등장 시 Pop 효과음 삽입 (경로 없으면 자동 합성)')
    # SSML 나레이션 강화
    parser.add_argument('--ssml',            action='store_true',
                        help='숫자 emphasis + 물음표 300ms break SSML 적용')
    return parser.parse_args()

# ─────────────────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    args   = parse_args()
    slides = collect_slides(args.images_dir)

    canvas_w, canvas_h = (CARD_W, CARD_H) if args.portrait else (REELS_W, REELS_H)
    ratio_label        = '4:5 (1080×1350)' if args.portrait else '9:16 릴스 (1080×1920)'
    print(f"📸 슬라이드 {len(slides)}장 | 포맷: {ratio_label} | moviepy v{'2' if MOVIEPY_V2 else '1'}")

    if args.output:
        output_path = Path(args.output)
    else:
        folder_name = Path(args.images_dir).name
        output_path = Path('output/video') / f"{folder_name}.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    broll_cache = Path('output/video/broll_cache')

    # ── TTS 모드 ─────────────────────────────────────────────────────────────
    if args.tts:
        print("\n🎙️  TTS 모드 시작")

        if args.narration and Path(args.narration).exists():
            narration_text = Path(args.narration).read_text(encoding='utf-8').strip()
            print(f"  📄 나레이션 파일 로드: {args.narration} ({len(narration_text)}자)")
        elif args.generate_narration:
            narration_text = generate_narration_with_claude(args.script)
            save_path = Path('output/drafts/narration.txt')
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(narration_text, encoding='utf-8')
            print(f"  💾 나레이션 저장: {save_path}")
        else:
            print("❌ TTS 모드: --narration 또는 --generate-narration 필요")
            sys.exit(1)

        tts_output_dir = Path('output/video/tts_cache')
        use_ssml = hasattr(args, 'ssml') and args.ssml
        tts_audio_path, srt_segments = generate_tts(
            narration_text, args.tts_voice, tts_output_dir, use_ssml=use_ssml,
        )

        tts_duration = AudioFileClip(str(tts_audio_path)).duration
        per_slide    = tts_duration / len(slides)
        print(f"  ⏱️  TTS 길이: {tts_duration:.1f}초 → 슬라이드당 {per_slide:.1f}초")

        # 클립 생성
        print("\n🎬 클립 생성 중...")
        clips    = []
        t_offset = 0.0

        for idx, slide_path in enumerate(slides, 1):
            # 슬라이드별 Zoom In/Out 교대 (홀수→Zoom-in, 짝수→Zoom-out)
            z_type = 'in' if idx % 2 == 1 else 'out'
            print(f"  [{idx}/{len(slides)}] {slide_path.name} [zoom-{z_type}]", flush=True)
            clip = make_slide_clip_tts(
                img_path        = slide_path,
                duration        = per_slide,
                fps             = args.fps,
                srt_segments    = srt_segments,
                t_offset        = t_offset,
                canvas_w        = canvas_w,
                canvas_h        = canvas_h,
                enable_ken_burns= not args.no_ken_burns,
                letterbox       = args.letterbox,
                zoom_type       = z_type,
                trans_dur       = args.transition,
            )
            clips.append(clip)
            t_offset += per_slide - (args.transition if idx < len(slides) else 0.0)

            # 규칙 2: B-Roll 삽입 (슬라이드 2번, 5번 전환 구간)
            if args.broll and idx in (2, 5) and idx < len(slides):
                broll = fetch_broll_clip(
                    args.topic, min(3.0, per_slide * 0.3),
                    canvas_w, canvas_h, args.fps, broll_cache,
                )
                if broll:
                    clips.append(broll)
                    t_offset += broll.duration - args.transition

        # 연결
        print(f"\n🔗 크로스페이드 {args.transition}s 적용...")
        video = build_video(clips, per_slide, args.transition, canvas_w, canvas_h)

        # 규칙 3 + SFX: 덕킹 BGM 믹싱
        sfx_arg = args.sfx if hasattr(args, 'sfx') and args.sfx else None
        if not args.no_subtitles:
            video = mix_tts_bgm(
                video, tts_audio_path, args.bgm,
                srt_segments, args.bgm_volume,
                sfx_path=sfx_arg,
            )
        else:
            video = mix_tts_bgm(video, tts_audio_path, None, [], None)

    # ── 기본 모드 ─────────────────────────────────────────────────────────────
    else:
        subtitles: dict = {}
        if not args.no_subtitles:
            subtitles = parse_script_md(args.script)
            if subtitles:
                print(f"💬 자막 {len(subtitles)}슬라이드 로드")

        print("\n🎬 클립 생성 중...")
        clips = []
        for idx, slide_path in enumerate(slides, 1):
            m         = re.search(r'slide-0*(\d+)', slide_path.name)
            slide_num = int(m.group(1)) if m else idx
            sub_text  = subtitles.get(slide_num, '')
            print(f"  [{idx}/{len(slides)}] {slide_path.name}"
                  + (' | 자막' if sub_text else ''), flush=True)
            clip = make_slide_clip(
                img_path        = slide_path,
                duration        = args.duration,
                fps             = args.fps,
                subtitle_text   = sub_text,
                canvas_w        = canvas_w,
                canvas_h        = canvas_h,
                enable_ken_burns= not args.no_ken_burns,
                enable_subtitles= not args.no_subtitles,
                letterbox       = args.letterbox,
            )
            clips.append(clip)

        print(f"\n🔗 크로스페이드 {args.transition}s 적용...")
        video = build_video(clips, args.duration, args.transition, canvas_w, canvas_h)

        if args.bgm and Path(args.bgm).exists():
            vol = args.bgm_volume if args.bgm_volume else 0.30
            print(f"🎵 BGM: {args.bgm} (볼륨 {vol})")
            video = attach_bgm_only(video, args.bgm, vol)

    # ── 렌더링 ────────────────────────────────────────────────────────────────
    total_sec  = video.duration
    sfx_on     = hasattr(args, 'sfx') and args.sfx
    ssml_on    = hasattr(args, 'ssml') and args.ssml
    mode_parts = ['TTS+중앙임팩트자막+덕킹BGM'] if args.tts else ['기본']
    if sfx_on:  mode_parts.append('SFX')
    if ssml_on: mode_parts.append('SSML')
    mode_label = '+'.join(mode_parts)
    cpu_threads = max(4, min(os.cpu_count() or 4, 8))
    print(f"\n🎥 렌더링 시작 [{mode_label}] → {output_path}")
    print(f"   길이: {total_sec:.1f}초 | FPS: {args.fps} | 코덱: libx264 | threads: {cpu_threads}")

    video.write_videofile(
        str(output_path),
        fps           = args.fps,
        codec         = 'libx264',
        audio_codec   = 'aac',
        threads       = cpu_threads,
        preset        = 'fast',
        ffmpeg_params = ['-pix_fmt', 'yuv420p'],
        logger        = 'bar',
    )

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ 완료!")
    print(f"   파일: {output_path}")
    print(f"   크기: {size_mb:.1f} MB | 길이: {total_sec:.1f}초")


if __name__ == '__main__':
    main()
