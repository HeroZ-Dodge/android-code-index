# Android 项目结构指导文档

## 概述

本项目采用模块化架构设计，通过 Gradle 插件实现模块间的 SDK/Impl 分离机制。每个模块被拆分为 SDK 和 Implementation 两部分，实现了接口与实现的解耦。

## 核心架构特性

### 1. SDK/Impl 分离机制

每个模块的代码被分为两个部分：

- **SDK 部分** (`src/main/sdk/`)
  - 包含模块对外暴露的接口、数据模型、事件类等
  - 在项目 Config 阶段被预编译成 JAR 包
  - 供其他模块通过 `implementation component(':moduleName')` 方式引用

- **Impl 部分** (`src/main/java/`)
  - 包含模块内部的业务逻辑实现
  - 实现 SDK 中定义的接口
  - 不直接暴露给其他模块的内部实现代码

**⚠️ 重要**: 模块间依赖只能使用 `implementation component(':moduleName')` 方式，**禁止**使用 `implementation project(':moduleName')`。

**SDK vs Impl 的划分原则**：
- **SDK 部分**: 需要暴露给其他模块使用的接口、数据类、工具类和实现
- **Impl 部分**: 模块内部使用的私有实现，不希望其他模块访问的代码

### 2. 模块类型

项目包含三类模块：

#### Component 层（组件层）
- **命名规范**: `comp*` (如 `compfeed`, `compmkey`, `compsetting`)
- **职责**: 封装特定业务功能的组件
- **依赖**: 可以依赖 Service 层模块

#### Service 层（服务层）
- **命名规范**: `service*` (如 `serviceaccount`, `servicefeed`, `servicenet`)
- **职责**: 提供基础服务能力
- **依赖**: Service 之间可以相互依赖，但应避免循环依赖

#### Plugin 层（插件层）
- **命名规范**: `plugin-*` 或 `*-plugin-*`
- **职责**: 插件化功能模块
- **位置**: 通常位于 `plugin-core/` 或独立目录

### 3. 模块依赖配置

所有模块的 SDK 声明和依赖关系统一在 `gradlescript/component.gradle` 文件中管理。

#### 配置文件位置
```
gradlescript/component.gradle
```

#### 模块声明示例

```groovy
component {
    // 声明生效的模块
    include ':main', 'compfeed', 'compmkey', 'serviceaccount', 'servicebase', ...

    sdk {
        configuration {
            'compfeed' {
                groupId 'com.netease.gl.component'
                artifactId 'feed'
                dependencies {
                    // 依赖其他组件的 SDK
                    implementation component(':serviceconfig')
                    implementation component(':servicefeed')
                    implementation component(':servicecbg')
                    implementation component(':serviceim')
                    implementation component(':servicebase')
                    // 外部依赖
                    implementation deps.androidx.app_compat
                    implementation deps.kotlin.stdlib
                }
            }

            'serviceaccount' {
                groupId 'com.netease.gl.service'
                artifactId 'account'
                dependencies {
                    implementation component(':servicebase')
                    implementation deps.gllib.base
                }
            }
        }
    }
}
```

## 模块结构示例

以 `compfeed` 模块为例：

```
compfeed/
├── src/
│   └── main/
│       ├── sdk/                          # SDK 部分（对外暴露）
│       │   └── com/netease/gl/compfeed/
│       │       ├── entity/              # 数据实体
│       │       │   ├── NeteaseVipCustomServiceEntity.kt
│       │       │   └── NeteaseVipPrivilegeEntity.kt
│       │       ├── event/               # 事件定义
│       │       │   ├── CheckJumpLandingEvent.kt
│       │       │   └── UpdateSelfAvatarEvent.kt
│       │       └── utils/               # 接口定义
│       │           ├── IAutoSelectSquareHelper.kt
│       │           ├── IFeedHistoryManager.kt
│       │           └── IVideoParamHelper.kt
│       │
│       ├── java/                        # Impl 部分（内部实现）
│       │   └── com/netease/gl/
│       │       └── [具体业务实现代码]
│       │
│       ├── res/                         # 资源文件
│       ├── assets/                      # 资源文件
│       └── AndroidManifest.xml
│
└── build.gradle                         # 模块构建配置
```

## 依赖关系图示

