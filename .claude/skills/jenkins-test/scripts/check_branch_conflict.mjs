#!/usr/bin/env node
// 检查是否有 Jenkins Job 已使用指定分支
// 用法: node check_branch_conflict.mjs <BRANCH>
// 输出: 冲突的 Job 名称（无冲突则无输出）

const JENKINS_BASE = 'http://10.0.9.238:8080/jenkins';
const AUTH = 'lianghanguang:11712f96945ee628b3b843842129a84bc2';
const AUTH_HEADER = 'Basic ' + Buffer.from(AUTH).toString('base64');
const CONCURRENCY = 10;

const branch = process.argv[2];
if (!branch) {
  console.error('用法: node check_branch_conflict.mjs <BRANCH>');
  process.exit(1);
}

async function jenkinsGet(path) {
  const res = await fetch(`${JENKINS_BASE}${path}`, {
    headers: { 'Authorization': AUTH_HEADER },
  });
  if (!res.ok) return null;
  return res.text();
}

async function listJobs() {
  const res = await fetch(`${JENKINS_BASE}/api/json?tree=${encodeURIComponent('jobs[name]')}`, {
    headers: { 'Authorization': AUTH_HEADER },
  });
  if (!res.ok) throw new Error('无法获取 Job 列表');
  const data = await res.json();
  return data.jobs.map(j => j.name).filter(n => !n.includes('ForCopyDocker'));
}

function extractBranch(configXml) {
  const match = configXml.match(
    /<name>GIT_BRANCH<\/name>[\s\S]*?<defaultValue>([^<]*)<\/defaultValue>/
  );
  return match?.[1] ?? null;
}

async function checkJob(jobName) {
  const config = await jenkinsGet(`/job/${encodeURIComponent(jobName)}/config.xml`);
  if (!config) return null;
  const jobBranch = extractBranch(config);
  return jobBranch === branch ? jobName : null;
}

// 带并发限制的批量执行
async function runWithConcurrency(items, concurrency, fn) {
  let index = 0;
  const results = [];

  async function worker() {
    while (index < items.length) {
      const i = index++;
      results[i] = await fn(items[i]);
    }
  }

  await Promise.all(Array.from({ length: Math.min(concurrency, items.length) }, () => worker()));
  return results;
}

async function main() {
  const jobs = await listJobs();
  const results = await runWithConcurrency(jobs, CONCURRENCY, checkJob);
  const conflict = results.find(r => r !== null);
  if (conflict) {
    console.log(conflict);
  }
}

main().catch(err => {
  console.error(err.message);
  process.exit(1);
});
