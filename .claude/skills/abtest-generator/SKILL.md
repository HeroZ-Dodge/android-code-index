---
name: abtest-generator
description: CMS AB 测试代码生成器。当用户提到"CMS AB测试"、"ABTest"、"ABTestEntityV2"、"AbTestHelper"或需要添加/修改 CMS 配置的 AB 测试时自动触发。专门用于自动生成 CMS 上配置的 ABTest 相关代码（修改 ABTestEntityV2.java、IAbTestHelper.java、AbTestHelper.java）
---

# CMS AB 测试代码生成器

根据用户提供的 AB 测试配置信息，自动生成符合项目规范的代码，涉及 3 个核心文件的修改。

## 必须修改的 3 个核心文件

### 1. ABTestEntityV2.java
**路径**: `services/foundation/config/src/main/sdk/com/netease/gl/serviceconfig/abtest/ABTestEntityV2.java`
**职责**: AB 测试实体类，定义所有 AB 测试名称常量和目标值常量

### 2. IAbTestHelper.java
**路径**: `services/foundation/config/src/main/sdk/com/netease/gl/serviceconfig/IAbTestHelper.java`
**职责**: AB 测试接口定义，声明所有业务方法

### 3. AbTestHelper.java
**路径**: `services/foundation/config/src/main/java/com/netease/gl/service/config/abtest/AbTestHelper.java`
**职责**: AB 测试辅助实现类，实现所有接口方法

---

## 用户输入格式

### 必填字段
- **name**: AB 测试名称（下划线分隔，小写）
- **分流描述**: 功能描述（中文）
- **target**: 目标值说明（如：1.开启;0.关闭）
- **byUser**: 是否基于用户分桶（true/false）

### 可选字段
- **needSquareId**: 是否需要圈子维度（默认：false）
- **methodType**: 方法返回类型（boolean/string，默认：boolean）
- **isGlobal**: 是否支持全局配置（默认：false）
- **defaultValue**: 字符串方法的默认返回值（仅 methodType=string 时需要）
- **versionNote**: 版本说明或功能替换备注

---

## 命名转换规则

### 常量名: 下划线小写 -> 全大写下划线
```
show_ai → SHOW_AI = "show_ai"
circle_staggered → CIRCLE_STAGGERED = "circle_staggered"
```

### 方法名: 下划线小写 -> 驼峰 + 前缀
```
Boolean 方法: is + 驼峰  (show_ai → isShowAi())
String 方法:  get + 驼峰 (launch_ad_button_color → getLaunchAdButtonColor())
```

### 特殊语义保留
- `match_` 前缀保留为 `Match` (match_video_da_bing → isMatchVideoDaBing())
- `is_` 前缀移除（因为方法已有 `is` 前缀）

---

## ABTestEntityV2.java 代码生成规则

### 常量定义格式
```java
public static final String [常量名] = "[name]"; // [分流描述]
// 或带版本说明:
public static final String [常量名] = "[name]"; // [版本]，[分流描述]
```

### 目标值常量（通用，已定义）
```java
TARGET_TRUE = "true", TARGET_FALSE = "false"
TARGET_OPEN = "open", TARGET_CLOSE = "close"
TARGET_0 = "0", TARGET_1 = "1", TARGET_2 = "2", TARGET_3 = "3", TARGET_4 = "4"
TARGET_NEW = "NEW", TARGET_KOL = "kol"
VALUE_TYPE_GLOBAL = "global"
```

### 特定值常量（可选）
如果 target 包含特定值（如颜色），生成专用常量:
```java
public static final String LAUNCH_AD_BUTTON_RED_COLOR = "#EC4747";
public static final String LAUNCH_AD_BUTTON_BLUE_COLOR = "#1A203D";
```

### 插入位置: 按功能分组，靠近相关常量

---

## IAbTestHelper.java 代码生成规则

### 6 种接口方法类型

#### 类型 1: 简单布尔判断（全局）
```java
/**
 * [分流描述]
 * @return 是否匹配AB测试
 */
@WorkerThread
boolean is[MethodName]();
```

#### 类型 2: 带 squareId 的布尔判断
```java
/**
 * [分流描述]
 * @param squareId 圈子ID
 * @return 是否匹配AB测试
 */
boolean is[MethodName](String squareId);
```

