#!/usr/bin/env node
// 发送提测通知给指定开发人员和 QA - 直接调用 API
// 用法:
//   node notify_developers.mjs --list <issue_id>
//   node notify_developers.mjs <issue_id> <job_name> <branch> [emails]

import { getIssue, getIssueWithChildrenDeep } from './pm-api.mjs';

const JENKINS_BASE = 'http://10.0.9.238:8080/jenkins/job';

// POPO 机器人配置
const POPO_CONFIG = {
  baseUrl: 'https://open.popo.netease.com',
  appKey: 'MqsoQxR0lzVRDs0SSim5',
  appSecret: '1hkDgKG6MwV0T0vo2mG3FUOqJjCb2Qvzr8Y19niKcVc2e6XMnMN5uUHsC01hyc40'
};

// 解析参数
const isListMode = process.argv[2] === '--list';
let issueId, jobName, branch, customEmails;

if (isListMode) {
  issueId = process.argv[3];
  if (!issueId) {
    console.error('用法: node notify_developers.mjs --list <issue_id>');
    process.exit(1);
  }
} else {
  [,, issueId, jobName, branch, customEmails] = process.argv;
  if (!issueId || !jobName) {
    console.error('用法: node notify_developers.mjs <issue_id> <job_name> <branch> [emails]');
    process.exit(1);
  }
}

const jobUrl = jobName ? `${JENKINS_BASE}/${encodeURIComponent(jobName)}/` : '';