```
┌─────────────────┐
│   Component 层  │ (compfeed, compmkey, compsetting)
└────────┬────────┘
         │ 依赖
         ↓
┌─────────────────┐
│   Service 层    │ (serviceaccount, servicefeed, servicenet)
└────────┬────────┘
         │ 依赖
         ↓
┌─────────────────┐
│   Core/基础库   │ (component-core, gllib.base)
└─────────────────┘
```

## SDK 之间的依赖关系

SDK 之间可以有依赖关系，通过 `component(':moduleName')` 声明：

```groovy
'compfeed' {
    dependencies {
        // compfeed 的 SDK 依赖于以下模块的 SDK
        implementation component(':serviceconfig')  // 配置服务
        implementation component(':servicefeed')    // 动态服务
        implementation component(':servicebase')    // 基础服务
        implementation component(':servicenet')     // 网络服务
    }
}
```

## 快速定位指南

### 1. 查找模块声明
所有模块在 `settings.gradle` 中声明：
```groovy
// Component
include ':compfeed'
include ':compmkey'

// Service
include ':serviceaccount'
include ':servicebase'
```

### 2. 查找模块 SDK 配置
所有 SDK 配置在 `gradlescript/component.gradle` 文件的 `sdk.configuration` 块中。

### 3. 查找模块对外接口
在模块的 `src/main/sdk/` 目录下查找：
- 接口定义（通常以 `I` 开头）
- 数据模型（Entity, Model）
- 事件定义（Event）
- 常量定义（Constant）

### 4. 查找模块实现
在模块的 `src/main/java/` 目录下查找具体实现代码。

## 开发规范

### 1. SDK 代码规范

**命名规范**：
- **接口命名**: 以 `I` 开头，如 `IFeedHistoryManager`
- **事件命名**: 以 `Event` 结尾，如 `UpdateSelfAvatarEvent`
- **实体命名**: 以 `Entity`, `Model`, `Sdk` 等结尾
- **保持精简**: SDK 包含对外暴露的接口、实体类和需要共享的实现

**⚠️ SDK 内容限制（强制规范）**：

1. **禁止 import 资源相关类**
   ```kotlin
   // ❌ 错误！SDK 中禁止引用资源
   import com.netease.gl.compfeed.R
   import android.content.res.Resources

   // ✅ 正确：SDK 只包含接口和数据模型
   interface IFeedHelper {
       fun doSomething()
   }
   ```

2. **禁止 import 同模块的 impl 实现类**
   ```kotlin
   // ❌ 错误！SDK 不能依赖 impl 实现
   import com.netease.gl.compfeed.FeedHelperImpl

   // ✅ 正确：SDK 只定义接口
   interface IFeedHelper {
       fun doSomething()
   }
   ```

3. **第三方依赖必须在 component 配置中声明**
   - 如果 SDK 中使用了第三方库（如 Gson、RxJava 等）
   - 必须在 `gradlescript/component.gradle` 的对应模块配置中添加依赖

   ```groovy
   'compfeed' {
       groupId 'com.netease.gl.component'
       artifactId 'feed'
       dependencies {
           // SDK 中使用了 Gson，必须在这里声明
           implementation deps.code_gson
           // SDK 中使用了 RxJava，必须在这里声明
           implementation deps.rx.java
       }
   }
   ```

**SDK 应该包含的内容**：
- ✅ 接口定义（Interface）
- ✅ 数据类/实体类（Data Class / Entity）
- ✅ 事件类（Event）
- ✅ 常量定义（Constant）
- ✅ 枚举类型（Enum）
- ✅ 注解定义（Annotation）
- ✅ 具体实现类（对外暴露的实现）
- ✅ 业务逻辑实现（需要暴露给其他模块的）

**SDK 不应该包含的内容**：
- ❌ Android 资源引用（R.xxx）
- ❌ 同模块 impl 包下的类引用（SDK 不能依赖 impl）

### 2. 依赖管理规范

**⚠️ 重要规则：模块依赖方式**

- **✅ 正确方式**: 使用 `implementation component(':moduleName')` 引用其他模块的 SDK
  ```groovy
  dependencies {
      implementation component(':servicebase')
      implementation component(':servicenet')
  }
  ```

- **❌ 禁止方式**: 不允许使用 `implementation project(':moduleName')` 直接引用其他模块
  ```groovy
  dependencies {
      // ❌ 错误！禁止这样写
      implementation project(':servicebase')
  }
  ```

