---
name: create-proto
description: 根据接口文档或截图自动生成 Android Proto 类（继承 GLBaseProto）。当用户提供接口文档截图、JSON 格式的接口定义、或要求创建新的 Proto 接口类时触发。支持从 YApi 导出的 JSON、接口文档截图等多种输入格式。关键词：proto、接口。
---
# Android Proto 类生成器

根据接口文档或截图自动生成符合项目规范的 Android Proto 类，继承 GLBaseProto 及其子类。

## 使用说明文档

详细使用文档请参考：[Proto 类生成器使用指南](https://docs.popo.netease.com/team/pc/android/pageDetail/da3a43aa532d491c856ee1a3e16938c5)

## 工作流程

### 1. 解析输入

支持两种输入格式：

**格式A：JSON 字符串**（通常来自 YApi 导出）
从 JSON 中提取：

- `path` → 接口路径
- `req_body_other` → 请求参数定义（JSON Schema）
- `res_body` → 响应数据定义（JSON Schema）

**格式B：截图**
从截图中识别并提取：

- 接口路径（如 `/v1/app/cc/room/getCcRoomInfo`）
- 请求参数的 Body 部分
- 返回数据的 Result 部分

### 2. 检查接口是否已存在

使用 Grep 搜索项目中是否已有相同路径的接口：

```bash
# 搜索 api() 方法中返回的路径
grep -r "return \"/v1/app/cc/room/getCcRoomInfo\"" services/
```

如果发现已存在，提示用户并终止流程。

### 3. 确定接口host 

通过 AskUserQuestion 与用户确认接口host（要继承的 GLBaseProto 子类）：

**选项1：GLApiProto（推荐）**

- 最常用的选择，适用于大部分通用 API

**选项2：其他子类**

- 用户可输入：

  - Proto 类名（如 `GLActProto`、`GLExpProto`）
  - 或 GLServers 中的 host 关键词（如 `act`、`exp`、`wallet`）
- 系统自动识别映射：

  - `act` → GLActProto
  - `exp` / `privilege` → GLExpProto
  - `recharge` / `ecard` → GLRechargeProto
  - `search` → GLSearchProto
  - `open` → GLOpenProto
  - `wallet` → GLWalletProto
  - `incentive` → GLIncentiveProto
  - `ai` → GlAiProto
  - 等等（参见 references/proto-template.md）

### 4. 查找相似的抽象类（仅限 GLApiProto）

如果用户选择了 GLApiProto，执行以下步骤：

1. 使用 Grep 查找所有继承 GLApiProto 的**抽象类**：

```bash
grep -r "abstract class.*extends GLApiProto" services/
```

2. 分析每个抽象类的请求和响应结构
3. 比对当前接口的请求/响应与这些抽象类的相似度
4. 如果找到相似的抽象类（建议相似度 > 60%），推荐用户继承该抽象类而非直接继承 GLApiProto

### 5. 检查响应数据模型

对于响应数据中的非基础类型对象：

1. 使用 Grep 搜索项目中已存在的数据模型类
2. 比对字段相似度（60% 以上认为相似）
3. 如果找到相似模型：
   - **完全匹配**：直接复用
   - **需要修改**：询问用户是否修改后使用
4. 避免重复定义相同的数据模型

搜索示例：

```bash
# 搜索可能的数据模型类
grep -r "class.*RoomInfo" services/ --include="*.java" --include="*.kt"
grep -r "public String ccId" services/ --include="*.java" --include="*.kt"
```

### 6. 确定文件位置

自动推断并与用户确认保存位置：

**推断规则：**

- 根据接口路径推断模块（如 `/app/cc/` → CC 相关 → feed 模块）
- 根据 Proto 父类推断模块（如 GLActProto → 可能在 activity 相关模块）
- 参考项目现有结构

**目录结构：**

```
services/[模块]/[子模块]/src/main/java/com/netease/gl/service[模块]/[子模块]/
├── proto/      # Proto 类
└── model/      # 数据模型类
```

使用 AskUserQuestion 与用户确认最终目录。

### 7. 生成代码

生成完整的 Kotlin 文件，包括：

**Proto 类：**

- 包声明
- 必要的 import 语句
- 注释（包含 API 描述和路径）
- 类定义和构造函数
- api() 方法
- packParams() 方法
- **unpackResults() 方法** - 根据返回数据的 result 字段类型选择正确的方法重载：
  - `unpackResults(results: JsonObject?)` - result 是对象时使用（最常见）
  - `unpackResults(results: JsonArray?)` - result 是数组时使用
  - `unpackResults(results: JsonPrimitive?)` - result 是基础类型时使用
- 响应字段声明（public，带默认值）

**数据模型类（如需要）：**

- 位于 model 包下
- 包含所有字段定义
- 可选：添加 Gson 序列化注解

参考 references/proto-template.md 了解标准模板结构。

### 8. 类型映射

使用 references/json-schema-mapping.md 中的映射规则：

- `string` → `String`
- `integer` → `int` 或 `long`
- `number` → `float` 或 `double`
- `boolean` → `boolean`
- `object` → 自定义类
- `array` → `List<T>`
- `enum` → `String`（带注释说明可能的值）

必填字段（`required`）在构造函数中作为参数。

## 输出示例

假设输入接口路径为 `/v1/app/cc/room/getCcRoomInfo`，请求参数包含 `ccId`（必填），响应包含 `ccId`、`roomId`、`roomType` 等字段：

**生成的 Proto 类：**

```java
package com.netease.gl.servicefeed.feed.proto;

import com.google.gson.JsonObject;
import com.netease.gl.servicenet.proto.GLApiProto;

/**
 * 获取CC房间详情
 * API: /v1/app/cc/room/getCcRoomInfo
 */
public class CCRoomInfoProto extends GLApiProto {

    private final String ccId;

    public String roomId = "";
    public String roomType = "";
    public String channelId = "";

    public CCRoomInfoProto(String ccId) {
        this.ccId = ccId;
    }

    @Override
    protected String api() {
        return "/v1/app/cc/room/getCcRoomInfo";
    }

    @Override
    protected void packParams(JsonObject params) {
        super.packParams(params);
        params.addProperty("ccId", ccId);
    }

    @Override
    protected void unpackResults(JsonObject results) {
        super.unpackResults(results);
        // 注意：results 参数已经是返回数据中的 result 部分，无需再次解析外层的 result 字段
        if (results != null) {
            try {
                if (results.has("roomId")) {
                    roomId = results.get("roomId").getAsString();
                }
                if (results.has("roomType")) {
                    roomType = results.get("roomType").getAsString();
                }
                if (results.has("channelId")) {
                    channelId = results.get("channelId").getAsString();
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }
}
```

## 参考资料

- **Proto 类模板和最佳实践**: 参见 [proto-template.md](references/proto-template.md)
- **JSON Schema 类型映射规则**: 参见 [json-schema-mapping.md](references/json-schema-mapping.md)

## 注意事项

1. 始终使用 kotlin 实现
2. 始终检查接口是否已存在，避免重复实现
3. 优先复用现有的数据模型类，避免冗余定义
4. 如果选择 GLApiProto，优先查找并推荐相似的抽象类
5. 生成的代码必须完整可编译，包含所有必要的 import
6. 遵循项目命名规范和代码风格
7. 响应字段使用 public 修饰，无需 getter 方法
8. 使用安全的默认值初始化所有响应字段
9. 解包时始终进行空值检查，避免空指针异常
10. 实现的 api 方法不要包含 /v1 前缀
11. `unpackResults` 方法中的 `results` 参数已经是服务端返回的 `result` 字段内容，直接从中读取字段即可，无需再检查或解析外层的 `result` 字段
12. 根据接口返回数据的 `result` 字段类型，选择正确的 `unpackResults` 方法重载：
    - `result` 是 JSON 对象（最常见）→ 使用 `override fun unpackResults(results: JsonObject?)`
    - `result` 是 JSON 数组 → 使用 `override fun unpackResults(results: JsonArray?)`
    - `result` 是基础类型（string/number/boolean）→ 使用 `override fun unpackResults(results: JsonPrimitive?)`
13. 在 `packParams()` 方法中，仅在需要父类参数时才调用 `super.packParams(params)`。如果接口只需要自己的参数，不要调用 `super.packParams()`，以避免传递不必要的参数给服务端
