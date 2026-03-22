#!/bin/bash
# 分析开发者在分支中的提交和改动
# 用法: ./analyze_author_commits.sh [branch_name] [author_name] [base_branch]

BRANCH=${1:-HEAD}
AUTHOR=$2
BASE=$3

if [ -z "$AUTHOR" ]; then
    echo "Error: Author name is required"
    echo "Usage: $0 <branch_name> <author_name> [base_branch]"
    exit 1
fi

# 自动检测 base branch (如果未提供)
if [ -z "$BASE" ]; then
    echo "自动检测 base branch..."

    # 优先级1: 检查是否从 develop 拉出
    if git show-ref --verify --quiet refs/heads/develop; then
        # 检查当前分支是否从 develop 分叉
        if git merge-base --is-ancestor develop $BRANCH 2>/dev/null; then
            BASE="develop"
            echo "✅ 检测到从 develop 拉出的分支"
        fi
    fi

    # 优先级2: 如果不是从 develop，查找最近的 release 分支
    if [ -z "$BASE" ]; then
        # 查找所有 release 分支
        RELEASE_BRANCHES=$(git for-each-ref --format='%(refname:short)' refs/heads/release/ 2>/dev/null | sort -V -r)

        for release in $RELEASE_BRANCHES; do
            # 检查当前分支是否从这个 release 分叉
            if git merge-base --is-ancestor $release $BRANCH 2>/dev/null; then
                BASE="$release"
                echo "✅ 检测到从 $release 拉出的分支"
                break
            fi
        done
    fi

    # 优先级3: 回退到 main/master（基本不会到这里）
    if [ -z "$BASE" ]; then
        if git show-ref --verify --quiet refs/heads/main; then
            BASE="main"
            echo "⚠️  使用默认 base: main"
        elif git show-ref --verify --quiet refs/heads/master; then
            BASE="master"
            echo "⚠️  使用默认 base: master"
        else
            echo "Error: Cannot auto-detect base branch"
            echo "Please specify base branch explicitly: $0 <branch> <author> <base-branch>"
            exit 1
        fi
    fi

    echo ""
fi

# 检查分支是否已合并到 base
MERGED=false
ANALYSIS_RANGE=""

if git merge-base --is-ancestor $BRANCH $BASE 2>/dev/null; then
    MERGED=true
    echo "检测到分支已合并到 $BASE，尝试自动查找合并提交..."
    echo ""

    # 提取分支名（去掉refs/heads/等前缀）
    BRANCH_NAME=$(echo $BRANCH | sed 's/.*\///')

    # 方法1: 查找包含分支名的merge commit
    MERGE_COMMIT=$(git log --merges $BASE --grep="$BRANCH_NAME" --format=%H -1 2>/dev/null)

    # 方法2: 如果方法1失败，查找最近的将$BRANCH合并进来的commit
    if [ -z "$MERGE_COMMIT" ]; then
        # 获取$BRANCH的当前commit
        BRANCH_TIP=$(git rev-parse $BRANCH 2>/dev/null)

        if [ -n "$BRANCH_TIP" ]; then
            # 查找所有merge commits，找到包含$BRANCH_TIP的那个
            for commit in $(git log --merges $BASE --format=%H --since="3 months ago"); do
                # 检查这个merge commit的第二个parent是否包含BRANCH_TIP
                PARENT2=$(git rev-parse ${commit}^2 2>/dev/null)
                if [ -n "$PARENT2" ]; then
                    # 检查BRANCH_TIP是否是PARENT2的祖先或就是PARENT2
                    if git merge-base --is-ancestor $BRANCH_TIP $PARENT2 2>/dev/null || [ "$BRANCH_TIP" = "$PARENT2" ]; then
                        MERGE_COMMIT=$commit
                        break
                    fi
                fi
            done
        fi
    fi

    if [ -n "$MERGE_COMMIT" ]; then
        echo "✅ 找到合并提交: ${MERGE_COMMIT:0:8}"
        echo "   $(git log --format=%s -1 $MERGE_COMMIT)"

        # 获取merge commit的两个parents
        PARENT1=$(git rev-parse ${MERGE_COMMIT}^1 2>/dev/null)  # base分支的parent
        PARENT2=$(git rev-parse ${MERGE_COMMIT}^2 2>/dev/null)  # feature分支的parent

        if [ -n "$PARENT2" ]; then
            # 找到原始分叉点
            MERGE_BASE=$(git merge-base $PARENT1 $PARENT2 2>/dev/null)

            if [ -n "$MERGE_BASE" ]; then
                echo "✅ 找到原始分叉点: ${MERGE_BASE:0:8}"
                echo "分析范围: ${MERGE_BASE:0:8}..${PARENT2:0:8}"
                echo ""
                ANALYSIS_RANGE="${MERGE_BASE}..${PARENT2}"
            fi
        fi
    fi

    # 如果无法自动找到，提示用户手动操作
    if [ -z "$ANALYSIS_RANGE" ]; then
        echo "=========================================="
        echo "⚠️  无法自动识别合并范围"
        echo "=========================================="
        echo ""
        echo "分支已合并到 $BASE，但无法自动找到合并提交。"
        echo ""
        echo "建议操作："
        echo "1. 查看该作者最近的提交："
        echo "   git log --author='$AUTHOR' -n 20 --oneline"
        echo ""
        echo "2. 如果知道原始分叉点，可以指定："
        echo "   bash $0 $BRANCH '$AUTHOR' $BASE <原始分叉点>"
        echo ""
        echo "3. 按时间范围查看："
        echo "   git log --author='$AUTHOR' --since='2 weeks ago' --oneline"
        echo ""
        exit 1
    fi