**原因说明**：
- `component()` 方式引用的是模块预编译后的 SDK JAR 包，只包含对外暴露的接口
- `project()` 方式会引用整个模块的源码，破坏了 SDK/Impl 分离的设计
- 使用 `component()` 可以实现模块间的隔离，提高编译速度和代码安全性

**其他依赖规范**：
- **避免循环依赖**: 模块之间不应形成循环依赖
- **分层依赖**: Component 层可依赖 Service 层，Service 层可依赖其他 Service
- **外部依赖**: 通过 `deps.xxx` 引用外部库

### 3. 模块化原则
- **单一职责**: 每个模块专注于一个特定领域
- **接口隔离**: SDK 只暴露必要的接口
- **依赖倒置**: 通过接口而非实现进行依赖

## 常见模块说明

| 模块名 | 类型 | 职责 |
|--------|------|------|
| compfeed | Component | 动态组件，处理社区内容 |
| compmkey | Component | 密钥管理组件 |
| compsetting | Component | 设置组件 |
| serviceaccount | Service | 账号服务 |
| serviceadmin | Service | 管理员服务（动态、评论、用户管理） |
| servicebase | Service | 基础服务 |
| servicefeed | Service | 动态服务 |
| serviceuser | Service | 用户服务 |
| servicenet | Service | 网络服务 |
| serviceconfig | Service | 配置服务 |
| serviceim | Service | 即时通讯服务 |
| servicecc | Service | CC直播服务 |

## 构建系统说明

### Gradle 插件
项目使用组件化插件 `ComponentCornerstone` 来管理模块化架构：

**插件信息**：
- **插件名称**: `com.github.DSAppTeam:ComponentCornerstone`
- **应用方式**:
  ```groovy
  apply plugin: 'com.android.component'
  ```

该插件提供了 SDK/Impl 分离、模块依赖管理、SDK 自动编译打包等核心能力。

### SDK 编译流程
1. Config 阶段：扫描各模块的 `src/main/sdk/` 目录
2. 预编译：将 SDK 代码编译为 JAR 包
3. 版本管理：插件自动处理 SDK 版本号
4. 发布：JAR 包发布到 Maven 仓库或本地
5. 引用：其他模块通过 `component()` 引用 JAR

### 本地调试模式
通过 `forceUseLocal` 参数控制是否使用本地代码：

```groovy
'compfeed' {
    forceUseLocal false  // false: 使用 Maven 仓库的 JAR, true: 使用本地源码
}
```

## 注意事项

### ⚠️ 关键规则

1. **禁止使用 `implementation project()`**
   - 模块之间依赖**必须**使用 `implementation component(':moduleName')`
   - **禁止**使用 `implementation project(':moduleName')` 方式
   - 这是强制性规范，违反会破坏项目的模块化架构

2. **SDK 内容限制**
   - **禁止** import 资源相关类（如 `R.xxx`、`Resources` 等）
   - **禁止** import 同模块的 impl 实现类
   - SDK 中使用第三方库**必须**在 `gradlescript/component.gradle` 中声明依赖
   - 详细规范参见"开发规范 > SDK 代码规范"部分

3. **修改 SDK 接口的影响**
   - 如果修改了模块的 SDK 部分（`src/main/sdk/`），所有依赖该模块的模块都需要重新编译
   - SDK 修改后需要重新发布 JAR 包

4. **版本管理**
   - SDK 版本由 ComponentCornerstone 插件自动化管理
   - 无需手动维护 `sdkVersion` 和 `implVersion`
   - 插件会根据代码变更自动处理版本号更新

5. **Maven 仓库**
   - 项目使用私有 Maven 仓库存储编译后的 SDK JAR 包
   - 仓库配置在 `gradlescript/component.gradle` 的 `repositories` 块中

6. **构建顺序**
   - Gradle 会自动处理模块间的构建依赖顺序
   - SDK 会在依赖它的模块之前先编译完成

## 文件路径速查

| 用途 | 路径 |
|------|------|
| 模块声明 | `settings.gradle` |
| SDK 配置 | `gradlescript/component.gradle` |
| 模块 SDK 代码 | `{moduleName}/src/main/sdk/` |
| 模块实现代码 | `{moduleName}/src/main/java/` |
| 主应用入口 | `main/` |
| 基准配置 | `baselineprofile/`, `benchmark/` |

