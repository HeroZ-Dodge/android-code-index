---
name: branch-review
description: "Validates developer's code changes against requirement documents by analyzing Git commits and generating comprehensive verification reports. Automatically filters commits by author to identify scope, matches changed files to requirements, verifies implementation completeness, and produces detailed reports with code locations, quality assessment, and testing recommendations. Use when: (1) Validating branch implementation before code review, (2) Generating self-check reports before testing, (3) Confirming all assigned requirements are implemented, (4) Identifying scope of work in feature branches. Triggers: \"验证分支\", \"branch review\", \"检查分支改动\", \"validate branch\", \"check my branch\", \"review my changes\", \"生成验证报告\", or when mentioning requirement documents/需求文档 verification."
---

# Branch Review

Validate code changes in a Git branch against requirement documents and generate comprehensive verification reports.

## Prerequisites

**Required tools:**
- Git (for commit analysis)
- Bash shell (for running helper scripts)

**For DOCX file support:**
- Add anthropic-agent-skills marketplace and install document-skills:
  ```bash
  # Step 1: Add the marketplace
  claude plugin marketplace add https://github.com/anthropics/skills.git

  # Step 2: Install document-skills plugin
  claude plugin install document-skills

  # Step 3: Restart Claude Code to activate the plugin
  # You can use Ctrl+C to exit, then restart the session
  ```
- **IMPORTANT**: After installation, you must **restart Claude Code** for the plugin to become available
- The `document-skills` will be available for parsing .docx files after restart

**Without document-skills:**
- You can still use PDF files (.pdf) and images (.png, .jpg, .jpeg)
- Or convert DOCX to PDF manually before using this skill

## Workflow

### 1. Gather Information

Ask the user for:
- **Branch name**: The Git branch to analyze (e.g., `feature/user-authentication`)
  - If not provided, use current branch: `git branch --show-current`
- **Base branch**: The branch this feature branched from (e.g., `develop`, `master`, `main`)
  - If not provided, auto-detect by checking: `develop` → `main` → `master`
- **Requirements document path**: One of the following:
  - Absolute path to a single PDF file (e.g., `/path/to/requirements.pdf`)
  - Absolute path to a folder containing multiple PDF files and/or images (e.g., `/path/to/requirements/`)
  - Multiple file paths (separated by spaces or new lines)

**Supported formats**: PDF files (.pdf), Word documents (.docx), and images (.png, .jpg, .jpeg)

**Note**: DOCX support requires document-skills (will be auto-installed if needed in Step 2)

**Auto-detection example**:
```bash
# Detect current branch
CURRENT_BRANCH=$(git branch --show-current)

# Detect base branch (priority: develop > main > master)
if git show-ref --verify --quiet refs/heads/develop; then
    BASE_BRANCH="develop"
elif git show-ref --verify --quiet refs/heads/main; then
    BASE_BRANCH="main"
else
    BASE_BRANCH="master"
fi

echo "Analyzing branch: $CURRENT_BRANCH (base: $BASE_BRANCH)"
```

### 2. Check DOCX Support (If Needed)

**IMPORTANT**: Only perform this check if the user provided a DOCX file path.

**Step 2.1: Detect if Document is DOCX**

Check if any of the provided document paths is a DOCX file:
```bash
# Check file extension
if [[ "$DOC_PATH" == *.docx ]]; then
    echo "DOCX file detected, checking document-skills availability..."
fi
```

**Step 2.2: Check Available Skills**

When a DOCX file is detected, check if `document-skills:docx` is in the available skills list:
- The Skill tool's description includes a list of "Available skills"
- Look for `document-skills:docx` in that list
- If NOT found → Auto-install it (Step 2.3)
- If found → Continue to Step 3

**Step 2.3: Auto-Install document-skills (If NOT Available)**

If DOCX file is detected but `document-skills:docx` is NOT in the available skills list, **automatically install it for the user**:

**Action 2.3.1: Inform User**

```markdown
⚠️ **检测到 DOCX 文件，需要安装 document-skills 插件**

检测到需求文档是 DOCX 格式 (.docx)，但当前环境未安装 document-skills。

正在自动安装...
```

