#!/usr/bin/env node
/**
 * trend-collector.js
 *
 * SCV: 트렌드 데이터를 수집하여 /output/data/trend-data.json으로 저장합니다.
 *
 * 사용법:
 *   node .claude/scv/trend-collector.js --mode auto
 *   node .claude/scv/trend-collector.js --mode keyword --keyword "퇴사 후 프리랜서"
 *
 * 출력: output/data/trend-data.json
 *
 * 실제 운영 시 Puppeteer 기반 스크래핑으로 대체 가능합니다.
 * 현재는 타겟 독자(퇴사 희망자/예비 창업가) 관련 샘플 데이터를 반환합니다.
 */

const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join('output', 'data');
const OUTPUT_FILE = path.join(OUTPUT_DIR, 'trend-data.json');
const LOG_DIR = path.join('output', 'logs');

// CLI 인자 파싱
function parseArgs(argv) {
  const args = { mode: 'auto', keyword: null };
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === '--mode' && argv[i + 1]) {
      args.mode = argv[++i];
    } else if (argv[i] === '--keyword' && argv[i + 1]) {
      args.keyword = argv[++i];
    }
  }
  return args;
}

// 디렉토리 생성
function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

// 에러 로그
function logError(message) {
  ensureDir(LOG_DIR);
  const logFile = path.join(LOG_DIR, 'error.log');
  const entry = `${new Date().toISOString()} [trend-collector] ${message}\n`;
  fs.appendFileSync(logFile, entry, 'utf8');
}

