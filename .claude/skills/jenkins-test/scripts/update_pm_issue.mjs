#!/usr/bin/env node
// 更新易协作单（父单+子单）- 直接调用 API
// 用法: node update_pm_issue.mjs <issue_id> <job_name> <branch> [--status <status>] [--dry-run]
//
// 功能:
//   1. 在父单 description 中智能更新打包信息（已有则替换，没有则追加）
//   2. 更新父单和所有子单的状态为"开发完成"（可通过 --status 自定义）
//
// --dry-run: 仅展示将要执行的变更，不实际修改任何数据

import { getIssueWithChildrenDeep, updateIssue } from './pm-api.mjs';

// 解析参数
const args = process.argv.slice(2);
const issueId = args[0];
const jobName = args[1];
const branch = args[2];
const dryRun = args.includes('--dry-run');
let status = '开发完成';

const statusIdx = args.indexOf('--status');
if (statusIdx !== -1 && args[statusIdx + 1]) {
  status = args[statusIdx + 1];
}

if (!issueId || !jobName || !branch) {
  console.error('用法: node update_pm_issue.mjs <issue_id> <job_name> <branch> [--status <status>] [--dry-run]');
  process.exit(1);
}

if (dryRun) {
  console.log(`=== [预览] 易协作单 #${issueId} 将执行以下变更 ===`);
} else {
  console.log(`=== 更新易协作单 #${issueId} ===`);
}

// 1. 获取父单（含子单）
const parentIssue = await getIssueWithChildrenDeep(issueId);
const currentDesc = parentIssue.description ?? '';

// 2. 构建 Jenkins Job URL
const jobUrl = `http://10.0.9.238:8080/jenkins/job/${encodeURIComponent(jobName)}/`;

// 3. 构建新 description（智能替换打包信息区块，使用 HTML 格式确保换行）
const issueUrl = `https://a19.pm.netease.com/v6/issues/${issueId}`;
const packBlock = `<hr/>打包机: ${jobName}<br/>代码分支: ${branch}<br/>Jenkins: <a href="${jobUrl}">${jobUrl}</a><br/>需求单: <a href="${issueUrl}">${issueUrl}</a>`;

// 检测已有的打包信息区块（兼容纯文本和 HTML 两种格式）
const packPatternHtml = /\s*<hr\s*\/?>[\s\S]*打包机:[\s\S]*$/;
const packPatternText = /\r?\n?\r?\n?---\r?\n打包机:[\s\S]*$/;
let newDesc;
if (packPatternHtml.test(currentDesc)) {
  newDesc = currentDesc.replace(packPatternHtml, `\n${packBlock}`);
  console.log('检测到已有打包信息(HTML)，将替换更新');
} else if (packPatternText.test(currentDesc)) {
  newDesc = currentDesc.replace(packPatternText, `\n${packBlock}`);
  console.log('检测到已有打包信息(纯文本)，将替换更新');
} else {
  newDesc = currentDesc + `\n${packBlock}`;
  console.log('未检测到打包信息，将新增追加');
}

// 4. 获取 Android 子单列表
const children = (parentIssue.children ?? []).filter(c => c.tracker?.name === '大神_Android');

// dry-run 模式：展示变更预览后退出
if (dryRun) {
  console.log('');
  console.log('将执行的变更:');
  console.log(`  1. 更新父单 #${issueId} description（追加/替换打包信息）`);
  console.log(`  2. 更新父单 #${issueId} 状态: ${parentIssue.status?.name ?? '未知'} → ${status}`);
  if (children.length > 0) {
    console.log(`  3. 更新 ${children.length} 个 Android 子单状态为「${status}」:`);
    for (const child of children) {
      console.log(`     - #${child.id} ${child.subject ?? ''} (${child.status?.name ?? '未知'} → ${status})`);
    }
  } else {
    console.log('  3. 无 Android 子单需要更新');
  }
  console.log('');
  console.log('DRY_RUN_COMPLETE');
  process.exit(0);
}

// 5. 更新父单 description
console.log('更新父单 description...');
await updateIssue(issueId, { description: newDesc });

// 6. 更新父单状态
console.log(`更新父单状态为: ${status}`);
await updateIssue(issueId, { status });

// 7. 更新子单状态
if (children.length > 0) {
  console.log(`更新 ${children.length} 个子单状态...`);
  for (const child of children) {
    try {
      await updateIssue(String(child.id), { status });
      console.log(`  #${child.id} ok`);
    } catch {
      console.log(`  #${child.id} 更新失败`);
    }
  }
} else {
  console.log('无子单需要更新');
}

console.log('');
console.log('=== 更新完成 ===');
console.log(`父单: https://a19.pm.netease.com/v6/issues/${issueId}`);
console.log(`打包机: ${jobUrl}`);
console.log('SUCCESS');
