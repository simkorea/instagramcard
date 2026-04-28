#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
threads-uploader.py

공식 Meta Threads API를 사용해 카드뉴스를 스레드에 캐러셀로 업로드합니다.
이미지는 catbox.moe에 임시 업로드하여 공개 URL을 확보합니다.

사전 준비 (최초 1회):
  1. developers.facebook.com 에서 Meta 앱 생성
  2. Threads API 추가
  3. access_token 발급 → .threads_credentials.json 에 저장

  자세한 방법: python threads-uploader.py --setup-guide

사용법:
  python .claude/scv/threads-uploader.py \
    --images-dir "output/final/20260416_아파트매수타이밍"

요구사항:
  pip install requests pillow
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ requests 미설치. pip install requests")
    sys.exit(1)


THREADS_API  = "https://graph.threads.net/v1.0"


# ─────────────────────────────────────────
# 셋업 가이드
# ─────────────────────────────────────────

SETUP_GUIDE = """
╔══════════════════════════════════════════════════════════════╗
║          Threads API 액세스 토큰 발급 가이드 (5단계)          ║
╚══════════════════════════════════════════════════════════════╝

1. Meta 개발자 앱 생성
   ① https://developers.facebook.com 접속 (Meta 계정 로그인)
   ② 우측 상단 "내 앱" → "앱 만들기" 클릭
   ③ 유형 선택: "기타" → "소비자"
   ④ 앱 이름 입력 (예: "threads-uploader") → 앱 만들기

2. Threads API 추가
   ① 앱 대시보드 → "제품 추가"
   ② "Threads API" 찾아서 "설정" 클릭

3. 액세스 토큰 발급
   ① 좌측 메뉴 "Threads API" → "빠른 시작"
   ② "사용자 토큰 생성기"에서 본인 계정(aptshowhome) 선택
   ③ 권한 선택:
      ✅ threads_basic
      ✅ threads_content_publish
   ④ "토큰 생성" 클릭 → 표시된 토큰 복사

4. 장기 토큰으로 교환 (60일 유효)
   아래 주소를 브라우저에서 열기:
   https://graph.threads.net/access_token?
     grant_type=th_exchange_token&
     client_id={앱_ID}&
     client_secret={앱_시크릿}&
     access_token={위에서_받은_토큰}

   → 반환된 access_token 값 복사

5. 자격증명 파일 저장
   .threads_credentials.json 파일에 저장:
   {
     "access_token": "여기에_발급받은_토큰_붙여넣기",
     "user_id": ""  ← 비워두면 자동으로 조회됩니다
   }

완료 후 업로드 실행:
  python .claude/scv/threads-uploader.py --images-dir "output/final/..."
"""


# ─────────────────────────────────────────
# CLI 파싱
# ─────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description='스레드 캐러셀 업로드 (공식 Threads API)')
    p.add_argument('--images-dir', '-i', help='이미지 폴더 경로 (PNG)')
    p.add_argument('--caption-file', default='output/drafts/script.md')
    p.add_argument('--hashtags-file', default='output/drafts/hashtags.md')
    p.add_argument('--caption', help='캡션 직접 입력')
    p.add_argument('--creds-file', default='.threads_credentials.json')
    p.add_argument('--dry-run', action='store_true', help='업로드 없이 미리보기')
    p.add_argument('--yes', '-y', action='store_true', help='확인 프롬프트 자동 승인')
    p.add_argument('--setup-guide', action='store_true', help='액세스 토큰 발급 가이드 출력')
    return p.parse_args()


# ─────────────────────────────────────────
# 자격증명
# ─────────────────────────────────────────

def load_creds(creds_file: str) -> dict:
    path = Path(creds_file)
    if not path.exists():
        print(f"❌ 자격증명 파일 없음: {creds_file}")
        print("   python .claude/scv/threads-uploader.py --setup-guide")
        sys.exit(1)
    creds = json.loads(path.read_text(encoding='utf-8'))
    if not creds.get('access_token'):
        print(f"❌ access_token이 비어 있습니다: {creds_file}")
        print("   python .claude/scv/threads-uploader.py --setup-guide")
        sys.exit(1)
    return creds


def get_user_id(token: str, stored_id: str) -> str:
    if stored_id:
        return stored_id
    print("[threads] user_id 조회 중...")
    r = requests.get(f"{THREADS_API}/me", params={"access_token": token, "fields": "id,username"})
    r.raise_for_status()
    data = r.json()
    print(f"[threads] 계정: @{data.get('username')} (id={data['id']})")
    return data['id']


