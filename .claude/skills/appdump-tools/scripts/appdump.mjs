#!/usr/bin/env node

/**
 * AppDump Crash Query Script
 * 查询 AppDump 平台的 crash 上报记录
 *
 * Usage:
 *   node appdump.mjs issues [--from <ms>] [--to <ms>] [--hours <n>] [--filters <json>] [--top <n>]
 *   node appdump.mjs hit --identify <id> [--from <ms>] [--to <ms>] [--hours <n>] [--filters <json>]
 *   node appdump.mjs info [--from <s>] [--to <s>] [--days <n>] [--identifys <id1,id2,...>]
 *   node appdump.mjs firsttime [--from <s>] [--to <s>] [--days <n>] [--identifys <id1,id2,...>] [--order asc|desc] [--oversea]
 *   node appdump.mjs tag --identify <id> --tags <t1,t2,...> [--mode set]
 *   node appdump.mjs link --identify <id> --issue-id <pmId>
 *   node appdump.mjs url --field <field> --value <value> [--time last_1_hour]
 */

const BASE_URL = 'https://unisdk.nie.netease.com/api/appdump';
const PROJECT = 'a19';
const TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiJiMWQ2N2MzNS1hOWY0LTRkYTAtODdhZi0xYjRmNzRiYzRlZTQiLCJ1c2VybmFtZSI6Il9hcGlfYTE5X2FwcGR1bXBfX2FwaV9hMTlfYXBwZHVtcF9zeW10b29sX29ic2VydmVyIiwibG9naW5fY2hhbm5lbCI6Im5ldGVhc2UiLCJncmFudF90eXBlIjoiaXNzdWUiLCJ1c2VyX3R5cGUiOjEwMCwiZXhwIjo0OTI2ODAwMzc3LCJpYXQiOjE3NzMyMDAzNzcsImlzcyI6InVuaXNkayIsIm5iZiI6MTc3MzIwMDM3Mn0.q8k7SdKX0mk9TCqL9YgGpgJnbxpp3hOqrUydYb9AGx8';

function parseArgs(argv) {
  const args = { command: argv[0] };
  for (let i = 1; i < argv.length; i++) {
    if (argv[i] === '--from') args.from = argv[++i];
    else if (argv[i] === '--to') args.to = argv[++i];
    else if (argv[i] === '--hours') args.hours = argv[++i];
    else if (argv[i] === '--days') args.days = argv[++i];
    else if (argv[i] === '--identify') args.identify = argv[++i];
    else if (argv[i] === '--identifys') args.identifys = argv[++i];
    else if (argv[i] === '--filters') args.filters = argv[++i];
    else if (argv[i] === '--top') args.top = argv[++i];
    else if (argv[i] === '--tags') args.tags = argv[++i];
    else if (argv[i] === '--mode') args.mode = argv[++i];
    else if (argv[i] === '--issue-id') args.issueId = argv[++i];
    else if (argv[i] === '--order') args.order = argv[++i];
    else if (argv[i] === '--oversea') args.oversea = true;
    else if (argv[i] === '--field') args.field = argv[++i];
    else if (argv[i] === '--value') args.value = argv[++i];
    else if (argv[i] === '--time') args.time = argv[++i];
  }
  return args;
}

function getTimeRangeMs(args) {
  const now = Date.now();
  const hours = parseInt(args.hours || '24', 10);
  const maxHours = 72;
  const effectiveHours = Math.min(hours, maxHours);
  const from = args.from ? parseInt(args.from, 10) : now - effectiveHours * 3600 * 1000;
  const to = args.to ? parseInt(args.to, 10) : now;
  return { from, to };
}

function getTimeRangeSec(args) {
  const now = Math.floor(Date.now() / 1000);
  const days = parseInt(args.days || '7', 10);
  const maxDays = 90;
  const effectiveDays = Math.min(days, maxDays);
  const from = args.from ? parseInt(args.from, 10) : now - effectiveDays * 86400;
  const to = args.to ? parseInt(args.to, 10) : now;
  return { from, to };
}

