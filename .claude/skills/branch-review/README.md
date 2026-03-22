# Branch Review Skill

验证 Git 分支代码改动与需求文档的一致性，生成详细的验证报告。

## 功能特性

- ✅ 自动分析开发者提交的 commit
- ✅ 识别开发者负责的需求范围
- ✅ 验证需求实现的完整性
- ✅ 生成详细的验证报告
- ✅ 支持多种文档格式：PDF、DOCX、图片
- 🆕 **智能前置检查**：自动检测 DOCX 文件并引导安装

## 安装要求

### 基础要求
- Git
- Bash shell

### DOCX 文件支持（可选）

如果需要处理 Word 文档（.docx 格式），需要安装 `document-skills` 插件：

```bash
# 1. 添加 marketplace
claude plugin marketplace add https://github.com/anthropics/skills.git

# 2. 安装 document-skills 插件
claude plugin install document-skills

# 3. 重启 Claude Code（必需步骤）
# 按 Ctrl+C 退出当前会话，然后重新启动
```

**重要**：安装完成后必须**重启 Claude Code**，插件才会生效。

**说明**：
- PDF 和图片文件无需额外安装，开箱即用
- DOCX 文件需要 document-skills 插件支持
- 🆕 **全自动安装**：使用 DOCX 文件时，skill 会自动检测并安装插件
- 🔄 **重启提示**：安装后会提示重启 Claude Code，重启后即可使用
- 如果团队成员没有安装该插件，建议先将 DOCX 转换为 PDF 后使用

## 使用方法

### 基本用法

```
验证分支，文档在 /path/to/requirements.pdf
```

### 支持的文档格式

**✅ PDF 文件**（无需额外安装）
```
验证分支，文档在 /path/to/requirements.pdf
```

**✅ DOCX 文件**（需要安装 document-skills）
```
验证分支，文档在 /path/to/requirements.docx
```

**✅ 图片文件**（无需额外安装）
```
验证分支，文档在 /path/to/design.png
```

**✅ 文件夹**（支持混合格式）
```
验证分支，文档在 /path/to/docs/
```

**✅ 多个文件**
```
验证分支，文档是：/path/doc.pdf /path/design.png /path/spec.docx
```

## 常见问题

### Q: 使用 DOCX 文件时会发生什么？

**情况1: 已安装 document-skills**
- ✅ 自动解析 DOCX 文件，无需任何操作
- ✅ 继续正常的验证流程

**情况2: 未安装 document-skills**
- ⚠️ skill 会立即检测到并**自动安装**
- 🔄 安装完成后会提示你**重启 Claude Code**
- 📝 重启后重新运行验证命令即可
- 🛡️ 如果不想重启，也会提供 PDF 转换等替代方案

### Q: 出现 "Skill not found: document-skills:docx" 错误

**原因**: 没有安装 document-skills 插件

**说明**: 从 v1.2.0 开始，这个错误应该不会再出现，因为 skill 会在执行前主动检测并引导安装。如果仍然遇到，请升级到最新版本。

**解决方案**:
1. 添加 marketplace：`claude plugin marketplace add https://github.com/anthropics/skills.git`
2. 安装插件：`claude plugin install document-skills`
3. **重启 Claude Code**（按 Ctrl+C 退出，然后重启）
4. 重新运行验证命令
5. 或者将 DOCX 转换为 PDF 后使用

### Q: 为什么不内置 DOCX 支持？

**原因**:
- DOCX 解析需要额外的依赖库
- document-skills 提供了专业的文档处理能力
- 通过插件方式可以保持核心功能轻量化

### Q: 团队成员都需要安装 document-skills 吗？

**建议**:
- 如果团队经常使用 DOCX 格式，建议统一安装（一行命令即可）
- 如果只有少数人使用，可以由这些人负责转换 DOCX 为 PDF 后共享
- PDF 格式兼容性更好，建议作为标准格式

## 技术架构

```
branch-review/
├── SKILL.md                    # 主要技能定义和工作流程
├── README.md                   # 本文件：使用说明和安装指南
├── scripts/
│   ├── analyze_author_commits.sh   # 分析作者提交的 commit
│   └── list_requirement_docs.sh    # 列出文档文件
└── references/
    └── report-template.md      # 验证报告模板
```

## 更新日志

### v1.2.1 (2026-01-21) - 最新
- 🔄 **重启提示**：安装 document-skills 后会明确提示需要重启
- 📝 **文档修正**：修正所有"无需重启"的误导性说明
- 🎯 **流程优化**：引导用户在安装后重启并继续验证流程

### v1.2.0 (2026-01-20)
- 🆕 **智能前置检查**：自动检测 DOCX 文件是否可处理
- 🚀 **主动引导**：未安装 document-skills 时，提供清晰的安装指南
- 📚 **替代方案**：提供 PDF 转换和截图方案
- 🛡️ **避免错误**：检测到不支持时不再继续执行，避免产生错误

### v1.1.0
- ✅ 新增 DOCX 文件支持
- ✅ 集成 document-skills 自动解析
- ✅ 优化文档类型自动识别
- ✅ 添加安装指南和故障排除

### v1.0.0
- ✅ 支持 PDF 和图片文件
- ✅ 自动分析 Git commit
- ✅ 生成验证报告

## 贡献

如有问题或建议，欢迎反馈！