// 타겟 독자 관련 기본 트렌드 데이터
function getBaseTrends() {
  return {
    instagram: [
      { title: '퇴사 준비 체크리스트 5가지', source: 'instagram', url: null, summary: '퇴사 전 반드시 확인해야 할 실무 준비 항목' },
      { title: '프리랜서 첫 프로젝트 수주 방법', source: 'instagram', url: null, summary: '포트폴리오 없이도 첫 클라이언트를 만드는 전략' },
      { title: '1인 비즈니스 첫 달 생존기', source: 'instagram', url: null, summary: '독립 초기 현실적인 수익 구조 만들기' },
      { title: '직장 다니며 부업 월 50만원', source: 'instagram', url: null, summary: '퇴사 전 수익 파이프라인 테스트 방법' },
      { title: '창업 아이디어 24시간 검증법', source: 'instagram', url: null, summary: '실제 고객 반응을 빠르게 확인하는 린 방법' },
      { title: '퇴사 후 첫 수익까지 걸린 시간', source: 'instagram', url: null, summary: '실제 프리랜서들의 첫 수익 타임라인 공개' },
      { title: '프리랜서 단가 설정 가이드', source: 'instagram', url: null, summary: '경력별 적정 단가 책정 기준과 협상 전략' },
      { title: '1인 사업자 세금 기초 정리', source: 'instagram', url: null, summary: '사업소득 신고 전 알아야 할 세무 기본 지식' },
      { title: '재직 중 네트워크 활용하기', source: 'instagram', url: null, summary: '현직 경험을 첫 고객과 연결하는 방법' },
      { title: '디지털 노마드 현실 vs 환상', source: 'instagram', url: null, summary: '자유로운 일하기 방식의 실제 장단점 정리' },
      { title: '온라인 클래스로 수익화하기', source: 'instagram', url: null, summary: '전문 지식을 강의로 전환하는 입문 가이드' },
      { title: 'SNS 브랜딩으로 고객 유치하기', source: 'instagram', url: null, summary: '퍼스널 브랜드를 비즈니스로 연결하는 전략' },
    ],
    youtube: [
      { title: '월급쟁이 퇴사 준비 6개월 타임라인', source: 'youtube', url: null, summary: '퇴사 결심부터 독립까지 단계별 준비 과정' },
      { title: '프리랜서 첫 3개월 수익 공개', source: 'youtube', url: null, summary: '시작 단계의 현실적인 수익 데이터와 교훈' },
      { title: '1인 비즈니스 vs 취업 장단점 비교', source: 'youtube', url: null, summary: '두 가지 선택지의 현실적 비교 분석' },
      { title: '대기업 퇴사 후 6개월 솔직 후기', source: 'youtube', url: null, summary: '안정적인 직장을 그만둔 실제 경험담' },
      { title: '창업 실패 후 다시 시작하는 법', source: 'youtube', url: null, summary: '첫 도전 실패에서 얻은 교훈과 재기 전략' },
      { title: '부업으로 월 300만원 버는 현실', source: 'youtube', url: null, summary: '사이드 인컴 실현까지의 구체적인 과정' },
      { title: '재취업 vs 창업 선택 기준', source: 'youtube', url: null, summary: '퇴사 후 방향 설정을 위한 판단 프레임' },
      { title: '프리랜서 시간 관리 루틴 공개', source: 'youtube', url: null, summary: '자율 근무 환경에서 생산성 유지하는 법' },
      { title: '1인 사업자 세금 신고 완전 정복', source: 'youtube', url: null, summary: '종합소득세 신고 실전 가이드' },
      { title: '퇴직금 실업급여 최대한 활용하기', source: 'youtube', url: null, summary: '퇴사 후 받을 수 있는 지원금 완벽 정리' },
      { title: 'SNS 콘텐츠로 수익화 로드맵', source: 'youtube', url: null, summary: '콘텐츠 크리에이터로의 전환 단계별 전략' },
      { title: '온라인 강의 제작부터 판매까지', source: 'youtube', url: null, summary: '지식 상품화의 처음부터 끝까지 실전 가이드' },
    ],
    naver: [
      { title: '퇴사 후 해야 할 일 순서 정리', source: 'naver', url: null, summary: '퇴사 직후 행정/실무 처리 우선순위' },
      { title: '프리랜서 계약서 필수 항목', source: 'naver', url: null, summary: '분쟁 예방을 위한 계약서 체크리스트' },
      { title: '1인 사업자 종합소득세 신고 방법', source: 'naver', url: null, summary: '세무사 없이 직접 신고하는 실전 가이드' },
      { title: '퇴사 후 건강보험 지역가입자 전환', source: 'naver', url: null, summary: '독립 후 4대 보험 처리 완전 정리' },
      { title: '실업급여 수급 조건과 신청 방법', source: 'naver', url: null, summary: '자발적 퇴사도 받을 수 있는 경우의 수' },
      { title: '프리랜서 포트폴리오 없이 시작하기', source: 'naver', url: null, summary: '경력을 증거로 활용하는 포트폴리오 대안' },
      { title: '사업자등록 개인사업자 vs 법인', source: 'naver', url: null, summary: '1인 창업자를 위한 사업자 유형 선택 가이드' },
      { title: '재취업 지원금 활용 방법', source: 'naver', url: null, summary: '정부 창업 지원 프로그램 총정리' },
      { title: '온라인 플랫폼별 프리랜서 단가 현황', source: 'naver', url: null, summary: '업종별 프리랜서 시장 단가 조사 결과' },
      { title: '퇴사 전 인맥 관리하는 방법', source: 'naver', url: null, summary: '커리어 자본을 유지하는 관계 관리 전략' },
      { title: '1인 기업 브랜딩 시작하기', source: 'naver', url: null, summary: '개인 브랜드 구축을 위한 온라인 presence 전략' },
      { title: '부업 세금 신고 꼭 해야 하나', source: 'naver', url: null, summary: '부업 수입 세금 신고 기준과 절세 방법' },
    ],
  };
}

