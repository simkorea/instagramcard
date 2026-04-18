#!/usr/bin/env node
/**
 * html-renderer.js
 *
 * SCV: HTML 슬라이드 파일들을 1080×1350px PNG 이미지로 변환합니다.
 * Puppeteer를 사용하여 실제 브라우저 렌더링 결과를 스크린샷합니다.
 *
 * 사용법:
 *   # 날짜+주제 폴더 자동 생성 (권장)
 *   node .claude/scv/html-renderer.js --input output/drafts/slides/ --topic "직장인부업_시간관리법"
 *   → output/final/20260411_직장인부업_시간관리법/
 *
 *   # 출력 경로 직접 지정
 *   node .claude/scv/html-renderer.js --input output/drafts/slides/ --output output/final/images/
 *
 * 요구사항:
 *   npm install puppeteer
 *
 * 출력: output/final/YYYYMMDD_주제명/slide-01.png ~ slide-N.png
 */

const fs = require('fs');
const path = require('path');

const LOG_DIR = path.join('output', 'logs');
const SLIDE_WIDTH = 1080;
const SLIDE_HEIGHT = 1350;

function getDatePrefix() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}${mm}${dd}`;
}

function parseArgs(argv) {
  const args = {
    input: path.join('output', 'drafts', 'slides'),
    output: null,
    topic: null,
  };
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === '--input' && argv[i + 1]) {
      args.input = argv[++i];
    } else if (argv[i] === '--output' && argv[i + 1]) {
      args.output = argv[++i];
    } else if (argv[i] === '--topic' && argv[i + 1]) {
      args.topic = argv[++i];
    }
  }
  // --topic 있으면 날짜+주제 폴더 자동 생성
  if (!args.output) {
    const slug = args.topic
      ? args.topic.replace(/\s+/g, '_').replace(/[^\w가-힣_-]/g, '')
      : 'images';
    args.output = path.join('output', 'final', `${getDatePrefix()}_${slug}`);
  }
  return args;
}

function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function logError(message) {
  ensureDir(LOG_DIR);
  const logFile = path.join(LOG_DIR, 'error.log');
  fs.appendFileSync(logFile, `${new Date().toISOString()} [html-renderer] ${message}\n`, 'utf8');
}

// HTML 파일 목록 조회 (숫자 순 정렬)
function getHtmlFiles(inputDir) {
  if (!fs.existsSync(inputDir)) {
    throw new Error(`입력 디렉토리 없음: ${inputDir}`);
  }
  const files = fs.readdirSync(inputDir)
    .filter(f => f.endsWith('.html'))
    .sort((a, b) => {
      const numA = parseInt(a.match(/\d+/)?.[0] ?? '0', 10);
      const numB = parseInt(b.match(/\d+/)?.[0] ?? '0', 10);
      return numA - numB;
    });
  if (files.length === 0) {
    throw new Error(`HTML 파일 없음: ${inputDir}`);
  }
  return files;
}

// Puppeteer로 HTML → PNG 변환
async function renderWithPuppeteer(inputDir, outputDir, htmlFiles) {
  let puppeteer;
  try {
    puppeteer = require('puppeteer');
  } catch {
    throw new Error(
      'puppeteer 패키지가 설치되지 않았습니다.\n' +
      '실행: npm install puppeteer\n' +
      '또는: npm install puppeteer-core'
    );
  }

  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--font-render-hinting=none',
    ],
  });

  const results = [];

  try {
    for (const htmlFile of htmlFiles) {
      const htmlPath = path.resolve(inputDir, htmlFile);
      const pngName = htmlFile.replace('.html', '.png');
      const pngPath = path.join(outputDir, pngName);

      const page = await browser.newPage();
      await page.setViewport({
        width: SLIDE_WIDTH,
        height: SLIDE_HEIGHT,
        deviceScaleFactor: 1,
      });

      // 로컬 HTML 파일 로드
      await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0', timeout: 15000 });

      // 폰트 로딩 대기 (Google Fonts 등)
      await page.evaluateHandle('document.fonts.ready');

      // 스크린샷
      await page.screenshot({
        path: pngPath,
        clip: { x: 0, y: 0, width: SLIDE_WIDTH, height: SLIDE_HEIGHT },
      });

      await page.close();

      // 크기 검증
      const stat = fs.statSync(pngPath);
      results.push({
        file: pngName,
        path: pngPath,
        size: stat.size,
        ok: stat.size > 1000,
      });

      console.log(`[html-renderer] ✅ ${pngName} (${(stat.size / 1024).toFixed(1)}KB)`);
    }
  } finally {
    await browser.close();
  }

  return results;
}

// 폴백: puppeteer 없을 때 흰 PNG 생성
function createFallbackPng(outputPath) {
  const width = SLIDE_WIDTH;
  const height = SLIDE_HEIGHT;

  const zlib = require('zlib');

  const row = Buffer.alloc(1 + width * 3);
  row[0] = 0; // filter type
  row.fill(255, 1); // white pixels

  const raw = Buffer.alloc(height * row.length);
  for (let y = 0; y < height; y++) {
    row.copy(raw, y * row.length);
  }

  const compressed = zlib.deflateSync(raw);

  const ihdrData = Buffer.alloc(13);
  ihdrData.writeUInt32BE(width, 0);
  ihdrData.writeUInt32BE(height, 4);
  ihdrData.writeUInt8(8, 8); // bit depth
  ihdrData.writeUInt8(2, 9); // color type RGB
  ihdrData.writeUInt8(0, 10);
  ihdrData.writeUInt8(0, 11);
  ihdrData.writeUInt8(0, 12);

  const { createHash } = require('crypto');
  function crc32(buf) {
    const crcTable = Buffer.alloc(1024);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) {
        c = (c & 1) ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      }
      crcTable.writeUInt32LE(c, n * 4);
    }
    let crc = 0xffffffff;
    for (let i = 0; i < buf.length; i++) {
      crc = crcTable.readUInt32LE(((crc ^ buf[i]) & 0xff) * 4) ^ (crc >>> 8);
    }
    return (crc ^ 0xffffffff) >>> 0;
  }

  function chunk(type, data) {
    const len = Buffer.alloc(4);
    len.writeUInt32BE(data.length);
    const typeStr = Buffer.from(type);
    const crc = Buffer.alloc(4);
    crc.writeUInt32BE(crc32(Buffer.concat([typeStr, data])));
    return Buffer.concat([len, typeStr, data, crc]);
  }

  const png = Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdrData),
    chunk('IDAT', compressed),
    chunk('IEND', Buffer.alloc(0)),
  ]);

  fs.writeFileSync(outputPath, png);
}

async function main() {
  const { input, output } = parseArgs(process.argv);

  console.log(`[html-renderer] 시작`);
  console.log(`[html-renderer] 입력: ${input}`);
  console.log(`[html-renderer] 출력: ${output}`);

  ensureDir(output);
  ensureDir(LOG_DIR);

  const htmlFiles = getHtmlFiles(input);
  console.log(`[html-renderer] HTML 파일 ${htmlFiles.length}개 발견: ${htmlFiles.join(', ')}`);

  let results;

  try {
    results = await renderWithPuppeteer(input, output, htmlFiles);
  } catch (err) {
    // Puppeteer 없을 때 폴백
    if (err.message.includes('puppeteer')) {
      console.warn(`[html-renderer] ⚠️  ${err.message}`);
      console.warn('[html-renderer] 폴백 모드: 흰색 PNG 생성 (실제 렌더링 불가)');

      results = htmlFiles.map((htmlFile, idx) => {
        const pngName = htmlFile.replace('.html', '.png');
        const pngPath = path.join(output, pngName);
        createFallbackPng(pngPath);
        console.log(`[html-renderer] ⚠️  ${pngName} (폴백 — 흰 이미지)`);
        return { file: pngName, path: pngPath, size: 0, ok: false, fallback: true };
      });
    } else {
      throw err;
    }
  }

  // 최종 결과
  const ok = results.filter(r => r.ok && !r.fallback).length;
  const fallback = results.filter(r => r.fallback).length;
  const failed = results.filter(r => !r.ok && !r.fallback).length;

  console.log('\n[html-renderer] 완료 요약:');
  console.log(`  성공: ${ok}개`);
  if (fallback > 0) console.log(`  폴백(흰 이미지): ${fallback}개 — puppeteer 설치 후 재실행 필요`);
  if (failed > 0) console.log(`  실패: ${failed}개`);
  console.log(`  저장 경로: ${output}`);

  if (failed > 0) {
    process.exit(1);
  }
}

main().catch(err => {
  console.error(`[html-renderer] ❌ 오류: ${err.message}`);
  logError(err.message);
  process.exit(1);
});