#### 类型 3: 获取字符串配置（全局）
```java
/**
 * 获取[分流描述]
 * @return AB测试目标值
 */
@WorkerThread
String get[MethodName]();
```

#### 类型 4: 获取字符串配置（带 squareId）
```java
/**
 * 获取[分流描述]
 * @param squareId 圈子ID
 * @return AB测试目标值
 */
String get[MethodName](String squareId);
```

#### 类型 5: 多目标值判断（一个 AB 测试多个方法）
```java
boolean is[MethodName]Condition1();
boolean is[MethodName]Condition2();
```

#### 类型 6: 带特殊逻辑的判断（少见，与类型 2 签名相同）

### @WorkerThread 注解规则
- **全局方法**（不带 squareId）: 添加 `@WorkerThread`
- **带 squareId 的方法**: 不添加 `@WorkerThread`

---

## AbTestHelper.java 代码生成规则

### 核心基础方法
```java
private boolean isMatchABTest(boolean byUser, String name, String target);
private boolean isMatchABTest(boolean byUser, String name, String target, String squareId);
private boolean isMatchABTest(boolean byUser, String name, String target, String squareId, boolean isGlobal);
private String getABTestTarget(boolean byUser, String name, String squareId, String defaultValue);
private String getABTestTarget(boolean byUser, String name, String squareId, boolean isGlobal, String defaultValue);
```

### 7 种实现模式

#### 模式 1: 简单布尔（用户维度, byUser=true, 无squareId）
```java
@Override
@WorkerThread
public boolean is[MethodName]() {
    return isMatchABTest(true, ABTestEntityV2.[常量名], ABTestEntityV2.TARGET_[目标]);
}
```

#### 模式 2: 简单布尔（设备维度, byUser=false, 无squareId）
```java
@Override
@WorkerThread
public boolean is[MethodName]() {
    return isMatchABTest(false, ABTestEntityV2.[常量名], ABTestEntityV2.TARGET_[目标]);
}
```

#### 模式 3: 带 squareId 的布尔
```java
@Override
public boolean is[MethodName](String squareId) {
    return isMatchABTest([byUser], ABTestEntityV2.[常量名], ABTestEntityV2.TARGET_[目标], squareId);
}
```

#### 模式 4: 带 squareId + isGlobal
```java
@Override
public boolean is[MethodName](String squareId) {
    return isMatchABTest([byUser], ABTestEntityV2.[常量名], ABTestEntityV2.TARGET_[目标], squareId, true);
}
```

#### 模式 5: 字符串配置（全局）
```java
@Override
@WorkerThread
public String get[MethodName]() {
    return getABTestTarget([byUser], ABTestEntityV2.[常量名], "", [默认值]);
}
```
**注意**: squareId 参数传空字符串 `""`，不是 `null`

#### 模式 6: 字符串配置（带 squareId）
```java
@Override
public String get[MethodName](String squareId) {
    return getABTestTarget([byUser], ABTestEntityV2.[常量名], squareId, [默认值]);
}
```

#### 模式 7: 特殊 squareId 处理
```java
@Override
public boolean is[MethodName](String squareId) {
    String targetSquareId = [squareId 转换逻辑];
    if ([条件]) {
        return isMatchABTest([byUser], ABTestEntityV2.[常量名], ABTestEntityV2.TARGET_[目标], targetSquareId, true);
    } else {
        return isMatchABTest([byUser], ABTestEntityV2.[常量名], ABTestEntityV2.TARGET_[目标], targetSquareId);
    }
}
```

### 模式选择决策

| 条件 | 模式 |
|------|------|
| boolean + 无squareId + byUser=true | 模式 1 |
| boolean + 无squareId + byUser=false | 模式 2 |
| boolean + squareId + 无isGlobal | 模式 3 |
| boolean + squareId + isGlobal=true | 模式 4 |
| string + 无squareId | 模式 5 |
| string + squareId | 模式 6 |
| 特殊squareId处理 | 模式 7 |

### target 目标值映射

| target 描述 | 对应常量 |
|------------|---------|
| "1" | `ABTestEntityV2.TARGET_1` |
| "0" | `ABTestEntityV2.TARGET_0` |
| "2" | `ABTestEntityV2.TARGET_2` |
| "3" | `ABTestEntityV2.TARGET_3` |
| "true" | `ABTestEntityV2.TARGET_TRUE` |
| "false" | `ABTestEntityV2.TARGET_FALSE` |
| "open" | `ABTestEntityV2.TARGET_OPEN` |
| "close" | `ABTestEntityV2.TARGET_CLOSE` |
| "NEW" | `ABTestEntityV2.TARGET_NEW` |

