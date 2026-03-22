# Change App Version Skill

自动修改 Android APP 版本号的 Claude Code Skill。

## 文件结构

```
change-app-version/
├── SKILL.md        # 核心 skill 配置和执行指令
├── reference.md    # 技术参考文档 (版本号规范、Gradle 配置等)
├── examples.md     # 使用示例和工作流
└── README.md       # 本文件
```

## 快速开始

**触发示例:**
```
修改 app 版本为 4.8.0
change version to 5.0.0
app 版本改为 4.9.0-beta
```

**Skill 会自动:**
1. 提取目标版本号
2. 读取 `gradlescript/gl_config.gradle`
3. 修改 `app_configs.version_name` 的值
4. 报告修改结果

## 验证 Skill

### 1. 检查 Skill 是否可用

重启 Claude Code 后,询问:
```
有哪些 skills 可用?
```

应该能看到 `change-app-version` skill。

### 2. 测试 Skill 激活

使用包含触发关键词的问题:
```
修改 app 版本为 4.8.1
```

Skill 应该自动激活并执行。

### 3. 验证修改结果

检查文件是否已修改:
```bash
grep "version_name" gradlescript/gl_config.gradle
```

应该看到:
```groovy
app_configs.version_name = "4.8.1"
```

## 调试

如果 skill 未被激活,启用调试模式:
```bash
claude --debug
```

## 相关配置

- **配置文件**: `gradlescript/gl_config.gradle`
- **配置行号**: 约第 135 行
- **配置格式**: `app_configs.version_name = "版本号"`

## 版本历史

- **v1.0.0** (2025-12-01): 初始版本
