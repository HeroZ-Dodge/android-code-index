# 模块依赖关系图（SDK vs Impl）

## 📋 文档说明

本文档基于真实的依赖配置，**明确区分 SDK 层依赖和 Impl 层依赖**。

**关键概念**：
- **SDK 依赖** = 接口间的依赖关系（在 `gradlescript/component.gradle` 中配置）
- **Impl 依赖** = 实现代码的实际依赖（在各模块的 `build.gradle` 中配置）

**数据来源**:
- SDK 依赖: `gradlescript/component.gradle`
- Impl 依赖: `各模块/build.gradle`

**最后更新**: 2025-10-24

---

## 一、核心概念解析

### 1.1 SDK/Impl 分离架构

```
┌─────────────────────────────────────────────────┐
│                 模块结构                         │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────────────────────────┐      │
│  │  SDK (src/main/sdk/)                 │      │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │      │
│  │  • 对外接口定义 (IXxxManager)       │      │
│  │  • 数据模型 (Entity, Model)         │      │
│  │  • 事件定义 (Event)                 │      │
│  │  • 常量定义 (Constant)              │      │
│  │                                      │      │
│  │  🔒 只能依赖其他模块的 SDK           │      │
│  │  📝 在 component.gradle 中配置       │      │
│  │  📦 编译为 JAR 包发布                │      │
│  └──────────────────────────────────────┘      │
│                     ↑                           │
│                     │ 实现                      │
│  ┌──────────────────────────────────────┐      │
│  │  Impl (src/main/java/)               │      │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │      │
│  │  • 接口实现 (XxxManagerImpl)        │      │
│  │  • 业务逻辑                          │      │
│  │  • UI 组件 (Activity, Fragment)     │      │
│  │  • ViewModel, Repository            │      │
│  │                                      │      │
│  │  ✅ 可以依赖本模块的 SDK             │      │
│  │  ✅ 可以依赖其他模块的 SDK           │      │
│  │  ✅ 可以依赖外部库                   │      │
│  │  📝 在模块自己的 build.gradle 中配置 │      │
│  └──────────────────────────────────────┘      │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 1.2 依赖方式对比

| 依赖类型 | 配置位置 | 语法 | 含义 | 编译产物 |
|---------|---------|------|------|---------|
| **SDK 依赖** | `gradlescript/component.gradle` | `implementation component(':moduleA')` | SDK 依赖另一个模块的 SDK | JAR 包 |
| **Impl 依赖（推荐）** | `模块/build.gradle` | `implementation component(':moduleB')` | Impl 依赖另一个模块的 SDK | JAR 包 |
| **Impl 依赖（不推荐）** | `模块/build.gradle` | `implementation project(':moduleC')` | Impl 依赖另一个模块的 SDK+Impl | 源码 |

**⚠️ 重要规则**：
- ✅ **推荐**: 使用 `component()` 依赖 SDK
- ❌ **不推荐**: 使用 `project()` 依赖完整源码（破坏 SDK/Impl 分离）

---

## 二、项目依赖现状分析

### 2.1 关键发现

根据自动分析脚本 `.AI/scripts/analyze_sdk_impl_dependencies.py` 的扫描结果：

📊 **统计数据**：
- SDK 依赖配置：30 个模块
- Impl 层代码：31 个模块
- **⚠️ 使用 `project()` 的模块：28 个**

### 2.2 project() 使用情况（需要改进）

发现 **28 个模块**使用了 `implementation project()`，违反了项目规范：

#### Top 10 违规最多的模块

| 排名 | 模块 | project() 依赖数量 | 主要 project() 依赖 |
|------|------|------------------|-------------------|
| 1 | main | 8 | compfeed, compsetting, libim, serviceaccount, servicebase, serviceim, servicemedia |
| 2 | serviceim | 4 | libim, libmediabase, servicebase, servicemedia |
| 3 | serviceshortvideo | 3 | libmediabase, servicebase, servicemedia |
| 4 | compfeed | 3 | servicebase, serviceim, servicemedia |
| 5 | servicecc | 3 | plugin-ccsdk, service-plugin-host-common, servicebase |
| 6 | compsetting | 3 | compfeed, compmkey, servicebase |
| 7+ | 其他22个模块 | 1-2 | 主要是 servicebase |

**🔴 最严重问题**：
- **servicebase** 被 25 个模块通过 `project()` 方式依赖
- **servicemedia** 被 6 个模块通过 `project()` 方式依赖
- **serviceim** 被 2 个模块通过 `project()` 方式依赖

**💡 改进建议**：
```groovy
// ❌ 当前（错误）
implementation project(':servicebase')

