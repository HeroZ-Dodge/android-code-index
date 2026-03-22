---
name: change-app-version
description: 修改 Android APP 版本号。当用户说"修改 app 版本"、"change version"、"app 版本改为"、"升级版本到"或类似表达时使用此 skill。适用于需要更新 gradlescript/gl_config.gradle 中的 version_name 配置。
---

# 修改 APP 版本号

自动修改项目的 Android APP 版本号配置。

## 执行步骤

### 1. 确认目标版本号

从用户输入中提取目标版本号。支持的格式示例:
- "修改 app 版本为 4.8.0"
- "change version to 5.0.0"
- "app 版本改为 4.9.0-beta"
- "升级版本到 5.1.0"

**版本号格式**: 通常为 `x.y.z` 或 `x.y.z-suffix` (如 `4.8.0`, `5.0.0-beta`)

### 2. 读取配置文件

读取项目配置文件: `gradlescript/gl_config.gradle`

版本号配置位于文件的第 135 行左右，格式为:
```groovy
app_configs.version_name = "4.8.0"
```

### 3. 修改版本号

使用 Edit 工具精确替换版本号:

**重要**: 只替换 `app_configs.version_name = "旧版本"` 这一行的值，保持其他配置不变。

**替换示例**:
- 旧值: `app_configs.version_name = "4.7.0"`
- 新值: `app_configs.version_name = "4.8.0"`

### 4. 验证修改

修改完成后，读取文件的第 135 行附近内容，确认版本号已正确更新。

### 5. 输出结果

向用户报告修改结果，格式如下:

```
✅ APP 版本号修改成功

**配置文件**: gradlescript/gl_config.gradle
**旧版本**: 4.7.0
**新版本**: 4.8.0

注意: 版本号修改完成，无需手动编译验证。
```

## 注意事项

1. **不要编译**: 遵循项目 CLAUDE.md 规则，修改完成后不执行编译操作
2. **精确替换**: 只修改 `app_configs.version_name` 的值，不影响其他配置
3. **版本格式**: 保持引号格式，确保是有效的 Groovy 字符串
4. **错误处理**: 如果找不到配置行或格式异常，应明确告知用户

## 使用示例

**场景 1**: 标准版本号升级
```
用户: 修改 app 版本为 4.8.0
结果: version_name = "4.8.0"
```

**场景 2**: 带后缀的版本号
```
用户: change version to 5.0.0-beta
结果: version_name = "5.0.0-beta"
```

**场景 3**: 大版本升级
```
用户: app 版本改为 5.0.0
结果: version_name = "5.0.0"
```

## 技术细节

- **配置文件路径**: `gradlescript/gl_config.gradle`
- **配置行号**: 约第 135 行
- **配置格式**: `app_configs.version_name = "版本号"`
- **语法**: Groovy (Gradle 配置语言)

## 版本历史

- **v1.0.0** (2025-12-01): 初始版本，支持基本的版本号修改功能
