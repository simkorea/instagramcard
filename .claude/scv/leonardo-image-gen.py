import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("LEONARDO_API_KEY")

# 카드뉴스 배경 이미지 공통 부정 프롬프트
# - 텍스트/글자 혼입 방지, 구도 왜곡 방지, 인물 노출 방지
DEFAULT_NEGATIVE_PROMPT = (
    "text, letters, words, numbers, watermark, signature, logo, caption, label, "
    "distortion, fisheye, lens distortion, warped, skewed, perspective distortion, "
    "blurry, out of focus, low quality, pixelated, jpeg artifacts, noise, grain, "
    "people, faces, humans, person, crowd, "
    "cartoon, illustration, painting, drawing, anime, 3d render, cgi, "
    "overexposed, underexposed, bad composition, cropped"
)

def generate_leonardo_image(prompt, page_num, negative_prompt=None):
    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {API_KEY}"
    }

    # 레오나르도 설정 (부동산/카드뉴스 배경 최적화)
    # 모델: Lucid Realism (05ce0082) — 실사 특화 최신 모델
    # 크기: 768x960 (4:5 비율, 카드뉴스 1080x1350과 동일 비율) — 최대 지원 크기
    payload = {
        "height": 960,
        "width": 768,
        "modelId": "05ce0082-2d80-4a2d-8653-4d1c85e2418e",  # Lucid Realism
        "prompt": prompt,
        "negative_prompt": negative_prompt or DEFAULT_NEGATIVE_PROMPT,
        "num_images": 1
    }

    # 1. 생성 요청
    response = requests.post(url, json=payload, headers=headers)
    generation_id = response.json()['sdGenerationJob']['generationId']
    print(f"🎨 {page_num}번 이미지 생성 시작 (ID: {generation_id})")

    # 2. 생성 대기 (약 15~20초 소요)
    while True:
        time.sleep(5)
        check_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
        res = requests.get(check_url, headers=headers)
        data = res.json()['generations_by_pk']

        if data['status'] == 'COMPLETE':
            image_url = data['generated_images'][0]['url']
            break
        print("...아직 그리는 중입니다...")

    # 3. 이미지 저장
    img_data = requests.get(image_url).content
    filename = f"output/assets/images/leonardo-slide-{page_num}.png"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'wb') as f:
        f.write(img_data)

    return filename
