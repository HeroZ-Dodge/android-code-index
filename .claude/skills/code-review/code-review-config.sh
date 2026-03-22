# ============================================================
# Auto Code Review Configuration
# ============================================================

# Claude AI 审查配置
ENABLE_CLAUDE_REVIEW=true         # 是否启用 Claude AI 审查
CLAUDE_REVIEW_TIMEOUT=60          # Claude AI 审查超时时间（秒）

# 自动 Push 配置
AUTO_PUSH_AFTER_FIX=true         # 自动修复后是否自动 push（true: 自动push, false: 手动push）

# 审查范围配置
REVIEW_ONLY_LAST_COMMIT=false     # 只审查最新的 commit（true: 只审查最后一个, false: 审查所有未推送的）
SKIP_MERGE_COMMIT_REVIEW=true     # 跳过 merge 提交的审查（true: 跳过, false: 审查）

# 本地规则检查配置
ENABLE_LOCAL_RULES=true           # 是否启用本地规则检查
AUTO_FIX_ENABLED=true             # 是否自动修复问题

# 具体检查项开关
CHECK_PRINT_STACK_TRACE=true      # 检查 printStackTrace
CHECK_BANG_BANG_OPERATOR=true     # 检查 !! 操作符
CHECK_GENERIC_EXCEPTION=true      # 检查泛型 Exception
CHECK_EMPTY_CATCH=true            # 检查空 catch 块
CHECK_EMPTY_TODO=true             # 检查空 TODO
CHECK_CHINESE_COMMENT=true        # 检查中文注释格式
CHECK_CONTEXT_LEAK=true           # 检查 Context 泄漏
CHECK_HANDLER_LEAK=true           # 检查 Handler 泄漏
CHECK_FRAGMENT_TRANSACTION=true   # 检查 Fragment transaction
CHECK_OBJECT_IN_LOOP=true         # 检查循环中创建对象
CHECK_STRING_CONCAT_IN_LOOP=true  # 检查循环中字符串拼接

# 自动修复开关
AUTO_FIX_PRINT_STACK_TRACE=true   # 自动修复 printStackTrace
AUTO_FIX_BANG_BANG=true           # 自动修复 !! 操作符
AUTO_FIX_EMPTY_TODO=true          # 自动删除空 TODO
AUTO_FIX_CHINESE_COMMENT=true     # 自动修复中文注释

# 输出配置
VERBOSE_OUTPUT=false              # 详细输出模式
COLOR_OUTPUT=true                 # 彩色输出
SAVE_REVIEW_LOG=true              # 保存审查日志
REVIEW_LOG_DIR=".code-review-logs"  # 审查日志目录

# Claude AI 审查范围
CLAUDE_CHECK_LOGIC_ERRORS=true    # 检查逻辑错误
CLAUDE_CHECK_PERFORMANCE=true     # 检查性能问题
CLAUDE_CHECK_SECURITY=true        # 检查安全问题
CLAUDE_CHECK_ARCHITECTURE=true    # 检查架构设计

# 高级选项
FAIL_ON_CRITICAL=false            # 发现严重问题时是否阻止 push
INTERACTIVE_MODE=false            # 交互模式（询问用户）