## 示例：如何创建新模块

### 完整步骤

以创建一个新的 Service 模块 `service-newmodule` 为例，按照以下步骤操作：

#### 1. 在 `settings.gradle` 中声明模块

```groovy
// Service
include ':service-newmodule'
project(':service-newmodule').projectDir = new File('services/content/newmodule')
```

#### 2. 在 `gradlescript/component.gradle` 中配置模块

需要进行两步配置：

**步骤 2.1: 在 `include` 中声明模块**

在 `component` 块的 `include` 部分添加模块名（注意：不需要冒号前缀）：

```groovy
component {
    include ':main',
            'compfeed', 'compmkey', 'compsetting',
            'service-account', 'service-base', 'service-net',
            'service-feed', 'service-user', 'service-admin',
            'service-newmodule',  // ← 添加新模块
            // ... 其他模块
}
```

**步骤 2.2: 在 `sdk.configuration` 中配置 SDK**

在 `sdk.configuration` 块中添加模块的详细配置：

```groovy
sdk {
    configuration {
        'service-newmodule' {
            groupId 'com.netease.gl.service'
            artifactId 'newmodule'
            forceUseLocal false  // false: 使用 Maven 仓库的 JAR, true: 使用本地源码
            dependencies {
                // 基础依赖
                implementation component(':service-base')
                implementation component(':service-net')
                implementation component(':service-config')

                // Kotlin 和其他必要依赖
                implementation deps.kotlin.stdlib
                implementation deps.code_gson
                implementation deps.gllib.base
            }
        }

        // ... 其他模块配置
    }
}
```

**配置说明**：
- `include`: 声明哪些模块会被组件系统管理（模块名不带冒号）
- `groupId`: Maven 坐标的 group ID
- `artifactId`: Maven 坐标的 artifact ID
- `forceUseLocal`: 是否强制使用本地源码（开发调试时可设为 true）
- `dependencies`: SDK 的依赖声明

#### 3. 创建模块目录结构

```
services/content/newmodule/
├── src/
│   └── main/
│       ├── sdk/                                    # SDK 部分（对外暴露）
│       │   └── com/netease/gl/servicenewmodule/
│       │       ├── sdk/                           # SDK 接口和工具
│       │       │   ├── ServiceNewModuleSdk.kt    # SDK 接口定义
│       │       │   └── Sdks.kt                   # SDK 获取工具类
│       │       ├── repo/                         # Repository 接口
│       │       └── entity/                       # 数据实体
│       │
│       ├── java/                                  # Impl 部分（内部实现）
│       │   └── com/netease/gl/servicenewmodule/
│       │       ├── component/                    # 组件相关
│       │       │   ├── ServiceNewModuleSdkImp.kt # SDK 接口实现
│       │       │   └── ServiceNewModuleComponent.kt # Component 注册
│       │       ├── repo/                         # Repository 实现
│       │       └── [其他业务实现代码]
│       │
│       └── AndroidManifest.xml
│
└── build.gradle                                   # 模块构建配置
```

#### 4. 创建 `build.gradle` 文件

```groovy
apply plugin: 'com.android.library'
apply plugin: 'kotlin-android'

android {
    compileSdkVersion build_versions.compile_sdk

    defaultConfig {
        minSdkVersion build_versions.min_sdk
        targetSdkVersion build_versions.target_sdk
    }

    buildTypes {
        debug {
            minifyEnabled false
        }
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }

    compileOptions {
        sourceCompatibility build_versions.java_source
        targetCompatibility build_versions.java_target
    }

    kotlinOptions {
        jvmTarget = build_versions.jvm_target
    }

    namespace 'com.netease.gl.servicenewmodule'

    buildFeatures {
        buildConfig = true
    }
}

dependencies {
    // 基础依赖
    implementation deps.kotlin.stdlib
    implementation deps.code_gson
    implementation deps.gllib.base

    // Service 依赖
    implementation project(':service-base')
    implementation component(':service-net')
    implementation component(':service-config')
}
```

#### 5. 定义 SDK 接口（SDK 部分）

创建 `src/main/sdk/com/netease/gl/servicenewmodule/sdk/ServiceNewModuleSdk.kt`：

