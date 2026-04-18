#!/usr/bin/env node
/**
 * file-handler.js
 *
 * SCV: 파일/디렉토리 읽기, 쓰기, 정리를 담당하는 유틸리티입니다.
 * 모든 직원(리서처, 콘텐츠 기획자, 카피라이터, 디자이너)이 공용으로 사용합니다.
 *
 * 사용법:
 *   node .claude/scv/file-handler.js --action read --path output/data/trend-data.json
 *   node .claude/scv/file-handler.js --action write --path output/data/foo.json --content '{"key":"val"}'
 *   node .claude/scv/file-handler.js --action list --path output/drafts/slides/
 *   node .claude/scv/file-handler.js --action mkdir --path output/final/images/
 *   node .claude/scv/file-handler.js --action state --stage 3 --mode auto --topic "주제명"
 *   node .claude/scv/file-handler.js --action status
 */

const fs = require('fs');
const path = require('path');

const STATE_FILE = path.join('output', 'state.json');
const LOG_DIR = path.join('output', 'logs');

function parseArgs(argv) {
  const args = { action: null, path: null, content: null, stage: null, mode: null, topic: null };
  for (let i = 2; i < argv.length; i++) {
    if (argv[i].startsWith('--') && argv[i + 1]) {
      const key = argv[i].slice(2);
      args[key] = argv[++i];
    }
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
  fs.appendFileSync(
    path.join(LOG_DIR, 'error.log'),
    `${new Date().toISOString()} [file-handler] ${message}\n`,
    'utf8'
  );
}

// 액션: 파일 읽기
function actionRead(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`파일 없음: ${filePath}`);
  }
  const content = fs.readFileSync(filePath, 'utf8');
  process.stdout.write(content);
}

// 액션: 파일 쓰기
function actionWrite(filePath, content) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, content, 'utf8');
  console.log(`[file-handler] ✅ 저장: ${filePath}`);
}

// 액션: 디렉토리 파일 목록
function actionList(dirPath) {
  if (!fs.existsSync(dirPath)) {
    console.log(`[file-handler] 디렉토리 없음: ${dirPath}`);
    return;
  }
  const files = fs.readdirSync(dirPath);
  if (files.length === 0) {
    console.log(`[file-handler] 비어있음: ${dirPath}`);
  } else {
    files.forEach(f => console.log(path.join(dirPath, f)));
  }
}

// 액션: 디렉토리 생성
function actionMkdir(dirPath) {
  ensureDir(dirPath);
  console.log(`[file-handler] ✅ 디렉토리 준비: ${dirPath}`);
}

// 액션: state.json 업데이트
function actionState(stage, mode, topic) {
  ensureDir(path.dirname(STATE_FILE));

  let state = {};
  if (fs.existsSync(STATE_FILE)) {
    try {
      state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    } catch {
      state = {};
    }
  }

  const stageNum = parseInt(stage, 10);
  const completed = state.completedStages ?? [];
  if (!completed.includes(stageNum - 1) && stageNum > 1) {
    completed.push(stageNum - 1);
  }

  const updated = {
    currentStage: stageNum,
    completedStages: [...new Set(completed)].sort((a, b) => a - b),
    mode: mode ?? state.mode ?? 'auto',
    selectedTopic: topic ?? state.selectedTopic ?? null,
    startedAt: state.startedAt ?? new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  fs.writeFileSync(STATE_FILE, JSON.stringify(updated, null, 2), 'utf8');
  console.log(`[file-handler] ✅ state.json 업데이트 — 현재 단계: ${stageNum}`);
}

// 액션: 파이프라인 상태 확인
function actionStatus() {
  const checks = [
    { stage: 1, file: path.join('output', 'data', 'trend-data.json'), label: '트렌드 수집' },
    { stage: 2, file: path.join('output', 'data', 'research.md'), label: '자료 리서치' },
    { stage: 3, file: path.join('output', 'drafts', 'content-plan.md'), label: '주제 기획' },
    { stage: 4, file: path.join('output', 'drafts', 'script.md'), label: '스크립트 작성' },
    { stage: 5, file: path.join('output', 'drafts', 'slides'), label: '카드뉴스 디자인' },
    { stage: 6, file: path.join('output', 'final', 'images'), label: 'PNG 이미지 생성' },
  ];

  console.log('\n[file-handler] 파이프라인 상태:\n');

  let lastCompleted = 0;
  for (const check of checks) {
    const exists = fs.existsSync(check.file);
    const icon = exists ? '✅' : '⬜';
    const detail = exists && fs.statSync(check.file).isDirectory()
      ? `(${fs.readdirSync(check.file).length}개 파일)`
      : '';
    console.log(`  ${icon} ${check.stage}단계: ${check.label} ${detail}`);
    if (exists) lastCompleted = check.stage;
  }

  const nextStage = lastCompleted + 1;
  const stageLabels = { 1: '트렌드 수집', 2: '자료 리서치', 3: '주제 기획', 4: '스크립트 작성', 5: '카드뉴스 디자인', 6: 'PNG 생성', 7: '최종 검토' };
  console.log(`\n  → 다음 단계: ${nextStage}단계 (${stageLabels[nextStage] ?? '완료'})\n`);

  // state.json 로드
  if (fs.existsSync(STATE_FILE)) {
    const state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    console.log(`  [state.json] 모드: ${state.mode} / 주제: ${state.selectedTopic ?? '미선택'} / 업데이트: ${state.updatedAt}`);
  }
}

async function main() {
  const args = parseArgs(process.argv);

  if (!args.action) {
    console.log('사용법:');
    console.log('  --action read   --path <파일경로>');
    console.log('  --action write  --path <파일경로> --content <내용>');
    console.log('  --action list   --path <디렉토리>');
    console.log('  --action mkdir  --path <디렉토리>');
    console.log('  --action state  --stage <번호> [--mode auto/keyword] [--topic "주제명"]');
    console.log('  --action status');
    process.exit(0);
  }

  ensureDir(LOG_DIR);

  switch (args.action) {
    case 'read':
      actionRead(args.path);
      break;
    case 'write':
      actionWrite(args.path, args.content ?? '');
      break;
    case 'list':
      actionList(args.path);
      break;
    case 'mkdir':
      actionMkdir(args.path);
      break;
    case 'state':
      actionState(args.stage, args.mode, args.topic);
      break;
    case 'status':
      actionStatus();
      break;
    default:
      console.error(`[file-handler] 알 수 없는 액션: ${args.action}`);
      process.exit(1);
  }
}

main().catch(err => {
  console.error(`[file-handler] ❌ 오류: ${err.message}`);
  logError(err.message);
  process.exit(1);
});