**Action 2.3.2: Auto-Install**

Execute the following bash commands sequentially:

```bash
# 1. Add marketplace
claude plugin marketplace add https://github.com/anthropics/skills.git

# 2. Install document-skills plugin
claude plugin install document-skills
```

**Action 2.3.3: Prompt User to Restart**

After installation completes, inform the user:

```markdown
✅ **document-skills 安装完成！**

**下一步：重启 Claude Code**

插件已安装，但需要重启才能生效。

请按以下步骤操作：
1. 按 **Ctrl+C** 退出当前 Claude Code 会话
2. 重新启动 Claude Code
3. 重新运行验证命令：`验证分支，文档在 <文档路径>`

重启后，DOCX 文件将自动解析，无需任何额外操作。

---

**可选方案**（如果不想重启）：
- 转换为 PDF：`soffice --headless --convert-to pdf "需求文档.docx"`
- 或使用文档截图（PNG/JPG 格式）
```

**CRITICAL**:
- Do NOT proceed with the verification workflow after installation
- STOP and wait for user to restart
- The user must restart Claude Code for the plugin to become available

### 3. Get Git User Identity

```bash
git config user.name
git config user.email
```

This identifies the author to filter commits.

### 4. Analyze User's Commits

**Step 4.1: Run the analysis script**

```bash
# The script will auto-detect base branch (develop > main > master)
bash .claude/skills/branch-review/scripts/analyze_author_commits.sh <branch-name> "<author-name>"

# Or explicitly specify base branch
bash .claude/skills/branch-review/scripts/analyze_author_commits.sh <branch-name> "<author-name>" <base-branch>

# Examples:
# Auto-detect base: bash analyze_author_commits.sh feature/xxx "username"
# Explicit base: bash analyze_author_commits.sh feature/xxx "username" develop
```

**Auto-detection priority**: develop → main → master

**How it works**: The script uses `git log $BRANCH --not $BASE` to find commits that exist in the branch but not in the base branch. This accurately identifies "commits that belong to this branch".

**Key features**:
- ✅ Auto-detects base branch if not specified (develop > main > master)
- ✅ Only counts commits that belong to the feature branch
- ✅ Automatically filters out merge commits (--no-merges)
- ✅ Works correctly even if branch pulled updates from base
- ⚠️ **Limitation**: If branch is already merged to base, script will detect and show warning with alternatives

This script provides:
- Commit count (ONLY commits belonging to this branch)
- Commit list (latest 20)
- Changed files with statistics
- Files sorted by frequency
- Lines added/deleted summary

**Why this approach**:
- ❌ `git log feature-branch` → Counts ALL commits including inherited history
- ❌ `git log merge-base..feature-branch` → Fails after branch is merged
- ✅ `git log feature-branch --not base-branch` → Accurate before merge, with clear warning after merge

### 5. Identify Key Changed Files

From the changed files, identify the main feature files (exclude auto-generated, config, or trivial changes):

```bash
# Get unique files in specific directories
git log --author="<username>" --name-only --pretty=format:"" --no-merges <branch-name> -- "path/to/feature/**" | sort | uniq
```

Focus on files with substantial changes (>50 lines).

### 6. Read Requirements Documents

**Determine document type and read accordingly:**

**Step 6.1: Detect File Type**

For each document path provided, detect its file extension:
```bash
# Check file extension
case "$DOC_PATH" in
    *.pdf)   FILE_TYPE="pdf" ;;
    *.docx)  FILE_TYPE="docx" ;;
    *.png|*.jpg|*.jpeg)  FILE_TYPE="image" ;;
    *)       FILE_TYPE="folder" ;;
esac
```

**Step 6.2: Read Based on File Type**

**Option A: Single PDF file**
```bash
# Check if path is a single PDF file
if [ -f "$DOC_PATH" ] && [[ "$DOC_PATH" == *.pdf ]]; then
    # Read the PDF file directly using Read tool
    Read tool: $DOC_PATH
fi
```