```kotlin
package com.netease.gl.servicenewmodule.sdk

import com.netease.gl.servicenewmodule.repo.NewModuleRepo

/**
 * Service NewModule SDK 接口
 * 提供新模块功能的对外接口
 */
interface ServiceNewModuleSdk {
    /**
     * 创建新的 NewModuleRepo 实例
     */
    fun newNewModuleRepo(repo: Any, repos: Any): NewModuleRepo

    /**
     * 获取 NewModuleRepo 实例
     */
    fun getNewModuleRepo(): NewModuleRepo?
}
```

#### 6. 创建 SDK 获取工具类（SDK 部分）

创建 `src/main/sdk/com/netease/gl/servicenewmodule/sdk/Sdks.kt`：

```kotlin
package com.netease.gl.servicenewmodule.sdk

import android.app.Application
import com.netease.gl.service.runtime.ServiceCacheSdk
import com.plugin.component.ComponentManager
import com.plugin.component.SdkManager

/**
 * SDK 获取工具类
 * 提供统一的 SDK 实例获取方式
 */
object Sdks {
    /**
     * 初始化组件管理器
     */
    @JvmStatic
    fun init(application: Application) {
        ComponentManager.init(application)
    }

    /**
     * 获取 ServiceCacheSdk 实例
     * 使用 lazy 延迟初始化，只在首次访问时创建
     */
    @JvmStatic
    val serviceCacheSdk by lazy {
        SdkManager.getSdk(ServiceCacheSdk::class.java)!!
    }

    // 可以在这里添加其他常用 SDK 的获取方法
    // 例如：
    // @JvmStatic
    // val serviceNetSdk by lazy {
    //     SdkManager.getSdk(ServiceNetSdk::class.java)!!
    // }
}
```

**Sdks.kt 使用说明**：
- `init(application)`: 在 Component 中调用，初始化组件管理器
- `serviceCacheSdk`: 通过 `SdkManager.getSdk()` 获取其他模块的 SDK 实例
- 使用 `lazy` 委托实现延迟初始化，提高性能
- 使用 `!!` 断言 SDK 不为空（如果为空会抛出异常，帮助及早发现配置问题）

#### 7. 实现 SDK 接口（Impl 部分）

创建 `src/main/java/com/netease/gl/servicenewmodule/component/ServiceNewModuleSdkImp.kt`：

```kotlin
package com.netease.gl.servicenewmodule.component

import com.netease.gl.servicenewmodule.repo.NewModuleRepo
import com.netease.gl.servicenewmodule.repo.NewModuleRepoHelper
import com.netease.gl.servicenewmodule.sdk.ServiceNewModuleSdk
import com.plugin.component.anno.AutoInjectImpl

/**
 * Service NewModule SDK 实现类
 * 使用 @AutoInjectImpl 注解自动注册到组件系统
 */
@AutoInjectImpl(sdk = [ServiceNewModuleSdk::class])
class ServiceNewModuleSdkImp : ServiceNewModuleSdk {

    override fun newNewModuleRepo(repo: Any, repos: Any): NewModuleRepo {
        return NewModuleRepoHelper.newNewModuleRepo(repo, repos)
    }

    override fun getNewModuleRepo(): NewModuleRepo? {
        return NewModuleRepoHelper.getNewModuleRepo()
    }
}
```

**关键注解说明**：
- `@AutoInjectImpl(sdk = [ServiceNewModuleSdk::class])`:
  - 自动将该实现类注册到组件系统
  - 指定实现的 SDK 接口类
  - 使其他模块可以通过 `SdkManager.getSdk()` 获取实例

#### 8. 创建 Component 注册类（Impl 部分）

创建 `src/main/java/com/netease/gl/servicenewmodule/component/ServiceNewModuleComponent.kt`：

```kotlin
package com.netease.gl.servicenewmodule.component

import android.app.Application
import com.netease.gl.servicenewmodule.sdk.Sdks
import com.plugin.component.IComponent
import com.plugin.component.anno.AutoInjectComponent

/**
 * Service NewModule Component
 * 新模块组件，负责模块的初始化和清理
 */
@AutoInjectComponent(impl = [ServiceNewModuleSdkImp::class])
class ServiceNewModuleComponent : IComponent {

    /**
     * 组件附加时调用
     * 在应用启动时由组件系统自动调用
     */
    override fun attachComponent(application: Application) {
        // 初始化模块
        Sdks.init(application)

        // 这里可以添加其他初始化逻辑
        // 例如：注册监听器、初始化数据库等
    }

    /**
     * 组件分离时调用
     * 在应用退出或模块卸载时调用
     */
    override fun detachComponent() {
        // 清理资源
        // 例如：注销监听器、关闭数据库连接等
    }
}
```

