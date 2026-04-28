# @aptshowhome 카드뉴스 자동화 — 프로젝트 요약본

> 새 대화창에서 이 문서를 붙여넣으면 Claude가 즉시 상황을 파악하고 작업을 이어갑니다.

---

## 1. 개발 환경

| 항목 | 값 |
|------|-----|
| OS | Windows 11 Home |
| Python | 3.10.11 |
| 작업 디렉토리 | `c:\다운로드\ai등 공부 자료 및 잡동\instagramcard` |
| Shell | bash (VSCode 터미널) |

### 주요 패키지
| 패키지 | 버전 |
|--------|------|
| instagrapi | 2.3.0 |
| requests | 2.32.5 |
| python-dotenv | 1.2.2 |
| google-api-python-client | 2.194.0 |

---

## 2. 프로젝트 개요

- **채널**: @aptshowhome (인스타그램 + 스레드 + 유튜브 쇼츠 + 틱톡)
- **콘텐츠**: 20~50대 대상 부동산 청약 카드뉴스 (PNG 6~8장) + 릴스 영상
- **이미지 생성**: Leonardo AI — Lucid Realism 모델 (`05ce0082-2d80-4a2d-8653-4d1c85e2418e`)
  - 카드뉴스 배경: 768×960px (4:5)
  - 영상 전용 배경: 720×1280px (9:16)

---

## 3. 주요 파일 구조

```
instagramcard/
├── .env                          # API 키 모음 (Leonardo, TikTok)
├── .instagram_credentials.json  # 인스타 계정 (username/password)
├── .instagram_session.json      # 인스타 세션 캐시
├── .threads_credentials.json    # Threads access_token + user_id
├── .youtube_token.json          # 유튜브 OAuth 토큰 (자동 갱신)
├── .tiktok_token.json           # 틱톡 OAuth 토큰 (만료: 2026-04-29 10:35)
├── .tiktok_pkce.json            # 인증 중 임시 PKCE 데이터 (교환 후 자동 삭제)
├── client_secrets.json          # 유튜브 OAuth 클라이언트 시크릿
├── .claude/scv/
│   ├── leonardo-image-gen.py    # Leonardo AI 이미지 생성
│   ├── instagram-uploader.py    # 인스타그램 카드뉴스 업로드
│   ├── threads-uploader.py      # 스레드 카드뉴스 업로드
│   ├── reels-uploader.py        # 인스타 + 스레드 릴스 업로드
│   ├── youtube-uploader.py      # 유튜브 쇼츠 업로드
│   ├── tiktok-uploader.py       # 틱톡 업로드 (2단계 인증)
│   ├── total_sns_uploader.py    # 4개 플랫폼 일괄 업로드
│   ├── video_maker.py           # TTS + BGM + 영상 합성
│   └── html-renderer.js         # HTML → PNG 변환
├── output/
│   ├── drafts/slides/           # HTML 슬라이드 (slide-1.html ~ slide-N.html)
│   ├── drafts/narration.txt     # 릴스 나레이션 스크립트
│   ├── drafts/hashtags.md       # 해시태그 목록
│   ├── assets/images/           # Leonardo 카드뉴스 배경 (leonardo-slide-N.png)
│   ├── assets/video-bg/         # Leonardo 영상 전용 배경 (video-N.png)
│   ├── final/YYYYMMDD_주제명/   # 완성 PNG (slide-1.png ~ slide-N.png)
│   └── video/                   # 완성 MP4 영상
└── .vscode/settings.json        # python.terminal.useEnvFile: true
```

---

## 4. .env 구성

```
LEONARDO_API_KEY=38a16281-f428-46ae-9a93-3e411a28ecbb
TIKTOK_CLIENT_KEY=sbawgp0r0pefq26hiy
TIKTOK_CLIENT_SECRET=jjUVdzuuxFhf7jaTFDuAvS0Z3wDxHF2d
```

---

## 5. TikTok 인증 설정 (핵심)

| 항목 | 값 |
|------|-----|
| Redirect URI | `https://b9a3c932a64086.lhr.life/callback` |
| Scope | `user.info.basic,video.upload,video.publish` |
| PKCE | S256 방식 (code_verifier → SHA256 → base64url) |
| 인증 방식 | 2단계 분리 (--get-url → 브라우저 → --exchange-code) |
| 토큰 파일 | `.tiktok_token.json` |
| 현재 토큰 만료 | 2026-04-29 10:35 (만료 시 재인증 필요) |
| 앱 상태 | 샌드박스 (미심사) — 비공개 계정에만 게시 가능 |
| 업로드 성공 상태 | `PUBLISH_COMPLETE` |