# ─────────────────────────────────────────
# 이미지 준비 (PNG → JPG)
# ─────────────────────────────────────────

def prepare_images(images_dir: str) -> list[Path]:
    from PIL import Image

    dir_path = Path(images_dir)
    if not dir_path.exists():
        print(f"❌ 폴더 없음: {images_dir}")
        sys.exit(1)

    pngs = sorted(dir_path.glob('*.png'),
                  key=lambda p: int(m.group()) if (m := re.search(r'\d+', p.stem)) else 0)
    if not pngs:
        print(f"❌ PNG 없음: {images_dir}")
        sys.exit(1)

    if len(pngs) > 20:
        print("⚠️  Threads 최대 20장 — 앞 20장만 사용")
        pngs = pngs[:20]

    jpg_dir = Path(str(dir_path) + '_jpg')
    jpg_dir.mkdir(exist_ok=True)
    jpgs = []
    for p in pngs:
        out = jpg_dir / (p.stem + '.jpg')
        if not out.exists():
            Image.open(p).convert('RGB').save(out, 'JPEG', quality=95)
        jpgs.append(out)
    print(f"[threads] JPEG 변환: {len(jpgs)}장 → {jpg_dir}")
    return jpgs


# ─────────────────────────────────────────
# 이미지 공개 URL 업로드 (imgur → litterbox 순서로 시도)
# ─────────────────────────────────────────

def upload_to_imgur(jpg_path: Path) -> str:
    with open(jpg_path, 'rb') as f:
        r = requests.post(
            'https://api.imgur.com/3/image',
            headers={'Authorization': 'Client-ID 546c25a59c58ad7'},
            files={'image': (jpg_path.name, f, 'image/jpeg')},
            timeout=60
        )
    if r.ok:
        data = r.json()
        if data.get('success'):
            return data['data']['link']
    raise ValueError(f"imgur 업로드 실패: {r.text[:100]}")


def upload_to_litterbox(jpg_path: Path) -> str:
    with open(jpg_path, 'rb') as f:
        r = requests.post(
            'https://litterbox.catbox.moe/resources/internals/api.php',
            data={'reqtype': 'fileupload', 'time': '72h'},
            files={'fileToUpload': (jpg_path.name, f, 'image/jpeg')},
            timeout=60
        )
    r.raise_for_status()
    url = r.text.strip()
    if not url.startswith('http'):
        raise ValueError(f"litterbox 업로드 실패: {url}")
    return url


def upload_image_public(jpg_path: Path) -> str:
    try:
        return upload_to_litterbox(jpg_path)
    except Exception as e1:
        print(f"    litterbox 실패({e1}), imgur 시도...")
        try:
            return upload_to_imgur(jpg_path)
        except Exception as e2:
            raise ValueError(f"모든 업로드 실패 — litterbox: {e1} / imgur: {e2}")


# ─────────────────────────────────────────
# 캡션 생성
# ─────────────────────────────────────────

def load_hashtags(hashtags_file: str) -> str:
    path = Path(hashtags_file)
    if not path.exists():
        return ''
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
    return ' '.join(tags)


def build_caption(caption_file: str, hashtags_str: str, override: str | None) -> str:
    if override:
        body = override
    elif Path(caption_file).exists():
        content = Path(caption_file).read_text(encoding='utf-8')
        title_m = re.search(r'\*\*제목\*\*[^\n]*\n>\s*(.+)', content)
        sub_m   = re.search(r'\*\*서브카피\*\*[^\n]*\n>\s*(.+)', content)
        cta_m   = re.search(r'\*\*CTA 문구\*\*[^\n]*\n>\s*(.+)', content)
        lines = []
        if title_m: lines.append(title_m.group(1).strip())
        if sub_m:   lines.append(sub_m.group(1).strip())
        lines.append('')
        lines.append(cta_m.group(1).strip() if cta_m else '저장해두고 꺼내보세요')
        body = '\n'.join(lines)
    else:
        body = '새로운 인사이트를 공유합니다.'

    caption = f"{body}\n\n{hashtags_str}" if hashtags_str else body

    # Threads 500자 제한
    if len(caption) > 500:
        parts = caption.split('\n\n')
        body_part = parts[0]
        tags = parts[-1].split()[:25] if len(parts) > 1 else []
        caption = body_part + ('\n\n' + ' '.join(tags) if tags else '')
    return caption


# ─────────────────────────────────────────
# Threads API 업로드
# ─────────────────────────────────────────

def create_carousel_item(user_id: str, token: str, image_url: str) -> str:
    r = requests.post(f"{THREADS_API}/{user_id}/threads", params={
        "media_type": "IMAGE",
        "image_url": image_url,
        "is_carousel_item": "true",
        "access_token": token,
    })
    r.raise_for_status()
    return r.json()['id']


