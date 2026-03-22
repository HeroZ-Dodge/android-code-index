


# 本地代码知识库服务搭建方案

## 一、方案全景对比

### 1.1 主流方案矩阵

| 方案 | 索引类型 | 搜索速度 | 语义理解 | Android/Kotlin 支持 | 部署复杂度 | 适合场景 |
|------|---------|---------|---------|-------------------|-----------|---------|
| **Sourcegraph (本地)** | 符号+全文+正则 | ⚡ 亚秒 | ⭐⭐ | ✅ 优秀 | 中 | 中大型团队，多仓库 |
| **Zoekt** | Trigram 全文索引 | ⚡ 亚秒 | ⭐ | ✅ 良好 | 低 | 轻量快速全文搜索 |
| **Ctags/Gtags + API** | 符号索引 | ⚡ 亚秒 | ⭐ | ✅ 良好 | 低 | 函数/类签名精准查找 |
| **Tree-sitter + 自建** | AST 结构化索引 | ⚡ 亚秒 | ⭐⭐⭐ | ✅ 优秀 | 中高 | 深度结构化，最灵活 |
| **Embedding 向量库** | 语义向量 | 快 | ⭐⭐⭐⭐ | ✅ 通用 | 中 | 模糊语义搜索 |
| **Lsif/Scip + DB** | 编译级符号图 | ⚡ 亚秒 | ⭐⭐⭐ | ⚠️ 需配置 | 高 | 精确跳转/引用关系 |



## 二、方案 ：Tree-sitter + SQLite 结构化索引（⭐ 推荐首选）



# Android 项目全文件类型索引策略

## 一、核心判断框架

> **索引决策原则：这类文件在AI开发时，是否会被"需要先查再写"？**

```
                    AI 开发时查询频率
                    高 ──────────────── 低
                    │                    │
    复现成本  高 ── │  ✅ 必须索引       │ ⚠️ 按需索引  │
    (重写代价)      │  函数签名/接口协议  │  主题/样式    │
                    │                    │               │
              低 ── │  ✅ 建议索引       │ ❌ 不索引     │
                    │  布局ID/字符串资源  │  图片/raw资源  │
                    └────────────────────┴───────────────┘
```

## 二、逐类文件分析

### 2.1 完整分类决策表

| 文件类型 | 索引? | 优先级 | 索引什么 | 理由 |
|---------|------|--------|---------|------|
| **Kotlin 源码 (.kt)** | ✅ 必须 | P0 | 函数签名、类、接口、扩展函数 | AI 编码核心依赖 |
| **Java 源码 (.java)** | ✅ 必须 | P0 | 函数签名、类、接口 | 遗留代码大量存在 |
| **布局 XML** | ✅ 建议 | P1 | View ID、自定义组件引用、include 关系 | 避免 ID 冲突、复用已有布局 |
| **strings.xml** | ✅ 建议 | P1 | 字符串 key-value 对 | 避免重复定义、保持命名一致 |
| **AndroidManifest.xml** | ✅ 建议 | P1 | Activity/Service/Permission 注册清单 | AI 需知道哪些组件已注册 |
| **styles/themes.xml** | ⚠️ 按需 | P2 | style 名称、parent 关系 | 避免重复样式、保持 UI 一致 |
| **dimens.xml** | ⚠️ 按需 | P2 | 尺寸 key-value | 复用已有尺寸定义 |
| **colors.xml** | ⚠️ 按需 | P2 | 颜色 key-value | 保持配色一致 |
| **Gradle 配置** | ⚠️ 按需 | P2 | 依赖列表、版本号、build 配置 | 避免重复引入依赖 |
| **drawable XML** | ❌ 低优 | P3 | 文件名即可 | 仅需知道"有没有"，不需要内容 |
| **图片/音频/字体** | ❌ 不索引 | - | - | 二进制文件，无结构化信息 |
| **生成代码 (build/)** | ❌ 不索引 | - | - | 自动生成，会变 |
| **测试代码** | ❌ 不索引 | P3 | 测试类名和方法名 | 了解覆盖情况 |

