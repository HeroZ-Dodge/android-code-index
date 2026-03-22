---
name: abtestv2-generator
description: 达尔文 AB 测试代码生成器。当用户提到"达尔文"、"达尔文实验"、"达尔文AB测试"、"ABTestV2"、"sceneSn"或需要添加/修改达尔文实验配置时自动触发。专门用于自动生成 ABTestV2 相关的模板代码（修改 SceneSn.kt、ABTestType.kt、ABTestV2Sdk.kt、ABTestV2SdkImp.kt）
---

# ABTestV2 代码生成器

根据用户提供的达尔文实验配置，自动生成 ABTestV2 框架代码，涉及 4 个核心文件的修改。

## 输入格式

### 基本格式
功能场景字符串（可能包含多个用 `|` 分隔的场景），例如：
- `video_player|pip` (小窗播放)
- `video_player|auto_play_next` (自动连播)
- `follow_live|kandian_tab` (关注直播看点标签)
- `ai_sidebar` (AI 侧边栏，单场景)

### 扩展格式
用户可能会提供额外信息：
- **默认值**: 如 "默认开启" -> `default: "on"`
- **维度类型**: 如 "基于圈子" -> 添加 squareId 维度方法
- **批量判断**: 如 "批量获取视频播放器特性" -> 创建批量判断方法

## 文件路径
```
serviceim/src/main/java/com/netease/god/im/sdk/
├── SceneSn.kt                    # 场景常量定义
├── ABTestType.kt                 # AB 测试类型枚举
├── ABTestV2Sdk.kt               # AB 测试接口
└── ABTestV2SdkImp.kt            # AB 测试实现
```

## 工作流程

### 第 1-2 步: 输入分析和重复检查（委托 haiku）

**使用 Task 工具委托给 haiku 模型执行**：

Task(
  subagent_type="general-purpose",
  model="haiku",
  prompt="""
  1. 在以下 4 个文件中搜索场景常量 "{sceneSn}" 是否已存在：
     - serviceim/.../SceneSn.kt
     - serviceim/.../ABTestType.kt
     - serviceim/.../ABTestV2Sdk.kt
     - serviceim/.../ABTestV2SdkImp.kt
  2. 找到各文件中最后一个同类定义的位置（用于确定插入点）
  返回 JSON: {"exists": true/false, "insertPositions": {...}}
  """
)

### 第 3 步: 生成代码片段（主模型执行）

按顺序生成 4 个文件的代码：
1. **SceneSn.kt** - 场景常量（私有 + 公开）
2. **ABTestType.kt** - 枚举定义（sceneSn + key + default）
3. **ABTestV2Sdk.kt** - 接口声明（带默认值）
4. **ABTestV2SdkImp.kt** - 接口实现（无默认值）

### 第 4 步: 应用修改并验证（委托 haiku）

**使用 Task 工具委托给 haiku 模型执行**：

Task(
  subagent_type="general-purpose",
  model="haiku",
  prompt="""
  检查刚修改的 4 个文件：
  1. 确认方法签名一致性（接口有默认值，实现无默认值）
  2. 确认引用关系正确（SceneSn → ABTestType → Sdk/Imp）
  3. 确认代码风格和注释完整
  返回 JSON: {"valid": true/false, "issues": [...]}
  """
)

详细的代码生成规则请参考 reference.md。
