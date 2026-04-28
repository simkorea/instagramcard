#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tiktok-uploader.py — MP4 영상을 TikTok에 업로드 (Content Posting API v2)

인증 2단계 흐름:
  # 1단계: URL 생성 → 브라우저에서 로그인 → 리다이렉트 URL 복사
  python .claude/scv/tiktok-uploader.py --get-url

  # 2단계: 복사한 리다이렉트 URL로 토큰 교환
  python .claude/scv/tiktok-uploader.py --exchange-code "https://lvh.me:8765/callback?code=..."

업로드:
  python .claude/scv/tiktok-uploader.py --video output/video/영상.mp4
  python .claude/scv/tiktok-uploader.py --video output/video/영상.mp4 --title "제목 #해시태그"
"""

import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
import base64
import hashlib
import json
import os
import time
import urllib.parse
import secrets
import webbrowser
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# ── 상수 ─────────────────────────────────────────────────────────────────────
CLIENT_KEY    = os.getenv('TIKTOK_CLIENT_KEY')
CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET')
REDIRECT_URI  = 'https://b9a3c932a64086.lhr.life/callback'
TOKEN_FILE    = '.tiktok_token.json'
PKCE_FILE     = '.tiktok_pkce.json'
SCOPE         = 'user.info.basic,video.upload,video.publish'

AUTH_URL      = 'https://www.tiktok.com/v2/auth/authorize/'
TOKEN_URL     = 'https://open.tiktokapis.com/v2/oauth/token/'
UPLOAD_INIT   = 'https://open.tiktokapis.com/v2/post/publish/video/init/'
UPLOAD_STATUS = 'https://open.tiktokapis.com/v2/post/publish/status/fetch/'
CREATOR_INFO  = 'https://open.tiktokapis.com/v2/post/publish/creator_info/query/'

# ─────────────────────────────────────────────────────────────────────────────
# OAuth 2.0 인증
# ─────────────────────────────────────────────────────────────────────────────

def _make_pkce_pair() -> tuple[str, str]:
    """PKCE code_verifier / code_challenge(S256) 쌍 생성"""
    code_verifier  = secrets.token_urlsafe(32)
    digest         = hashlib.sha256(code_verifier.encode('ascii')).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
    return code_verifier, code_challenge


def cmd_get_url():
    """1단계: 인증 URL 생성 + PKCE verifier 파일 저장 후 즉시 종료"""
    state                         = secrets.token_urlsafe(16)
    code_verifier, code_challenge = _make_pkce_pair()

    Path(PKCE_FILE).write_text(
        json.dumps({'code_verifier': code_verifier, 'state': state}, ensure_ascii=False),
        encoding='utf-8'
    )

    params = {
        'client_key':            CLIENT_KEY,
        'response_type':         'code',
        'scope':                 SCOPE,
        'redirect_uri':          REDIRECT_URI,
        'state':                 state,
        'code_challenge':        code_challenge,
        'code_challenge_method': 'S256',
    }
    auth_url = AUTH_URL + '?' + urllib.parse.urlencode(params)

    print(f"\n{'─'*62}")
    print("  [1단계] 아래 URL을 브라우저에서 열어 TikTok 로그인 후 권한을 허용하세요.")
    print(f"{'─'*62}")
    print(f"\n  {auth_url}\n")
    print(f"{'─'*62}")
    print("  권한 허용 후 브라우저 주소창에 표시되는 리다이렉트 URL을 복사하세요.")
    print("  (페이지가 오류여도 주소창 URL만 복사하면 됩니다)\n")
    print("  복사했으면 아래 명령으로 2단계를 진행하세요:")
    print(f'  python .claude/scv/tiktok-uploader.py --exchange-code "복사한URL"\n')
    webbrowser.open(auth_url)


def cmd_exchange_code(redirect_url: str):
    """2단계: 저장된 PKCE verifier로 auth code → access token 교환"""
    if not Path(PKCE_FILE).exists():
        print("❌ PKCE 데이터 없음. 먼저 --get-url로 URL을 생성하세요.")
        sys.exit(1)

    pkce          = json.loads(Path(PKCE_FILE).read_text(encoding='utf-8'))
    code_verifier = pkce['code_verifier']

    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(redirect_url).query)
    code   = parsed.get('code', [None])[0]
    if not code:
        print("❌ URL에서 code를 찾지 못했습니다. 리다이렉트 URL 전체를 붙여넣으세요.")
        sys.exit(1)

    print(f"  code 추출 완료 ({code[:20]}...)")
    tok = _exchange_token(code, code_verifier)
    tok['expires_at'] = time.time() + tok.get('expires_in', 86400)
    Path(TOKEN_FILE).write_text(json.dumps(tok, ensure_ascii=False, indent=2), encoding='utf-8')
    Path(PKCE_FILE).unlink(missing_ok=True)
    print(f"  ✅ 토큰 저장 완료: {TOKEN_FILE}")
    return tok


def _exchange_token(code: str, code_verifier: str) -> dict:
    """auth code + code_verifier로 access_token 교환 (PKCE)"""
    r = requests.post(TOKEN_URL, data={
        'client_key':     CLIENT_KEY,
        'client_secret':  CLIENT_SECRET,
        'code':           code,
        'grant_type':     'authorization_code',
        'redirect_uri':   REDIRECT_URI,
        'code_verifier':  code_verifier,
    })
    data = r.json()
    if 'access_token' not in data:
        print(f"❌ 토큰 교환 실패: {data}")
        sys.exit(1)
    return data


def _refresh_token(refresh_tok: str) -> dict:
    r = requests.post(TOKEN_URL, data={
        'client_key':     CLIENT_KEY,
        'client_secret':  CLIENT_SECRET,
        'grant_type':     'refresh_token',
        'refresh_token':  refresh_tok,
    })
    return r.json()


def get_token() -> dict:
    """저장된 토큰 로드 (만료 시 refresh). 토큰 없으면 --get-url 안내 후 종료."""
    if Path(TOKEN_FILE).exists():
        tok = json.loads(Path(TOKEN_FILE).read_text(encoding='utf-8'))
        if tok.get('expires_at', 0) > time.time() + 60:
            print("  ✅ 저장된 토큰 재사용")
            return tok
        if tok.get('refresh_token'):
            print("  토큰 갱신 중...")
            new_tok = _refresh_token(tok['refresh_token'])
            if 'access_token' in new_tok:
                new_tok['expires_at'] = time.time() + new_tok.get('expires_in', 86400)
                Path(TOKEN_FILE).write_text(json.dumps(new_tok, ensure_ascii=False, indent=2), encoding='utf-8')
                print("  ✅ 토큰 갱신 완료")
                return new_tok

    print("❌ 저장된 토큰 없음. 먼저 인증을 완료하세요:")
    print("   1) python .claude/scv/tiktok-uploader.py --get-url")
    print('   2) python .claude/scv/tiktok-uploader.py --exchange-code "리다이렉트URL"')
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# 크리에이터 정보 조회
# ─────────────────────────────────────────────────────────────────────────────

def get_creator_info(access_token: str) -> dict:
    r = requests.post(CREATOR_INFO,
        headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json; charset=UTF-8'},
        json={}
    )
    return r.json().get('data', {})

# ─────────────────────────────────────────────────────────────────────────────
# 영상 업로드
# ─────────────────────────────────────────────────────────────────────────────

def upload_video(access_token: str, video_path: str, title: str,
                 privacy: str = 'SELF_ONLY') -> str:
    """
    TikTok Content Posting API v2 — FILE_UPLOAD 방식
    sandbox: privacy_level = SELF_ONLY (실제 게시 안 됨)
    """
    file_size = Path(video_path).stat().st_size

    # 1. 업로드 초기화
    print("  [1/3] 업로드 초기화 중...")
    init_body = {
        'post_info': {
            'title':          title,
            'privacy_level':  privacy,
            'disable_duet':   False,
            'disable_comment':False,
            'disable_stitch': False,
        },
        'source_info': {
            'source':          'FILE_UPLOAD',
            'video_size':      file_size,
            'chunk_size':      file_size,  # 단일 청크
            'total_chunk_count': 1,
        }
    }
    r = requests.post(UPLOAD_INIT,
        headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json; charset=UTF-8'},
        json=init_body
    )
    res = r.json()
    if res.get('error', {}).get('code', 'ok') != 'ok':
        print(f"❌ 초기화 실패: {res}")
        sys.exit(1)

    publish_id  = res['data']['publish_id']
    upload_url  = res['data']['upload_url']
    print(f"  publish_id: {publish_id}")

    # 2. 파일 업로드
    print("  [2/3] 영상 파일 업로드 중...")
    with open(video_path, 'rb') as f:
        video_data = f.read()

    upload_r = requests.put(
        upload_url,
        data=video_data,
        headers={
            'Content-Type':  'video/mp4',
            'Content-Range': f'bytes 0-{file_size-1}/{file_size}',
            'Content-Length': str(file_size),
        }
    )
    if upload_r.status_code not in (200, 201, 206):
        print(f"❌ 파일 업로드 실패: {upload_r.status_code} {upload_r.text}")
        sys.exit(1)
    print("  ✅ 파일 전송 완료")

    # 3. 처리 상태 대기
    print("  [3/3] TikTok 처리 대기 중...")
    for _ in range(20):
        time.sleep(5)
        status_r = requests.post(UPLOAD_STATUS,
            headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json; charset=UTF-8'},
            json={'publish_id': publish_id}
        )
        status_data = status_r.json().get('data', {})
        status = status_data.get('status', '')
        print(f"  상태: {status}")
        if status in ('PUBLISH_COMPLETE', 'SEND_TO_USER_INBOX'):
            return publish_id
        if status in ('FAILED', 'PUBLISH_FAILED'):
            print(f"❌ 게시 실패: {status_data}")
            sys.exit(1)

    return publish_id

# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description='MP4 → TikTok 업로드')
    p.add_argument('--video',          '-v', default=None, help='업로드할 MP4 파일')
    p.add_argument('--title',          '-t', default=None, help='영상 제목 + 해시태그')
    p.add_argument('--privacy',              default='SELF_ONLY',
                   choices=['SELF_ONLY', 'MUTUAL_FOLLOW_FRIENDS', 'FOLLOWER_OF_CREATOR', 'PUBLIC_TO_EVERYONE'],
                   help='공개 설정 (샌드박스: SELF_ONLY)')
    p.add_argument('--get-url',              action='store_true', help='[1단계] 인증 URL 생성 + 브라우저 열기')
    p.add_argument('--exchange-code',        default=None, metavar='REDIRECT_URL',
                   help='[2단계] 리다이렉트 URL로 토큰 교환')
    p.add_argument('--yes',            '-y', action='store_true', help='확인 건너뜀')
    return p.parse_args()


def main():
    args = parse_args()

    if not CLIENT_KEY or not CLIENT_SECRET:
        print("❌ .env에 TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET 필요")
        sys.exit(1)

    # ── 인증 단계 명령 ──────────────────────────────────────────────────────────
    if args.get_url:
        cmd_get_url()
        return

    if args.exchange_code:
        print("\n[TikTok] 토큰 교환 중...")
        cmd_exchange_code(args.exchange_code)
        print("[TikTok] ✅ 인증 완료. 이제 --video 옵션으로 업로드하세요.")
        return

    if not args.video:
        print("❌ --video 옵션 필요")
        sys.exit(1)

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"❌ 파일 없음: {args.video}")
        sys.exit(1)

    title = args.title or f"공덕역 자이르네 청약 D-1 #공덕역청약 #서울청약 #부동산 #청약정보 #aptshowhome"
    size_mb = video_path.stat().st_size / (1024 * 1024)

    print(f"\n{'─'*52}")
    print("[ TikTok 업로드 미리보기 ]")
    print(f"{'─'*52}")
    print(f"파일    : {args.video} ({size_mb:.1f} MB)")
    print(f"제목    : {title}")
    print(f"공개설정: {args.privacy}")
    print(f"{'─'*52}")

    if not args.yes:
        ans = input("\n업로드할까요? (y/N): ").strip().lower()
        if ans != 'y':
            print("취소됨")
            return

    print("\n[TikTok] 인증 확인 중...")
    tok          = get_token()
    access_token = tok['access_token']

    print("[TikTok] 업로드 시작...")
    publish_id = upload_video(access_token, str(video_path), title, args.privacy)

    print(f"\n{'═'*52}")
    print("[ TikTok 업로드 완료 ]")
    print(f"  publish_id: {publish_id}")
    print(f"  ※ 샌드박스 모드: 실제 공개 게시 안 됨 (SELF_ONLY)")
    print(f"  ※ 실제 게시 시: --privacy PUBLIC_TO_EVERYONE")
    print(f"{'═'*52}\n")


if __name__ == '__main__':
    main()