### TikTok 재인증 절차 (토큰 만료 시)
```bash
# 1단계: URL 생성 (code_verifier 파일 저장됨)
python .claude/scv/tiktok-uploader.py --get-url

# 브라우저에서 로그인 → 권한 허용 → 주소창 URL 복사

# 2단계: 토큰 교환
python .claude/scv/tiktok-uploader.py --exchange-code "https://b9a3c932a64086.lhr.life/callback?code=..."
```

> **주의**: Redirect URI `https://b9a3c932a64086.lhr.life/callback`는 lhr.life 임시 도메인입니다.
> 만료 시 새 주소로 바꾸고 TikTok Developer Portal에도 동일하게 등록해야 합니다.

---

## 6. 완성된 업로드 기능

### 플랫폼별 업로더

| 스크립트 | 플랫폼 | 방식 | 상태 |
|---------|--------|------|------|
| `instagram-uploader.py` | 인스타그램 | 카드뉴스 (이미지) | ✅ 완료 |
| `threads-uploader.py` | 스레드 | 카드뉴스 (이미지) | ✅ 완료 |
| `reels-uploader.py` | 인스타 + 스레드 | 릴스 영상 | ✅ 완료 |
| `youtube-uploader.py` | 유튜브 쇼츠 | OAuth2 + 재개 업로드 | ✅ 완료 |
| `tiktok-uploader.py` | 틱톡 | PKCE OAuth2 + FILE_UPLOAD | ✅ 완료 |
| `total_sns_uploader.py` | 4개 플랫폼 동시 | 순차 실행 | ✅ 완료 |

### total_sns_uploader.py 사용법
```bash
# 4개 플랫폼 전체 업로드
python .claude/scv/total_sns_uploader.py --video output/video/영상.mp4 --yes

# 특정 플랫폼만
python .claude/scv/total_sns_uploader.py --video output/video/영상.mp4 --skip threads youtube

# 틱톡 실제 공개 (앱 심사 후)
python .claude/scv/total_sns_uploader.py --video output/video/영상.mp4 --tiktok-privacy PUBLIC_TO_EVERYONE
```

---

## 7. 카드뉴스 제작 파이프라인

```
1. 트렌드 수집    → node .claude/scv/trend-collector.js
2. 리서치         → node .claude/scv/research-crawler.js
3. 기획/스크립트  → Claude (CEO 에이전트)
4. 이미지 생성    → python .claude/scv/leonardo-image-gen.py  (Lucid Realism)
5. HTML 슬라이드  → output/drafts/slides/slide-1.html ~ slide-N.html
6. PNG 변환       → node .claude/scv/html-renderer.js
7. 카드뉴스 업로드 → python .claude/scv/instagram-uploader.py + threads-uploader.py
8. 릴스 영상 생성 → python .claude/scv/video_maker.py --tts --narration ...
9. 전체 SNS 업로드 → python .claude/scv/total_sns_uploader.py
```

---

## 8. 슬라이드 디자인 규칙

- **테마**: Photo Hero Dark (전면 배경 + 다크 그라데이션 오버레이)
- **글라스모피즘 카드**: `background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); backdrop-filter: blur(16px)`
- **배경 이미지**: Leonardo AI 전용 생성 (Unsplash 사용 금지)
- **파일 네이밍**: `slide-1.html` (하이픈 + 한 자리 숫자, `slide-01` 형식 금지)

---

## 9. Threads API 주의사항

- **토큰 만료**: 60일 (다음 만료일 확인 필요)
- **user_id**: `35068100699471114`
- **영상 호스팅**: catbox.moe 우선 → imgur 폴백 (imgur는 400 오류 발생)
- **자격증명**: `.threads_credentials.json`

---

## 10. 다음 작업 후보

- [ ] TikTok 앱 심사(App Review) 신청 → 공개 계정 업로드 허용
- [ ] `total_sns_uploader.py` 실전 테스트 (4개 플랫폼 동시)
- [ ] Threads 토큰 만료일 확인 및 갱신
- [ ] lhr.life Redirect URI 영구 도메인으로 교체 검토
