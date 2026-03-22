---
name: module-generator
user-invocable: true
description: Android 模块代码生成器。当用户提到"创建模块"、"新建模块"、"添加模块"、"生成模块"、"create module"、"new module"、"service模块"、"component模块"或需要创建新的 Service/Component 模块时使用此 skill。专门用于根据项目 SDK/Impl 分离架构自动生成完整的模块代码结构。
---

# Android 模块代码生成器

基于用户提供的模块信息，自动生成符合项目 SDK/Impl 分离架构规范的完整模块代码。

## 核心限制

- 严格按照文档示例描述，不要创建和生成文档中未提及的文件
- 生成文件内容严格按照示例，不要添加额外的未提及内容，不能缺少提及的内容
- 文件结构及生成的包名严格按照文档提供的目录结构，包名必须允许包含comp或者service，如comptest,servicetest

## 用户输入格式

### 必填字段
- **moduleName**: 模块名称（如 `service-newmodule` 或 `compnewmodule`）
- **moduleType**: 模块类型（`service` 或 `component`）
- **description**: 模块功能描述（中文）

### 可选字段
- **projectDir**: 模块物理目录路径（默认根据类型自动推断）
- **packageName**: 包名（默认根据模块名自动生成）
- **dependencies**: 依赖的其他模块列表（默认包含基础依赖）

### 输入示例
```
moduleName: service-payment
moduleType: service
description: 支付服务模块，提供支付相关功能
```

## 执行步骤

### 1. 解析用户输入

从用户输入中提取模块信息，进行命名转换：
- 模块名 → 包名：`service-payment` → `com.netease.gl.servicepayment`
- 模块名 → 类名：`service-payment` → `ServicePaymentSdk`, `ServicePaymentSdkImp`, `ServicePaymentComponent`
- 模块名 → groupId：service 类型用 `com.netease.gl.service`，component 类型用 `com.netease.gl.component`
- 模块名 → artifactId：提取核心名称，如 `service-payment` → `payment`

### 2. 修改 settings.gradle

在 `settings.gradle` 文件中添加模块声明：

```groovy
include ':service-newmodule'
project(':service-newmodule').projectDir = new File('services/newmodule')
```

**Service 模块路径推断规则**：
1. 优先查找现有同类模块的路径模式
2. 如果用户指定了 projectDir，使用用户指定的路径
3. 默认路径：`services/{moduleName去掉service-前缀}`

### 3. 修改 gradlescript/component.gradle

**位置 1**: 在 `component` 块的 `include` 部分添加模块名

**位置 2**: 在 `sdk.configuration` 块中添加配置：

```groovy
'service-newmodule' {
    groupId 'com.netease.gl.service'
    artifactId 'newmodule'
    forceUseLocal false
    dependencies {
        implementation component(':servicebase')
        implementation component(':service-net')
        implementation deps.kotlin.stdlib
        implementation deps.code_gson
        implementation deps.gllib.base
        implementation deps.component_core
    }
}
```

### 4. 创建模块目录结构

**Service 模块结构**：
```
services/newmodule/
├── src/main/
│   ├── sdk/com/netease/gl/servicenewmodule/
│   │   └── sdk/
│   │       └── ServiceNewModuleSdk.kt
│   ├── java/com/netease/gl/servicenewmodule/
│   │   └── component/
│   │       ├── ServiceNewModuleSdkImp.kt
│   │       ├── ServiceNewModuleComponent.kt
│   │       └── Sdks.kt
│   └── AndroidManifest.xml
└── build.gradle
```

### 5. 生成 build.gradle

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

    namespace '{{NAMESPACE}}'  // 与模块包名一致，如 com.netease.gl.servicenewmodule

    buildFeatures {
        buildConfig = true
    }
}

dependencies {
    implementation deps.kotlin.stdlib
    implementation deps.code_gson
    implementation deps.gllib.base
    implementation deps.component_core
    implementation project(':servicebase')
    implementation component(':service-net')
}
```

### 6. 生成 SDK 接口 (ServiceXxxSdk.kt)

放在 `src/main/sdk/com/netease/gl/{{PACKAGE_NAME}}/sdk/` 目录：

```kotlin
package com.netease.gl.{{PACKAGE_NAME}}.sdk

/**
 * {{MODULE_DESCRIPTION}}
 * 提供{{MODULE_NAME}}功能的对外接口
 */
