#!/usr/bin/env node
// POPO 文档导出器
// 从 POPO 团队空间链接导出文档内容为 Markdown
//
// 用法:
//   node popo-doc.mjs <url> [--output <file>]
//   node popo-doc.mjs login            # 交互式登录获取 token
//   node popo-doc.mjs check            # 检查登录状态
//
// 示例:
//   node popo-doc.mjs "https://docs.popo.netease.com/team/pc/android/pageDetail/d9d428bb..."
//   node popo-doc.mjs "https://docs.popo.netease.com/team/pc/android/pageDetail/d9d428bb..." --output /tmp/doc.md

import { readFileSync, writeFileSync, mkdirSync, existsSync, unlinkSync } from 'node:fs';
import { join } from 'node:path';
import { homedir, tmpdir } from 'node:os';
import { createInterface } from 'node:readline';
import { execSync } from 'node:child_process';

const CONFIG_DIR = join(homedir(), '.config', 'popo-doc-cli');
const CONFIG_FILE = join(CONFIG_DIR, 'config.json');
const BASE_URL = 'https://docs.popo.netease.com';
const OPEN_API_BASE = 'https://open.popo.netease.com';
const DEFAULT_TIMEOUT = 30_000;
const POLL_INTERVAL = 2_000;
const POLL_MAX_WAIT = 60_000;

// 内置 Open API 凭据（团队共享，开箱即用）
const BUILTIN_APP_ID = 'CoyAA6Oco9sDlCiBcp';
const BUILTIN_APP_SECRET = 'qhgV70ybSbxX8TpI4CyDbOkfQP9Dd8PwqTvZ44ECfCSjDivCzsyc8Tkr894QKRTf';

// ─── Config ───

function readConfig() {
  try {
    return JSON.parse(readFileSync(CONFIG_FILE, 'utf-8'));
  } catch {
    return {};
  }
}

function writeConfig(config) {
  mkdirSync(CONFIG_DIR, { recursive: true });
  writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
}

// ─── Auth ───