async function fetchGET(path, params) {
  const url = new URL(BASE_URL + path);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
  }
  const resp = await fetch(url.toString(), {
    headers: { 'X-UAUTH-TOKEN': TOKEN, 'X-UAUTH-PROJECT': PROJECT },
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
  return resp.json();
}

async function fetchPOST(path, body) {
  const url = BASE_URL + path;
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'X-UAUTH-TOKEN': TOKEN,
      'X-UAUTH-PROJECT': PROJECT,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
  return resp.json();
}

// 4.10 获取 issue 列表
async function queryIssues(args) {
  const { from, to } = getTimeRangeMs(args);
  const params = { project: PROJECT, from, to };
  if (args.filters) params.filters = args.filters;

  const result = await fetchGET('/api/v2/capi/pull/issue', params);
  if (result.code !== 200) {
    console.error('API Error:', JSON.stringify(result));
    process.exit(1);
  }

  const issues = result.data || [];
  const topN = parseInt(args.top || '20', 10);
  issues.sort((a, b) => b.count - a.count);

  const totalCrashes = issues.reduce((s, i) => s + i.count, 0);
  const totalUsers = issues.reduce((s, i) => s + i.users, 0);

  console.log(JSON.stringify({
    summary: {
      time_range: { from: new Date(from).toISOString(), to: new Date(to).toISOString() },
      total_issues: issues.length,
      total_crashes: totalCrashes,
      total_affected_users: totalUsers,
    },
    top_issues: issues.slice(0, topN).map((i, idx) => ({
      rank: idx + 1, identify: i.identify, count: i.count, users: i.users,
    })),
  }, null, 2));
}

// 4.11 获取 issue 一条上报记录
async function queryHit(args) {
  if (!args.identify) {
    console.error('Error: --identify is required');
    process.exit(1);
  }
  const { from, to } = getTimeRangeMs(args);
  const params = { project: PROJECT, from, to, identify: args.identify };
  if (args.filters) params.filters = args.filters;

  const result = await fetchGET('/api/v2/capi/pull/issue/hit', params);
  if (result.code !== 200) {
    console.error('API Error:', JSON.stringify(result));
    process.exit(1);
  }
  console.log(JSON.stringify(result.data, null, 2));
}

// 4.8 获取易协作提单单号 & Tag 信息
async function queryInfo(args) {
  const params = {};
  if (args.identifys) {
    params.identifys = args.identifys;
  } else {
    const { from, to } = getTimeRangeSec(args);
    params.from = from;
    params.to = to;
  }
  const result = await fetchGET('/dataexport/api/v1/issue/info', params);
  console.log(JSON.stringify(result, null, 2));
}

// 4.9 获取某时间范围内首次出现的 issue
async function queryFirstTime(args) {
  const body = { project: PROJECT };
  if (args.identifys) {
    body.identifys = args.identifys.split(',');
  } else {
    const { from, to } = getTimeRangeSec(args);
    body.from = from;
    body.to = to;
  }
  if (args.order) body.order = args.order;
  if (args.oversea) body.is_oversea = true;

  const result = await fetchPOST('/dataexport/api/v1/issue/firsttime/list', body);
  console.log(JSON.stringify(result, null, 2));
}

// 4.6 给问题打 Tag
async function setTag(args) {
  if (!args.identify) {
    console.error('Error: --identify is required');
    process.exit(1);
  }
  if (!args.tags) {
    console.error('Error: --tags is required (comma-separated)');
    process.exit(1);
  }
  const body = {
    project: PROJECT,
    params: {
      identify: args.identify,
      tag: args.tags.split(',').map(t => t.trim()),
    },
  };
  if (args.mode) body.mode = args.mode;

  const result = await fetchPOST('/dataexport/api/v1/issue/tag', body);
  console.log(JSON.stringify(result, null, 2));
}

// 4.5 关联易协作工单
async function linkIssue(args) {
  if (!args.identify || !args.issueId) {
    console.error('Error: --identify and --issue-id are required');
    process.exit(1);
  }
  const body = {
    project: PROJECT,
    params: {
      identify: args.identify,
      issueId: parseInt(args.issueId, 10),
    },
  };
  const result = await fetchPOST('/dataexport/api/v1/issue/createjoin', body);
  console.log(JSON.stringify(result, null, 2));
}

// 4.7 生成 AppDump 控制台 URL
function generateUrl(args) {
  if (!args.field || !args.value) {
    console.error('Error: --field and --value are required');
    process.exit(1);
  }
  const time = args.time || 'last_1_hour';
  const filter = JSON.stringify({ field: args.field, value: [args.value], operate: 'term' });
  const url = `https://unisdk.nie.netease.com/appdump/${PROJECT}/crash-list?custom_field[0]=${encodeURIComponent(filter)}&time=${time}`;
  console.log(url);
}

async function main() {
  const argv = process.argv.slice(2);
  if (argv.length === 0) {
    console.log(`Usage:
  node appdump.mjs issues   [--hours <n>] [--from <ms>] [--to <ms>] [--filters <json>] [--top <n>]
  node appdump.mjs hit      --identify <id> [--hours <n>] [--from <ms>] [--to <ms>] [--filters <json>]
  node appdump.mjs info     [--days <n>] [--from <s>] [--to <s>] [--identifys <id1,id2>]
  node appdump.mjs firsttime [--days <n>] [--from <s>] [--to <s>] [--identifys <id1,id2>] [--order asc|desc] [--oversea]
  node appdump.mjs tag      --identify <id> --tags <t1,t2> [--mode set]
  node appdump.mjs link     --identify <id> --issue-id <pmId>
  node appdump.mjs url      --field <field> --value <value> [--time last_1_hour]

Commands:
  issues     查询 issue 列表（时间范围最大3天，时间戳毫秒）
  hit        获取 issue 的一条上报记录详情
  info       获取 issue 的易协作工单和 Tag 信息（时间范围最大90天，时间戳秒）
  firsttime  获取时间范围内首次出现的 issue（时间跨度最大2个月，时间戳秒）
  tag        给 issue 打 Tag（追加模式，--mode set 替换模式）
  link       关联易协作工单到 issue
  url        生成 AppDump 控制台查询链接`);
    process.exit(0);
  }

  const args = parseArgs(argv);
  const commands = {
    issues: queryIssues,
    hit: queryHit,
    info: queryInfo,
    firsttime: queryFirstTime,
    tag: setTag,
    link: linkIssue,
    url: generateUrl,
  };

  const handler = commands[args.command];
  if (!handler) {
    console.error(`Unknown command: ${args.command}`);
    process.exit(1);
  }
  await handler(args);
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
