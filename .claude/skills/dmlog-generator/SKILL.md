---
name: dmlog-generator
description: DM 埋点日志代码生成器。根据产品需求文档自动生成符合网易大神埋点规范的 Kotlin 日志类。当用户提到"埋点"、"日志"、"DM日志"、"生成日志代码"、"DmLog"、"埋点代码"、"trackEvent"时自动触发。
---

# DM 埋点日志代码生成器

根据产品需求文档自动生成符合网易大神埋点规范的 Kotlin 日志类。

## 代码生成规范

### 方法命名规范

- **曝光埋点**：`exp{功能英文名}`（驼峰）— 示例：`expVipMypageTop`
- **点击埋点**：`clk{功能英文名}`（驼峰）— 示例：`clkChatTeamEntrance`
- **其他行为**：根据行为类型命名 — 示例：`submitFeedback`

### 参数规范

- **pageId**: `String?` — 统计口径，必须是第一个参数
- 优先使用 nullable 类型：`String?`, `Int?`, `Long?`, `Boolean?`
- 复杂信息封装到 `info` JSON 字段，简单信息作为独立字段
- **废弃参数**（禁止使用）：~~pageParam~~、~~referPageKey~~、~~referPageParam~~

### 代码风格

- 使用 `object` 单例，`mutableMapOf` 构建 JSON
- 按功能分组（曝光、点击），添加分隔注释
- 所有公开方法必须有 KDoc 注释（中文）
- JSON 字段名使用下划线分隔

### 文件路径

```
{模块名}/src/main/java/com/netease/gl/{子包名}/log/{功能名}DmLog.kt
```

详细代码模板和 Excel 解析规则请参考 [reference.md](reference.md)。

## 工作流程

### 步骤 1: 需求确认（主模型执行）

询问用户提供：
1. 埋点需求文档（Excel/Word 文件路径或截图）
2. 目标模块名称（如 servicevip、serviceim）
3. 功能名称（如 VipMypage、ChatTeam）
4. 是创建新文件还是修改现有文件

### 步骤 2: 文档解析和现有代码检查（委托 haiku）

**使用 Task 工具委托给 haiku 模型执行**：

Task(
  subagent_type="general-purpose",
  model="haiku",
  prompt="""
  1. 读取用户提供的文档，提取埋点定义
  2. 在目标模块的 log/ 目录下搜索是否已存在同名 DmLog 文件
  3. 如果存在，读取文件内容
  返回 JSON: {"events": [...], "existingFile": "path or null", "existingMethods": [...]}
  """
)

### 步骤 3: 代码生成（主模型执行）

1. 按事件类型分组（曝光、点击）
2. 应用代码规范（参考下方规范部分）
3. 生成完整的 KDoc 注释
4. 使用 Write/Edit 写入文件

### 步骤 4: 代码审查（委托 haiku）

**使用 Task 工具委托给 haiku 模型执行**：

Task(
  subagent_type="general-purpose",
  model="haiku",
  prompt="""
  检查生成的 DmLog 文件：
  1. 方法命名是否符合 exp/clk 前缀规范
  2. 是否包含废弃参数（pageParam、referPageKey）
  3. 参数类型是否为 nullable
  4. import 语句是否正确
  返回 JSON: {"valid": true/false, "issues": [...]}
  """
)

## 质量保证检查清单

- [ ] 包名正确（com.netease.gl.{模块名}）
- [ ] import 语句完整
- [ ] 方法命名符合规范（exp/clk 前缀）
- [ ] pageId 作为第一个参数
- [ ] 所有参数使用 nullable 类型
- [ ] 无废弃参数（pageParam、referPageKey）
- [ ] JSON 字段命名使用下划线
- [ ] KDoc 注释完整
- [ ] 无冗余代码
- [ ] 事件名称与方法名对应

