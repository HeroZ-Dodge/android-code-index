---
name: codemaker-proxy
description: |
  通过 CodeMaker CLI 将问题转发给大模型，获取另一个 AI 的回答作为参考。
  当用户说"用 codemaker 问一下"、"问问 codemaker"、"转发给 codemaker"、"让 codemaker 看看"、"codemaker 帮我"或明确想通过 codemaker 工具获取 AI 回答时触发。
  文档地址：https://docs.popo.netease.com/team/pc/codemaker/pageDetail/2ce6945997ae4ebf931457def1d04bab
---

# CodeMaker Proxy

通过 `codemaker run` 将用户问题转发给 CodeMaker CLI，并将回答呈现给用户。

## 可用模型

模型前缀统一为 `netease-codemaker/`，常用选项：

| 模型 | 特点 |
|------|------|
| `netease-codemaker/claude-sonnet-4-6` | **默认**，平衡性能与速度 |
| `netease-codemaker/claude-opus-4-6` | 最强推理和编码 |
| `netease-codemaker/gpt-5.2-codex-2026-01-14` | 深度编码 |
| `netease-codemaker/gpt-5.2-2025-12-11` | GPT 系列旗舰 |
| `netease-codemaker/kimi-k2.5` | 性价比高 |
| `netease-codemaker/claude-haiku-4-5-20251001` | 快速轻量 |

## 执行流程

### 1. 检查安装

```bash
codemaker --version
```

若命令不存在，提示用户安装：
```bash
curl -fsSL https://codemaker.netease.com/package/codemaker-cli/install | bash
```

### 2. 构建并执行命令

**必须通过 `-m` 指定模型**，默认使用 `netease-codemaker/claude-sonnet-4-6`：

```bash
codemaker run -m "netease-codemaker/claude-sonnet-4-6" "用户的问题"
```

用户若指定其他模型，替换模型名即可：
```bash
codemaker run -m "netease-codemaker/claude-opus-4-6" "用户的问题"
```

附加文件（用户提到具体文件时用 `-f`）：
```bash
codemaker run -m "netease-codemaker/claude-sonnet-4-6" -f path/to/file "用户的问题"
# 多文件：-f file1 -f file2
```

### 3. 输出结果

将 codemaker 的回答完整呈现给用户，注明来源为 CodeMaker CLI。

## 注意事项

- **必须指定 `-m` 参数**，默认模型为 `netease-codemaker/claude-sonnet-4-6`
- 用户明确要求其他模型时，从上方模型表选择对应名称
- 命令执行超时建议设置 120 秒
- 若返回登录错误，提示用户先在终端执行 `codemaker`，运行 `/login` 完成登录
