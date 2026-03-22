# 使用示例

本文档展示 `change-app-version` skill 的实际使用场景和效果。

## 基础示例

### 示例 1: 标准版本升级

**用户输入:**
```
修改 app 版本为 4.8.0
```

**Skill 执行流程:**
1. 提取目标版本号: `4.8.0`
2. 读取 `gradlescript/gl_config.gradle` 文件
3. 定位到第 135 行: `app_configs.version_name = "4.7.0"`
4. 使用 Edit 工具替换为: `app_configs.version_name = "4.8.0"`
5. 验证修改成功

**预期输出:**
```
✅ APP 版本号修改成功

配置文件: gradlescript/gl_config.gradle
旧版本: 4.7.0
新版本: 4.8.0

注意: 版本号修改完成,无需手动编译验证。
```

### 示例 2: 大版本升级

**用户输入:**
```
change version to 5.0.0
```

**修改前:**
```groovy
app_configs.version_name = "4.8.0"
```

**修改后:**
```groovy
app_configs.version_name = "5.0.0"
```

### 示例 3: 测试版本

**用户输入:**
```
app 版本改为 4.9.0-beta
```

**修改前:**
```groovy
app_configs.version_name = "4.8.0"
```

**修改后:**
```groovy
app_configs.version_name = "4.9.0-beta"
```

## 高级示例

### 示例 4: 预发布版本

**用户输入:**
```
升级版本到 5.0.0-rc1
```

**用途:** 发布候选版本 (Release Candidate)

**修改结果:**
```groovy
app_configs.version_name = "5.0.0-rc1"
```

### 示例 5: 补丁版本

**用户输入:**
```
修改 app 版本为 4.8.1
```

**用途:** 紧急修复 bug 的小版本更新

**修改前:**
```groovy
app_configs.version_name = "4.8.0"
```

**修改后:**
```groovy
app_configs.version_name = "4.8.1"
```

## 典型工作流

### 场景 1: 功能开发完成,准备发布新版本

```bash
# 1. 切换到 develop 分支
git checkout develop

# 2. 合并功能分支
git merge feature/new-feature

# 3. 使用 skill 升级版本号
# 用户: "修改 app 版本为 4.9.0"

# 4. 提交版本号变更
git add gradlescript/gl_config.gradle
git commit -m "#253400 升级 APP 版本至 4.9.0"

# 5. 构建测试
./gradlew assembleDebug

# 6. 推送到远程
git push
```

### 场景 2: 热修复发布

```bash
# 1. 从 master 创建热修复分支
git checkout -b hotfix/4.8.1 master

# 2. 修复 bug
# ... 代码修改 ...

# 3. 升级补丁版本号
# 用户: "app 版本改为 4.8.1"

# 4. 提交修复和版本号
git add .
git commit -m "#253401 修复严重 bug,发布 4.8.1"

# 5. 合并回 master 和 develop
git checkout master
git merge hotfix/4.8.1
git checkout develop
git merge hotfix/4.8.1
```

### 场景 3: 测试版本迭代

```bash
# Beta 1
# 用户: "修改 app 版本为 5.0.0-beta1"

# 测试并修复 bug...

# Beta 2
# 用户: "修改 app 版本为 5.0.0-beta2"

# 继续测试...

# Release Candidate
# 用户: "修改 app 版本为 5.0.0-rc1"

# 最终发布
# 用户: "修改 app 版本为 5.0.0"
```

## 触发关键词总结

Skill 能识别的各种表达方式:

### 中文触发词
- "修改 app 版本为 X.X.X"
- "app 版本改为 X.X.X"
- "升级版本到 X.X.X"
- "更新版本号为 X.X.X"
- "设置 app 版本 X.X.X"
- "版本号改成 X.X.X"

### 英文触发词
- "change version to X.X.X"
- "update version to X.X.X"
- "set version to X.X.X"
- "upgrade version to X.X.X"
- "change app version to X.X.X"

### 混合表达
- "change app 版本 to X.X.X"
- "修改 version 为 X.X.X"

## 注意事项

### ✅ 推荐做法

1. **遵循语义化版本规范**
   - 主版本号: 重大更新 (4.x.x -> 5.0.0)
   - 次版本号: 新功能 (4.7.x -> 4.8.0)
   - 修订号: Bug 修复 (4.8.0 -> 4.8.1)

2. **提交版本号变更到 Git**
   ```bash
   git add gradlescript/gl_config.gradle
   git commit -m "#ISSUE_ID 升级版本至 X.X.X"
   ```

3. **同时考虑 version_code**
   - version_name: 用户可见 (如 "4.8.0")
   - version_code: 系统内部编号 (必须递增)

### ❌ 避免的做法

1. **不要随意降低版本号**
   - 可能导致应用商店上传失败
   - 用户无法收到更新推送

2. **不要跳过测试阶段直接发布**
   - 建议: 4.8.0-beta -> 4.8.0-rc1 -> 4.8.0

3. **不要忘记更新 version_code**
   - 每次修改 version_name 时,应同步递增 version_code

## 相关 Skills

- `jenkins-test`: 修改版本号后,可使用此 skill 提交测试打包
- `fast-update`: 拉取最新代码后,可能需要同步版本号

## 常见问题

**Q: Skill 执行后需要重启 Android Studio 吗?**
A: 不需要,但需要重新同步 Gradle 项目 (Sync Now)。

**Q: 修改版本号会影响正在运行的调试版本吗?**
A: 不会,只影响下次编译生成的 APK。

**Q: 能否同时修改多个配置项?**
A: 当前 skill 专注于修改 version_name。如需修改其他配置,建议手动编辑或创建专用 skill。

**Q: Skill 是否会自动提交 Git?**
A: 不会,需要手动执行 `git add` 和 `git commit`。
