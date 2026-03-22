# 代码审查 Checklist

完整的代码审查检查清单，按优先级分类。

## 🔴 必查项（高优先级）

### 线程安全

- [ ] 是否存在**真正的**多线程并发访问？
- [ ] 图片加载回调（Glide/Picasso）是否误用了原子类？
- [ ] UI 回调（onClick、postDelayed、LiveData.observe）是否误用了原子类？
- [ ] 后台线程 + 主线程访问共享变量是否使用了同步机制？

**判断标准**：
- ✅ 需要原子类：后台线程写入 + 主线程读取
- ❌ 不需要原子类：所有操作都在主线程（UI 回调、图片加载回调等）

### 内存泄漏

- [ ] 全局单例是否持有 Activity/Fragment/Dialog/Context？
- [ ] 是否使用了 WeakReference？
- [ ] Dialog/Activity 生命周期管理是否正确？

**判断标准**：
- ✅ 需要弱引用：全局单例（object/static）持有短生命周期对象
- ❌ 不需要弱引用：Activity/Fragment 成员变量持有 Dialog

### 空值安全

- [ ] 可空类型是否使用了 **?.** 或明确的空值检查？
- [ ] 是否有 **!!** 强制解包（需要有充分理由）？
- [ ] 是否检查了 "null" 字符串（数据序列化问题）？

### 生命周期

- [ ] Fragment 操作前是否检查了 **isAdded/isResumed**？
- [ ] 异步回调中是否检查了生命周期状态？
- [ ] **onDestroyView()** 是否清理了所有监听器和资源？

## ⚠️ 中频问题

- [ ] RecyclerView position 是否检查了 **< 0** 的情况？
- [ ] RecyclerView **onBindViewHolder()** 开头是否重置了所有状态？
- [ ] debounce 延迟时间是否合理（消息类 ≤1500ms）？
- [ ] **Observable.just()** 是否正确处理线程调度？

## 🟡 代码质量

- [ ] 异常处理是否捕获了**具体的异常类型**（而非泛型 Exception）？
- [ ] catch 块是否使用了 LogUtil 而非 printStackTrace()？
- [ ] 是否有未使用的变量、方法、import？
- [ ] 命名是否符合项目规范（驼峰命名、有意义的名称）？

## 🟢 性能优化（可选）

- [ ] 是否有不必要的对象创建（如循环中创建对象）？
- [ ] 是否有重复的数据库/网络查询？
- [ ] 图片加载是否使用了合适的缓存策略？
- [ ] 列表滚动是否流畅（避免在 onBindViewHolder 中做耗时操作）？

## RecyclerView 专项检查

### position 检查

```kotlin
// ❌ 错误：未检查 position
override fun onBindViewHolder(holder: ViewHolder, position: Int) {
    val item = data[position]  // 如果 position < 0 会崩溃
}

// ✅ 正确：检查 position
override fun onBindViewHolder(holder: ViewHolder, position: Int) {
    if (position < 0 || position >= data.size) return
    val item = data[position]
}
```

### 状态重置

```kotlin
// ❌ 错误：未重置状态
override fun onBindViewHolder(holder: ViewHolder, position: Int) {
    val item = data[position]
    if (item.isHighlight) {
        holder.textView.setTextColor(Color.RED)  // 其他 item 会显示之前的颜色
    }
}

// ✅ 正确：开头重置所有状态
override fun onBindViewHolder(holder: ViewHolder, position: Int) {
    // 重置状态
    holder.textView.setTextColor(Color.BLACK)
    holder.imageView.visibility = View.GONE

    val item = data[position]
    if (item.isHighlight) {
        holder.textView.setTextColor(Color.RED)
    }
}
```

## debounce 延迟检查

### 常见场景的推荐延迟

| 场景 | 推荐延迟 | 原因 |
|------|---------|------|
| 搜索输入 | 300-500ms | 用户输入速度 |
| 按钮防抖 | 500-1000ms | 防止重复点击 |
| 消息发送 | ≤1500ms | 用户体验 |
| 滚动加载 | 200-300ms | 滚动流畅性 |

```kotlin
// ❌ 错误：消息发送延迟过长
button.setOnDebounceClickListener(3000) {  // 3秒太长
    sendMessage()
}

// ✅ 正确：合理延迟
button.setOnDebounceClickListener(1000) {
    sendMessage()
}
```

## RxJava 线程调度检查

### Observable.just() 陷阱

```kotlin
// ❌ 错误：数据在订阅前就已创建
fun loadData(): Observable<Data> {
    val data = heavyOperation()  // 在主线程执行！
    return Observable.just(data)
        .subscribeOn(Schedulers.io())  // 无效
}

// ✅ 正确：使用 fromCallable
fun loadData(): Observable<Data> {
    return Observable.fromCallable {
        heavyOperation()  // 在 io 线程执行
    }.subscribeOn(Schedulers.io())
}
```