**Component 职责说明**：
- 实现 `IComponent` 接口
- 使用 `@AutoInjectComponent` 注解自动注册，指定关联的 SDK 实现类
- `attachComponent()`: 在应用启动时初始化模块
- `detachComponent()`: 在应用退出时清理资源

#### 9. 创建 AndroidManifest.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.netease.gl.servicenewmodule">

    <!-- 如果需要权限，在这里声明 -->

</manifest>
```

### 其他模块如何使用新模块

#### 方式 1: 通过 component 依赖（推荐）

在其他模块的 `gradlescript/component.gradle` 配置中添加依赖：

```groovy
'compfeed' {
    dependencies {
        implementation component(':service-newmodule')
    }
}
```

然后在代码中通过 `SdkManager` 获取 SDK 实例：

```kotlin
import com.netease.gl.servicenewmodule.sdk.ServiceNewModuleSdk
import com.plugin.component.SdkManager

class SomeClass {
    private val newModuleSdk by lazy {
        SdkManager.getSdk(ServiceNewModuleSdk::class.java)!!
    }

    fun useNewModule() {
        val repo = newModuleSdk.getNewModuleRepo()
        // 使用 repo...
    }
}
```

#### 方式 2: 在模块的 Sdks.kt 中统一管理（推荐用于常用 SDK）

如果某个 SDK 在模块内部频繁使用，可以在模块自己的 `Sdks.kt` 中添加：

```kotlin
package com.netease.gl.compfeed.sdk

import com.netease.gl.servicenewmodule.sdk.ServiceNewModuleSdk
import com.plugin.component.SdkManager

object Sdks {
    @JvmStatic
    val serviceNewModuleSdk by lazy {
        SdkManager.getSdk(ServiceNewModuleSdk::class.java)!!
    }
}
```

### 核心概念总结

1. **SDK 接口定义** (`ServiceNewModuleSdk.kt`)
   - 定义模块对外暴露的能力
   - 放在 `src/main/sdk/` 目录
   - 其他模块可以依赖和调用

2. **SDK 实现类** (`ServiceNewModuleSdkImp.kt`)
   - 实现 SDK 接口
   - 使用 `@AutoInjectImpl` 注解自动注册
   - 放在 `src/main/java/` 目录（内部实现）

3. **Component 注册类** (`ServiceNewModuleComponent.kt`)
   - 实现 `IComponent` 接口
   - 使用 `@AutoInjectComponent` 注解自动注册
   - 负责模块的生命周期管理（初始化和清理）

4. **Sdks 工具类** (`Sdks.kt`)
   - 提供统一的 SDK 获取入口
   - 使用 `SdkManager.getSdk()` 获取其他模块的 SDK
   - 使用 `lazy` 延迟初始化提高性能

5. **模块间通信**
   - 通过 `SdkManager.getSdk()` 获取其他模块的 SDK 实例
   - 只能访问 SDK 部分定义的接口，无法访问 Impl 部分
   - 实现了模块间的解耦和隔离

---

**文档版本**: 1.2
**最后更新**: 2025-10-24
**适用项目**: godlike Android
**组件化插件**: com.github.DSAppTeam:ComponentCornerstone

## 最近变更记录

### v1.2 (2025-10-24)
- 新增 `service-admin` 模块：从 `service-feed` 中拆分出管理员功能
  - 包含动态管理、评论管理、用户管理等管理员相关功能
  - 依赖：servicebase, service-net, service-config, service-feed, service-user

- 新增 `service-user` 模块：从 `service-feed` 中拆分出用户相关功能
  - 包含用户信息、用户关系等用户相关功能
  - 依赖：servicebase, service-net, service-config, service-im, service-account 等

- 更新模块依赖关系：
  - `service-feed` 现在依赖 `service-admin` 和 `service-user`
  - `compfeed` 新增依赖 `service-admin` 和 `service-user`
  - `compsetting` 新增依赖 `service-admin`