### 2.2 为什么布局和资源文件值得索引

```
场景：AI 要给新页面写一个"用户信息卡片"

❌ 不索引资源文件时：
   AI → 新建 item_user_card.xml → 新定义 @dimen/card_margin → 新定义 @color/card_bg
   结果：和项目已有的 layout_user_info.xml 重复，尺寸颜色不统一

✅ 索引资源文件后：
   AI → 查到已有 layout_user_info.xml (含 @id/tv_name, @id/iv_avatar)
      → 查到已有 @dimen/margin_card_standard = 16dp
      → 查到已有 @color/surface_primary = #FFFFFF
   结果：直接复用或基于已有布局扩展，UI 一致性好
```

---

## 三、分层索引架构设计

```
┌───────────────────────────────────────────────────────────┐
│                     查询 API 层                            │
│       
├───────────────────────────────────────────────────────────┤
│                    索引存储 (SQLite)                       │
│                                                           │
│  ┌─ P0 代码索引 ──────────────────────────────────────┐   │
│  │  functions (Kotlin + Java)                         │   │
│  │  classes   (Kotlin + Java)                         │   │
│  │  interfaces (Kotlin + Java)                        │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─ P1 资源索引 ──────────────────────────────────────┐   │
│  │  layouts     (文件名, View ID 列表, include 关系)   │   │
│  │  strings     (key → value 映射)                    │   │
│  │  manifest    (组件注册清单)                          │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─ P2 配置索引 ──────────────────────────────────────┐   │
│  │  styles      (名称, parent 继承链)                  │   │
│  │  colors      (key → value)                         │   │
│  │  dimens      (key → value)                         │   │
│  │  gradle_deps (依赖库清单 + 版本)                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─ P3 资产清单 ──────────────────────────────────────┐   │
│  │  drawables   (仅文件名清单)                         │   │
│  │  fonts       (仅文件名清单)                         │   │
│  └────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
```

```

┌────────────────────────┬────────────────────────┬────────────────────┐
│ 接口                    │ 用途                    │ 优先级              │
├────────────────────────┼────────────────────────┼────────────────────┤
│ search(keyword)        │ 全文搜索所有符号类型      │ P0 必须             │
│ find_function(...)     │ 按条件查函数             │ P0 必须             │
│ find_class(...)        │ 按条件查类               │ P0 必须             │
│ find_interface(...)    │ 按条件查接口             │ P0 必须             │
│ get_file_symbols(path) │ 获取某文件的所有符号      │ P0 必须             │
│ get_module_overview()  │ 某模块的类/函数概览       │ P0 必须             │
├────────────────────────┼────────────────────────┼────────────────────┤
│ find_layout(...)       │ 查布局文件               │ P1                 │
│ find_string(...)       │ 查字符串资源             │ P1                 │
│ find_component(...)    │ 查 Manifest 组件         │ P1                 │
├────────────────────────┼────────────────────────┼────────────────────┤
│ get_inheritance(cls)   │ 查继承链                 │ P1                 │
│ get_implementations()  │ 查接口实现类             │ P1                 │
│ get_class_api(cls)     │ 查类的完整方法列表        │ P1                 │
├────────────────────────┼────────────────────────┼────────────────────┤
│ find_style(...)        │ 查样式                   │ P2                 │
│ find_color(...)        │ 查颜色                   │ P2                 │
│ find_navigation(...)   │ 查导航图                 │ P2                 │
│ find_dependency(...)   │ 查 Gradle 依赖           │ P2                 │
├────────────────────────┼────────────────────────┼────────────────────┤
│ project_stats()        │ 项目整体统计             │ P2                 │
└────────────────────────┴────────────────────────┴────────────────────┘

```



### 2.2 完整实现
## 1.1 创建代码索引项目结构

