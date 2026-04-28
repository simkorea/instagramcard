#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
reels-uploader.py — 릴스 MP4 파일을 인스타그램 + 스레드에 동시 업로드

사용법:
  python .claude/scv/reels-uploader.py --video output/reels/final_reels.mp4
  python .claude/scv/reels-uploader.py --video output/reels/final_reels.mp4 --no-threads
  python .claude/scv/reels-uploader.py --video output/reels/final_reels.mp4 --caption "직접 입력 캡션"
  python .claude/scv/reels-uploader.py --video output/reels/final_reels.mp4 --dry-run
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

THREADS_API = "https://graph.threads.net/v1.0"


# ─────────────────────────────────────────
# CLI
# ─────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description='릴스 MP4 인스타그램 + 스레드 업로드')
    p.add_argument('--video', '-v', required=True, help='업로드할 MP4 파일 경로')
    p.add_argument('--caption', help='캡션 직접 입력 (생략 시 narration.txt + hashtags.md 자동 조합)')
    p.add_argument('--narration-file', default='output/drafts/narration.txt', help='나레이션 파일')
    p.add_argument('--hashtags-file', default='output/drafts/hashtags.md', help='해시태그 파일')
    p.add_argument('--cover', help='커버 이미지 경로 (선택, 없으면 자동 생성)')
    p.add_argument('--ig-creds', default='.instagram_credentials.json')
    p.add_argument('--ig-session', default='.instagram_session.json')
    p.add_argument('--threads-creds', default='.threads_credentials.json')
    p.add_argument('--no-threads', action='store_true', help='스레드 업로드 건너뜀')
    p.add_argument('--no-instagram', action='store_true', help='인스타그램 업로드 건너뜀')
    p.add_argument('--yes', '-y', action='store_true', help='확인 프롬프트 건너뜀')
    p.add_argument('--dry-run', action='store_true', help='실제 업로드 없이 미리보기만')
    return p.parse_args()


# ─────────────────────────────────────────
# 캡션 생성
# ─────────────────────────────────────────

def load_hashtags(hashtags_file: str) -> str:
    path = Path(hashtags_file)
    if not path.exists():
        return '#부동산 #아파트 #aptshowhome'
    content = path.read_text(encoding='utf-8')
    seen, tags = set(), []
    for line in content.splitlines():
        s = line.strip()
        if s.startswith('##') or s.startswith('```'):
            continue
        for tag in re.findall(r'#[가-힣\w]+', s):
            if tag not in seen:
                seen.add(tag)
                tags.append(tag)
    return ' '.join(tags[:20])


def build_caption(narration_file: str, hashtags_str: str, override: str | None) -> str:
    if override:
        body = override
    elif Path(narration_file).exists():
        lines = Path(narration_file).read_text(encoding='utf-8').strip().splitlines()
        # 앞 3줄 = 훅 (캡션 상단), 마지막 2줄 = CTA
        hook = ' '.join(l.strip() for l in lines[:2] if l.strip())
        cta  = ' '.join(l.strip() for l in lines[-2:] if l.strip())
        body = f"{hook}\n\n{cta}"
    else:
        body = '지금 알아야 할 부동산 인사이트입니다.'

    caption = f"{body}\n\n{hashtags_str}" if hashtags_str else body

    # Instagram Reels 캡션 2200자 제한
    if len(caption) > 2200:
        caption = caption[:2197] + '...'
    return caption


def build_threads_caption(caption: str) -> str:
    """Threads 500자 제한 적용"""
    if len(caption) <= 500:
        return caption
    parts = caption.split('\n\n')
    body_part = parts[0]
    tags = parts[-1].split()[:15] if len(parts) > 1 else []
    return body_part[:400] + ('\n\n' + ' '.join(tags) if tags else '')


# ─────────────────────────────────────────
# 인스타그램 Reels 업로드 (instagrapi)
# ─────────────────────────────────────────