// ✅ 应该改为
implementation component(':servicebase')
```

---

## 三、SDK 依赖层级（接口依赖）

基于 `gradlescript/component.gradle` 中的 `implementation component()` 配置：

### 3.1 SDK 依赖层级总览

```
L0 (零依赖 SDK):
├── serviceruntime        - 运行时环境
├── serviceaccount        - 账号管理 ⭐ (被依赖9次)
├── servicedebug          - 调试工具
├── servicecrash          - 崩溃收集
├── serviceqrcode         - 二维码
├── serviceskin           - 皮肤换肤
├── servicehotfixrobust   - 热修复
├── servicern             - RN支持
└── service-plugin-host   - 插件宿主

L1:
└── servicebase ⭐⭐⭐ (被依赖14次)
    └── → serviceruntime

L2:
├── servicenet ⭐⭐⭐ (被依赖17次)
│   └── → serviceaccount, servicebase, servicedebug, serviceruntime
└── service-ipc
    └── → serviceaccount, servicebase

L3:
└── serviceconfig ⭐⭐ (被依赖12次)
    └── → servicebase, servicedebug, servicenet, serviceruntime

L4:
├── serviceim ⭐⭐ (被依赖9次)
│   └── → serviceaccount, servicebase, serviceconfig, servicenet, serviceruntime
├── servicelog
│   └── → serviceconfig, servicenet, serviceruntime
├── serviceupdate
│   └── → serviceconfig
└── compsetting
    └── → serviceaccount, servicebase, serviceconfig, servicenet, serviceruntime

L5:
├── servicecc (被依赖2次)
│   └── → servicebase, serviceconfig, serviceim, servicenet
└── servicepush
    └── → servicebase, serviceim, servicenet

L6:
├── serviceuser (被依赖若干次)
│   └── → serviceaccount, servicebase, serviceconfig, servicefeed, servicegamecenter, serviceim, servicenet, serviceruntime
└── servicefeed ⭐⭐ (被依赖11次)
    └── → serviceaccount, servicebase, servicecc, serviceconfig, serviceim, servicenet, serviceruntime

L7:
├── serviceadmin (新增模块)
│   └── → servicebase, serviceconfig, servicefeed, servicenet, serviceuser
├── servicecbg
│   └── → serviceconfig, servicefeed, servicenet
├── serviceh5 (被依赖5次)
│   └── → serviceaccount, servicebase, serviceconfig, servicefeed, serviceim, servicenet, serviceqrcode
├── servicemedia
│   └── → servicebase, servicefeed, serviceim
├── servicemusic
│   └── → servicefeed, servicenet
├── serviceoauth
│   └── → serviceaccount, servicebase, servicefeed, serviceim, servicenet
└── servicewallet
    └── → serviceaccount, servicefeed, servicenet

L8:
├── compfeed
│   └── → serviceadmin, servicebase, servicecbg, servicecc, serviceconfig, servicefeed, serviceim, servicenet, serviceuser
├── compmkey
│   └── → serviceaccount, servicebase, servicefeed, serviceh5, servicenet, serviceruntime, servicewallet
├── serviceappwidget
│   └── → serviceh5, servicenet, serviceruntime
├── servicesandbox
│   └── → serviceconfig, serviceh5
├── serviceshare
│   └── → servicebase, servicefeed, serviceh5, serviceim
└── serviceshortvideo
    └── → servicefeed, serviceh5, servicemusic, servicenet

L9:
└── servicegamecenter
    └── → serviceconfig, servicefeed, serviceim, servicenet, servicesandbox

L10:
└── servicecloudgame
    └── → serviceconfig, servicegamecenter
