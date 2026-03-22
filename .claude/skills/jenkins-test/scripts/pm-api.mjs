#!/usr/bin/env node
// 网易易协作 API 直接调用模块
// 跳过 pm-cli 命令行，直接调用 HTTP API
// 凭据从 ~/.config/pm-cli/config.json 读取
//
// 参考 pm-cli 源码:
//   - api-client.ts: BASE_URL, GET/POST, 30s timeout, form-urlencoded
//   - issue-service.ts: getIssue(GET 'issue'), updateIssue(POST 'update_issue')
//   - config.ts: ~/.config/pm-cli/config.json → default.{token, host, project}

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';

const API_BASE = 'http://redmineapi.nie.netease.com/api';
const DEFAULT_TIMEOUT = 30_000; // 30s，与 pm-cli 一致

/**
 * 读取 pm-cli 配置文件中的凭据
 */
export function readPmConfig() {
  const configPath = join(homedir(), '.config', 'pm-cli', 'config.json');
  const config = JSON.parse(readFileSync(configPath, 'utf-8'));
  return config.default;
}

/**
 * 构建查询字符串（与 pm-cli ApiClient.buildQueryString 一致，使用 encodeURIComponent）
 * 注意：不能用 URLSearchParams，它把空格编码为 + 而非 %20，会导致服务端 500
 */
function buildParams(params) {
  return Object.entries(params)
    .filter(([, v]) => v != null)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join('&');
}

/**
 * GET 请求（对应 pm-cli ApiClient.get）
 */
export async function pmGet(endpoint, params) {
  const qs = buildParams(params);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT);
  try {
    const res = await fetch(`${API_BASE}/${endpoint}?${qs}`, {
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
    return res.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * POST 请求（对应 pm-cli ApiClient.post，application/x-www-form-urlencoded）
 */
export async function pmPost(endpoint, params) {
  const body = buildParams(params);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT);
  try {
    const res = await fetch(`${API_BASE}/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
    return res.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * 获取单据详情（对应 pm-cli IssueService.getIssue）
 */
export async function getIssue(issueId) {
  const { token, host, project } = readPmConfig();
  const params = { token, host, issue_id: issueId };
  if (project) params.project = project;
  const result = await pmGet('issue', params);
  if (!result.success || !result.data) {
    throw new Error(`无法获取单据 #${issueId}: ${result.message || '未知错误'}`);
  }
  return result.data;
}

/**
 * 获取单据详情（含子单完整信息）
 * API 的 include=children 只返回简略子单（缺 assigned_to 等），
 * 所以需要先获取子单 ID 列表，再并行请求每个子单的完整详情
 * （与 pm-cli IssueService.getIssueWithChildren 逻辑一致）
 */
export async function getIssueWithChildren(issueId) {
  const { token, host, project } = readPmConfig();
  const params = { token, host, issue_id: issueId, include: JSON.stringify(['children']) };
  if (project) params.project = project;
  const result = await pmGet('issue', params);
  if (!result.success || !result.data) {
    throw new Error(`无法获取单据 #${issueId}: ${result.message || '未知错误'}`);
  }
  const issue = result.data;
  const childIds = (issue.children ?? []).map(c => c.id);
  if (childIds.length > 0) {
    const childParams = { token, host };
    if (project) childParams.project = project;
    const childResults = await Promise.all(
      childIds.map(id =>
        pmGet('issue', { ...childParams, issue_id: id }).catch(() => null)
      )
    );
    issue.children = childResults
      .filter(r => r?.success && r.data)
      .map(r => r.data);
  }
  return issue;
}

/**
 * 递归获取单据及所有后代子单的完整信息（BFS 深度遍历）
 * 与 getIssueWithChildren 不同，此方法会递归获取所有层级的子单
 * 返回的 issue.children 为扁平化的所有后代列表
 */
export async function getIssueWithChildrenDeep(issueId) {
  const { token, host, project } = readPmConfig();
  const baseParams = { token, host };
  if (project) baseParams.project = project;

  const rootResult = await pmGet('issue', {
    ...baseParams, issue_id: issueId, include: JSON.stringify(['children']),
  });
  if (!rootResult.success || !rootResult.data) {
    throw new Error(`无法获取单据 #${issueId}: ${rootResult.message || '未知错误'}`);
  }
  const rootIssue = rootResult.data;

  const allDescendants = [];
  const queue = (rootIssue.children ?? []).map(c => c.id);
  const visited = new Set([issueId]);

  while (queue.length > 0) {
    const batch = queue.splice(0).filter(id => !visited.has(id));
    if (batch.length === 0) break;
    batch.forEach(id => visited.add(id));

    const results = await Promise.all(
      batch.map(id =>
        pmGet('issue', { ...baseParams, issue_id: id, include: JSON.stringify(['children']) })
          .catch(() => null)
      )
    );

    for (const r of results) {
      if (!r?.success || !r.data) continue;
      const issue = r.data;
      allDescendants.push(issue);
      for (const child of (issue.children ?? [])) {
        if (!visited.has(child.id)) queue.push(child.id);
      }
    }
  }

  rootIssue.children = allDescendants;
  return rootIssue;
}

/**
 * 更新单据（对应 pm-cli IssueService.updateIssue，POST 'update_issue'）
 */
export async function updateIssue(issueId, updates) {
  const { token, host, project } = readPmConfig();
  const params = { token, host, issue_id: issueId, ...updates };
  if (project) params.project = project;
  const result = await pmPost('update_issue', params);
  if (!result.success) {
    throw new Error(`更新单据 #${issueId} 失败: ${result.message || '未知错误'}`);
  }
  return result.data;
}
