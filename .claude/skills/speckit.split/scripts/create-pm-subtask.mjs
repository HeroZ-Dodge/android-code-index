#!/usr/bin/env node
// 在 PM 系统上为父单创建子单
// 从父单继承 tracker、version、priority、自定义字段等信息
//
// 用法: node create-pm-subtask.mjs <父单ID> <子单标题> [指派人]
// 输出: JSON { id, subject, parent_id }

import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { homedir } from 'node:os';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const API_BASE = 'http://redmineapi.nie.netease.com/api';
const DEFAULT_TIMEOUT = 30_000;

// 自定义字段 ID: "是否AI介入" = 2014 (bool 类型)
const CUSTOM_FIELD_AI_INVOLVED = 2014;

function readPmConfig() {
  const configPath = join(homedir(), '.config', 'pm-cli', 'config.json');
  const config = JSON.parse(readFileSync(configPath, 'utf-8'));
  return config.default;
}

function buildParams(params) {
  return Object.entries(params)
    .filter(([, v]) => v != null)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join('&');
}

async function pmGet(endpoint, params) {
  const qs = buildParams(params);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT);
  try {
    const res = await fetch(`${API_BASE}/${endpoint}?${qs}`, {
      signal: controller.signal,
    });
    const json = await res.json();
    return json;
  } finally {
    clearTimeout(timeoutId);
  }
}

async function pmPost(endpoint, params) {
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
    // 先读取 body，不依赖 HTTP status code（API 有时状态码不准确）
    const json = await res.json();
    return json;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * 从父单的 custom_fields 构建子单的 custom_field 映射
 * 与 pm-cli 逻辑一致：继承父单的自定义字段，跳过 user 类型字段中的复杂结构
 */
function buildCustomFieldMap(parentCustomFields) {
  const customFieldMap = {};
  const followsMails = [];

  for (const field of parentCustomFields) {
    if (field.value === null || field.value === undefined || field.value === '') continue;

    if (field.identify === 'IssuesQCFollow') {
      // 跟进QA - 提取邮箱列表
      if (Array.isArray(field.value)) {
        for (const item of field.value) {
          if (item.user?.mail) followsMails.push(item.user.mail);
        }
      }
    } else if (field.field_format === 'user') {
      // user 类型字段 - 提取 ID
      if (field.multiple && Array.isArray(field.value)) {
        const userIds = field.value.map(item => item.user?.id).filter(Boolean);
        if (userIds.length > 0) customFieldMap[field.id] = userIds.join(',');
      } else if (field.value?.user?.id) {
        customFieldMap[field.id] = field.value.user.id;
      }
    } else {
      customFieldMap[field.id] = Array.isArray(field.value) ? field.value.join(',') : field.value;
    }
  }

  // 强制设置"是否AI介入"为 true
  customFieldMap[CUSTOM_FIELD_AI_INVOLVED] = '1';

  return { customFieldMap, followsMails };
}

async function createSubTask(parentId, subject, assignedTo) {
  const { token, host, project } = readPmConfig();

  // 1. 获取父单信息，继承 tracker、version、priority、自定义字段
  const parentResult = await pmGet('issue', { token, host, issue_id: parentId });
  if (!parentResult.success || !parentResult.data) {
    throw new Error(`无法获取父单 #${parentId} 信息: ${parentResult.message || '未知错误'}`);
  }
  const parent = parentResult.data;

  // 2. 构建创建参数（与 pm-cli create 逻辑一致）
  const params = {
    token,
    host,
    parent_issue_id: parentId,
    subject,
    status: '新建',
  };
  // project 优先从配置读取，否则从父单继承
  params.project = project || parent.project?.name;
  if (parent.tracker?.name) params.tracker = parent.tracker.name;
  if (parent.fixed_version?.name) params.version = parent.fixed_version.name;
  if (parent.priority?.id) params.priority_id = parent.priority.id;

  // 指派人：优先用参数指定，否则继承父单
  if (assignedTo) {
    params.assigned_to = assignedTo;
  } else if (parent.assigned_to?.mail) {
    params.assigned_to_mail = parent.assigned_to.mail;
  }

  // 3. 继承父单自定义字段 + 设置"是否AI介入"
  if (parent.custom_fields && parent.custom_fields.length > 0) {
    const { customFieldMap, followsMails } = buildCustomFieldMap(parent.custom_fields);
    if (Object.keys(customFieldMap).length > 0) {
      params.custom_field = JSON.stringify(customFieldMap);
    }
    if (followsMails.length > 0) {
      params.follows = followsMails.join(',');
    }
  }

  // 4. 创建子单
  const result = await pmPost('create_issue', params);
  if (!result.success) {
    throw new Error(`创建子单失败: ${result.api_error_msg || result.message || JSON.stringify(result)}`);
  }

  // 5. 创建后再次确保"是否AI介入"已设置（兜底）
  const issueId = result.data?.id;
  if (issueId) {
    try {
      await pmPost('update_issue', {
        token,
        host,
        issue_id: issueId,
        custom_field: JSON.stringify({ [CUSTOM_FIELD_AI_INVOLVED]: '1' }),
      });
    } catch (_) {
      // 忽略更新失败，子单已创建成功
    }
  }

  return result.data;
}

// CLI entry
const [parentId, subject, assignedTo] = process.argv.slice(2);
if (!parentId || !subject) {
  console.error('Usage: create-pm-subtask.mjs <parentId> <subject> [assignedTo]');
  process.exit(1);
}

try {
  const data = await createSubTask(parentId, subject, assignedTo);
  console.log(JSON.stringify({ id: data.id, subject: data.subject, parent_id: parentId }));
} catch (err) {
  console.error(`Error: ${err.message}`);
  process.exit(1);
}
