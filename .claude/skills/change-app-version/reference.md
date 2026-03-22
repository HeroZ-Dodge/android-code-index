# 版本号管理参考文档

## Android 版本号体系

Android 应用有两个关键的版本标识:

### 1. version_name (版本名称)
- **用途**: 面向用户的版本标识
- **格式**: 语义化版本号 (Semantic Versioning)
- **示例**: `4.8.0`, `5.0.0-beta`, `4.7.1`
- **位置**: 本项目中位于 `gradlescript/gl_config.gradle`

### 2. version_code (版本号)
- **用途**: 系统内部用于版本比较
- **格式**: 整数，必须递增
- **示例**: `1`, `48`, `100`
- **规则**: 新版本的 version_code 必须大于旧版本

## 语义化版本号规范 (Semantic Versioning)

格式: `MAJOR.MINOR.PATCH[-SUFFIX]`

### 版本号组成部分

- **MAJOR (主版本号)**: 不兼容的 API 修改
- **MINOR (次版本号)**: 向下兼容的功能新增
- **PATCH (修订号)**: 向下兼容的问题修复
- **SUFFIX (后缀)**: 可选，如 `beta`, `alpha`, `rc1`

### 版本号递增规则

```
4.7.0 -> 4.7.1   # 修复 bug
4.7.0 -> 4.8.0   # 新增功能
4.7.0 -> 5.0.0   # 重大更新
5.0.0 -> 5.0.0-beta  # 测试版本
```

## Gradle 配置文件格式

### 文件位置
```
godlike4/
└── gradlescript/
    └── gl_config.gradle
```

### 配置结构

```groovy
def app_configs = [:]
app_configs.version_code = "1"
app_configs.version_name = "4.8.0"
app_configs.app_tag = "godlike"
// ... 其他配置
```

### 语法说明

- 使用 Groovy 语言 (Gradle 的配置语言)
- `app_configs` 是一个 Map 类型的配置对象
- 版本号必须用**双引号**包裹 (字符串类型)
- 每行配置以换行符结束，无需分号

## 修改版本号的影响范围

### 构建系统
- Gradle 构建时读取该配置
- 生成的 APK 文件名可能包含版本号
- AndroidManifest.xml 中的版本信息自动更新

### 应用商店
- Google Play Store 使用 version_code 判断版本新旧
- 应用内显示的版本号来自 version_name
- 版本更新提示依赖版本号对比

### 用户体验
- 用户在"关于"页面看到 version_name
- 崩溃报告工具 (如 Bugly) 记录版本信息
- 版本更新推送基于版本号判断

## 版本发布流程建议

### 1. 开发分支
```
feature/xxx -> version_name = "4.8.0-dev"
```

### 2. 测试版本
```
develop -> version_name = "4.8.0-beta"
```

### 3. 预发布版本
```
release/4.8.0 -> version_name = "4.8.0-rc1"
```

### 4. 正式版本
```
master -> version_name = "4.8.0"
```

## 常见问题

### Q: 是否需要同时修改 version_code?
A: 通常需要。每次发布新版本时，version_code 应该递增。本 skill 暂时只修改 version_name，version_code 需要手动或通过 CI/CD 自动递增。

### Q: 修改版本号后需要重新编译吗?
A: 需要重新编译才能生效，但根据项目规范，skill 执行完毕后不自动编译，由用户决定何时编译。

### Q: 版本号能回退吗?
A: version_name 可以修改为任意值，但 version_code 不应回退，否则应用商店可能拒绝上传。

### Q: 支持哪些版本号格式?
A: 支持任意字符串格式，但建议遵循语义化版本号规范，保持 `x.y.z` 或 `x.y.z-suffix` 格式。

## 相关命令

### 查看当前版本
```bash
grep "version_name" gradlescript/gl_config.gradle
```

### 查看版本历史
```bash
git log --all --grep="version" --oneline
```

### 构建特定版本
```bash
./gradlew assembleRelease
```

## 参考资料

- [Semantic Versioning 官方规范](https://semver.org/lang/zh-CN/)
- [Android Versioning 官方文档](https://developer.android.com/studio/publish/versioning)
- [Gradle 配置指南](https://docs.gradle.org/current/userguide/build_environment.html)
