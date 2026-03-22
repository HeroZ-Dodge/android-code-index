---
name: ulink-parser
description: 在大神项目中添加新的 ulink 解析功能，自动完成 Adapter、Handler 创建和注册。当用户需要添加新的 ulink action、实现新的 scheme 处理逻辑、提到 "ulink"、"scheme"、"router" 相关的功能开发时使用。
---

# ULink 解析器

## 说明

用于在大神项目中添加新的 ulink 解析功能。自动完成所有必要的文件修改，包括创建 Adapter、Handler、注册相关组件等。

## 工作流程

### 1. 收集需求信息（主模型执行）

询问用户：action 名称、参数列表、处理逻辑、是否需要登录验证。

### 2. 查找现有代码和可用 ID（委托 haiku）

**使用 Task 工具委托给 haiku 模型执行**：

Task(
  subagent_type="general-purpose",
  model="haiku",
  prompt="""
  1. 在 SchemeConstant 中搜索 action "{actionName}" 是否已存在
  2. 读取 RouterAction 文件，找到当前最大的 RouterId 值
  3. 确认 GlRouterChainFactory 文件路径
  返回 JSON: {"exists": true/false, "maxRouterId": N, "factoryPath": "..."}
  """
)

### 3. 实现步骤（主模型执行）

#### 步骤 1：在 SchemeConstant 定义 action
- 查找 `SchemeConstant` 接口文件
- 添加新的常量定义：
```java
/**
 * @see "相关文档链接"
 * [功能描述]
 */
String [ACTION_NAME] = "[actionValue]";
```

#### 步骤 2：创建 AbsSchemeAdapter 实现类
- 创建新文件：`Scheme[功能名]Adapter.kt`
- 实现模板：
```kotlin
class Scheme[功能名]Adapter : AbsSchemeAdapter() {
    override fun actionType(): String {
        return SchemeConstant.[ACTION_NAME]
    }

    override fun parse(uri: Uri): GlRouterParams {
        val params = GlRouterParams(RouterAction.[ROUTER_ID], uri.toString())
        val extMap: MutableMap<String, String?> = ArrayMap([参数数量])
        listOf([参数列表]).forEach { key ->
            extMap[key] = uri.getQueryParameter(key)
        }
        params.extStr = JsonUtil.toJsonString(extMap)
        return params
    }
}
```

#### 步骤 3：注册 Adapter
- 文件：`GlRouterChainFactory`
- 方法：`createSchemeChain()`
- 在 `SchemeUnsupportedAdapter()` 之前添加：
```java
adapterChain.addAdapter(new Scheme[功能名]Adapter());
```

#### 步骤 4：在 RouterAction 添加 RouterId
- 文件：`RouterAction` 注解类
- 添加新的路由 ID：
```java
int [ROUTER_NAME] = [下一个可用ID]; // [功能描述]
```

#### 步骤 5：创建 Handler 实现类
- 创建新文件：`[功能名]Handler.kt`
- 基类选择：
  - 需要登录验证：继承 `SupportAuthRouterHandler`
  - 不需要登录：继承 `AbsRouterHandler`
- 实现模板：
```kotlin
class [功能名]Handler : SupportAuthRouterHandler() {
    private val tag = "[功能名]Handler"

    override fun actionType(): Int {
        return RouterAction.[ROUTER_NAME]
    }

    override fun handleInternal(context: Context, params: GlRouterParams) {
        val map: Map<String, String>? = JsonUtil.fromJson(
            params.extStr,
            object : TypeToken<Map<String, String>>() {}
        )

        if (map != null) {
            // 获取参数
            val [参数1] = map["[参数1]"]
            val [参数2] = map["[参数2]"]

            // 实现业务逻辑
            [具体业务逻辑实现]
        }
    }
}
```

#### 步骤 6：注册 Handler
- 文件：`GlRouterChainFactory`
- 方法：`createHandlerChain()`
- 添加：
```java
handlerChain.addHandler(new [功能名]Handler());
```

### 4. 验证清单

完成实现后，确保：
- [ ] SchemeConstant 中定义了 action 常量
- [ ] 创建了 Adapter 类并正确实现了 actionType() 和 parse() 方法
- [ ] 在 GlRouterChainFactory.createSchemeChain() 中注册了 Adapter
- [ ] RouterAction 中添加了对应的 RouterId
- [ ] 创建了 Handler 类并实现了业务逻辑
- [ ] 在 GlRouterChainFactory.createHandlerChain() 中注册了 Handler

### 5. 测试示例

生成测试 URL 格式：
```
https://app.16163.com/ds/ulinks/?action=[actionName]&[param1]=[value1]&[param2]=[value2]
```

## 注意事项

1. 确保 action 名称在整个项目中唯一
2. RouterId 值不能与现有的重复，查找最大值并加 1
3. 需要登录验证的功能必须继承 `SupportAuthRouterHandler`
4. 参数获取时要进行空值判断
5. 异常处理要添加适当的日志和用户提示

## 相关文件路径模式

- Adapter 文件：`*/scheme/adapter/` 目录下
- Handler 文件：`*/router/handler/` 目录下
- SchemeConstant：`*/constant/` 或 `*/scheme/` 目录下
- RouterAction：`*/router/` 目录下
- GlRouterChainFactory：`*/router/` 目录下