**Option B: Single DOCX file (Word document)**
```bash
# Check if path is a single DOCX file
if [ -f "$DOC_PATH" ] && [[ "$DOC_PATH" == *.docx ]]; then
    # Use document-skills:docx to parse the DOCX file
    # This requires document-skills to be installed
    Skill tool: skill="document-skills:docx", args="$DOC_PATH"

    # After parsing, the content will be available for analysis
    # Continue with the normal verification workflow
fi
```

**IMPORTANT for DOCX processing:**
- **Requires**: `document-skills` marketplace plugin must be installed
- If document-skills is not available, the skill will **automatically install it** in Step 2
- After auto-installation, you must **restart Claude Code** for the plugin to work
- User will be prompted to restart and re-run the verification command
- The skill will automatically convert the document to markdown format after restart
- Do NOT attempt to use Read tool directly on .docx files

**Auto-Installation Process**:
1. Skill detects DOCX file and missing document-skills (Step 2)
2. Automatically runs installation commands
3. Prompts user to restart Claude Code
4. User restarts and re-runs verification
5. DOCX file is automatically parsed

**Option C: Folder with multiple documents**
```bash
# Use the helper script to list all requirement documents
bash .claude/skills/branch-review/scripts/list_requirement_docs.sh "$FOLDER_PATH"

# Read each document based on its type
for file in "$FOLDER_PATH"/*; do
    if [[ "$file" == *.pdf ]]; then
        Read tool: $file
    elif [[ "$file" == *.docx ]]; then
        Skill tool: skill="document-skills:docx", args="$file"
    elif [[ "$file" == *.png ]] || [[ "$file" == *.jpg ]] || [[ "$file" == *.jpeg ]]; then
        Read tool: $file
    fi
done
```

**Option D: Multiple file paths**
```bash
# Read each provided path based on type
for path in $PATHS; do
    if [[ "$path" == *.pdf ]]; then
        Read tool: $path
    elif [[ "$path" == *.docx ]]; then
        Skill tool: skill="document-skills:docx", args="$path"
    elif [[ "$path" == *.png ]] || [[ "$path" == *.jpg ]] || [[ "$path" == *.jpeg ]]; then
        Read tool: $path
    fi
done
```

**Understand from all documents:**
- Overall requirements structure
- Specific feature requirements
- Technical specifications
- Acceptance criteria
- UI designs (from images)

**Document Processing Notes:**
- PDF files: Use Read tool (native support)
- DOCX files: Use `Skill tool` with `document-skills:docx`
- Images: Use Read tool (native multimodal support)
- After processing any document type, continue with normal verification workflow

### 7. Match Code to Requirements

Based on the changed files, identify which requirements the developer is responsible for:

**Matching logic:**
- If code changes include `AuthenticationService.kt` → Developer handles authentication requirements
- If code changes include `DualColumnScoreBoardDetailHolder.kt` → Developer handles dual-column theme card requirements
- If code changes include share/poster related files → Developer handles share poster requirements

**Key principle:** The developer's scope is determined by what they actually implemented, not by the entire requirements document.

### 8. Analyze Implementation Completeness

**IMPORTANT: Optimize for performance while ensuring completeness**