def upload_instagram_reels(video_path: Path, caption: str, ig_creds_file: str, ig_session_file: str) -> str:
    try:
        from instagrapi import Client
    except ImportError:
        print("❌ instagrapi 미설치. pip install instagrapi")
        sys.exit(1)

    creds_path = Path(ig_creds_file)
    if not creds_path.exists():
        print(f"❌ 인스타그램 자격증명 파일 없음: {ig_creds_file}")
        sys.exit(1)

    creds = json.loads(creds_path.read_text(encoding='utf-8'))
    username = creds.get('username', '')
    password = creds.get('password', '')

    cl = Client()
    cl.delay_range = [1, 3]

    session_path = Path(ig_session_file)
    if session_path.exists():
        try:
            cl.load_settings(session_path)
            cl.login(username, password)
            print(f"[instagram] 세션 재사용: {ig_session_file}")
        except Exception:
            print("[instagram] 세션 만료 — 새로 로그인")
            cl = Client()
            cl.delay_range = [1, 3]
            cl.login(username, password)
            cl.dump_settings(session_path)
    else:
        cl.login(username, password)
        cl.dump_settings(session_path)
        print(f"[instagram] 새 세션 저장: {ig_session_file}")

    print(f"[instagram] 릴스 업로드 중: {video_path.name} ({video_path.stat().st_size // 1024 // 1024} MB)")
    media = cl.clip_upload(
        path=video_path,
        caption=caption,
    )
    url = f"https://www.instagram.com/reel/{media.code}/"
    print(f"[instagram] ✅ 업로드 완료: {url}")
    return url


# ─────────────────────────────────────────
# 영상 공개 URL 확보 (Threads용)
# ─────────────────────────────────────────

def upload_video_to_catbox(video_path: Path) -> str:
    """catbox.moe에 영상 업로드 → 공개 URL 반환 (Threads VIDEO API 필요)"""
    size_mb = video_path.stat().st_size / 1024 / 1024
    print(f"[threads] 영상 공개 URL 확보 중 ({size_mb:.1f} MB)...")
    with open(video_path, 'rb') as f:
        r = requests.post(
            'https://catbox.moe/user/api.php',
            data={'reqtype': 'fileupload', 'userhash': ''},
            files={'fileToUpload': (video_path.name, f, 'video/mp4')},
            timeout=180,
        )
    r.raise_for_status()
    url = r.text.strip()
    if not url.startswith('http'):
        raise ValueError(f"catbox 업로드 실패: {url}")
    print(f"[threads] 공개 URL: {url}")
    return url


# ─────────────────────────────────────────
# Threads 릴스 업로드 (Meta Threads API VIDEO)
# ─────────────────────────────────────────

