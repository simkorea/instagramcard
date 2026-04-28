#!/usr/bin/env python3
"""
Gemini Imagen - 슬라이드 맞춤 이미지 생성
사용법: python .claude/scv/gemini-image-gen.py --slide 2 --prompt "..." --output output/assets/images/gemini-slide-2.png
"""
import argparse, os, sys, base64
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--slide', type=int, required=True, help='슬라이드 번호')
    parser.add_argument('--prompt', type=str, required=True, help='이미지 생성 프롬프트 (영문 권장)')
    parser.add_argument('--output', type=str, required=True, help='저장 경로')
    parser.add_argument('--aspect', type=str, default='4:5', help='비율 (기본: 4:5 = 1080x1350)')
    args = parser.parse_args()

    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        print('[gemini-image-gen] ❌ GEMINI_API_KEY 환경변수가 없습니다.')
        print('   set GEMINI_API_KEY=AIza...')
        sys.exit(1)

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print('[gemini-image-gen] ❌ 패키지 없음. 실행: pip install google-genai')
        sys.exit(1)

    print(f'[gemini-image-gen] 슬라이드 {args.slide} 이미지 생성 중...')
    print(f'[gemini-image-gen] 프롬프트: {args.prompt[:80]}...' if len(args.prompt) > 80 else f'[gemini-image-gen] 프롬프트: {args.prompt}')

    client = genai.Client(api_key=api_key)
    result = client.models.generate_images(
        model='imagen-4.0-generate-preview-05-20',
        prompt=args.prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio=args.aspect,
            safety_filter_level='BLOCK_ONLY_HIGH',
            person_generation='DONT_ALLOW',
        )
    )

    if not result.generated_images:
        print('[gemini-image-gen] ❌ 이미지 생성 실패')
        sys.exit(1)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img_bytes = result.generated_images[0].image.image_bytes
    out_path.write_bytes(img_bytes)
    print(f'[gemini-image-gen] ✅ 저장 완료: {out_path} ({len(img_bytes)//1024}KB)')

if __name__ == '__main__':
    main()
