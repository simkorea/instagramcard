#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
instagram-uploader.py

SCV: 생성된 카드뉴스 이미지를 인스타그램 캐러셀 + 스레드에 자동 업로드합니다.

사용법:
  python .claude/scv/instagram-uploader.py \
    --images-dir "output/final/20260416_아파트매수타이밍"

  # 스레드 업로드 건너뛰기
  python .claude/scv/instagram-uploader.py \
    --images-dir "output/final/..." --no-threads

  # Dry-run (미리보기만)
  python .claude/scv/instagram-uploader.py \
    --images-dir "output/final/..." --dry-run

요구사항:
  pip install instagrapi pillow threads-api
"""

import argparse
import getpass
import json
import os
import re
import sys
from pathlib import Path


# ─────────────────────────────────────────
# CLI 인자 파싱
# ─────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description='인스타그램 캐러셀 + 스레드 자동 업로드',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--username', '-u', help='아이디 (생략 시 프롬프트 또는 credentials 파일)')
    parser.add_argument('--password', '-p', help='비밀번호 (생략 권장 — 프롬프트로 안전 입력)')
    parser.add_argument('--images-dir', '-i', required=True,
                        help='업로드할 이미지 폴더 경로')
    parser.add_argument('--caption-file', default='output/drafts/script.md',
                        help='캡션 추출용 스크립트 파일')
    parser.add_argument('--hashtags-file', default='output/drafts/hashtags.md',
                        help='해시태그 파일')
    parser.add_argument('--caption', help='캡션 직접 입력')
    parser.add_argument('--session-file', default='.instagram_session.json',
                        help='세션 저장 파일')
    parser.add_argument('--no-threads', action='store_true',
                        help='스레드 업로드 건너뛰기')
    parser.add_argument('--threads-only', action='store_true',
                        help='스레드만 업로드 (인스타그램 건너뛰기)')
    parser.add_argument('--dry-run', action='store_true',
                        help='실제 업로드 없이 미리보기만')
    return parser.parse_args()


# ─────────────────────────────────────────
# 자격증명 로드
# ─────────────────────────────────────────

def load_credentials(username_arg: str | None, password_arg: str | None):
    """CLI 인자 → credentials 파일 → 프롬프트 순으로 자격증명 확보"""
    creds_file = Path('.instagram_credentials.json')

    username = username_arg
    password = password_arg

    if (not username or not password) and creds_file.exists():
        try:
            creds = json.loads(creds_file.read_text(encoding='utf-8'))
            username = username or creds.get('username', '')
            password = password or creds.get('password', '')
            if username and password:
                print(f"[uploader] 자격증명 파일 사용: {creds_file}")
        except Exception as e:
            print(f"[uploader] ⚠️  자격증명 파일 읽기 실패: {e}")

    if not username:
        username = input('아이디: ').strip()
    if not password:
        password = getpass.getpass('비밀번호 (입력 숨김): ')

    return username, password


# ─────────────────────────────────────────
# 이미지 로드 (PNG → JPEG 변환 포함)
# ─────────────────────────────────────────

def load_and_convert_images(images_dir: str) -> list[Path]:
    """PNG 폴더를 받아 JPEG로 변환된 이미지 목록 반환"""
    dir_path = Path(images_dir)
    if not dir_path.exists():
        print(f"[uploader] ❌ 이미지 폴더 없음: {images_dir}")
        sys.exit(1)

    png_images = sorted(
        dir_path.glob('*.png'),
        key=lambda p: int(m.group()) if (m := re.search(r'\d+', p.stem)) else 0,
    )

    if not png_images:
        print(f"[uploader] ❌ PNG 이미지 없음: {images_dir}")
        sys.exit(1)

    if len(png_images) > 10:
        print(f"[uploader] ⚠️  인스타그램 최대 10장 제한 — 앞 10장만 사용합니다.")
        png_images = png_images[:10]

    # JPEG 변환
    try:
        from PIL import Image
    except ImportError:
        print("[uploader] ❌ Pillow 미설치. pip install pillow")
        sys.exit(1)

    jpg_dir = Path(str(dir_path) + '_jpg')
    jpg_dir.mkdir(exist_ok=True)

    jpg_images = []
    for png in png_images:
        jpg_path = jpg_dir / (png.stem + '.jpg')
        if not jpg_path.exists():
            img = Image.open(png).convert('RGB')
            img.save(jpg_path, 'JPEG', quality=95)
        jpg_images.append(jpg_path)

    print(f"[uploader] JPEG 변환 완료: {len(jpg_images)}장 → {jpg_dir}")
    return jpg_images


# ─────────────────────────────────────────
# 해시태그 파싱
# ─────────────────────────────────────────

def load_hashtags(hashtags_file: str) -> str:
    path = Path(hashtags_file)
    if not path.exists():
        return ''
    content = path.read_text(encoding='utf-8')
    seen = set()
    tags = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith('##') or stripped.startswith('```'):
            continue
        for tag in re.findall(r'#[가-힣\w]+', stripped):
            if tag not in seen:
                seen.add(tag)
                tags.append(tag)
    return ' '.join(tags)


# ─────────────────────────────────────────
# 캡션 생성
# ─────────────────────────────────────────

def build_caption(caption_file: str, hashtags_str: str, caption_override: str | None) -> str:
    if caption_override:
        body = caption_override
    elif Path(caption_file).exists():
        content = Path(caption_file).read_text(encoding='utf-8')
        title_m = re.search(r'\*\*제목\*\*[^\n]*\n>\s*(.+)', content)
        sub_m   = re.search(r'\*\*서브카피\*\*[^\n]*\n>\s*(.+)', content)
        cta_m   = re.search(r'\*\*CTA 문구\*\*[^\n]*\n>\s*(.+)', content)
        title = title_m.group(1).strip() if title_m else ''
        sub   = sub_m.group(1).strip()   if sub_m   else ''
        cta   = cta_m.group(1).strip()   if cta_m   else '저장해두고 꺼내보세요'
        lines = []
        if title: lines.append(title)
        if sub:   lines.append(sub)
        lines.append('')
        lines.append(cta)
        body = '\n'.join(lines)
    else:
        body = '새로운 인사이트를 공유합니다.'

    if hashtags_str:
        return f"{body}\n\n{hashtags_str}"
    return body


# ─────────────────────────────────────────
# 인스타그램 로그인 (세션 재사용)
# ─────────────────────────────────────────

def instagram_login(cl, username: str, password: str, session_file: str):
    session_path = Path(session_file)
    if session_path.exists():
        try:
            print(f"[instagram] 저장된 세션 로드: {session_file}")
            cl.load_settings(session_path)
            cl.login(username, password)
            cl.get_timeline_feed()
            print("[instagram] ✅ 세션 재사용 성공")
            return
        except Exception:
            print("[instagram] ⚠️  세션 만료 — 새로 로그인합니다.")
            session_path.unlink(missing_ok=True)

    print(f"[instagram] 로그인 중: {username}")
    cl.login(username, password)
    cl.dump_settings(session_path)
    print(f"[instagram] ✅ 로그인 성공 (세션 저장)")


# ─────────────────────────────────────────
# 인스타그램 캐러셀 업로드
# ─────────────────────────────────────────

def upload_instagram(username: str, password: str, images: list[Path], caption: str, session_file: str) -> str | None:
    try:
        from instagrapi import Client
    except ImportError:
        print("[instagram] ❌ instagrapi 미설치. pip install instagrapi")
        return None

    cl = Client()
    cl.delay_range = [2, 5]
    instagram_login(cl, username, password, session_file)

    image_paths = [str(p.resolve()) for p in images]
    print(f"[instagram] 캐러셀 업로드 중... ({len(image_paths)}장)")
    media = cl.album_upload(paths=image_paths, caption=caption)

    url = f"https://www.instagram.com/p/{media.code}/"
    print(f"[instagram] ✅ 업로드 완료: {url}")
    return url


# ─────────────────────────────────────────
# 스레드 업로드 (공식 Threads API — threads-uploader.py 위임)
# ─────────────────────────────────────────

def upload_threads(username: str, password: str, images: list[Path], caption: str) -> str | None:
    import subprocess, sys, shutil
    from pathlib import Path as _Path

    # threads-uploader.py 경로 탐색
    here = _Path(__file__).parent
    uploader = here / 'threads-uploader.py'
    if not uploader.exists():
        print("[threads] ❌ threads-uploader.py 없음")
        return None

    # 자격증명 확인
    creds_file = here.parent.parent / '.threads_credentials.json'
    if not creds_file.exists():
        print("[threads] ❌ .threads_credentials.json 없음")
        print("[threads] 공식 Threads API 토큰이 필요합니다.")
        print("[threads]   python .claude/scv/threads-uploader.py --setup-guide 참고")
        return None

    # images_dir: 이미지들이 있는 폴더를 전달
    images_dir = str(images[0].parent)

    cmd = [sys.executable, str(uploader), '--images-dir', images_dir, '--yes']
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode == 0:
        return f"https://www.threads.net/@{username}"
    return None


# ─────────────────────────────────────────
# 메인
# ─────────────────────────────────────────

def main():
    args = parse_args()

    # 자격증명
    username, password = load_credentials(args.username, args.password)

    # 이미지 로드 + JPEG 변환
    print(f"\n[uploader] 이미지 폴더: {args.images_dir}")
    images = load_and_convert_images(args.images_dir)
    print(f"[uploader] {len(images)}장 준비 완료")

    # 캡션 + 해시태그 조합
    hashtags_str = load_hashtags(args.hashtags_file)
    caption = build_caption(args.caption_file, hashtags_str, args.caption)

    # 미리보기
    print(f"\n{'─'*50}")
    print("[ 업로드 미리보기 ]")
    print(f"{'─'*50}")
    print(f"이미지 수  : {len(images)}장")
    print(f"폴더       : {args.images_dir}")
    if args.threads_only:
        upload_target = "스레드만"
    elif args.no_threads:
        upload_target = "인스타그램만"
    else:
        upload_target = "인스타그램 + 스레드"
    print(f"업로드 대상: {upload_target}")
    print(f"\n[ 캡션 ]\n{caption[:300]}{'...' if len(caption) > 300 else ''}")
    print(f"{'─'*50}\n")

    if args.dry_run:
        print("[uploader] --dry-run 모드: 실제 업로드를 건너뜁니다.")
        sys.exit(0)

    # 업로드 최종 확인
    confirm = input('이 내용으로 업로드할까요? (y/N): ').strip().lower()
    if confirm != 'y':
        print('[uploader] 업로드 취소됨.')
        sys.exit(0)

    results = {}

    # ── 인스타그램 업로드 ──
    if not args.threads_only:
        print(f"\n{'═'*50}")
        print("[ 인스타그램 업로드 ]")
        print(f"{'═'*50}")
        ig_url = upload_instagram(username, password, images, caption, args.session_file)
        if ig_url:
            results['instagram'] = ig_url

    # ── 스레드 업로드 ──
    if not args.no_threads:
        print(f"\n{'═'*50}")
        print("[ 스레드 업로드 ]")
        print(f"{'═'*50}")
        th_url = upload_threads(username, password, images, caption)
        if th_url:
            results['threads'] = th_url

    # ── 최종 결과 ──
    print(f"\n{'═'*50}")
    print("[ 업로드 결과 ]")
    print(f"{'═'*50}")
    if results.get('instagram'):
        print(f"  인스타그램: {results['instagram']}")
    if results.get('threads'):
        print(f"  스레드    : {results['threads']}")
    if not results:
        print("  ⚠️  업로드된 플랫폼이 없습니다.")
    print()


if __name__ == '__main__':
    main()