def upload_threads_reels(video_url: str, caption: str, creds_file: str) -> str:
    creds_path = Path(creds_file)
    if not creds_path.exists():
        raise FileNotFoundError(f"Threads 자격증명 파일 없음: {creds_file}")

    creds = json.loads(creds_path.read_text(encoding='utf-8'))
    token = creds['access_token']
    user_id = creds.get('user_id', '')

    if not user_id:
        r = requests.get(f"{THREADS_API}/me", params={"fields": "id", "access_token": token})
        r.raise_for_status()
        user_id = r.json()['id']

    threads_caption = build_threads_caption(caption)

    # 1단계: VIDEO 컨테이너 생성
    print("[threads] VIDEO 컨테이너 생성 중...")
    r = requests.post(f"{THREADS_API}/{user_id}/threads", params={
        "media_type": "VIDEO",
        "video_url": video_url,
        "text": threads_caption,
        "access_token": token,
    })
    if not r.ok:
        print(f"[threads] 컨테이너 오류: {r.status_code} {r.text[:200]}")
        r.raise_for_status()
    container_id = r.json()['id']
    print(f"[threads] 컨테이너 ID: {container_id}")

    # 2단계: 처리 완료 대기 (최대 90초)
    print("[threads] 영상 처리 대기 중...", end='', flush=True)
    for _ in range(18):
        time.sleep(5)
        print('.', end='', flush=True)
        check = requests.get(f"{THREADS_API}/{container_id}", params={
            "fields": "status,error_message",
            "access_token": token,
        })
        if check.ok:
            data = check.json()
            status = data.get('status', '')
            if status == 'FINISHED':
                print(' 완료')
                break
            elif status == 'ERROR':
                print(f"\n[threads] ❌ 처리 오류: {data.get('error_message', '알 수 없음')}")
                raise RuntimeError(f"Threads 영상 처리 실패: {data.get('error_message')}")
    else:
        print('\n[threads] ⚠️  처리 타임아웃 — 그래도 게시 시도')

    # 3단계: 게시
    print("[threads] 게시 중...")
    r = requests.post(f"{THREADS_API}/{user_id}/threads_publish", params={
        "creation_id": container_id,
        "access_token": token,
    })
    if not r.ok:
        print(f"[threads] 게시 오류: {r.status_code} {r.text[:200]}")
        r.raise_for_status()
    media_id = r.json()['id']

    # 퍼머링크 조회
    r = requests.get(f"{THREADS_API}/{media_id}", params={
        "fields": "id,permalink",
        "access_token": token,
    })
    url = r.json().get('permalink', 'https://www.threads.net/') if r.ok else 'https://www.threads.net/'
    print(f"[threads] ✅ 게시 완료: {url}")
    return url


# ─────────────────────────────────────────
# 메인
# ─────────────────────────────────────────

def main():
    args = parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"❌ 파일 없음: {video_path}")
        sys.exit(1)

    # 캡션 준비
    hashtags = load_hashtags(args.hashtags_file)
    caption  = build_caption(args.narration_file, hashtags, args.caption)

    size_mb  = video_path.stat().st_size / 1024 / 1024

    print(f"\n{'─'*55}")
    print("[ 릴스 업로드 미리보기 ]")
    print(f"{'─'*55}")
    print(f"파일    : {video_path} ({size_mb:.1f} MB)")
    print(f"캡션({len(caption)}자):\n{caption[:300]}{'...' if len(caption) > 300 else ''}")
    print(f"{'─'*55}")
    print(f"인스타그램 릴스: {'건너뜀' if args.no_instagram else '업로드 예정'}")
    print(f"스레드 영상     : {'건너뜀' if args.no_threads else '업로드 예정'}")
    print(f"{'─'*55}\n")

    if args.dry_run:
        print("--dry-run: 실제 업로드 건너뜀")
        return

    if not args.yes:
        confirm = input('업로드를 진행할까요? (y/N): ').strip().lower()
        if confirm != 'y':
            print('취소됨.')
            return

    ig_url      = None
    threads_url = None
    video_public_url = None

    # ── 인스타그램 릴스 ──
    if not args.no_instagram:
        print("\n[1/2] 인스타그램 릴스 업로드")
        try:
            ig_url = upload_instagram_reels(video_path, caption, args.ig_creds, args.ig_session)
        except Exception as e:
            print(f"[instagram] ❌ 실패: {e}")

    # ── Threads 영상 ──
    if not args.no_threads:
        print("\n[2/2] 스레드 영상 업로드")
        try:
            video_public_url = upload_video_to_catbox(video_path)
            threads_url = upload_threads_reels(video_public_url, caption, args.threads_creds)
        except Exception as e:
            print(f"[threads] ❌ 실패: {e}")

    # 결과 요약
    print(f"\n{'═'*55}")
    print("[ 업로드 완료 ]")
    if ig_url:
        print(f"  인스타그램: {ig_url}")
    if threads_url:
        print(f"  스레드    : {threads_url}")
    if not ig_url and not threads_url:
        print("  ⚠️  업로드된 플랫폼 없음")
    print(f"{'═'*55}")


if __name__ == '__main__':
    main()