```

### 3.2 SDK 被依赖排行（Top 10）

| 排名 | 模块 | 层级 | SDK 被依赖次数 | 说明 |
|------|------|------|--------------|------|
| 1 | **servicenet** | L2 | 17 | 网络请求基础设施 |
| 2 | **servicebase** | L1 | 14 | 基础服务框架 |
| 3 | **serviceconfig** | L3 | 12 | 配置管理 |
| 4 | **servicefeed** | L6 | 11 | 动态内容服务 |
| 5 | **serviceim** | L4 | 9 | 即时通讯 |
| 6 | **serviceaccount** | L0 | 9 | 账号管理 |
| 7 | **serviceruntime** | L0 | 9 | 运行时环境 |
| 8 | **serviceh5** | L7 | 5 | H5容器 |
| 9 | **serviceadmin** | L7 | 新增 | 管理员服务 |
| 10 | **serviceuser** | L6 | 新增 | 用户服务 |
| 11 | **servicecc** | L5 | 2 | CC直播 |
| 12 | **servicedebug** | L0 | 2 | 调试工具 |

---

## 四、Impl 实际依赖（完整依赖）

### 4.1 Impl 层依赖特点

Impl 层的实际依赖通常比 SDK 层更多，因为：

1. **Impl 可以依赖更多模块的 SDK**（业务实现需要）
2. **Impl 需要依赖 UI 库、工具库**（SDK 不需要）
3. **Impl 之间可能有额外的协作**（通过 SDK 接口）

### 4.2 Impl 依赖数量对比

| 模块 | SDK 依赖数 | Impl 总依赖数 | 差值 | 说明 |
|------|----------|-------------|------|------|
| **compfeed** | 9 | 32+ | +23 | 组件层，新增依赖 service-admin 和 service-user |
| **serviceim** | 5 | 24 | +19 | IM 实现复杂，依赖多 |
| **serviceh5** | 7 | 20 | +13 | H5 容器需要多个服务支持 |
| **serviceaccount** | 0 | 18 | +18 | SDK 零依赖，但 Impl 需要其他服务 |
| **servicegamecenter** | 5 | 18 | +13 | 游戏中心功能复杂 |
| **main** | 0 | 21+ | +21 | 应用入口，新增依赖 service-admin |
| **compsetting** | 5 | 17+ | +12 | 设置页面，新增依赖 service-admin |
| **serviceshortvideo** | 4 | 16 | +12 | 短视频功能复杂 |
| **servicefeed** | 7 | 13+ | +6 | 新增依赖 service-admin 和 service-user |
| **serviceadmin** | 5 | 5 | 0 | 新增模块，依赖精简 |
| **serviceuser** | 8+ | 12+ | +4 | 新增模块 |

**✅ 这是正常现象**: Impl 层依赖更多是合理的，关键是要通过 `component()` 依赖 SDK，而非 `project()` 依赖源码。

---

## 五、理想的依赖结构

### 5.1 推荐的模块间依赖

```mermaid
graph TB
    subgraph 应用层
        main[main - 应用入口]
    end

    subgraph 组件层
        compfeed[compfeed - 动态组件]
        compmkey[compmkey - 密钥组件]
        compsetting[compsetting - 设置组件]
    end

    subgraph 业务服务层
        servicefeed[servicefeed - 动态服务]
        serviceim[serviceim - IM服务]
        serviceh5[serviceh5 - H5容器]
    end

    subgraph 基础服务层
        servicenet[servicenet - 网络]
        serviceconfig[serviceconfig - 配置]
        serviceaccount[serviceaccount - 账号]
    end

    subgraph 底层服务
        servicebase[servicebase - 基础框架]
        serviceruntime[serviceruntime - 运行时]
    end

    %% Impl 层依赖（使用 component()）
    main -.->|component()| compfeed
    main -.->|component()| compmkey
    main -.->|component()| servicefeed

    compfeed -.->|component()| servicefeed
    compfeed -.->|component()| serviceim

    servicefeed -.->|component()| servicenet
    servicefeed -.->|component()| serviceconfig
    servicefeed -.->|component()| serviceaccount

    servicenet -.->|component()| servicebase
    serviceconfig -.->|component()| servicebase

    servicebase -.->|component()| serviceruntime

    %% SDK 层依赖（在 component.gradle 中）
    compfeed ==>|SDK| servicefeed
    servicefeed ==>|SDK| servicenet
    servicenet ==>|SDK| servicebase
    servicebase ==>|SDK| serviceruntime

    classDef app fill:#ff6b6b,stroke:#c92a2a,color:#fff
    classDef comp fill:#4ecdc4,stroke:#0a9396,color:#fff
    classDef service fill:#ffe66d,stroke:#f4a261,color:#000
    classDef base fill:#a8dadc,stroke:#457b9d,color:#000
    classDef runtime fill:#e0e0e0,stroke:#9e9e9e,color:#000

    class main app
    class compfeed,compmkey,compsetting comp
    class servicefeed,serviceim,serviceh5 service
    class servicenet,serviceconfig,serviceaccount base
    class servicebase,serviceruntime runtime