interface {{SDK_INTERFACE_NAME}} {
    // 根据业务需求添加接口方法
}
```

### 7. 生成 Sdks.kt（放在 Impl 层）

放在 `src/main/java/com/netease/gl/{{PACKAGE_NAME}}/component/` 目录：

```kotlin
package com.netease.gl.{{PACKAGE_NAME}}.component

import android.app.Application
import com.netease.gl.{{PACKAGE_NAME}}.sdk.{{SDK_INTERFACE_NAME}}
import com.plugin.component.ComponentManager
import com.plugin.component.SdkManager

object Sdks {
    @JvmStatic
    fun init(application: Application) {
        ComponentManager.init(application)
    }

    @JvmStatic
    val {{SDK_INSTANCE_NAME}} by lazy {
        SdkManager.getSdk({{SDK_INTERFACE_NAME}}::class.java)!!
    }
}
```

### 8. 生成 SDK 实现类 (ServiceXxxSdkImp.kt)

放在 `src/main/java/com/netease/gl/{{PACKAGE_NAME}}/component/` 目录：

```kotlin
package com.netease.gl.{{PACKAGE_NAME}}.component

import com.netease.gl.{{PACKAGE_NAME}}.sdk.{{SDK_INTERFACE_NAME}}
import com.plugin.component.anno.AutoInjectImpl

@AutoInjectImpl(sdk = [{{SDK_INTERFACE_NAME}}::class])
class {{SDK_IMPL_NAME}} : {{SDK_INTERFACE_NAME}} {

}
```

### 9. 生成 Component 注册类 (ServiceXxxComponent.kt)

放在 `src/main/java/com/netease/gl/{{PACKAGE_NAME}}/component/` 目录：

```kotlin
package com.netease.gl.{{PACKAGE_NAME}}.component

import android.app.Application
import com.plugin.component.IComponent
import com.plugin.component.anno.AutoInjectComponent

@AutoInjectComponent(impl = [{{SDK_IMPL_NAME}}::class])
class {{COMPONENT_NAME}} : IComponent {

    override fun attachComponent(application: Application) {
        Sdks.init(application)
    }

    override fun detachComponent() {
    }
}
```

### 10. 生成 AndroidManifest.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{{NAMESPACE}}">

</manifest>
```

### 11. 输出结果

向用户报告生成结果：

```
✅ 模块代码生成成功

**模块名**: {{moduleName}}
**模块类型**: {{moduleType}}
**描述**: {{description}}
**包名**: {{packageName}}
**目录**: {{projectDir}}

**修改的文件**:
1. settings.gradle
2. gradlescript/component.gradle

**创建的文件**:
1. build.gradle
2. {{SDK_INTERFACE_NAME}}.kt
3. Sdks.kt
4. {{SDK_IMPL_NAME}}.kt
5. {{COMPONENT_NAME}}.kt
6. AndroidManifest.xml

**后续步骤**:
1. 同步 Gradle 项目
2. 在 SDK 接口中添加业务方法
3. 在 SDK 实现类中实现业务逻辑
4. 其他模块通过 `component(':{{moduleName}}')` 依赖此模块
```

## 命名转换规则

| 模块名 | 包名 | SDK接口名 | SDK实现名 | Component名 |
|--------|------|-----------|-----------|-------------|
| service-payment | com.netease.gl.servicepayment | ServicePaymentSdk | ServicePaymentSdkImp | ServicePaymentComponent |
| comppayment | com.netease.gl.comppayment | CompPaymentSdk | CompPaymentSdkImp | CompPaymentComponent |

## 常见错误

1. **使用 project() 而不是 component()** - sdk.configuration 的 dependencies 中应使用 `component(':moduleName')`
2. **SDK 中引用资源** - SDK 不能引用 R 资源
3. **SDK 依赖 Impl** - SDK 不能 import Impl 层的类
4. **忘记添加注解** - SDK 实现类需要 `@AutoInjectImpl`，Component 类需要 `@AutoInjectComponent`
5. **Sdks.kt 放在 SDK 层** - Sdks.kt 必须放在 Impl 层（java 目录）

## 注意事项

1. **不要编译**: 遵循项目 CLAUDE.md 规则，修改完成后不执行编译操作
2. **严格按模板**: 不要添加文档未提及的额外内容
3. **包名规范**: 包名必须包含 comp 或 service，如 comptest, servicetest
