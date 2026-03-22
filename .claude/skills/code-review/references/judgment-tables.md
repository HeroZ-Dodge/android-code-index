# 判断标准参考表

本文档包含代码审查中的详细判断标准和常见误判场景。

## 线程安全判断表

| 场景 | 是否需要线程安全 | 原因 |
|------|----------------|------|
| Glide/Picasso 回调 | ❌ 否 | 主线程回调 |
| View.postDelayed() | ❌ 否 | 主线程消息队列 |
| LiveData.observe() | ❌ 否 | 主线程 Observer |
| onClick/onTouch 等 UI 回调 | ❌ 否 | 主线程事件 |
| 后台线程 + 主线程 | ✅ 是 | 真正的竞争 |
| RxJava Schedulers.io() + mainThread() | ✅ 是 | 跨线程访问 |

### 检查方法

1. 追踪变量的所有读写位置
2. 确认是否有跨线程访问
3. 特别注意：Glide、UI 回调、postDelayed 都在主线程

## 弱引用判断表

| 持有者 | 被持有对象 | 是否需要弱引用 | 原因 |
|--------|-----------|---------------|------|
| 全局单例 (object/static) | Activity | ✅ 必须 | 生命周期不匹配 |
| 全局单例 (object/static) | Fragment | ✅ 必须 | 生命周期不匹配 |
| 全局单例 (object/static) | Dialog | ✅ 必须 | 生命周期不匹配 |
| 全局单例 (object/static) | Context | ✅ 必须 | 应使用 ApplicationContext |
| Activity 成员变量 | Dialog | ❌ 否 | 生命周期一致 |
| Fragment 成员变量 | View | ❌ 否 | 生命周期一致 |
| ViewModel | Activity/Fragment | ❌ 否 | ViewModel 已处理 |

### 口诀

> "全局单例持有短生命周期对象 → 必须用弱引用"

## 常见误判场景

### 1. 原子类误用

**❌ 错误判断**：看到计数器就建议用 AtomicInteger

**✅ 正确判断**：先确认是否存在多线程竞争

**示例**：

```kotlin
// ❌ 误判为需要原子类
private var imageLoadCount = 0

fun onImageLoaded() {
    imageLoadCount++  // 在 Glide 回调中，实际都在主线程
}
```

**正确分析**：
- Glide 的回调在主线程执行
- 不存在多线程竞争
- 不需要 AtomicInteger

### 2. 弱引用误用

**❌ 错误判断**：看到单例持有引用就建议改成弱引用

**✅ 正确判断**：判断持有者和被持有对象的生命周期关系

**示例**：

```kotlin
// ✅ 需要弱引用（全局单例持有 Dialog）
object DialogManager {
    private var dialog: Dialog? = null  // ❌ 应该用 WeakReference<Dialog>
}

// ❌ 不需要弱引用（Activity 成员持有 Dialog）
class MyActivity : Activity() {
    private var dialog: Dialog? = null  // ✅ 生命周期一致，不需要弱引用
}
```

### 3. 同步锁误用

**❌ 错误判断**：看到共享变量就建议加锁

**✅ 正确判断**：确认是否在多个线程中访问

**示例**：

```kotlin
// ❌ 误判为需要加锁
private val listeners = mutableListOf<Listener>()

fun addListener(listener: Listener) {
    listeners.add(listener)  // 如果都在主线程调用，不需要同步
}
```

## 空值安全判断

### 需要检查的场景

| 场景 | 检查方式 | 原因 |
|------|---------|------|
| 可空类型 | 使用 **?.** 或明确检查 | Kotlin null-safety |
| 强制解包 **!!** | 需要充分理由和注释 | 可能抛出 NPE |
| "null" 字符串 | 检查 `"null".equals(str)` | 数据序列化问题 |
| 空集合 | 使用 `isNullOrEmpty()` | 避免 NPE |

### 常见错误

```kotlin
// ❌ 错误
val name = user.name!!  // 无理由的强制解包

// ✅ 正确
val name = user.name ?: "Unknown"

// ❌ 错误
if (list.size > 0)  // 如果 list 为 null 会 NPE

// ✅ 正确
if (!list.isNullOrEmpty())
```

## 生命周期检查清单

### Fragment 操作

```kotlin
// ❌ 错误：未检查生命周期
fun updateUI() {
    binding.textView.text = "Hello"  // Fragment 可能已 detach
}

// ✅ 正确：检查 isAdded
fun updateUI() {
    if (isAdded) {
        binding.textView.text = "Hello"
    }
}
```

### 异步回调

```kotlin
// ❌ 错误：异步回调未检查生命周期
viewModel.loadData { data ->
    binding.textView.text = data  // 可能已销毁
}

// ✅ 正确：检查生命周期
viewModel.loadData { data ->
    if (isResumed) {
        binding.textView.text = data
    }
}
```

### onDestroyView 清理

```kotlin
// ✅ 必须清理的内容
override fun onDestroyView() {
    super.onDestroyView()
    // 清理监听器
    viewModel.data.removeObservers(viewLifecycleOwner)
    // 清理定时器
    handler.removeCallbacksAndMessages(null)
    // 清理 binding
    _binding = null
}
```