async function prompt(question) {
  const rl = createInterface({ input: process.stdin, output: process.stderr });
  return new Promise(resolve => {
    rl.question(question, answer => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

function getArg(name) {
  const idx = process.argv.indexOf(name);
  return idx !== -1 && process.argv[idx + 1] ? process.argv[idx + 1] : null;
}

async function loginWithPassword() {
  let email = getArg('--email');
  let password = getArg('--password');

  if (!email || !password) {
    console.error('=== POPO 文档登录 (邮箱密码) ===\n');
    if (!email) email = await prompt('网易邮箱 (如 zhangsan@corp.netease.com): ');
    if (!password) password = await prompt('密码: ');
  }

  if (!email || !password) {
    console.error('Error: 邮箱和密码不能为空');
    process.exit(1);
  }

  // 使用 Playwright 自动化浏览器登录（POPO 的 bs-user API 只能从 SPA 内调用）
  console.error('正在通过浏览器自动登录...');

  const tmpScript = join(tmpdir(), `popo-login-${Date.now()}.cjs`);
  const scriptContent = `
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  try {
    await page.goto('https://docs.popo.netease.com/login?redirect=%2Fdrive%2Frecent', { waitUntil: 'networkidle', timeout: 30000 });
    const emailInput = page.locator('input').first();
    await emailInput.waitFor({ timeout: 15000 });
    await emailInput.fill(${JSON.stringify(email)});
    const passwordInput = page.locator('input[type="password"]').first();
    await passwordInput.waitFor({ timeout: 5000 });
    await passwordInput.fill(${JSON.stringify(password)});
    try {
      const cb = page.locator('input[type="checkbox"]').first();
      const checked = await cb.isChecked({ timeout: 2000 });
      if (!checked) await cb.check({ force: true });
    } catch {}
    const btn = page.locator('button').filter({ hasText: '登录' }).first();
    await btn.click();
    await page.waitForURL(url => !url.toString().includes('/login'), { timeout: 30000 }).catch(() => {});
    const cookies = await context.cookies();
    const result = {};
    for (const c of cookies) {
      if (c.name === 'accessToken') result.accessToken = c.value;
      if (c.name === 'refreshToken') result.refreshToken = c.value;
    }
    console.log(JSON.stringify(result));
  } finally {
    await browser.close();
  }
})();
`;

  writeFileSync(tmpScript, scriptContent);

  try {
    const nodePath = resolvePlaywrightNodePath();
    const result = execSync(`node "${tmpScript}"`, {
      timeout: 60000,
      env: { ...process.env, NODE_PATH: nodePath },
      stdio: ['pipe', 'pipe', 'pipe'],
    }).toString().trim();
    const tokens = JSON.parse(result);
    if (!tokens.accessToken) {
      throw new Error('登录后未获取到 accessToken，请检查邮箱和密码是否正确');
    }

    const config = { accessToken: tokens.accessToken, refreshToken: tokens.refreshToken || '', updatedAt: new Date().toISOString() };
    writeConfig(config);
    console.error('登录成功! Token 已保存到 ' + CONFIG_FILE);
  } catch (e) {
    if (e.message.includes('Cannot find')) {
      throw new Error('需要安装 playwright: npm i -g playwright');
    }
    throw new Error('浏览器登录失败: ' + (e.stderr?.toString() || e.message));
  } finally {
    try { unlinkSync(tmpScript); } catch {}
  }
}

async function loginWithToken() {
  let accessToken = getArg('--access-token');
  let refreshToken = getArg('--refresh-token');

  if (!accessToken) {
    console.error('=== POPO 文档登录 (手动 Token) ===');
    console.error('请在浏览器 F12 → Application → Cookies 中找到以下值：\n');
    accessToken = await prompt('accessToken: ');
    refreshToken = refreshToken || await prompt('refreshToken: ');
  }

  if (!accessToken) {
    console.error('Error: accessToken 不能为空');
    process.exit(1);
  }

  const config = { accessToken, refreshToken: refreshToken || '', updatedAt: new Date().toISOString() };
  writeConfig(config);
  console.error('登录信息已保存到 ' + CONFIG_FILE);

  try {
    const id = await apiGet('/api/bs-team-space/web/v1/teamSpace/id', { teamSpaceKey: 'android' });
    console.error('登录成功! teamSpaceId: ' + id);
  } catch (e) {
    console.error('Warning: 登录验证失败，token 可能已过期: ' + e.message);
  }
}

async function login() {
  const mode = process.argv.includes('--token') ? 'token'
    : process.argv.includes('--app') ? 'app'
    : 'password';
  if (mode === 'token') {
    await loginWithToken();
  } else if (mode === 'app') {
    await loginWithApp();
  } else {
    await loginWithPassword();
  }
}

async function loginWithApp() {
  let appId = getArg('--app-id');
  let appSecret = getArg('--app-secret');

  if (!appId || !appSecret) {
    console.error('=== POPO 开放平台配置 ===\n');
    if (!appId) appId = await prompt('appId: ');
    if (!appSecret) appSecret = await prompt('appSecret: ');
  }

  if (!appId || !appSecret) {
    console.error('Error: appId 和 appSecret 不能为空');
    process.exit(1);
  }

  const config = readConfig();
  config.appId = appId;
  config.appSecret = appSecret;
  writeConfig(config);
  console.error('开放平台凭据已保存到 ' + CONFIG_FILE);

  try {
    await getOpenAccessToken();
    console.error('验证成功!');
  } catch (e) {
    console.error('Warning: 验证失败: ' + e.message);
  }
}

async function checkLogin() {
  const config = readConfig();
  if (!config.accessToken) {
    console.error('未登录。请运行: node popo-doc.mjs login');
    process.exit(1);
  }
  try {
    const id = await apiGet('/api/bs-team-space/web/v1/teamSpace/id', { teamSpaceKey: 'android' });
    console.log(JSON.stringify({ status: 'ok', tokenPrefix: config.accessToken.substring(0, 16) + '...', updatedAt: config.updatedAt }, null, 2));
  } catch (e) {
    console.error('Token 已过期或无效: ' + e.message);
    console.error('请重新运行: node popo-doc.mjs login');
    process.exit(1);
  }
}

async function refreshAccessToken() {
  // bs-user OAuth 端点在 CLI 下不可用（返回 HTML），跳过自动刷新
  return false;
}

// ─── API ───

async function apiGet(path, params, retry = true) {
  const config = readConfig();
  if (!config.accessToken) {
    throw new Error('未登录。请运行: node popo-doc.mjs login');
  }

  const url = new URL(path, BASE_URL);
  for (const [k, v] of Object.entries(params)) {
    if (v != null) url.searchParams.set(k, String(v));
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT);

  try {
    const res = await fetch(url.toString(), {
      headers: {
        'Accept': 'application/json',
        'Authorization': config.accessToken,
      },
      signal: controller.signal,
    });

    const text = await res.text();
    let json;
    try {
      json = JSON.parse(text);
    } catch {
      throw new Error('API 返回非 JSON 响应（可能未登录或 token 已过期）');
    }

    if (json.status === 305 && retry) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        return apiGet(path, params, false);
      }
      throw new Error('登录已过期，请重新运行: node popo-doc.mjs login');
    }

    if (json.status !== 200 && json.status !== 0 && json.status !== 1) {
      throw new Error(`API Error [${json.status}]: ${json.message || JSON.stringify(json)}`);
    }

    return json.data;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ─── Open API (appId/appSecret) ───

let openAccessTokenCache = null;
let openAccessTokenExpiry = 0;

async function getOpenAccessToken() {
  const config = readConfig();
  const appId = config.appId || BUILTIN_APP_ID;
  const appSecret = config.appSecret || BUILTIN_APP_SECRET;

  if (openAccessTokenCache && Date.now() < openAccessTokenExpiry - 60_000) {
    return openAccessTokenCache;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT);
  try {
    const res = await fetch(`${OPEN_API_BASE}/open-apis/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ appId, appSecret }),
      signal: controller.signal,
    });
    const json = await res.json();
    if (json.errcode !== 0 || !json.data?.openAccessToken) {
      throw new Error(`获取 openAccessToken 失败: ${json.errmsg || JSON.stringify(json)}`);
    }
    openAccessTokenCache = json.data.openAccessToken;
    openAccessTokenExpiry = json.data.accessExpiredAt || (Date.now() + 7200_000);
    return openAccessTokenCache;
  } finally {
    clearTimeout(timeoutId);
  }
}

async function openApiGet(path, params = {}) {
  const token = await getOpenAccessToken();
  const url = new URL(path, OPEN_API_BASE);
  for (const [k, v] of Object.entries(params)) {
    if (v != null) url.searchParams.set(k, String(v));
  }
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT);
  try {
    const res = await fetch(url.toString(), {
      headers: { 'Open-Access-Token': token, 'Content-Type': 'application/json' },
      signal: controller.signal,
    });
    const json = await res.json();
    if (json.errcode !== 0) {
      throw new Error(`Open API [${json.errcode}]: ${json.errmsg || JSON.stringify(json)}`);
    }
    return json.data;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ─── URL 解析 ───

function parsePopoUrl(url) {
  // Team space: /team/pc/{key}/pageDetail/{pageId}
  const teamMatch = url.match(/docs\.popo\.netease\.com\/team\/pc\/([^/]+)\/pageDetail\/([a-f0-9]+)/);
  if (teamMatch) return { docType: 'team', teamSpaceId: teamMatch[1], pageId: teamMatch[2] };

  // Doc space: /doc/pageDetail/{pageId}
  const docMatch = url.match(/docs\.popo\.netease\.com\/doc\/pageDetail\/([a-f0-9]+)/);
  if (docMatch) return { docType: 'team', teamSpaceId: null, pageId: docMatch[1] };

  // Lingxi: /lingxi/{docId}
  const lingxiMatch = url.match(/docs\.popo\.netease\.com\/lingxi\/([a-f0-9]+)/);
  if (lingxiMatch) return { docType: 'lingxi', teamSpaceId: null, pageId: lingxiMatch[1] };

  // Raw 32-char hex ID
  const rawMatch = url.match(/^([a-f0-9]{32})$/);
  if (rawMatch) return { docType: 'unknown', teamSpaceId: null, pageId: rawMatch[1] };

  throw new Error(`无法解析 POPO 文档链接: ${url}`);
}

// ─── teamSpaceKey → teamSpaceId 解析 ───

const teamSpaceIdCache = {};

async function resolveTeamSpaceId(teamSpaceKey) {
  if (!teamSpaceKey) return null;
  if (/^[a-f0-9]{32}$/.test(teamSpaceKey)) return teamSpaceKey;
  if (teamSpaceIdCache[teamSpaceKey]) return teamSpaceIdCache[teamSpaceKey];

  const id = await apiGet('/api/bs-team-space/web/v1/teamSpace/id', { teamSpaceKey });
  teamSpaceIdCache[teamSpaceKey] = id;
  return id;
}

// ─── 导出 ───

function resolvePlaywrightNodePath() {
  const methods = [
    () => { const p = execSync('node -e "console.log(require.resolve(\'playwright\'))"', { timeout: 5000, stdio: ['pipe', 'pipe', 'pipe'] }).toString().trim(); return join(p, '..', '..'); },
    () => { const p = execSync('find ~/.npm/_npx -path "*/node_modules/playwright/index.js" 2>/dev/null | head -1', { timeout: 5000 }).toString().trim(); return p ? join(p, '..', '..') : ''; },
    () => { const p = execSync('find ~/.npm/_npx -name playwright -type d -maxdepth 5 2>/dev/null | head -1', { timeout: 5000 }).toString().trim(); return p ? join(p, '..') : ''; },
  ];
  for (const method of methods) {
    try {
      const result = method();
      if (result && existsSync(join(result, 'playwright'))) return result;
    } catch {}
  }
  throw new Error('找不到 playwright 模块，请运行: npx playwright install chromium');
}

async function getDocDetail(docId) {
  return apiGet(`/api/bs-doc/v1/document/get/${docId}`, { update: 1 });
}

async function getPageDetail(teamSpaceId, pageId) {
  teamSpaceId = await resolveTeamSpaceId(teamSpaceId);
  return apiGet('/api/bs-team-space/web/v1/page/detail', { teamSpaceId, pageId });
}

async function exportPageAsync(teamSpaceKey, pageId) {
  return openApiGet('/open-apis/drive-space/v1/page/export', { teamSpaceKey, pageId });
}

async function pollTaskResult(taskId) {
  const startTime = Date.now();
  while (Date.now() - startTime < POLL_MAX_WAIT) {
    const task = await openApiGet('/open-apis/drive/v1/task', { taskId });
    if (task && task.taskCompleteStatus === 1) {
      return task;
    }
    if (task && task.taskStatus && task.taskStatus !== 200 && task.taskCompleteStatus !== 0) {
      throw new Error(`导出任务失败: ${JSON.stringify(task)}`);
    }
    await new Promise(r => setTimeout(r, POLL_INTERVAL));
  }
  throw new Error('导出任务超时');
}

async function downloadFile(url) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT);
  try {
    const res = await fetch(url, { signal: controller.signal });
    if (!res.ok) throw new Error(`下载失败: ${res.status}`);
    return Buffer.from(await res.arrayBuffer());
  } finally {
    clearTimeout(timeoutId);
  }
}

async function exportAndDownloadDocx(teamSpaceKey, pageId, outputPath) {
  console.error('正在导出文档 (Open API)...');
  const exportData = await exportPageAsync(teamSpaceKey, pageId);

  if (!exportData || !exportData.id) {
    throw new Error('创建导出任务失败');
  }

  console.error(`导出任务已创建 (ID: ${exportData.id})，等待完成...`);
  const task = await pollTaskResult(exportData.id);

  if (!task.taskExtra) {
    throw new Error('导出任务完成但未返回下载链接');
  }

  console.error('正在下载文件...');
  const fileBuffer = await downloadFile(task.taskExtra);
  writeFileSync(outputPath, fileBuffer);
  console.error('docx 文件已导出到: ' + outputPath);
}

// ─── 团队空间表格通过 bs-team-space API 导出 Excel ───

async function exportTeamSheetViaApi(teamSpaceId, pageId, outputPath) {
  console.error('正在通过团队空间 API 导出表格...');

  // Step 1: 创建导出任务（exportType=2 表示 Excel）
  const exportData = await apiGet('/api/bs-team-space/web/v1/page/export', {
    teamSpaceId,
    pageId,
    exportType: 2,
  });

  if (!exportData || !exportData.id) {
    throw new Error('创建团队空间表格导出任务失败');
  }

  const taskId = exportData.id;
  console.error(`导出任务已创建 (ID: ${taskId})，等待完成...`);

  // Step 2: 轮询任务状态
  const startTime = Date.now();
  while (Date.now() - startTime < POLL_MAX_WAIT) {
    const taskRes = await apiGet(`/api/bs-doc/v1/task/${taskId}`, {});
    if (taskRes && taskRes.taskCompleteStatus === 1) {
      if (!taskRes.taskExtra) {
        throw new Error('导出任务完成但未返回下载链接');
      }
      // Step 3: 下载 Excel
      console.error('正在下载 Excel 文件...');
      const fileBuffer = await downloadFile(taskRes.taskExtra);
      writeFileSync(outputPath, fileBuffer);
      console.error('Excel 文件已导出到: ' + outputPath);
      return;
    }
    await new Promise(r => setTimeout(r, POLL_INTERVAL));
  }
  throw new Error('导出任务超时');
}

// ─── 灵犀文档通过 bs-doc API 导出 ───

async function exportLingxiDocViaApi(docId, outputPath, exportType = 2) {
  const typeLabel = exportType === 1 ? 'docx' : 'xlsx';
  console.error(`正在导出灵犀文档 (${typeLabel})...`);

  // Step 1: 创建导出任务
  const config = readConfig();
  const url = new URL('/api/bs-doc/v1/document/lingxi/export/new', BASE_URL);
  url.searchParams.set('docId', docId);
  url.searchParams.set('exportType', String(exportType));

  const res = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Accept': 'application/json', 'Authorization': config.accessToken },
  });
  const exportJson = await res.json();
  if (exportJson.status !== 1 || !exportJson.data?.id) {
    throw new Error('创建灵犀文档导出任务失败: ' + (exportJson.message || JSON.stringify(exportJson)));
  }

  const taskId = exportJson.data.id;
  console.error(`导出任务已创建 (ID: ${taskId})，等待完成...`);

  // Step 2: 轮询任务状态
  const startTime = Date.now();
  while (Date.now() - startTime < POLL_MAX_WAIT) {
    const taskRes = await apiGet(`/api/bs-doc/v1/task/${taskId}`, {});
    if (taskRes && taskRes.taskCompleteStatus === 1) {
      if (!taskRes.taskExtra) {
        throw new Error('导出任务完成但未返回下载链接');
      }
      // Step 3: 下载文件
      console.error(`正在下载 ${typeLabel} 文件...`);
      const fileBuffer = await downloadFile(taskRes.taskExtra);
      writeFileSync(outputPath, fileBuffer);
      console.error(`${typeLabel} 文件已导出到: ` + outputPath);
      return;
    }
    await new Promise(r => setTimeout(r, POLL_INTERVAL));
  }
  throw new Error('导出任务超时');
}

// ─── 灵犀文档导出（自动判断文档/表格类型） ───

async function exportLingxiDoc(docId, outputFile, docDetail) {
  // 通过文档详情的 type 字段判断：type=1 普通文档，type=2 表格文档
  const detail = docDetail || await getDocDetail(docId);
  const isSheet = detail.type === 2;

  if (isSheet) {
    const xlsxPath = outputFile
      ? outputFile.replace(/\.(md|docx|xlsx)$/i, '') + '.xlsx'
      : '/tmp/popo-doc-output.xlsx';
    await exportLingxiDocViaApi(docId, xlsxPath, 2);
    return `表格文档已导出为 Excel: ${xlsxPath}`;
  }

  const docxPath = outputFile
    ? outputFile.replace(/\.(md|docx|xlsx)$/i, '') + '.docx'
    : '/tmp/popo-doc-output.docx';
  await exportLingxiDocViaApi(docId, docxPath, 1);
  return `文档已导出为 docx: ${docxPath}`;
}

// ─── Main ───

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    console.error(`用法:
  node popo-doc.mjs <url>                     # 导出文档到 stdout
  node popo-doc.mjs <url> --output <file>     # 导出文档到文件
  node popo-doc.mjs login                     # 邮箱密码登录 (推荐)
  node popo-doc.mjs login --token             # 手动粘贴 Cookie Token 登录
  node popo-doc.mjs check                     # 检查登录状态
  node popo-doc.mjs detail <url>              # 获取页面详情 JSON`);
    process.exit(0);
  }

  if (args[0] === 'login') {
    await login();
    return;
  }

  if (args[0] === 'check') {
    await checkLogin();
    return;
  }

  const isDetail = args[0] === 'detail';
  const url = isDetail ? args[1] : args[0];

  if (!url) {
    console.error('Error: 请提供 POPO 文档链接');
    process.exit(1);
  }

  const { docType, teamSpaceId, pageId } = parsePopoUrl(url);

  if (docType === 'lingxi') {
    let detail = null;
    try {
      detail = await getDocDetail(pageId);
      if (isDetail) {
        console.log(JSON.stringify(detail, null, 2));
        return;
      }
    } catch (e) {
      console.error('获取文档详情失败: ' + e.message);
      if (isDetail) { process.exit(1); }
    }

    let output;
    const outputIdx2 = args.indexOf('--output');
    const outputFile = outputIdx2 !== -1 ? args[outputIdx2 + 1] : null;
    try {
      output = await exportLingxiDoc(pageId, outputFile, detail);
    } catch (e) {
      console.error('导出失败: ' + e.message);
      process.exit(1);
    }

    console.log(output);
    return;
  }

  // 团队空间文档流程（使用 Open API，无需用户登录）
  let detail;
  try {
    detail = await getPageDetail(teamSpaceId, pageId);
  } catch (e) {
    detail = { pageName: '' };
    console.error('获取页面详情失败: ' + e.message);
  }

  if (isDetail) {
    console.log(JSON.stringify(detail, null, 2));
    return;
  }

  // 团队空间中嵌入的灵犀文档（pageType=2, externalType=1）
  // 通过团队空间自己的导出 API 导出 Excel
  if (detail.pageType === 2 && detail.externalType === 1) {
    console.error('检测到团队表格文档（嵌入的灵犀文档），导出 Excel...');
    const outputIdx = args.indexOf('--output');
    const outputFile = outputIdx !== -1 ? args[outputIdx + 1] : null;
    const xlsxPath = outputFile
      ? outputFile.replace(/\.(md|xlsx)$/i, '') + '.xlsx'
      : '/tmp/popo-doc-output.xlsx';

    const resolvedTeamSpaceId = detail.teamSpaceId || await resolveTeamSpaceId(teamSpaceId);
    await exportTeamSheetViaApi(resolvedTeamSpaceId, pageId, xlsxPath);
    console.log(`表格文档已导出为 Excel: ${xlsxPath}`);
    return;
  }

  // 团队普通文档：直接导出 docx
  const outputIdx = args.indexOf('--output');
  const outputFile = outputIdx !== -1 ? args[outputIdx + 1] : null;
  const docxPath = outputFile
    ? outputFile.replace(/\.(md|docx)$/i, '') + '.docx'
    : '/tmp/popo-doc-output.docx';

  try {
    await exportAndDownloadDocx(teamSpaceId || 'android', pageId, docxPath);
    console.log(`文档已导出为 docx: ${docxPath}`);
  } catch (e) {
    console.error('导出失败: ' + e.message);
    // 回退: 输出页面详情 JSON
    const parts = [];
    if (detail.pageName) parts.push(`# ${detail.pageName}\n`);
    parts.push(JSON.stringify(detail, null, 2));
    const output = parts.join('\n');
    if (outputFile) {
      writeFileSync(outputFile, output, 'utf-8');
      console.error('已回退导出页面详情到: ' + outputFile);
    } else {
      console.log(output);
    }
  }
}

main().catch(err => {
  console.error('Error: ' + err.message);
  process.exit(1);
});