// 키워드를 반영한 트렌드 생성
function buildTrendData(mode, keyword) {
  const base = getBaseTrends();
  const collected_at = new Date().toISOString();

  // 자동 모드: 상위 주제 추천 3개 생성
  const topicCandidates = mode === 'auto' ? [
    {
      rank: 1,
      title: '퇴사 후 보험·세금 한 번에 해결하는 법',
      reason: '퇴사 직후 가장 많이 검색되는 행정 문제. 건강보험 지역가입자 전환·실업급여·세금 처리 등 실제로 막히는 지점을 단계별로 해결해주는 콘텐츠 저장율 최상위',
    },
    {
      rank: 2,
      title: '포트폴리오 없이 첫 클라이언트 잡는 실전 스크립트',
      reason: '초보 프리랜서의 가장 큰 벽인 "경력 없음" 문제를 직접 해결. 실제 DM·제안서 문구까지 제공하는 초실용 포맷이 저장·공유율 압도적',
    },
    {
      rank: 3,
      title: '퇴사 전 6개월, 지금 당장 해야 할 돈 준비',
      reason: '막연한 퇴사 계획을 구체적 재무 액션으로 전환. 비상금 계산법·수익 파이프라인 테스트·지출 구조 조정 등 수치 기반 실행 가이드 수요 급증',
    },
  ] : null;

  // 키워드 모드: 키워드로 채널 데이터 필터링/태깅
  const channels = {};
  for (const [channel, items] of Object.entries(base)) {
    if (keyword) {
      channels[channel] = items.map(item => ({
        ...item,
        title: `[${keyword}] ${item.title}`,
      }));
    } else {
      channels[channel] = items;
    }
  }

  return {
    mode,
    keyword: keyword || null,
    collected_at,
    topicCandidates,
    selectedTopic: null, // 자동 모드 시 사용자 선택 후 채워짐
    channels,
  };
}

// 유효성 검증
function validate(data) {
  const errors = [];
  const channels = ['instagram', 'youtube', 'naver'];
  for (const ch of channels) {
    const count = data.channels[ch]?.length ?? 0;
    if (count < 3) {
      errors.push(`${ch} 트렌드 부족: ${count}개 (최소 3개 필요)`);
    }
  }
  if (data.mode === 'auto' && (!data.topicCandidates || data.topicCandidates.length < 3)) {
    errors.push('자동 모드: 추천 주제 3개 생성 실패');
  }
  return errors;
}

// 메인
async function main() {
  const { mode, keyword } = parseArgs(process.argv);

  console.log(`[trend-collector] 시작 — 모드: ${mode}${keyword ? ` / 키워드: "${keyword}"` : ''}`);

  ensureDir(OUTPUT_DIR);
  ensureDir(LOG_DIR);

  // 트렌드 수집 (현재: 샘플 데이터, 실제 운영 시 Puppeteer 스크래핑으로 교체)
  const data = buildTrendData(mode, keyword);

  // 유효성 검증
  const errors = validate(data);
  if (errors.length > 0) {
    const msg = `유효성 검증 실패:\n${errors.join('\n')}`;
    console.error(`[trend-collector] ❌ ${msg}`);
    logError(msg);
    process.exit(1);
  }

  // 저장
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(data, null, 2), 'utf8');

  // 요약 출력
  const counts = Object.entries(data.channels).map(([ch, items]) => `${ch}: ${items.length}개`).join(' / ');
  console.log(`[trend-collector] ✅ 저장 완료: ${OUTPUT_FILE}`);
  console.log(`[trend-collector] 수집량 — ${counts}`);

  if (mode === 'auto' && data.topicCandidates) {
    console.log('\n[trend-collector] 추천 주제 3개:');
    data.topicCandidates.forEach(t => {
      console.log(`  ${t.rank}. ${t.title}`);
      console.log(`     이유: ${t.reason}`);
    });
    console.log('\n리서처가 CEO에게 위 주제를 보고하고 사용자 선택을 기다립니다.');
  }
}

main().catch(err => {
  console.error(`[trend-collector] ❌ 오류: ${err.message}`);
  logError(err.message);
  process.exit(1);
});