fi

echo "=== Branch Review Analysis ==="
echo "Branch: $BRANCH"
echo "Author: $AUTHOR"
echo "Base: $BASE"
if [ "$MERGED" = true ]; then
    echo "Status: 已合并（使用 merge commit 分析）"
fi
echo ""

# 确定分析范围
if [ -n "$ANALYSIS_RANGE" ]; then
    # 已合并的分支，使用找到的范围
    RANGE="$ANALYSIS_RANGE"
else
    # 未合并的分支，使用标准方式
    RANGE="$BRANCH --not $BASE"
fi

echo "=== Author's Commit Count ==="
COMMIT_COUNT=$(git log --author="$AUTHOR" --oneline --no-merges $RANGE | wc -l | xargs)
echo "Total commits: $COMMIT_COUNT"
echo ""

if [ "$COMMIT_COUNT" -eq 0 ]; then
    echo "⚠️  未找到作者 '$AUTHOR' 在此分支的提交"
    echo ""
    echo "可能的原因："
    echo "1. 作者名称不匹配（请检查 git config user.name）"
    echo "2. 该作者没有在此分支提交过代码"
    echo "3. 所有提交都是 merge commits（已被 --no-merges 过滤）"
    echo ""
    exit 0
fi

echo "=== Author's Commits (Latest 20) ==="
git log --author="$AUTHOR" --oneline --no-merges $RANGE | head -20
echo ""

echo "=== Author's Changed Files (with stats) ==="
git log --author="$AUTHOR" --stat --no-merges --pretty=format:"" $RANGE | grep -E '^\s+[^ ]' | sort | uniq
echo ""
echo ""

echo "=== Author's Changed Files (by frequency) ==="
git log --author="$AUTHOR" --name-only --no-merges --pretty=format:"" $RANGE | grep -v '^$' | sort | uniq -c | sort -rn | head -30
echo ""

echo "=== Author's File Changes (grouped by directory) ==="
git log --author="$AUTHOR" --name-only --no-merges --pretty=format:"" $RANGE | grep -v '^$' | sort | uniq | awk -F'/' '{
    if (NF > 1) {
        dir = $1;
        for (i = 2; i < NF; i++) dir = dir "/" $i;
        print dir "/" $NF;
    } else {
        print $0;
    }
}' | head -50
echo ""

echo "=== Lines Changed by Author ==="
git log --author="$AUTHOR" --numstat --no-merges --pretty=format:"" $RANGE | awk '{add+=$1; del+=$2} END {print "Lines added: " add "\nLines deleted: " del "\nNet change: " (add-del)}'
echo ""

echo "=== Analysis Complete ==="