**Step 8.1: Categorize Changed Files (Don't skip important ones)**

From the changed files list, categorize into:

**A. 真正的噪音（可以跳过）**:
- Auto-generated files: `build/`, `*.generated.kt`, `.gradle/`
- Build artifacts: `*.apk`, `*.jar`, `*.class`
- IDE files: `.idea/`, `*.iml`

**B. 核心实现文件（必须验证，即使改动小）**:
- Feature code: `*.kt`, `*.java` in `src/main/`
- Layout files: `*.xml` in `res/layout/`
- Important configs that match requirements

**C. 辅助文件（根据需求决定是否验证）**:
- Resource files: strings, colors, dimensions
- Gradle configs, manifests
- Test files

**Key principle**: File importance is determined by **relevance to requirements**, not by lines changed.

**Step 8.2: Smart Verification Strategy**

**For large changes (>20 files), use a hybrid approach:**

1. **Quick scan all files with git diff**:
```bash
# Get overview of all changes (fast, shows what changed)
git diff develop..feature-branch --stat
git diff develop..feature-branch -- path/to/file.kt | head -100
```

2. **Use Grep for keyword verification** (faster than reading full files):
```bash
# Verify specific features are implemented
grep -n "关键词" file1.kt file2.kt file3.kt
```

3. **Read full files selectively**:
   - Read complex files where diff isn't enough to understand
   - Limit to **5-10 most complex/critical files**
   - For other files, git diff + grep is sufficient

**Step 8.3: Verification Checklist**

For each requirement:
1. **Identify related files** from git log output (already done in step 3)
2. **Check commit messages** for any adjustments or modifications
3. **Use git diff** to see actual changes in those files
4. **Use grep** to verify key features/methods are present
5. **Read full file** only if diff is unclear or logic is complex
6. **Reference code locations** using file:line from grep/diff results

**CRITICAL: Conflict Resolution Rule**

When there's inconsistency between requirement docs and commit messages:

**✅ Commit message takes priority** (if it explicitly mentions the change)

Example:
- 需求文档: "超时时长设置为 6 秒"
- Commit 说明: "调整超时时长从 6 秒改为 10 秒"
- 实际代码: `timeout = 10`
- **验证结果**: ✅ 已完成（以 commit 说明为准）

**Why**:
- Commit messages reflect actual implementation decisions
- Requirements may be adjusted during development
- Developer's commit explanation shows intentional changes

**How to verify**:
1. If code differs from requirement, check commit message first
2. If commit explicitly mentions adjustment/modification → Mark as ✅ completed
3. If commit doesn't mention it → Mark as ⚠️ deviation and flag for review
4. Always note in report: "已根据 commit [hash] 调整，与原需求不同"

**Performance vs Completeness Balance**:
- ✅ Use git diff for all files (fast, shows changes)
- ✅ Use grep for keyword verification (fast, targeted)
- ✅ Read full files only when necessary (slow, but thorough)
- ❌ Don't read all files completely (slow, unnecessary)

### 9. Generate Verification Report

**CRITICAL: Scope Determination Logic**

The verification scope is determined by **developer's actual commits and changed files**, NOT by issue numbers or requirement IDs.

**Correct approach:**
1. Analyze developer's commits → Identify changed files
2. Match changed files to requirement document content
3. Verify requirements related to those files
4. Optionally extract issue numbers from commit messages as metadata

**Wrong approach (DO NOT do this):**
- ❌ Ask user for issue number first
- ❌ Use issue number to filter which requirements to verify
- ❌ Ignore code changes that don't match a specific issue number

**Report Focus**: Keep the report concise and focused on these THREE key points:
1. **需求改动点** - Extract all requirement changes from documents
2. **使用者负责范围** - Determine user's scope via their commits (may be multi-person collaboration)
3. **完整性验证** - Verify user's assigned requirements are fully implemented without omissions or errors

Create a simplified Markdown report with:

#### 1. 报告概览 (Report Overview)
- 分支名称 (Branch name)
- 开发者 (Developer name from git user)
- 提交数量 (Commit count)
- 代码变更量 (Lines added/deleted summary)
- **可选**: 涉及需求编号 (Extract #XXX from commit messages, informational only)

#### 2. 需求改动点 (Requirement Changes)
**From requirement documents, list ALL feature requirements:**
- Use a simple numbered list or table
- Format: `需求点 X: [简短描述]`
- Keep descriptions concise (1-2 lines per requirement)
- DO NOT include detailed specs or implementation details here

#### 3. 使用者负责范围 (User's Scope)
**Based on user's commits, determine which requirements they are responsible for:**
- List only the requirements assigned to THIS user
- Format: Table with columns: 需求点 | 相关文件 | 负责人
- Clearly mark: ✅ 本人负责 / ❌ 其他人负责 (name)
- **Key principle**: Scope is determined by actual code changes, not entire doc

#### 4. 完整性验证 (Completeness Verification)
**For user's assigned requirements only, verify:**

Table format:
| 需求点 | 状态 | 验证结果 | 关键代码位置 |
|-------|------|---------|-------------|
| 需求 X | ✅ 已完成 / ❌ 未完成 / ⚠️ 部分完成 | 简短说明 | file.kt:line |

**Verification criteria:**
- ✅ **已完成**: Fully implemented, matches requirements
- ⚠️ **部分完成**: Implemented but missing some aspects (list what's missing)
- ❌ **未完成**: Not implemented or significantly different from requirements

**DO NOT include:**
- Detailed code snippets (only key file:line references)
- Lengthy implementation explanations
- Code quality assessment (unless critical issues found)

#### 5. 验证结论 (Conclusion)
**Simple summary:**
- 总体完成度: X% (percentage of assigned requirements completed)
- 遗漏项: [List any missing implementations]
- 错误实现: [List any implementations that deviate from requirements]
- 建议: [Only critical suggestions, if any]

#### 6. Code Review 提示 (CONDITIONAL)
**根据完成度决定是否显示此提示**：

**当完成度 = 100% 时（所有负责的需求都已完成）**，在报告末尾添加：

```markdown
---

## ✅ 下一步：代码审查

所有需求已完成，建议进行深度代码审查以确保代码质量。

**审查重点**：
- 边界条件和异常处理
- 线程安全和内存泄漏
- 性能优化点
- 与需求文档的一致性

**开始审查**: 输入 `code review` 或 `/code-review`
```

**当完成度 < 100% 时（有未完成或部分完成的需求）**，在报告末尾添加：

```markdown
---

## ⚠️ 下一步：完成剩余需求

检测到部分需求尚未完成，建议先完成所有需求点后再进行代码审查：

[列出未完成的需求点]

完成后可运行验证分支来确认，然后进行代码审查。
```

### 10. Save and Output Report

**Report naming convention:**
```
<需求名称>-<分支名>-验证报告.md
```

- **需求名称**: Extract from requirement document filename (without extension), or use first few words from document title
- **分支名**: Use the actual branch name (sanitize special characters)
- Example: `评分榜产品形态升级二期-featrue_4.10.0_score_rank_update2-验证报告.md`

**Report metadata (header section):**
- ✅ Branch name, developer name, commit count, code changes
- ✅ List of requirement documents used
- ✅ **Optional**: Inferred issue numbers from commit messages (e.g., extract #XXX patterns)
- ❌ **Do NOT use** issue numbers to limit verification scope
- ❌ **Do NOT require** user to provide issue numbers

**Key principle**: Verification scope is determined by developer's commits and changed files, NOT by issue numbers.

**Steps:**
1. **Save the report** to repository root with the naming convention above
2. **Output the report content** to the user immediately after saving

**Important**: Keep the output concise and focused on the three key verification points.

## Example Usage

### Example 1: Single PDF file

**User**: "帮我验证 featrue/4.10.0_score_rank_update2 分支的代码改动，需求文档是 /Users/whimaggot/Downloads/需求文档.pdf"

**Process**:
1. Get git user: `gzhuangweiqiang`
2. Analyze commits: Find 21 commits by this user
3. Identify changed files: `DualColumnScoreBoardDetailHolder.kt`, `ScoreCommentShareFragment.kt`, etc.
4. Read single PDF requirements document
5. Match scope: Based on changed files, developer handles "主题小卡" and "分享海报" requirements
6. Verify implementation against matched requirements
7. Generate comprehensive report

### Example 2: Single DOCX file (Word document)

**User**: "验证分支，文档在 /Users/whimaggot/Downloads/评分榜产品形态升级二期.docx"

**Process**:
1. Get git user and current branch info
2. Analyze commits by this user
3. Identify changed files
4. **Detect DOCX file type → Use Skill tool with document-skills:docx**
5. Parse DOCX to markdown, extract requirements
6. Match scope based on changed files
7. Verify implementation completeness
8. Generate comprehensive report

**Key difference**: DOCX files are automatically parsed using document-skills, then proceed with normal workflow.

### Example 3: Folder with multiple documents

**User**: "验证分支 feature/user-auth，需求文档在 /Users/whimaggot/Documents/项目需求/ 文件夹里"

**Process**:
1. Get git user and branch info
2. List all files in folder: `需求文档.pdf`, `UI设计稿.png`, `接口文档.docx`
3. Read all documents:
   - PDF files → Use Read tool
   - DOCX files → Use Skill tool with document-skills:docx
   - Images → Use Read tool
4. Analyze commits and changed files
5. Cross-reference code with all requirement documents
6. Generate comprehensive report

### Example 4: Multiple specific files

**User**: "验证分支，需求文档是：/path/doc1.pdf /path/doc2.docx /path/design.png"

**Process**:
1. Parse multiple file paths
2. Read each document based on type:
   - doc1.pdf → Read tool
   - doc2.docx → Skill tool (document-skills:docx)
   - design.png → Read tool
3. Combine information from all documents
4. Perform verification
5. Generate report

## Performance Optimization Guidelines

**For large changes (>20 files or >1000 lines), use a hybrid approach:**

### Three-Tier Strategy:

**Tier 1: Fast Overview (All Files)**
- Use `git diff --stat` to see all changed files and line counts
- Use `git diff` to preview changes (faster than reading full files)
- Time cost: Seconds

**Tier 2: Targeted Verification (All Relevant Files)**
- Use `grep` to verify features in all requirement-related files
- Check if key methods/classes mentioned in requirements exist
- Time cost: Seconds

**Tier 3: Deep Reading (Selected Files Only)**
- Read full files **only** for complex logic that can't be verified via diff/grep
- Limit to 5-10 most critical files
- Time cost: Minutes

### What NOT to Skip:

**⚠️ Don't filter out based on lines changed alone**
- A 2-line change could be a critical bug fix
- A 5-line config change could be a key requirement
- Filter by file type (build artifacts), NOT by change size

**✅ DO skip these (true noise)**:
- `build/`, `*.apk`, `*.class` (build artifacts)
- `*.generated.*`, `**/generated/**` (auto-generated)
- `.gradle/`, `.idea/`, `*.iml` (IDE/build system)

**✅ DO verify these (even if small changes)**:
- All `.kt`, `.java` files in `src/main/`
- Layout/resource files mentioned in requirements
- Config changes that match requirement scope

### Performance Target:
- Small changes (<10 files): Complete in 10-30 seconds
- Large changes (20-50 files): Complete in 30-60 seconds
- Very large changes (>50 files): Complete in 1-2 minutes

## Key Principles

1. **Author filtering is critical**: Only analyze commits by the requesting user (`git log --author`)
2. **Scope by actual changes**: Developer's scope = what they actually coded, not entire requirements doc
3. **Issue numbers are metadata only**: Extract from commits for reference, but DO NOT use to limit verification scope
4. **Three-point focus**: Report must focus on: (1) All requirement changes, (2) User's assigned scope, (3) Completeness verification
5. **Concise reporting**: Avoid detailed code snippets, lengthy explanations, or unnecessary quality assessments
6. **Clear attribution**: Explicitly state which features are out of scope and who implemented them
7. **Commit message priority**: When code differs from requirements, commit messages take precedence if they explicitly mention adjustments

## Common Pitfalls to Avoid

❌ Analyzing all commits in the branch (include other developers' work)
✅ Filter commits by `git log --author`

❌ Verifying entire requirements document
✅ Only verify requirements related to developer's changed files

❌ Using issue numbers to limit verification scope
✅ Determine scope by developer's commits, extract issue numbers as optional metadata

❌ Vague statements like "implemented correctly"
✅ Specific references like "Line 154-177: Cache mechanism using Observable.zip"

❌ Missing other developers' contributions
✅ Explicitly state "DualColumnScoreBoardHolderV3.kt - developed by songsiting"

## Report Template Reference

See [references/report-template.md](references/report-template.md) for a detailed example report structure.
