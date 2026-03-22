# Proto 类模板参考

## 标准 Proto 类结构

```java
package com.netease.gl.service[模块].proto;

import com.google.gson.JsonObject;
import com.netease.gl.servicenet.proto.GLApiProto; // 或其他 GLBaseProto 子类

/**
 * [API 描述]
 * API: [API 路径]
 */
public class [类名]Proto extends GLApiProto {

    // 请求参数（如果有）
    private final String param1;
    private final int param2;

    // 响应字段（公开以便直接访问）
    public String resultField1 = "";
    public int resultField2 = 0;
    public [自定义模型] customObject = null;

    // 构造函数
    public [类名]Proto(String param1, int param2) {
        this.param1 = param1;
        this.param2 = param2;
    }

    @Override
    protected String api() {
        return "[API_PATH]";  // 例如："/v1/app/cc/room/getCcRoomInfo"
    }

    @Override
    protected void packParams(JsonObject params) {
        super.packParams(params);
        params.addProperty("param1", param1);
        params.addProperty("param2", param2);
    }

    @Override
    protected void unpackResults(JsonObject results) {
        super.unpackResults(results);
        if (results != null) {
            try {
                if (results.has("resultField1")) {
                    resultField1 = results.get("resultField1").getAsString();
                }
                if (results.has("resultField2")) {
                    resultField2 = results.get("resultField2").getAsInt();
                }
                if (results.has("customObject")) {
                    customObject = new Gson().fromJson(
                        results.get("customObject"),
                        [自定义模型].class
                    );
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }
}
```

## GLBaseProto 子类类型

### GLApiProto
- **Host**: 使用 `GLServers.getGLHost()`
- **适用场景**: 大部分通用 API 的默认选择
- **路径**: `services/foundation/net/src/main/sdk/com/netease/gl/servicenet/proto/GLApiProto.java`

### GLActProto
- **Host**: 使用 `GLServers.getACTHost()`
- **适用场景**: 活动相关 API
- **关键词**: act、activity、活动

### GLExpProto
- **Host**: 使用 `GLServers.getExpHost()`
- **适用场景**: 特权/实验相关 API
- **关键词**: exp、privilege、特权

### GLRechargeProto
- **Host**: 使用 `GLServers.getRechargeHost()`
- **适用场景**: 充值/支付相关 API
- **关键词**: recharge、ecard、充值、支付

### GLSearchProto
- **Host**: 使用 `GLServers.getSearchHost()`
- **适用场景**: 搜索相关 API
- **关键词**: search、搜索

### GLOpenProto
- **Host**: 使用 `GLServers.getOpenHost()`
- **适用场景**: 开放平台 API
- **关键词**: open、开放平台

### GLWalletProto
- **Host**: 使用 `GLServers.getWalletHost()`
- **适用场景**: 钱包相关 API
- **关键词**: wallet、钱包

### GLRedPacketProto
- **Host**: 使用 `GLServers.getRedPacketHost()`
- **适用场景**: 红包 API
- **关键词**: red packet、红包

### GLIncentiveProto
- **Host**: 使用 `GLServers.getIncentiveHost()`
- **适用场景**: 激励相关 API
- **关键词**: incentive、激励

### GLDesktopWidgetProto
- **Host**: 使用 `GLServers.getDesktopWidgetHost()`
- **适用场景**: 桌面小部件 API
- **关键词**: desktop widget、桌面小部件

### GlAiProto
- **Host**: 使用 `GLServers.getGodAiHost()`
- **适用场景**: AI 相关 API
- **关键词**: ai、人工智能

### GLMkeyProto
- **Host**: 使用 `GLServers.getMkeyHost()`
- **适用场景**: Mkey 相关 API
- **关键词**: mkey

## 命名规范

### Proto 类名
- 格式：`[功能][动作]Proto`
- 示例：
  - `CCVideoTokenProto` - 获取 CC 视频 token
  - `UserProfileUpdateProto` - 更新用户资料
  - `FeedListProto` - 获取动态列表

### 数据模型类名
- 格式：`[功能][实体]Model` 或 `[功能][实体]`
- 示例：
  - `CCRoomInfoModel` 或 `CCRoomInfo`
  - `UserProfileModel` 或 `UserProfile`
  - `FeedItemModel` 或 `FeedItem`

## 包结构

```
services/
└── [模块]/          # 例如：content, account, social
    └── [子模块]/   # 例如：feed, profile
        └── src/main/java/com/netease/gl/service[模块]/[子模块]/
            ├── proto/
            │   └── [功能]Proto.java
            └── model/
                └── [功能]Model.java
```

示例：
- Feed 模块：`services/content/feed/src/main/java/com/netease/gl/servicefeed/feed/proto/`
- 账号模块：`services/account/user/src/main/java/com/netease/gl/serviceaccount/user/proto/`

## 最佳实践

1. **构造函数参数**：只包含必需的请求参数
2. **响应字段**：设为 public 以便直接访问（无需 getter）
3. **默认值**：使用安全的默认值初始化响应字段（""、0、null）
4. **空值安全**：访问前始终检查 `results != null` 和 `results.has(key)`
5. **异常处理**：用 try-catch 包装解包逻辑以防止崩溃
6. **Gson 使用**：反序列化复杂对象时导入 `com.google.gson.Gson`
7. **文档注释**：包含 JavaDoc，说明 API 描述和路径