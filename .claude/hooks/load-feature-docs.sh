#!/bin/bash
# 智能分支-文档关联 Hook
# 支持三级匹配策略：需求单号 > .branches 文件 > 中央配置
# 在会话启动时输出当前分支对应的文档目录，供 Claude 查阅
#
# 环境变量控制：
#   GODLIKE_FEATURE_DOCS_ENABLED=true  启用此功能
#   在 ~/.zshrc 中添加: export GODLIKE_FEATURE_DOCS_ENABLED=true

# 检查是否启用此功能，未启用则静默退出
[ "$GODLIKE_FEATURE_DOCS_ENABLED" != "true" ] && exit 0

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
FEATURES_DIR="$PROJECT_ROOT/docs/features"
MAPPING_FILE="$PROJECT_ROOT/.claude/feature-mapping.json"
GIT_USER=$(git config user.name 2>/dev/null || echo "")

# 如果没有分支信息，静默退出
[ -z "$BRANCH" ] && exit 0

DOCS_DIR=""
MATCH_METHOD=""

# ============================================
# 策略 1: 从分支名提取需求单号，自动匹配目录前缀
# ============================================
TICKET_ID=$(echo "$BRANCH" | grep -oE '[0-9]{5,7}' | head -1)
if [ -n "$TICKET_ID" ] && [ -d "$FEATURES_DIR" ]; then
  # 查找以该单号开头的目录
  MATCHED_DIR=$(find "$FEATURES_DIR" -maxdepth 1 -type d -name "${TICKET_ID}*" 2>/dev/null | head -1)
  if [ -n "$MATCHED_DIR" ]; then
    DOCS_DIR="${MATCHED_DIR#$PROJECT_ROOT/}"
    MATCH_METHOD="需求单号自动匹配 ($TICKET_ID)"
  fi
fi

# ============================================
# 策略 2: 扫描 .branches 文件查找匹配
# ============================================
if [ -z "$DOCS_DIR" ] && [ -d "$FEATURES_DIR" ]; then
  for branches_file in "$FEATURES_DIR"/*/.branches; do
    [ -f "$branches_file" ] || continue

    # 逐行检查是否匹配
    while IFS= read -r pattern || [ -n "$pattern" ]; do
      # 跳过注释和空行
      [[ "$pattern" =~ ^#.*$ ]] && continue
      [[ -z "$pattern" ]] && continue

      # 将通配符转换为正则表达式
      regex_pattern=$(echo "$pattern" | sed 's/\*/.*/')

      if echo "$BRANCH" | grep -qE "^${regex_pattern}$"; then
        DOCS_DIR="${branches_file%/.branches}"
        DOCS_DIR="${DOCS_DIR#$PROJECT_ROOT/}"
        MATCH_METHOD=".branches 文件匹配"
        break 2
      fi
    done < "$branches_file"
  done
fi

# ============================================
# 策略 3: 回退到中央配置文件
# ============================================
if [ -z "$DOCS_DIR" ] && [ -f "$MAPPING_FILE" ]; then
  DOCS_DIR=$(python3 -c "
import json
with open('$MAPPING_FILE') as f:
    print(json.load(f).get('$BRANCH', ''))
" 2>/dev/null)

  if [ -n "$DOCS_DIR" ]; then
    MATCH_METHOD="中央配置文件"
  fi
fi

# ============================================
# 输出结果
# ============================================
if [ -n "$DOCS_DIR" ]; then
  echo "
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【分支需求文档关联】
当前分支: $BRANCH
需求文档目录: $DOCS_DIR
匹配方式: $MATCH_METHOD"
  [ -f "$PROJECT_ROOT/$DOCS_DIR/README.md" ] && echo "需求概述文件: $PROJECT_ROOT/$DOCS_DIR/README.md"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"

  # 查找用户专属的当前目标文件
  HINT="重要提示：在实现任何功能之前，请先到上述目录查阅相关文档。"
  if [ -n "$GIT_USER" ]; then
    USER_TARGET_FILE="$PROJECT_ROOT/$DOCS_DIR/${GIT_USER}-当前目标.md"
    if [ -f "$USER_TARGET_FILE" ]; then
      echo "【当前开发者目标】
开发者: $GIT_USER
目标文件: $USER_TARGET_FILE
"
      HINT="重要提示：请先查阅上述目标文件了解你的当前任务。"
    fi
  fi
  echo "$HINT
"
fi

exit 0
