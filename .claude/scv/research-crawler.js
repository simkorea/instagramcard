#!/usr/bin/env node
/**
 * research-crawler.js
 *
 * SCV: Claude API + 웹 검색으로 주제 관련 실제 데이터/인사이트를 수집합니다.
 * ANTHROPIC_API_KEY 환경변수 필요.
 *
 * 사용법:
 *   node .claude/scv/research-crawler.js --keyword "2026 아파트 시장" --output output/data/research.md
 */

const fs   = require('fs');
const path = require('path');

const LOG_DIR = path.join('output', 'logs');

function parseArgs(argv) {
  const args = { keyword: null, output: path.join('output', 'data', 'research.md') };
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === '--keyword' && argv[i + 1]) args.keyword = argv[++i];
    else if (argv[i] === '--output' && argv[i + 1]) args.output = argv[++i];
  }
  return args;
}

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function logError(msg) {
  ensureDir(LOG_DIR);
  fs.appendFileSync(path.join(LOG_DIR, 'error.log'),
    `${new Date().toISOString()} [research-crawler] ${msg}\n`, 'utf8');
}

// ─── Claude API 웹 검색 ───────────────────────────────────────────────────
async function researchWithClaude(keyword) {
  const Anthropic = require('@anthropic-ai/sdk');
  const client = new Anthropic.default();

  console.log(`[research-crawler] Claude API 웹 검색 시작: "${keyword}"`);

  const response = await client.messages.create({
    model: 'claude-opus-4-5',
    max_tokens: 4000,
    tools: [{ type: 'web_search_20250305', name: 'web_search' }],
    messages: [{
      role: 'user',
      content: `다음 주제에 대해 최신 실제 데이터와 인사이트를 한국어로 조사해주세요: "${keyword}"

아래 형식으로 6개 항목을 작성해주세요. 반드시 실제 수치/통계/사례를 포함하세요.

---ITEM---
TYPE: stat|case|insight|trend|failure|opportunity
TITLE: 제목 (30자 이내)
CONTENT: 구체적 내용 (수치, 날짜, 출처 포함, 150자 이내)
SOURCE: 출처명
---END---

각 항목 사이에 ---ITEM--- 구분자를 사용하세요.`
    }],
  });

  // 최종 텍스트 응답 추출
  let text = '';
  for (const block of response.content) {
    if (block.type === 'text') text += block.text;
  }

  if (!text.includes('---ITEM---')) {
    throw new Error('Claude 응답 파싱 실패: ---ITEM--- 구분자 없음');
  }

  // 파싱
  const items = [];
  const chunks = text.split('---ITEM---').slice(1);
  for (const chunk of chunks) {
    const end = chunk.indexOf('---END---');
    const body = end !== -1 ? chunk.slice(0, end) : chunk;
    const item = {};
    for (const line of body.split('\n')) {
      const colon = line.indexOf(':');
      if (colon === -1) continue;
      const key   = line.slice(0, colon).trim().toLowerCase();
      const value = line.slice(colon + 1).trim();
      if (key === 'type')    item.type    = value;
      if (key === 'title')   item.title   = value;
      if (key === 'content') item.content = value;
      if (key === 'source')  item.source  = value;
    }
    if (item.title && item.content) items.push(item);
  }

  console.log(`[research-crawler] Claude 웹 검색 완료 — ${items.length}건 수집`);
  return items;
}

// ─── Markdown 포맷 ────────────────────────────────────────────────────────
function formatAsMarkdown(keyword, items) {
  const now = new Date().toISOString();
  const typeLabel = {
    stat: '📊 데이터/통계', case: '💼 사례', insight: '💡 인사이트',
    trend: '📈 트렌드', failure: '⚠️ 주의 포인트', opportunity: '🎯 기회',
  };

  let md = `# 리서치 자료\n\n- **주제**: ${keyword}\n- **수집 일시**: ${now}\n- **항목 수**: ${items.length}건\n\n---\n\n`;
  items.forEach((item, i) => {
    const label = typeLabel[item.type] || '📝 자료';
    md += `## ${i + 1}. ${label}: ${item.title}\n\n${item.content}\n\n`;
    if (item.source) md += `> 출처: ${item.source}\n\n`;
    md += `---\n\n`;
  });
  return md;
}

// ─── 메인 ────────────────────────────────────────────────────────────────
async function main() {
  const { keyword, output } = parseArgs(process.argv);

  if (!keyword) {
    console.error('[research-crawler] ❌ --keyword 인자 필요');
    process.exit(1);
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    console.error('[research-crawler] ❌ ANTHROPIC_API_KEY 환경변수 없음');
    console.error('   set ANTHROPIC_API_KEY=sk-ant-...');
    process.exit(1);
  }

  ensureDir(path.dirname(output));
  ensureDir(LOG_DIR);

  let items;
  try {
    items = await researchWithClaude(keyword);
  } catch (err) {
    const msg = `Claude API 오류: ${err.message}`;
    console.error(`[research-crawler] ❌ ${msg}`);
    logError(msg);
    process.exit(1);
  }

  if (!items || items.length < 3) {
    const msg = `리서치 자료 부족: ${items?.length ?? 0}건 (최소 3건 필요)`;
    console.error(`[research-crawler] ❌ ${msg}`);
    logError(msg);
    process.exit(1);
  }

  const md = formatAsMarkdown(keyword, items);
  fs.writeFileSync(output, md, 'utf8');

  console.log(`[research-crawler] ✅ 저장 완료: ${output}`);
  items.forEach((item, i) => console.log(`  ${i + 1}. [${item.type}] ${item.title}`));
}

main().catch(err => {
  console.error(`[research-crawler] ❌ 오류: ${err.message}`);
  logError(err.message);
  process.exit(1);
});
