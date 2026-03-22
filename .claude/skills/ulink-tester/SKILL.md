---
name: ulink-tester
description: 网易大神应用 ulink 路由测试专家，能够自动分析路由 Handler 代码、生成正确的 ulink URL 并通过 adb 命令进行测试。当用户提到"测试 ulink"、"ulink test"、"测试路由"、"测试 scheme"、"scheme 路由"、"打开页面测试"、"跳转测试"或特定的 Handler 名称（如 OpenBotChatHandler）时自动激活。
allowed-tools: Read, Grep, Glob, Bash
---

# 网易大神 Ulink 路由测试专家

自动分析路由 Handler 代码、生成 ulink URL 并通过 adb 命令测试。

## 项目结构知识

### 关键文件位置
```
main/src/main/java/com/netease/gl/router/
├── handler/                    # Router Handler 类
│   ├── OpenBotChatHandler.java
│   ├── OpenH5Handler.java
│   └── ...
├── adapter/scheme/              # Scheme Adapter 类
│   ├── SchemeOpenBotChatAdapter.java
│   ├── SchemeH5Adapter.java
│   └── ...
└── RouterAction.java           # Action 常量定义

services/modbase/src/main/java/com/netease/gl/service/base/router/
└── SchemeConstant.java         # Scheme action 字符串常量
```

### Handler 模式识别
```java
public class XxxHandler extends SupportAuthRouterHandler {
    @Override
    public int actionType() {
        return RouterAction.XXX;  // 返回 action 类型
    }

    @Override
    public void handleInternal(Context context, GlRouterParams params) {
        Map<String, String> map = JsonUtil.fromJson(params.getExtStr(), ...);
        String param1 = map.get("param1");  // 提取参数
        String param2 = map.get("param2");
        // 业务逻辑处理
    }
}
```

### SchemeAdapter 模式识别
```java
public class SchemeXxxAdapter extends AbsSchemeAdapter {
    @Override
    String actionType() {
        return SchemeConstant.XXX;  // 返回 action 字符串
    }

    @Override
    public GlRouterParams parse(Uri uri) {
        String[] keys = {"param1", "param2", "param3"};  // 定义参数列表
        for (String key : keys) {
            extMap.put(key, uri.getQueryParameter(key));
        }
    }
}
```

## 工作流程

### 1. 接收测试请求
用户提供 Handler 名称或 action 名称。

### 2-3. 查找和分析代码（委托 haiku）

**使用 Task 工具委托给 haiku 模型执行**：

Task(
  subagent_type="general-purpose",
  model="haiku",
  prompt="""
  根据 Handler 名称 "{handlerName}" 查找相关代码：
  1. 在 main/src/main/java/com/netease/gl/router/handler/ 查找 Handler 文件
  2. 在 main/src/main/java/com/netease/gl/router/adapter/scheme/ 查找对应 SchemeAdapter
  3. 从 SchemeConstant.java 获取 action 字符串值
  4. 从 SchemeAdapter 的 parse() 方法提取参数列表
  返回 JSON: {"action": "...", "params": [{"name": "...", "required": true/false}], "handlerPath": "...", "adapterPath": "..."}
  """
)

### 4. 收集参数值（主模型执行）
对于识别出的参数，询问用户提供值：
```
检测到 openBotChat 需要以下参数：
- uid: 机器人的用户 ID（必需）
- url: 要打开的 H5 页面 URL（可选）
- utm_source: 来源标识（可选，如 signInCalendar）

请提供参数值：
```

### 5. 生成 ulink URL
基础格式：
```
https://app.16163.com/ds/ulinks/?action=<action>&param1=value1&param2=value2
```

示例：
```
https://app.16163.com/ds/ulinks/?action=openBotChat&uid=123456&utm_source=signInCalendar
```

### 6. 执行 ADB 命令
```bash
# 生成命令（注意转义）
adb shell am start -W -a android.intent.action.VIEW -d "https://app.16163.com/ds/ulinks/\?action=openBotChat\&uid=123456\&utm_source=signInCalendar"

# 执行并监控结果
adb shell am start -W -a android.intent.action.VIEW -d "..."
```

### 7. 监控日志（可选）
```bash
# 清除日志
adb logcat -c

# 监控路由相关日志
adb logcat | grep -E "Router|Scheme|Handler"
```

## 常见 Action 映射

| Handler 类 | RouterAction 常量 | SchemeConstant 值 | 常用参数 |
|-----------|------------------|------------------|---------|
| OpenBotChatHandler | OPEN_BOT_CHAT | openBotChat | uid, url, utm_source |
| OpenH5Handler | H5 | openUrl | url, title |
| UserInfoHandler | OPEN_USER_PAGE | user | uid |
| FeedDetailHandler | DETAIL | detail | feedId |
| TopicDetailHandler | TOPIC | topic | topicId |
| CircleHandler | CIRCLE | circle | circleId |
| ComposeHandler | COMPOSE | compose | type |

## 特殊参数处理

### URL 参数编码
如果参数值包含 URL，需要进行 URL 编码：
```javascript
encodeURIComponent("https://example.com/page?id=1")
// 结果：https%3A%2F%2Fexample.com%2Fpage%3Fid%3D1
```

### 中文参数
中文参数需要 URL 编码：
```javascript
encodeURIComponent("测试标题")
// 结果：%E6%B5%8B%E8%AF%95%E6%A0%87%E9%A2%98
```

## 测试示例

### 示例 1：测试打开机器人聊天
```bash
# 原始 URL
https://app.16163.com/ds/ulinks/?action=openBotChat&uid=gl_ai_1001&utm_source=signInCalendar

# ADB 命令（转义后）
adb shell am start -W -a android.intent.action.VIEW -d "https://app.16163.com/ds/ulinks/\?action=openBotChat\&uid=gl_ai_1001\&utm_source=signInCalendar"
```

### 示例 2：测试打开 H5 页面
```bash
# 原始 URL（URL 参数需要编码）
https://app.16163.com/ds/ulinks/?action=openUrl&url=https%3A%2F%2Fwww.16163.com%2Fpage&title=%E6%B5%8B%E8%AF%95

# ADB 命令
adb shell am start -W -a android.intent.action.VIEW -d "https://app.16163.com/ds/ulinks/\?action=openUrl\&url=https%3A%2F%2Fwww.16163.com%2Fpage\&title=%E6%B5%8B%E8%AF%95"
```

## 错误处理

### 常见错误
1. **Handler 未找到**：提示用户检查 Handler 名称拼写
2. **参数缺失**：提示必需参数并要求用户提供
3. **ADB 连接失败**：提示检查设备连接和 ADB 配置
4. **路由失败**：检查日志定位问题原因

### 调试建议
1. 使用 `adb devices` 确认设备连接
2. 使用 `adb logcat` 查看详细日志
3. 检查网易大神应用是否已安装并运行
4. 验证 action 名称是否正确

## 最佳实践

1. **参数验证**：始终验证必需参数是否提供
2. **转义处理**：正确处理 URL 中的特殊字符
3. **编码处理**：对包含特殊字符的参数值进行 URL 编码
4. **日志监控**：执行后检查日志确认路由成功
5. **错误反馈**：提供清晰的错误信息和解决建议
