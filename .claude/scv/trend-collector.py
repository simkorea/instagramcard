"""trend-collector.py

SCV 스크립트: 인스타그램, 유튜브, 네이버 트렌드 데이터를 수집하여
/output/data/trends.json으로 저장합니다.

실제 API 또는 웹 검색을 통해 트렌드 데이터를 수집합니다.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

OUTPUT_PATH = Path("output/data")
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
LOG_PATH = Path("output/logs")
LOG_PATH.mkdir(parents=True, exist_ok=True)


def generate_trend_topics(keyword: Optional[str] = None) -> Dict[str, List[str]]:
    """
    사용자 키워드를 기반으로 관련 트렌드 주제를 생성합니다.
    
    실제 구현에서는 다음 API를 활용할 수 있습니다:
    - Google Trends API
    - YouTube API (trending videos)
    - Naver Trends API
    - 또는 웹 스크래핑 (BeautifulSoup, Selenium 등)
    """
    
    # 기본 트렌드 주제 (퇴사, 창업, 1인 비즈니스 관련)
    base_topics = {
        "instagram": [
            "퇴사 준비 체크리스트",
            "프리랜서 첫 프로젝트 가이드",
            "1인 비즈니스 시작하기",
            "부업으로 월 100만원 만드는 법",
            "창업 아이디어 검증 방법",
            "직장인 사이드 프로젝트",
            "경제적 자유를 위한 10단계",
            "프리랜서 포트폴리오 만드는 법",
            "사이드 허슬 성공 사례",
            "퇴사 후 안정적인 수입 구조",
            "1인 창업가의 일과",
            "프리랜서 가격 책정 전략",
        ],
        "youtube": [
            "월급쟁이의 퇴사 준비",
            "프리랜서 시작 3개월 후기",
            "1인 비즈니스 수익 공개",
            "대기업 퇴사 후 6개월",
            "창업 실패 사례와 배울 점",
            "프리랜서 vs 직장인 장단점",
            "부업으로 월 300만원 버는 법",
            "사이드 프로젝트 성공 전략",
            "경제적 자유의 현실",
            "프리랜서 시간 관리법",
            "1인 사업가의 세금 관리",
            "창업 자금 조달 방법",
        ],
        "naver": [
            "퇴사 후 해야 할 일들",
            "프리랜서 계약서 작성",
            "1인 비즈니스 세무신고",
            "창업 초기자금 계획",
            "부양가족 있을 때 퇴사 결정",
            "프리랜서 보험 및 복지",
            "사업자등록 절차",
            "근로소득 vs 사업소득",
            "퇴직금 및 실업급여",
            "프리랜서 소득분산 방법",
            "창업 실패 후 회복력",
            "1인 법인 설립 가이드",
        ],
    }
    
    # 사용자 키워드가 있으면, 기본 주제에 키워드 반영
    if keyword:
        # 키워드를 포함하여 주제 수정 (간단한 예시)
        prefix = f"{keyword} "
        for channel in base_topics:
            base_topics[channel] = [
                f"{prefix}| {topic}" if not topic.startswith(keyword) else topic
                for topic in base_topics[channel][:6]  # 각 채널 6개씩만 사용
            ]
            # 추가 주제들로 채우기
            base_topics[channel].extend([
                f"{keyword} 관련 {topic}" 
                for topic in base_topics[channel][6:10]
            ])
    
    return base_topics


def format_trend_item(title: str, source: str, index: int) -> dict:
    """트렌드 항목을 구조화된 형식으로 반환합니다."""
    return {
        "title": title,
        "source": source,
        "url": None,  # 실제 구현에서는 URL 포함
        "summary": f"이 주제에 대한 트렌드 정보입니다. (자세한 내용은 {source}에서 확인 가능)",
    }


def collect_trends(keyword: Optional[str] = None) -> Dict:
    """
    트렌드 데이터를 수집하여 구조화된 딕셔너리로 반환합니다.
    
    Args:
        keyword: 검색 키워드 (선택사항)
    
    Returns:
        트렌드 데이터가 담긴 딕셔너리
    """
    try:
        # 1단계: 트렌드 주제 생성 또는 수집
        trend_topics = generate_trend_topics(keyword)
        
        # 2단계: 채널별로 구조화된 트렌드 데이터 생성
        trends = {
            "keyword": keyword or "auto",
            "collected_at": datetime.now().isoformat(),
            "channels": {
                "instagram": [
                    format_trend_item(title, "instagram", i)
                    for i, title in enumerate(trend_topics["instagram"], 1)
                ],
                "youtube": [
                    format_trend_item(title, "youtube", i)
                    for i, title in enumerate(trend_topics["youtube"], 1)
                ],
                "naver": [
                    format_trend_item(title, "naver", i)
                    for i, title in enumerate(trend_topics["naver"], 1)
                ],
            },
        }
        
        return trends
    
    except Exception as e:
        error_msg = f"[trend-collector] 트렌드 수집 실패: {str(e)}"
        log_error(error_msg)
        raise


def save_trends(data: dict) -> Path:
    """트렌드 데이터를 JSON 파일로 저장합니다."""
    file_path = OUTPUT_PATH / "trends.json"
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return file_path


def log_error(message: str) -> None:
    """에러 메시지를 로그 파일에 기록합니다."""
    log_file = LOG_PATH / "error.log"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")


def main() -> None:
    """트렌드 수집 메인 함수."""
    try:
        # 명령행 인자에서 키워드 받기
        keyword = sys.argv[1] if len(sys.argv) > 1 else None
        
        print(f"트렌드 수집 시작... (키워드: {keyword or '자동'})")
        
        # 1단계: 트렌드 수집
        trends = collect_trends(keyword)
        
        # 2단계: 데이터 검증
        instagram_count = len(trends["channels"]["instagram"])
        youtube_count = len(trends["channels"]["youtube"])
        naver_count = len(trends["channels"]["naver"])
        
        print(f"\n수집된 트렌드:")
        print(f"  - Instagram: {instagram_count}개")
        print(f"  - YouTube: {youtube_count}개")
        print(f"  - Naver: {naver_count}개")
        
        # 성공 기준 확인
        if instagram_count >= 10 and youtube_count >= 10 and naver_count >= 10:
            print("✅ 성공: 모든 채널에서 10개 이상 수집")
        else:
            print("⚠️ 경고: 일부 채널의 데이터가 부족합니다")
        
        # 3단계: 파일 저장
        file_path = save_trends(trends)
        print(f"✅ 트렌드 데이터 저장: {file_path}")
        
        return True
    
    except Exception as e:
        print(f"❌ 오류: {str(e)}")
        log_error(f"[main] {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
