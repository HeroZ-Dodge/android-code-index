#!/usr/bin/env node
// 查询易协作父单及子单的当前状态（直接调用 API）
// 用法: node list_pm_issues.mjs <issue_id>
// 输出: JSON 格式的单据列表 { parent: {...}, children: [...] }

import { getIssueWithChildrenDeep } from './pm-api.mjs';

const issueId = process.argv[2];
if (!issueId) {
  console.error('用法: node list_pm_issues.mjs <issue_id>');
  process.exit(1);
}

function pickFields(issue) {
  return {
    id: issue.id,
    title: issue.subject,
    status: issue.status?.name ?? issue.status,
    assignee: issue.assigned_to?.name ?? issue.assigned_to,
  };
}

try {
  const issue = await getIssueWithChildrenDeep(issueId);
  const parent = pickFields(issue);
  const children = (issue.children ?? [])
    .filter(c => c.tracker?.name === '大神_Android')
    .map(pickFields);
  console.log(JSON.stringify({ parent, children }, null, 2));
} catch (e) {
  console.error(e.message);
  process.exit(1);
}