```

**图例说明**：
- `==>` 实线：SDK 依赖 SDK（在 component.gradle 中配置）
- `-.->` 虚线：Impl 依赖 SDK（在 build.gradle 中用 component() 配置）

### 5.2 依赖规则总结

| 层级 | 可以依赖 | 不能依赖 | 配置位置 |
|------|---------|---------|---------|
| **main (App)** | 所有 Component SDK<br/>所有 Service SDK | - | main/build.gradle |
| **Component Impl** | Service SDK<br/>其他 Component SDK | Service Impl | comp*/build.gradle |
| **Service Impl** | 其他 Service SDK<br/>基础库 SDK | Component<br/>上层 Service | service*/build.gradle |
| **SDK** | 其他模块的 SDK | Impl 代码<br/>UI 库 | component.gradle |

---

## 六、改进建议

### 6.1 紧急需要修复的问题

#### 🔴 问题 1: 大量使用 `project()` 依赖

**当前状态**: 28 个模块使用 `implementation project()`

**影响**：
- 破坏了 SDK/Impl 分离架构
- 导致编译时依赖整个模块源码
- 增加编译时间
- 降低模块隔离性

**解决方案**：
```groovy
// 批量替换示例
// ❌ 错误写法
dependencies {
    implementation project(':servicebase')
    implementation project(':servicenet')
}

// ✅ 正确写法
dependencies {
    implementation component(':servicebase')
    implementation component(':servicenet')
}
```

**优先级**: 🔴 高
- 首先修复 **servicebase**（被 25 个模块错误依赖）
- 其次修复 **servicemedia**（被 6 个模块错误依赖）

#### 🟡 问题 2: SDK 依赖数量不一致

某些模块的 SDK 依赖配置可能不完整。

**检查方法**：
对比 `gradlescript/component.gradle` 和各模块 `build.gradle` 中的依赖，确保：
1. SDK 中声明的依赖都是必需的
2. Impl 中额外的依赖是合理的

#### 🟢 问题 3: 依赖链路较深（L0-L10）

**当前状态**: 最深依赖链路达 10 层

**改进方向**：
1. 评估是否可以减少中间层
2. 考虑将某些 L7-L10 模块合并
3. 使用事件总线解耦部分依赖

### 6.2 长期优化建议

#### 1. 建立依赖审查机制

在 Code Review 时检查：
- [ ] 是否使用 `component()` 而非 `project()`
- [ ] 依赖是否符合分层原则
- [ ] SDK 依赖是否最小化

#### 2. 自动化检查工具

```bash
# 检查是否有 project() 依赖
cd .AI/scripts
python3 analyze_sdk_impl_dependencies.py