特殊配置值（如颜色、URL等）: 有特定常量用常量，否则用字符串字面量。

### 默认值设定规则
- 新功能开关: `TARGET_0` 或 `false`（默认关闭）
- 颜色配置: 产品指定的默认颜色
- 字符串配置: 空字符串 `""` 或已有稳定值
- 已定义常量优先使用

---

## 完整工作流程

### 阶段 1-2: 输入解析和重复检查（委托 haiku）

**使用 Task 工具委托给 haiku 模型执行**：

Task(
  subagent_type="general-purpose",
  model="haiku",
  prompt="""
  在以下 3 个文件中搜索是否已存在 "{name}" 的定义：
  1. services/foundation/config/src/main/sdk/com/netease/gl/serviceconfig/abtest/ABTestEntityV2.java
  2. services/foundation/config/src/main/sdk/com/netease/gl/serviceconfig/IAbTestHelper.java
  3. services/foundation/config/src/main/java/com/netease/gl/service/config/abtest/AbTestHelper.java

  使用 Grep 搜索常量名和方法名。
  返回 JSON: {"exists": true/false, "details": "已有定义的位置和内容"}
  """
)

### 阶段 3-5: 代码生成（主模型执行）

根据输入参数和上述规则，依次生成 3 个文件的代码：
1. ABTestEntityV2.java — 常量定义
2. IAbTestHelper.java — 接口声明
3. AbTestHelper.java — 方法实现

### 阶段 6: 验证（委托 haiku）

**使用 Task 工具委托给 haiku 模型执行**：

Task(
  subagent_type="general-purpose",
  model="haiku",
  prompt="""
  检查刚修改的 3 个文件：
  1. 读取 ABTestEntityV2.java，确认新常量名格式正确（全大写+下划线）
  2. 读取 IAbTestHelper.java 和 AbTestHelper.java，确认方法签名一致
  3. 确认 @Override、@WorkerThread 注解正确
  返回 JSON: {"valid": true/false, "issues": [...]}
  """
)

---

## 常见错误（必须避免）

1. **squareId 传 null** -> 应传空字符串 `""`
2. **目标值用字符串字面量** -> 应使用 `ABTestEntityV2.TARGET_X` 常量
3. **接口和实现签名不一致** -> 参数类型、参数名、返回类型必须完全一致
4. **全局方法忘记 @WorkerThread** -> 不带参数的方法添加，带 squareId 的不添加
5. **实现方法缺少 @Override** -> 所有实现方法必须添加
6. **常量名用驼峰** -> 必须全大写+下划线
7. **方法名保留下划线** -> 必须转为驼峰
8. **byUser 参数搞反** -> true=用户维度，false=设备维度
9. **捕获泛型异常** -> AB 测试方法底层已处理，不需要 try-catch
10. **忘记添加版本注释** -> 有版本说明或功能替换信息时应添加

---

## 输出格式

生成代码后，按以下格式输出:

```markdown
## 已生成 CMS AB 测试代码

### 配置信息
- **AB 测试名称**: ${name}
- **分流描述**: ${分流描述}
- **目标值**: ${target}
- **分桶维度**: ${byUser ? "用户维度" : "设备维度"}
- **圈子维度**: ${needSquareId ? "是" : "否"}
- **全局支持**: ${isGlobal ? "是" : "否"}
- **方法类型**: ${methodType}

### 修改的文件和代码
（展示 3 个文件的修改内容）

### 验证清单
（所有检查项）

### 使用示例
（调用示例代码）

### 后续步骤
1. 在 CMS 后台配置对应的 AB 测试
2. 在业务代码中调用生成的方法
3. 进行功能测试和验证
```

---

详细的真实项目案例和特殊场景处理请参考 reference.md。

## 注意事项

1. 所有代码和注释使用中文（除非变量名、方法名等必须使用英文）
2. 严格遵循命名转换规则
3. 确保接口和实现类方法签名完全一致
4. 生成的代码必须能直接应用到项目中，无需手动修改
5. 不要遗漏任何一个文件的修改（3 个文件都要修改）
6. 检查是否存在重复定义，避免冲突
