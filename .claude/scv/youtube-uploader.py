#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
youtube-uploader.py — MP4 영상을 유튜브 쇼츠로 업로드

사용법:
  python .claude/scv/youtube-uploader.py --video output/video/영상.mp4
  python .claude/scv/youtube-uploader.py --video output/video/영상.mp4 --title "제목" --description "설명"
  python .claude/scv/youtube-uploader.py --video output/video/영상.mp4 --dry-run

최초 실행 시 브라우저 인증 필요 (이후 .youtube_token.json 재사용).
"""

import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
import json
import os
import time
from pathlib import Path

# ── 패키지 확인 ───────────────────────────────────────────────────────────────
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
except ImportError:
    print("❌ 필요 패키지 미설치. 아래 명령어로 설치하세요:")
    print("   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# ── 상수 ─────────────────────────────────────────────────────────────────────
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CLIENT_SECRETS = 'client_secrets.json'
TOKEN_FILE     = '.youtube_token.json'
API_SERVICE    = 'youtube'
API_VERSION    = 'v3'

# ─────────────────────────────────────────────────────────────────────────────
# 인증
# ─────────────────────────────────────────────────────────────────────────────

def get_authenticated_service():
    creds = None

    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("  토큰 갱신 중...")
            creds.refresh(Request())
        else:
            print("  브라우저에서 구글 계정 인증을 완료하세요...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)

        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            f.write(creds.to_json())
        print(f"  ✅ 토큰 저장: {TOKEN_FILE}")

    return build(API_SERVICE, API_VERSION, credentials=creds)


# ─────────────────────────────────────────────────────────────────────────────
# 업로드
# ─────────────────────────────────────────────────────────────────────────────

def upload_video(youtube, video_path: str, title: str, description: str,
                 tags: list, category_id: str = '22', privacy: str = 'public') -> str:
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id,  # 22 = People & Blogs (부동산 콘텐츠 일반)
        },
        'status': {
            'privacyStatus': privacy,
            'selfDeclaredMadeForKids': False,
        }
    }

    media = MediaFileUpload(
        video_path,
        chunksize=1024 * 1024,  # 1MB 청크
        resumable=True,
        mimetype='video/mp4',
    )

    print(f"  업로드 시작: {Path(video_path).name}")
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
            print(f"\r  [{bar}] {pct}%", end='', flush=True)

    print()
    video_id = response['id']
    return f"https://www.youtube.com/shorts/{video_id}"


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description='MP4 → 유튜브 쇼츠 업로드')
    p.add_argument('--video',       '-v', required=True, help='업로드할 MP4 파일 경로')
    p.add_argument('--title',       '-t', default=None,  help='영상 제목 (기본: 파일명 기반 자동 생성)')
    p.add_argument('--description', '-d', default=None,  help='영상 설명')
    p.add_argument('--tags',              default=None,  help='쉼표 구분 태그 (예: "청약,부동산,서울")')
    p.add_argument('--privacy',           default='public',
                   choices=['public', 'private', 'unlisted'], help='공개 설정 (기본: public)')
    p.add_argument('--client-secrets',    default=CLIENT_SECRETS, help='OAuth 클라이언트 시크릿 파일')
    p.add_argument('--dry-run',           action='store_true', help='실제 업로드 없이 미리보기만')
    p.add_argument('--yes', '-y',         action='store_true', help='확인 프롬프트 건너뜀')
    return p.parse_args()


def main():
    args = parse_args()

    # ── 파일 확인 ───────────────────────────────────────────────────────────
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"❌ 파일 없음: {args.video}")
        sys.exit(1)

    size_mb = video_path.stat().st_size / (1024 * 1024)

    # ── 메타데이터 자동 생성 ─────────────────────────────────────────────────
    title = args.title or f"{video_path.stem} #Shorts"
    # #Shorts가 제목에 없으면 쇼츠로 분류 안 될 수 있음
    if '#Shorts' not in title and '#shorts' not in title:
        title = title + ' #Shorts'

    description = args.description or (
        "부동산 청약 정보 | @aptshowhome\n\n"
        "#Shorts #부동산 #청약 #서울아파트 #aptshowhome"
    )

    tags = [t.strip() for t in args.tags.split(',')] if args.tags else [
        '청약', '부동산', '서울아파트', '쇼츠', 'Shorts', 'aptshowhome', '부동산정보'
    ]

    # ── 미리보기 ─────────────────────────────────────────────────────────────
    print("\n" + "─" * 54)
    print("[ 유튜브 쇼츠 업로드 미리보기 ]")
    print("─" * 54)
    print(f"파일    : {args.video} ({size_mb:.1f} MB)")
    print(f"제목    : {title}")
    print(f"태그    : {', '.join(tags[:5])}{'...' if len(tags) > 5 else ''}")
    print(f"공개설정: {args.privacy}")
    print(f"설명    :\n{description[:120]}{'...' if len(description) > 120 else ''}")
    print("─" * 54)

    if args.dry_run:
        print("🔍 Dry-run 완료 (실제 업로드 없음)")
        return

    if not args.yes:
        ans = input("\n이 내용으로 업로드할까요? (y/N): ").strip().lower()
        if ans != 'y':
            print("취소됨")
            sys.exit(0)

    # ── 인증 ─────────────────────────────────────────────────────────────────
    global CLIENT_SECRETS
    CLIENT_SECRETS = args.client_secrets
    print(f"\n[유튜브] 인증 중...")
    youtube = get_authenticated_service()
    print("[유튜브] ✅ 인증 완료")

    # ── 업로드 ───────────────────────────────────────────────────────────────
    print("\n[유튜브] 쇼츠 업로드 중...")
    try:
        url = upload_video(
            youtube, str(video_path),
            title=title,
            description=description,
            tags=tags,
            privacy=args.privacy,
        )
        print(f"\n{'═' * 54}")
        print("[ 업로드 완료 ]")
        print(f"  유튜브 쇼츠: {url}")
        print(f"{'═' * 54}\n")
    except HttpError as e:
        print(f"\n❌ 업로드 실패: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