def create_carousel_container(user_id: str, token: str, children: list[str], caption: str) -> str:
    r = requests.post(f"{THREADS_API}/{user_id}/threads", params={
        "media_type": "CAROUSEL",
        "children": ",".join(children),
        "text": caption,
        "access_token": token,
    })
    if not r.ok:
        print(f"[threads] 캐러셀 컨테이너 오류 응답: {r.status_code}\n{r.text}")
    r.raise_for_status()
    return r.json()['id']


def create_single_image_container(user_id: str, token: str, image_url: str, caption: str) -> str:
    r = requests.post(f"{THREADS_API}/{user_id}/threads", params={
        "media_type": "IMAGE",
        "image_url": image_url,
        "text": caption,
        "access_token": token,
    })
    r.raise_for_status()
    return r.json()['id']


def publish_container(user_id: str, token: str, container_id: str) -> dict:
    r = requests.post(f"{THREADS_API}/{user_id}/threads_publish", params={
        "creation_id": container_id,
        "access_token": token,
    })
    r.raise_for_status()
    return r.json()


def get_post_url(user_id: str, token: str, media_id: str) -> str:
    r = requests.get(f"{THREADS_API}/{media_id}", params={
        "fields": "id,permalink",
        "access_token": token,
    })
    if r.ok:
        return r.json().get('permalink', f"https://www.threads.net/")
    return "https://www.threads.net/"


# ─────────────────────────────────────────
# 메인
# ─────────────────────────────────────────

def main():
    args = parse_args()

    if args.setup_guide:
        print(SETUP_GUIDE)
        return

    if not args.images_dir:
        print("❌ --images-dir 필요")
        sys.exit(1)

    # 자격증명
    creds = load_creds(args.creds_file)
    token = creds['access_token']
    user_id = get_user_id(token, creds.get('user_id', ''))

    # 이미지 준비
    try:
        from PIL import Image as _
    except ImportError:
        print("❌ pillow 미설치. pip install pillow")
        sys.exit(1)
    images = prepare_images(args.images_dir)

    # 캡션
    hashtags = load_hashtags(args.hashtags_file)
    caption = build_caption(args.caption_file, hashtags, args.caption)

    # 미리보기
    print(f"\n{'─'*50}")
    print("[ 스레드 업로드 미리보기 ]")
    print(f"{'─'*50}")
    print(f"이미지 수 : {len(images)}장 (Threads 캐러셀)")
    print(f"캡션({len(caption)}자):\n{caption[:300]}{'...' if len(caption) > 300 else ''}")
    print(f"{'─'*50}\n")

    if args.dry_run:
        print("--dry-run: 업로드 건너뜀")
        return

    if args.yes:
        confirm = 'y'
    else:
        confirm = input('스레드에 업로드할까요? (y/N): ').strip().lower()
    if confirm != 'y':
        print('취소됨.')
        return

    # ── 이미지 공개 URL 업로드 (imgur / litterbox) ──
    print("\n[threads] 이미지를 공개 URL에 업로드 중...")
    image_urls = []
    for i, jpg in enumerate(images, 1):
        print(f"  [{i}/{len(images)}] {jpg.name} 업로드 중...", end=' ', flush=True)
        url = upload_image_public(jpg)
        print(url)
        image_urls.append(url)
        time.sleep(0.5)  # 요청 간격

    # ── Threads 컨테이너 생성 ──
    print("\n[threads] Threads 컨테이너 생성 중...")

    if len(image_urls) == 1:
        container_id = create_single_image_container(user_id, token, image_urls[0], caption)
        print(f"  단일 이미지 컨테이너: {container_id}")
    else:
        # 캐러셀 아이템 생성
        children = []
        for i, url in enumerate(image_urls, 1):
            item_id = create_carousel_item(user_id, token, url)
            print(f"  캐러셀 아이템 [{i}/{len(image_urls)}]: {item_id}")
            children.append(item_id)
            time.sleep(0.3)

        container_id = create_carousel_container(user_id, token, children, caption)
        print(f"  캐러셀 컨테이너: {container_id}")

    # ── 게시 ──
    print("[threads] 게시 중...")
    result = publish_container(user_id, token, container_id)
    media_id = result.get('id', '')

    post_url = get_post_url(user_id, token, media_id) if media_id else f"https://www.threads.net/"

    print(f"\n✅ 스레드 업로드 완료!")
    print(f"  게시물 URL: {post_url}")


if __name__ == '__main__':
    main()