# 如果发现 project() 使用，报告并阻止合并
```

#### 3. 定期更新依赖文档

```bash
# 每月运行一次，更新依赖关系
cd .AI/scripts
python3 analyze_dependencies.py
python3 analyze_sdk_impl_dependencies.py
```

---

## 七、快速参考

### 7.1 如何添加新依赖

#### 场景 1: SDK 需要依赖另一个模块的 SDK

**配置位置**: `gradlescript/component.gradle`

```groovy
'serviceA' {
    groupId 'com.netease.gl.service'
    artifactId 'a'
    dependencies {
        // 添加 SDK 依赖
        implementation component(':serviceB')
    }
}
```

#### 场景 2: Impl 需要额外依赖其他模块

**配置位置**: `serviceA/build.gradle`

```groovy
dependencies {
    // Impl 层额外依赖（SDK 中未声明的）
    implementation component(':serviceC')

    // ❌ 禁止使用 project()
    // implementation project(':serviceC')
}
```

### 7.2 依赖问题排查清单

遇到依赖问题时，按以下顺序检查：

1. **[ ] 检查是否使用了 `project()`**
   ```bash
   grep "implementation project" */build.gradle
   ```

2. **[ ] 检查 SDK 依赖是否配置**
   查看 `gradlescript/component.gradle` 中的配置

3. **[ ] 检查依赖层级是否合理**
   使用 `.AI/scripts/analyze_dependencies.py` 生成层级图

4. **[ ] 检查是否有循环依赖**
   查看依赖层级报告，确保没有循环

5. **[ ] 清理并重新构建**
   ```bash
   ./gradlew clean
   ./gradlew build
   ```

---

## 八、相关文档

- [项目结构指导文档](PROJECT_STRUCTURE.md) - SDK/Impl 分离详解
- [依赖关系分析报告](DEPENDENCY_ANALYSIS.md) - 自动生成的 SDK/Impl 依赖详细报告
- [AI 优化指南](../AI_OPTIMIZATION_GUIDE.md) - AI 友好化改造方案

---

## 九、常见问题

### Q1: 为什么不能使用 `project()` 依赖？

**A**:
- `component()` 依赖的是预编译的 SDK JAR 包（只包含接口）
- `project()` 依赖的是完整的源码（SDK + Impl）
- 使用 `project()` 会破坏 SDK/Impl 分离，增加编译依赖，降低模块隔离性

### Q2: SDK 依赖和 Impl 依赖有什么区别？

**A**:
- **SDK 依赖**: 接口间的依赖，在 `component.gradle` 中配置，编译为 JAR
- **Impl 依赖**: 实现代码的依赖，在模块自己的 `build.gradle` 中配置
- Impl 依赖数量通常比 SDK 依赖多，这是正常的

### Q3: 如何判断某个依赖应该放在 SDK 还是 Impl？

**A**: 遵循最小化原则
- **放在 SDK** (component.gradle): 如果其他模块的 SDK 需要这个依赖
- **放在 Impl** (build.gradle): 如果只有实现代码需要这个依赖

示例：
```groovy
// component.gradle - SDK 依赖
'servicefeed' {
    dependencies {
        // servicefeed 的 SDK 接口需要用到 servicenet 的接口
        implementation component(':servicenet')
    }
}

// servicefeed/build.gradle - Impl 额外依赖
dependencies {
    // Impl 实现需要用到，但 SDK 不需要
    implementation component(':servicelog')
}
```

### Q4: 依赖层级为什么这么深（L0-L10）？

**A**: 这是模块化架构的自然结果。关键不是层级深度，而是：
- ✅ 没有循环依赖
- ✅ 上层依赖下层，单向依赖
- ✅ 每层职责清晰

层级深度可以接受，但建议定期评估是否可以优化。

---

**文档版本**: 3.1 (区分 SDK/Impl 依赖，新增 service-admin 和 service-user 模块)
**维护者**: 开发团队

**自动化工具**: `.AI/scripts/analyze_sdk_impl_dependencies.py`

**使用方法**:
```bash
# 运行依赖分析
cd .AI/scripts && python3 analyze_sdk_impl_dependencies.py

# 查看生成的报告
cat ../DEPENDENCY_ANALYSIS.md
```

---

## 十、最近变更记录

### v3.1 (2025-10-24)

**新增模块**:
1. **service-admin** (L7层)
   - 从 service-feed 中拆分出管理员相关功能
   - 包含动态管理、评论管理、用户管理等
   - 依赖：servicebase, service-net, service-config, service-feed, service-user

2. **service-user** (L6层)
   - 从 service-feed 中拆分出用户相关功能
   - 包含用户信息、用户关系等
   - 依赖：servicebase, service-net, service-config, service-im, service-account 等

**依赖关系变更**:
- `service-feed` → 新增依赖 `service-admin`, `service-user`
- `compfeed` → 新增依赖 `service-admin`, `service-user`
- `compsetting` → 新增依赖 `service-admin`
- `main` → 新增依赖 `service-admin`

**架构影响**:
- 模块职责更加清晰，符合单一职责原则
- 依赖层级从 L10 增加到需要重新评估
- 建议后续关注新增模块的依赖关系，避免循环依赖