async function getPopoToken() {
  const resp = await fetch(`${POPO_CONFIG.baseUrl}/open-apis/robots/v1/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ appKey: POPO_CONFIG.appKey, appSecret: POPO_CONFIG.appSecret })
  });
  const data = await resp.json();
  if (data.errcode !== 0) throw new Error(`获取 Token 失败: ${data.errmsg}`);
  return data.data.accessToken;
}

async function sendMessage(token, receiver, content) {
  const resp = await fetch(`${POPO_CONFIG.baseUrl}/open-apis/robots/v1/im/send-msg`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Open-Access-Token': token },
    body: JSON.stringify({ receiver, message: { content }, msgType: 'text' })
  });
  const data = await resp.json();
  if (data.errcode !== 0) {
    console.error(`  [ERROR] ${receiver}: errcode=${data.errcode}, errmsg=${data.errmsg || 'unknown'}, traceId=${data.traceId || 'N/A'}`);
  }
  return data.errcode === 0;
}

/** 清理名字前缀（如 "L梁汉光" -> "梁汉光"） */
function cleanName(name) {
  return name ? name.replace(/^[A-Za-z]/, '') : '';
}

/**
 * 从子单提取 Android 开发人员和 QA
 * 同时返回父单标题，避免额外 API 调用
 */
async function getContactsFromChildren(issueId) {
  const issue = await getIssueWithChildrenDeep(issueId);
  const children = issue.children ?? [];

  const androidChildren = children.filter(c => c.tracker?.name === '大神_Android');
  if (androidChildren.length === 0) {
    console.log('未找到 Android 子单');
    return { developers: [], qas: [], title: issue.subject };
  }

  console.log(`找到 ${androidChildren.length} 个 Android 子单`);

  const developerMap = new Map();
  const qaMap = new Map();

  for (const child of androidChildren) {
    const assignedTo = child.assigned_to;
    if (assignedTo?.mail) {
      developerMap.set(assignedTo.mail, { name: cleanName(assignedTo.name), mail: assignedTo.mail });
    }

    const qaField = (child.custom_fields || []).find(cf => cf.name === '跟进QA');
    if (qaField && Array.isArray(qaField.value)) {
      for (const qa of qaField.value) {
        const user = qa.user;
        if (user?.mail) {
          qaMap.set(user.mail, { name: cleanName(user.firstname || user.name), mail: user.mail });
        }
      }
    }
  }

  const sortByMail = (a, b) => a.mail.localeCompare(b.mail);
  return {
    developers: Array.from(developerMap.values()).sort(sortByMail),
    qas: Array.from(qaMap.values()).sort(sortByMail),
    title: issue.subject
  };
}

function formatContact(contact) {
  if (typeof contact === 'string') return contact;
  return contact.name ? `${contact.name} <${contact.mail}>` : contact.mail;
}

function mergeContacts(developers, qas) {
  const map = new Map();
  for (const c of [...developers, ...qas]) {
    if (!map.has(c.mail)) map.set(c.mail, c);
  }
  return Array.from(map.values()).sort((a, b) => a.mail.localeCompare(b.mail));
}

// === 主流程 ===

if (isListMode) {
  console.log('=== 获取通知人员列表 ===\n');
  const { developers, qas } = await getContactsFromChildren(issueId);

  if (developers.length > 0) {
    console.log(`开发人员 (${developers.length}):`);
    developers.forEach(c => console.log(`   - ${formatContact(c)}`));
  }
  if (qas.length > 0) {
    console.log(`QA (${qas.length}):`);
    qas.forEach(c => console.log(`   - ${formatContact(c)}`));
  }

  const allContacts = mergeContacts(developers, qas);
  if (allContacts.length === 0) {
    console.log('未找到通知人员');
  } else {
    console.log(`\n总计 ${allContacts.length} 人`);
  }

  console.log('\n--- JSON_OUTPUT ---');
  console.log(JSON.stringify({
    developers: developers.map(c => c.mail),
    qas: qas.map(c => c.mail),
    all: allContacts.map(c => c.mail)
  }));
} else {
  console.log('=== 发送提测通知 ===\n');

  let emails;
  let issueTitle = '';

  if (customEmails) {
    console.log('使用自定义邮箱列表...');
    emails = customEmails.split(',').map(e => e.trim()).filter(Boolean);
    try {
      const issue = await getIssue(issueId);
      issueTitle = issue.subject || '';
    } catch { /* 获取标题失败不影响通知 */ }
  } else {
    console.log('从子单获取开发人员和 QA...');
    const { developers, qas, title } = await getContactsFromChildren(issueId);
    issueTitle = title || '';

    if (developers.length > 0) {
      console.log(`开发人员 (${developers.length}):`);
      developers.forEach(c => console.log(`   - ${formatContact(c)}`));
    }
    if (qas.length > 0) {
      console.log(`QA (${qas.length}):`);
      qas.forEach(c => console.log(`   - ${formatContact(c)}`));
    }

    const allContacts = mergeContacts(developers, qas);
    emails = allContacts.map(c => c.mail);
  }

  if (emails.length === 0) {
    console.log('未找到通知人员，跳过');
    process.exit(0);
  }

  console.log(`\n通知人员总计 ${emails.length} 人\n`);

  console.log('获取 POPO Token...');
  const token = await getPopoToken();

  const titlePart = issueTitle ? `#${issueId} ${issueTitle}` : `#${issueId}`;
  const message = `提测通知: ${titlePart}\n打包机: ${jobName}\n代码分支: ${branch || '未指定'}\n\nJenkins: ${jobUrl}\n需求单: https://a19.pm.netease.com/v6/issues/${issueId}\n\n请关注构建状态，构建完成后可下载测试包。`;

  console.log('发送通知...');
  let successCount = 0, failCount = 0;
  const failedEmails = [];

  for (const email of emails) {
    const ok = await sendMessage(token, email, message);
    if (ok) { console.log(`  ok ${email}`); successCount++; }
    else { console.log(`  fail ${email}`); failCount++; failedEmails.push(email); }
  }

  console.log('\n=== 通知发送完成 ===');
  console.log(`成功: ${successCount}, 失败: ${failCount}`);

  if (failedEmails.length > 0) {
    console.log('\n--- 以下人员通知失败，请手动发送 ---');
    console.log(`收件人: ${failedEmails.join(', ')}`);
    console.log('--- 消息内容(可直接复制) ---');
    console.log(message);
    console.log('--- END ---');
  }

  console.log('SUCCESS');
}
