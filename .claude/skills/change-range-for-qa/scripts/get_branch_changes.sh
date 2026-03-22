#!/bin/bash
# 获取分支变更信息脚本
# 用法: ./get_branch_changes.sh [branch_name] [base_branch]

BRANCH=${1:-HEAD}
BASE=${2:-develop}

# 获取 merge-base
MERGE_BASE=$(git merge-base $BRANCH $BASE 2>/dev/null)

if [ -z "$MERGE_BASE" ]; then
    echo "Error: Cannot find merge-base between $BRANCH and $BASE"
    exit 1
fi

echo "=== Branch Changes Report ==="
echo "Branch: $BRANCH"
echo "Base: $BASE"
echo "Merge-base: $MERGE_BASE"
echo ""

echo "=== Commits (excluding merges) ==="
git log ${MERGE_BASE}..${BRANCH} --oneline --no-merges --first-parent
echo ""

echo "=== Changed Files Summary ==="
git diff ${MERGE_BASE}..${BRANCH} --stat
echo ""

echo "=== Changed Files List ==="
git diff ${MERGE_BASE}..${BRANCH} --name-only
