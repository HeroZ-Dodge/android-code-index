# 业务逻辑分析指南

深入分析代码变更时，重点关注以下业务逻辑类型。

## 文件分类

| 路径模式 | 功能模块 |
|---------|---------|
| `**/activity/*` | 页面 |
| `**/fragment/*` | 页面 |
| `**/viewmodel/*` | 业务逻辑 |
| `**/adapter/*` | 列表展示 |
| `**/helper/*`, `**/manager/*` | 工具/管理类 |
| `**/entity/*`, `**/bean/*` | 数据模型 |
| `**/view/*`, `**/widget/*` | 自定义视图 |
| `**/dialog/*`, `**/popup/*` | 弹窗 |
| `**/res/layout/*` | UI布局 |
| `**/res/drawable*` | 图片资源 |
| `**/res/values/*` | 文案/样式 |

## 关键逻辑类型

### 1. 条件判断逻辑

什么条件下显示/隐藏、启用/禁用。

**代码示例**：
```kotlin
if (hasUpdate || hasPending || hasPaused) showRedDot()
```

**输出示例**：
> 红点显示条件 = 有待更新游戏 OR 有待安装游戏 OR 有暂停下载

### 2. 排序/过滤逻辑

列表如何排序、哪些数据会被过滤。

**代码示例**：
```kotlin
sortedByDescending { it.downloadTime }.filter { it.isInstalled }
```

**输出示例**：
> 已安装游戏按下载时间倒序排列

### 3. 数据匹配/关联规则

数据如何匹配、关联、去重。

**代码示例**：
```kotlin
find { it.packageName == installedPkg }  // 官服包完全匹配
Regex(pattern).matches(pkg)              // 渠道包正则匹配
```

**输出示例**：
> 官服包按包名完全匹配；渠道包优先完全匹配，其次正则匹配；同一游戏官服和渠道包都安装时只显示官服

### 4. 状态转换逻辑

状态如何变化、触发条件是什么。

**代码示例**：
```kotlin
when (status) {
    DOWNLOADING -> showProgress()
    PAUSED -> showResume()
}
```

**输出示例**：
> 下载中显示进度条，暂停时显示继续按钮

### 5. 优先级逻辑

多个条件同时满足时的处理规则。

**代码示例**：
```kotlin
candidates.sortedByDescending { it.priority }.firstOrNull()
```

**输出示例**：
> 多个红点同时存在时，显示优先级最高的

### 6. 分组/聚合逻辑

数据如何分组展示。

**代码示例**：
```kotlin
groupBy { it.moduleType }  // UPDATABLE, DOWNLOADING, INSTALLED
```

**输出示例**：
> 游戏列表按「推荐更新」「下载中」「已安装」三组展示

### 7. 缓存/加载策略

数据如何缓存、何时刷新。

**代码示例**：
```kotlin
if (cache != null) {
    asyncRefresh()
    return cache
} else {
    syncLoad()
}
```

**输出示例**：
> 有缓存时直接使用并异步刷新，无缓存时同步请求

### 8. 边界处理逻辑

空数据、异常、边界值的处理。

**代码示例**：
```kotlin
if (list.isEmpty()) showEmptyView()
```

**输出示例**：
> 无游戏时显示空状态页

## 分析原则

1. **用业务语言描述**：理解代码改动对应的业务功能变化
2. **关注 UI 交互**：按钮、页面、弹窗的变化
3. **关注数据流转**：接口、字段、状态的变化
4. **注意 ABTest**：实验分组对应的功能差异
5. **理解埋点**：用户行为追踪的变化
