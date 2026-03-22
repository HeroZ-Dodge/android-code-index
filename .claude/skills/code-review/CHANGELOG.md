# Code Review Skill - 更新日志

## 2026-01-20 - 严格审查标准更新

### 🎯 更新目标
根据用户反馈，优化代码审查策略，避免：
1. ❌ 建议不必要的 import
2. ❌ 提出收益不大的优化建议

### ✅ 主要改进

#### 1. 新增核心原则
```markdown
⚠️ If it ain't broke, don't fix it
只标记会导致实际问题的代码（bug、crash、内存泄漏、数据丢失）
不要仅仅因为代码"可以改进"或"可以优化"就标记它
```

#### 2. 明确问题分类规则

**🔴 Critical Issues (必须报告)**
- 内存泄漏：全局单例持有 Activity/Fragment/View 引用
- 生命周期问题：Fragment 操作未检查 isAdded
- 空指针异常：!! 强制解包未验证
- **线程安全：已确认的多线程数据竞争**（需要线程分析验证）
- 资源泄漏：未关闭的流、未注销的监听器
- 数据损坏：竞态条件、更新丢失

**要求**：必须追踪执行路径并确认 bug 会发生

**⚠️ Potential Issues (高风险问题)**
- 空 catch 块：静默吞噬异常
- printStackTrace()：应使用 LogUtil
- 危险模式：生产代码中使用 !!

**不报告**：如果代码在实践中正常工作

**🚫 DO NOT Report (不是实际问题)**
- ❌ "可以使用 let/apply/with" - Kotlin 作用域函数是可选的
- ❌ "可以缓存这个值" - 除非导致性能问题
- ❌ "可以使用 sealed class" - 除非导致类型安全问题
- ❌ "可以提取为函数" - 除非导致代码重复 bug
- ❌ "可以使用 data class" - 除非缺少 equals/hashCode 导致 bug
- ❌ "变量可以是 val" - 代码风格，不是 bug
- ❌ "可以使用 early return" - 代码风格偏好
- ❌ Import 建议 - 仅当代码无法编译时

**规则**：如果修改代码不能防止 bug，就不要报告

#### 3. Import 语句策略

**严格规则**：
- ❌ **永远不要建议添加 import**，除非代码字面上无法编译
- ❌ 如果建议使用新类（如 WeakReference、AtomicInteger），检查是否已导入
- ✅ 仅在以下情况建议 import：
  1. 你推荐使用新类，**并且**
  2. 该类未导入，**并且**
  3. 当前代码没有它无法工作
- 📌 **最佳实践**：在建议中提供完全限定的类名（如 `java.lang.ref.WeakReference`）而不是建议 import

#### 4. 性能优化策略

**严格规则**：
- ❌ 不要为假设的性能问题建议优化
- ✅ 仅在可以证明实际性能影响时建议（如"这将在每次滚动时创建 10,000 个对象"）
- ❌ 不要建议缓存，除非有重复昂贵操作的证据
- ❌ 不要建议 LruCache/WeakHashMap，除非当前代码导致 OOM 或可测量的内存压力

#### 5. 新增示例

添加了 5 个 **❌ Bad Review Examples**（不应该做什么）：
1. 建议不必要的 import
2. 建议假设性优化
3. 代码风格"改进"
4. 错误的线程安全担忧
5. 过早抽象

添加了 3 个 **✅ Good Review Examples**（应该做什么）：
1. 实际内存泄漏
2. 已确认的线程安全问题
3. 生命周期违规

### 📊 预期效果

**优化前问题**：
```
❌ "Missing import: import java.lang.ref.WeakReference"
❌ "Could use LruCache to prevent OOM"
❌ "Variable could be val instead of var"
❌ "isLoading should be AtomicBoolean for thread safety"
```

**优化后**：
```
✅ 只报告会导致实际 bug 的问题
✅ 不建议 import（除非代码无法编译）
✅ 不建议假设性优化
✅ 验证线程安全问题（确认多线程访问）
```

### 🎯 核心理念

> **If it ain't broke, don't fix it**
>
> 代码审查的目标是发现 bug，不是重写代码。
> 工作正常的代码不需要"优化"或"改进"。

### 📝 影响的文件

- `.claude/skills/code-review/SKILL.md` - 主配置文件
  - 新增第 6 条原则
  - 新增问题分类规则
  - 新增 Import 策略
  - 新增性能优化策略
  - 新增正反示例

### 🔗 相关文档

- [references/judgment-tables.md](references/judgment-tables.md) - 判断标准详细表格
- [references/checklist.md](references/checklist.md) - 完整检查清单

### 🙏 致谢

感谢用户反馈，帮助我们改进代码审查质量。