## 1.2 创建 Python 虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
# Windows: venv\Scripts\activate
```

## 1.3 安装依赖

**`requirements.txt`**：

```txt
# AST 解析
tree-sitter==0.24.0
tree-sitter-kotlin==0.1.0
tree-sitter-java==0.23.5

# Web API
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.9.0

# 文件监听（增量索引）
watchdog==4.0.0

# 工具
rich==13.7.0
click==8.1.7
```

```bash
pip install -r requirements.txt
```

> **如果 `tree-sitter-kotlin` 安装失败**，替代方案：
> ```bash
> pip install tree-sitter-languages
> ```
> 后续代码中会提供兼容写法。

## 1.4 全局配置文件

**`src/config.py`**：


## 1.5 验证环境

创建 **`scripts/verify_env.py`**：

```python
#!/usr/bin/env python3
"""验证所有依赖是否正确安装"""

def check():
    results = []

    # 1. tree-sitter
    try:
        from tree_sitter import Language, Parser
        results.append(("tree-sitter", "✅"))
    except ImportError as e:
        results.append(("tree-sitter", f"❌ {e}"))

    # 2. tree-sitter-kotlin
    try:
        import tree_sitter_kotlin as tskotlin
        lang = Language(tskotlin.language())
        results.append(("tree-sitter-kotlin", "✅"))
    except ImportError:
        try:
            from tree_sitter_languages import get_language
            lang = get_language("kotlin")
            results.append(("tree-sitter-kotlin (via tree-sitter-languages)", "✅"))
        except ImportError as e:
            results.append(("tree-sitter-kotlin", f"❌ {e}"))

    # 3. tree-sitter-java
    try:
        import tree_sitter_java as tsjava
        lang = Language(tsjava.language())
        results.append(("tree-sitter-java", "✅"))
    except ImportError:
        try:
            from tree_sitter_languages import get_language
            lang = get_language("java")
            results.append(("tree-sitter-java (via tree-sitter-languages)", "✅"))
        except ImportError as e:
            results.append(("tree-sitter-java", f"❌ {e}"))

    # 4. FastAPI
    try:
        import fastapi
        results.append(("fastapi", f"✅ v{fastapi.__version__}"))
    except ImportError as e:
        results.append(("fastapi", f"❌ {e}"))

    # 5. uvicorn
    try:
        import uvicorn
        results.append(("uvicorn", "✅"))
    except ImportError as e:
        results.append(("uvicorn", f"❌ {e}"))

    # 6. watchdog
    try:
        import watchdog
        results.append(("watchdog", "✅"))
    except ImportError as e:
        results.append(("watchdog", f"❌ {e}"))

    # 7. rich
    try:
        from rich.console import Console
        results.append(("rich", "✅"))
    except ImportError as e:
        results.append(("rich", f"❌ {e}"))

    # 8. SQLite FTS5
    import sqlite3
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE VIRTUAL TABLE t USING fts5(content)")
        conn.execute("DROP TABLE t")
        results.append(("SQLite FTS5", "✅"))
    except Exception as e:
        results.append(("SQLite FTS5", f"❌ {e}"))
    finally:
        conn.close()

    # 输出
    print("\n" + "=" * 50)
    print("  环境检查结果")
    print("=" * 50)
    all_ok = True
    for name, status in results:
        print(f"  {status}  {name}")
        if "❌" in status:
            all_ok = False
    print("=" * 50)

    if all_ok:
        print("  🎉 所有依赖就绪，可以开始！\n")
    else:
        print("  ⚠️  请修复上述问题后继续\n")

    return all_ok


if __name__ == "__main__":
    check()
```

运行验证：

```bash
python scripts/verify_env.py
```

期望输出：

```
==================================================
  环境检查结果
==================================================
  ✅  tree-sitter
  ✅  tree-sitter-kotlin
  ✅  tree-sitter-java
  ✅  fastapi v0.115.0
  ✅  uvicorn
  ✅  watchdog
  ✅  rich
  ✅  SQLite FTS5
==================================================
  🎉 所有依赖就绪，可以开始！
```

---

