#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
total_sns_uploader.py — 릴스 영상 1개를 4개 플랫폼에 동시 업로드

플랫폼: 인스타그램 릴스 → 스레드 영상 → 유튜브 쇼츠 → 틱톡

사용법:
  python .claude/scv/total_sns_uploader.py --video output/video/영상.mp4
  python .claude/scv/total_sns_uploader.py --video output/video/영상.mp4 --title "제목 #해시태그"
  python .claude/scv/total_sns_uploader.py --video output/video/영상.mp4 --skip instagram threads
  python .claude/scv/total_sns_uploader.py --video output/video/영상.mp4 --dry-run
"""

import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
import base64
import hashlib
import importlib.util
import json
import os
import re
import secrets
import ssl
import subprocess
import sys
import time
import threading
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# ── 자격증명 파일 경로 ──────────────────────────────────────────────────────
IG_CREDS_FILE      = '.instagram_credentials.json'
IG_SESSION_FILE    = '.instagram_session.json'
THREADS_CREDS_FILE = '.threads_credentials.json'
YT_CLIENT_SECRETS  = 'client_secrets.json'
YT_TOKEN_FILE      = '.youtube_token.json'
TT_TOKEN_FILE      = '.tiktok_token.json'

THREADS_API = "https://graph.threads.net/v1.0"

# ── TikTok API ──────────────────────────────────────────────────────────────
TT_CLIENT_KEY    = os.getenv('TIKTOK_CLIENT_KEY')
TT_CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET')
TT_REDIRECT_URI  = 'https://b9a3c932a64086.lhr.life/callback'
TT_SCOPE         = 'user.info.basic,video.upload,video.publish'
TT_AUTH_URL      = 'https://www.tiktok.com/v2/auth/authorize/'
TT_TOKEN_URL     = 'https://open.tiktokapis.com/v2/oauth/token/'
TT_UPLOAD_INIT   = 'https://open.tiktokapis.com/v2/post/publish/video/init/'
TT_UPLOAD_STATUS = 'https://open.tiktokapis.com/v2/post/publish/status/fetch/'


# ═══════════════════════════════════════════════════════════════════════════
# 공통 유틸
# ═══════════════════════════════════════════════════════════════════════════

def load_hashtags(hashtags_file: str = 'output/drafts/hashtags.md') -> str:
    path = Path(hashtags_file)
    if not path.exists():
        return '#부동산 #아파트 #청약 #aptshowhome'
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


def build_caption(narration_file: str, hashtags: str, override: str | None) -> str:
    if override:
        body = override
    elif Path(narration_file).exists():
        lines = Path(narration_file).read_text(encoding='utf-8').strip().splitlines()
        hook = ' '.join(l.strip() for l in lines[:2] if l.strip())
        cta  = ' '.join(l.strip() for l in lines[-2:] if l.strip())
        body = f"{hook}\n\n{cta}"
    else:
        body = '지금 알아야 할 부동산 인사이트입니다.'
    caption = f"{body}\n\n{hashtags}" if hashtags else body
    if len(caption) > 2200:
        caption = caption[:2197] + '...'
    return caption


def build_threads_caption(caption: str) -> str:
    if len(caption) <= 500:
        return caption
    parts = caption.split('\n\n')
    body  = parts[0]
    tags  = parts[-1].split()[:15] if len(parts) > 1 else []
    return body[:400] + ('\n\n' + ' '.join(tags) if tags else '')


# ═══════════════════════════════════════════════════════════════════════════
# 1. 인스타그램 릴스
# ═══════════════════════════════════════════════════════════════════════════

def upload_instagram(video_path: Path, caption: str) -> str | None:
    try:
        from instagrapi import Client
    except ImportError:
        print("  [instagram] ❌ instagrapi 미설치: pip install instagrapi")
        return None

    creds_path = Path(IG_CREDS_FILE)
    if not creds_path.exists():
        print(f"  [instagram] ❌ 자격증명 파일 없음: {IG_CREDS_FILE}")
        return None

    creds    = json.loads(creds_path.read_text(encoding='utf-8'))
    username = creds.get('username', '')
    password = creds.get('password', '')

    cl = Client()
    cl.delay_range = [1, 3]
    session_path = Path(IG_SESSION_FILE)

    if session_path.exists():
        try:
            cl.load_settings(session_path)
            cl.login(username, password)
        except Exception:
            cl = Client()
            cl.delay_range = [1, 3]
            cl.login(username, password)
            cl.dump_settings(session_path)
    else:
        cl.login(username, password)
        cl.dump_settings(session_path)

    print(f"  [instagram] 릴스 업로드 중...")
    media = cl.clip_upload(path=video_path, caption=caption)
    url   = f"https://www.instagram.com/reel/{media.code}/"
    print(f"  [instagram] ✅ {url}")
    return url


# ═══════════════════════════════════════════════════════════════════════════
# 2. 스레드 릴스
# ═══════════════════════════════════════════════════════════════════════════

def _upload_to_catbox(video_path: Path) -> str:
    print(f"  [threads] 공개 URL 생성 중 ({video_path.stat().st_size/1024/1024:.1f} MB)...")
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
        raise ValueError(f"catbox 실패: {url}")
    return url


def upload_threads(video_path: Path, caption: str) -> str | None:
    creds_path = Path(THREADS_CREDS_FILE)
    if not creds_path.exists():
        print(f"  [threads] ❌ 자격증명 파일 없음: {THREADS_CREDS_FILE}")
        return None

    creds   = json.loads(creds_path.read_text(encoding='utf-8'))
    token   = creds['access_token']
    user_id = creds.get('user_id', '')

    if not user_id:
        r = requests.get(f"{THREADS_API}/me", params={"fields": "id", "access_token": token})
        r.raise_for_status()
        user_id = r.json()['id']

    tc = build_threads_caption(caption)

    video_url = _upload_to_catbox(video_path)

    print("  [threads] 컨테이너 생성 중...")
    r = requests.post(f"{THREADS_API}/{user_id}/threads", params={
        "media_type": "VIDEO", "video_url": video_url,
        "text": tc, "access_token": token,
    })
    if not r.ok:
        print(f"  [threads] ❌ 컨테이너 오류: {r.status_code} {r.text[:200]}")
        return None
    container_id = r.json()['id']

    print("  [threads] 처리 대기 중.", end='', flush=True)
    for _ in range(18):
        time.sleep(5)
        print('.', end='', flush=True)
        chk = requests.get(f"{THREADS_API}/{container_id}",
                           params={"fields": "status,error_message", "access_token": token})
        if chk.ok:
            s = chk.json().get('status', '')
            if s == 'FINISHED':
                print(' 완료')
                break
            if s == 'ERROR':
                print(f"\n  [threads] ❌ 처리 오류: {chk.json().get('error_message')}")
                return None
    else:
        print('\n  [threads] ⚠️  타임아웃 — 그래도 게시 시도')

    r = requests.post(f"{THREADS_API}/{user_id}/threads_publish",
                      params={"creation_id": container_id, "access_token": token})
    if not r.ok:
        print(f"  [threads] ❌ 게시 오류: {r.status_code} {r.text[:200]}")
        return None
    media_id = r.json()['id']

    r = requests.get(f"{THREADS_API}/{media_id}",
                     params={"fields": "id,permalink", "access_token": token})
    url = r.json().get('permalink', 'https://www.threads.net/') if r.ok else 'https://www.threads.net/'
    print(f"  [threads] ✅ {url}")
    return url


# ═══════════════════════════════════════════════════════════════════════════
# 3. 유튜브 쇼츠
# ═══════════════════════════════════════════════════════════════════════════

def _get_youtube_service():
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        raise ImportError("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    creds  = None

    if Path(YT_TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(YT_TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("  [youtube] 토큰 갱신 중...")
            creds.refresh(Request())
        else:
            if not Path(YT_CLIENT_SECRETS).exists():
                raise FileNotFoundError(f"YouTube client_secrets.json 없음: {YT_CLIENT_SECRETS}")
            flow  = InstalledAppFlow.from_client_secrets_file(YT_CLIENT_SECRETS, SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
        Path(YT_TOKEN_FILE).write_text(creds.to_json(), encoding='utf-8')

    return build('youtube', 'v3', credentials=creds)


def upload_youtube(video_path: Path, title: str, caption: str) -> str | None:
    try:
        from googleapiclient.http import MediaFileUpload
        from googleapiclient.errors import HttpError
    except ImportError:
        print("  [youtube] ❌ google-api-python-client 미설치")
        return None

    if '#Shorts' not in title and '#shorts' not in title:
        title = title + ' #Shorts'

    description = caption[:4000] if caption else (
        "부동산 청약 정보 | @aptshowhome\n\n"
        "#Shorts #부동산 #청약 #서울아파트 #aptshowhome"
    )
    tags = ['청약', '부동산', '서울아파트', '쇼츠', 'Shorts', 'aptshowhome']

    try:
        youtube = _get_youtube_service()
    except (ImportError, FileNotFoundError) as e:
        print(f"  [youtube] ❌ {e}")
        return None

    body = {
        'snippet': {
            'title': title[:100],
            'description': description,
            'tags': tags,
            'categoryId': '22',
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        }
    }
    media   = MediaFileUpload(str(video_path), chunksize=1024*1024, resumable=True, mimetype='video/mp4')
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)

    print(f"  [youtube] 업로드 중...")
    response = None
    try:
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
                print(f"\r  [youtube] [{bar}] {pct}%", end='', flush=True)
        print()
    except HttpError as e:
        print(f"\n  [youtube] ❌ 업로드 실패: {e}")
        return None

    url = f"https://www.youtube.com/shorts/{response['id']}"
    print(f"  [youtube] ✅ {url}")
    return url


# ═══════════════════════════════════════════════════════════════════════════
# 4. 틱톡
# ═══════════════════════════════════════════════════════════════════════════

_tt_auth_code = None


def _tt_make_pkce_pair() -> tuple[str, str]:
    """PKCE code_verifier / code_challenge(S256) 쌍 생성"""
    code_verifier  = secrets.token_urlsafe(32)
    digest         = hashlib.sha256(code_verifier.encode('ascii')).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
    return code_verifier, code_challenge


class _TikTokCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _tt_auth_code
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _tt_auth_code = params.get('code', [None])[0]
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write('<h2>TikTok 인증 완료! 창을 닫아도 됩니다.</h2>'.encode('utf-8'))
    def log_message(self, format, *args):
        pass


def _tt_ensure_ssl_cert() -> tuple[str, str]:
    cert = '.tiktok_cert.pem'
    key  = '.tiktok_key.pem'
    if not (Path(cert).exists() and Path(key).exists()):
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', key, '-out', cert, '-days', '365', '-nodes',
            '-subj', '/CN=lvh.me', '-addext', 'subjectAltName=DNS:lvh.me',
        ], check=True, capture_output=True)
    return cert, key


def _tt_get_auth_code(state: str, code_challenge: str) -> str:
    global _tt_auth_code
    _tt_auth_code = None
    params = {
        'client_key': TT_CLIENT_KEY, 'response_type': 'code',
        'scope': TT_SCOPE, 'redirect_uri': TT_REDIRECT_URI, 'state': state,
        'code_challenge': code_challenge, 'code_challenge_method': 'S256',
    }
    url = TT_AUTH_URL + '?' + urllib.parse.urlencode(params)

    cert_file, key_file = _tt_ensure_ssl_cert()
    server  = HTTPServer(('', 8765), _TikTokCallbackHandler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_file, key_file)
    server.socket = context.wrap_socket(server.socket, server_side=True)

    thread = threading.Thread(target=server.handle_request)
    thread.start()
    print(f"\n  [tiktok] 브라우저에서 로그인 후 권한을 허용하세요.")
    print(f"  [tiktok] 인증서 경고 뜨면: 고급 → 계속 진행(lvh.me)")
    print(f"  [tiktok] URL:\n  {url}\n")
    webbrowser.open(url)
    thread.join(timeout=120)
    server.server_close()
    if not _tt_auth_code:
        raise TimeoutError("TikTok 인증 시간 초과 (120초)")
    return _tt_auth_code


def _tt_exchange_token(code: str, code_verifier: str) -> dict:
    r = requests.post(TT_TOKEN_URL, data={
        'client_key': TT_CLIENT_KEY, 'client_secret': TT_CLIENT_SECRET,
        'code': code, 'grant_type': 'authorization_code', 'redirect_uri': TT_REDIRECT_URI,
        'code_verifier': code_verifier,
    })
    data = r.json()
    if 'access_token' not in data:
        raise RuntimeError(f"TikTok 토큰 교환 실패: {data}")
    return data


def _tt_refresh_token(refresh_tok: str) -> dict:
    r = requests.post(TT_TOKEN_URL, data={
        'client_key': TT_CLIENT_KEY, 'client_secret': TT_CLIENT_SECRET,
        'grant_type': 'refresh_token', 'refresh_token': refresh_tok,
    })
    return r.json()


def _tt_get_token() -> dict:
    if Path(TT_TOKEN_FILE).exists():
        tok = json.loads(Path(TT_TOKEN_FILE).read_text(encoding='utf-8'))
        if tok.get('expires_at', 0) > time.time() + 60:
            print("  [tiktok] 저장된 토큰 재사용")
            return tok
        if tok.get('refresh_token'):
            print("  [tiktok] 토큰 갱신 중...")
            new_tok = _tt_refresh_token(tok['refresh_token'])
            if 'access_token' in new_tok:
                new_tok['expires_at'] = time.time() + new_tok.get('expires_in', 86400)
                Path(TT_TOKEN_FILE).write_text(json.dumps(new_tok, ensure_ascii=False, indent=2), encoding='utf-8')
                return new_tok
    state                         = secrets.token_urlsafe(16)
    code_verifier, code_challenge = _tt_make_pkce_pair()
    code = _tt_get_auth_code(state, code_challenge)
    tok  = _tt_exchange_token(code, code_verifier)
    tok['expires_at'] = time.time() + tok.get('expires_in', 86400)
    Path(TT_TOKEN_FILE).write_text(json.dumps(tok, ensure_ascii=False, indent=2), encoding='utf-8')
    return tok


def upload_tiktok(video_path: Path, title: str, privacy: str = 'SELF_ONLY') -> str | None:
    if not TT_CLIENT_KEY or not TT_CLIENT_SECRET:
        print("  [tiktok] ❌ .env에 TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET 필요")
        return None

    try:
        tok          = _tt_get_token()
        access_token = tok['access_token']
    except Exception as e:
        print(f"  [tiktok] ❌ 인증 실패: {e}")
        return None

    file_size = video_path.stat().st_size
    init_body = {
        'post_info': {
            'title': title[:150], 'privacy_level': privacy,
            'disable_duet': False, 'disable_comment': False, 'disable_stitch': False,
        },
        'source_info': {
            'source': 'FILE_UPLOAD', 'video_size': file_size,
            'chunk_size': file_size, 'total_chunk_count': 1,
        }
    }
    r = requests.post(TT_UPLOAD_INIT,
        headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json; charset=UTF-8'},
        json=init_body)
    res = r.json()
    if res.get('error', {}).get('code', 'ok') != 'ok':
        print(f"  [tiktok] ❌ 초기화 실패: {res}")
        return None

    publish_id = res['data']['publish_id']
    upload_url = res['data']['upload_url']

    print(f"  [tiktok] 파일 업로드 중 ({file_size/1024/1024:.1f} MB)...")
    with open(video_path, 'rb') as f:
        video_data = f.read()
    upload_r = requests.put(upload_url, data=video_data, headers={
        'Content-Type': 'video/mp4',
        'Content-Range': f'bytes 0-{file_size-1}/{file_size}',
        'Content-Length': str(file_size),
    })
    if upload_r.status_code not in (200, 201, 206):
        print(f"  [tiktok] ❌ 파일 전송 실패: {upload_r.status_code}")
        return None

    print("  [tiktok] TikTok 처리 대기 중.", end='', flush=True)
    for _ in range(20):
        time.sleep(5)
        print('.', end='', flush=True)
        status_r = requests.post(TT_UPLOAD_STATUS,
            headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json; charset=UTF-8'},
            json={'publish_id': publish_id})
        status_data = status_r.json().get('data', {})
        status      = status_data.get('status', '')
        if status in ('PUBLISH_COMPLETE', 'SEND_TO_USER_INBOX'):
            print(' 완료')
            privacy_label = '나만 보기(샌드박스)' if privacy == 'SELF_ONLY' else privacy
            url = f"https://www.tiktok.com/ [{privacy_label}] publish_id={publish_id}"
            print(f"  [tiktok] ✅ {url}")
            return url
        if status in ('FAILED', 'PUBLISH_FAILED'):
            print(f"\n  [tiktok] ❌ 게시 실패: {status_data}")
            return None
    print('\n  [tiktok] ⚠️  상태 확인 타임아웃')
    return f"publish_id={publish_id} (상태 미확인)"


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

PLATFORMS = ['instagram', 'threads', 'youtube', 'tiktok']

def parse_args():
    p = argparse.ArgumentParser(description='릴스 영상 → 인스타·스레드·유튜브·틱톡 일괄 업로드')
    p.add_argument('--video',    '-v', required=True, help='업로드할 MP4 파일 경로')
    p.add_argument('--title',    '-t', default=None,  help='영상 제목 (유튜브·틱톡 공용)')
    p.add_argument('--caption',        default=None,  help='캡션 직접 입력 (인스타·스레드 공용)')
    p.add_argument('--narration-file', default='output/drafts/narration.txt')
    p.add_argument('--hashtags-file',  default='output/drafts/hashtags.md')
    p.add_argument('--tiktok-privacy', default='SELF_ONLY',
                   choices=['SELF_ONLY', 'MUTUAL_FOLLOW_FRIENDS', 'FOLLOWER_OF_CREATOR', 'PUBLIC_TO_EVERYONE'],
                   help='TikTok 공개 설정 (샌드박스 기본: SELF_ONLY)')
    p.add_argument('--skip', nargs='+', choices=PLATFORMS, default=[],
                   metavar='PLATFORM', help='건너뛸 플랫폼 (예: --skip threads youtube)')
    p.add_argument('--dry-run',  action='store_true', help='미리보기만 (실제 업로드 안 함)')
    p.add_argument('--yes', '-y', action='store_true', help='확인 프롬프트 건너뜀')
    return p.parse_args()


def main():
    args = parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"❌ 파일 없음: {args.video}")
        sys.exit(1)

    size_mb  = video_path.stat().st_size / 1024 / 1024
    hashtags = load_hashtags(args.hashtags_file)
    caption  = build_caption(args.narration_file, hashtags, args.caption)
    title    = args.title or video_path.stem

    skip = set(args.skip)
    plan = [p for p in PLATFORMS if p not in skip]

    print(f"\n{'═'*58}")
    print("[ SNS 일괄 업로드 미리보기 ]")
    print(f"{'─'*58}")
    print(f"파일      : {args.video} ({size_mb:.1f} MB)")
    print(f"제목      : {title}")
    print(f"캡션({len(caption)}자) : {caption[:120]}{'...' if len(caption) > 120 else ''}")
    print(f"TikTok    : {args.tiktok_privacy}")
    print(f"{'─'*58}")
    for p in PLATFORMS:
        flag = '✅ 업로드 예정' if p in plan else '⏭️  건너뜀'
        print(f"  {p:<12}: {flag}")
    print(f"{'═'*58}\n")

    if args.dry_run:
        print("--dry-run: 실제 업로드 없음")
        return

    if not args.yes:
        confirm = input('위 내용으로 업로드할까요? (y/N): ').strip().lower()
        if confirm != 'y':
            print('취소됨')
            return

    results: dict[str, str | None] = {}
    step = 1

    if 'instagram' in plan:
        print(f"\n[{step}/{len(plan)}] 인스타그램 릴스 업로드")
        step += 1
        try:
            results['instagram'] = upload_instagram(video_path, caption)
        except Exception as e:
            print(f"  [instagram] ❌ {e}")
            results['instagram'] = None

    if 'threads' in plan:
        print(f"\n[{step}/{len(plan)}] 스레드 영상 업로드")
        step += 1
        try:
            results['threads'] = upload_threads(video_path, caption)
        except Exception as e:
            print(f"  [threads] ❌ {e}")
            results['threads'] = None

    if 'youtube' in plan:
        print(f"\n[{step}/{len(plan)}] 유튜브 쇼츠 업로드")
        step += 1
        try:
            results['youtube'] = upload_youtube(video_path, title, caption)
        except Exception as e:
            print(f"  [youtube] ❌ {e}")
            results['youtube'] = None

    if 'tiktok' in plan:
        print(f"\n[{step}/{len(plan)}] 틱톡 업로드")
        step += 1
        try:
            results['tiktok'] = upload_tiktok(video_path, title, args.tiktok_privacy)
        except Exception as e:
            print(f"  [tiktok] ❌ {e}")
            results['tiktok'] = None

    # 결과 요약
    success = [p for p, u in results.items() if u]
    fail    = [p for p, u in results.items() if u is None]

    print(f"\n{'═'*58}")
    print(f"[ 업로드 완료 — {len(success)}/{len(results)} 성공 ]")
    print(f"{'─'*58}")
    for p in PLATFORMS:
        if p in results:
            icon = '✅' if results[p] else '❌'
            val  = results[p] or '실패'
            print(f"  {icon} {p:<12}: {val}")
    if fail:
        print(f"\n  실패 플랫폼: {', '.join(fail)}")
    print(f"{'═'*58}\n")


if __name__ == '__main__':
    main()
