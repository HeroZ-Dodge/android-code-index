# 埋点文档 Excel 解析格式参考

## 已知的列布局

### 布局 A：新增页面类

表头关键词：第一列为"事件名"

| 列 | 字段 |
|----|------|
| A | 事件名（如 page_view） |
| B | 事件中文名 |
| C | 触发规则 |
| D | 字段名（中文） |
| E | 字段id（英文，对应 content JSON key） |
| F | 类型（string/json） |
| G | 字段内容/备注 |
| H | 交互图 |

### 布局 B：新增埋点类

表头关键词：包含"负责DM"或"负责策划"列

| 列 | 字段 |
|----|------|
| A | 事件名 |
| B | 事件中文名 |
| C | 描述 |
| D | 触发规则 |
| E | 负责DM |
| F | 负责策划 |
| G | 字段名（中文） |
| H | 字段id（英文，对应 content JSON key） |
| I | 类型（string/json） |
| J | 备注 |
| K | 交互图 |

### 布局 C：修改埋点类

表头关键词：第一列为"事件名"且不包含"负责DM"

| 列 | 字段 |
|----|------|
| A | 事件名 |
| B | 事件中文名 |
| C | 触发规则 |
| D | 字段名（中文） |
| E | 字段id（英文，对应 content JSON key） |
| F | 类型（string/json） |
| G | 备注 |
| H | 交互图 |

## 解析逻辑

### 表头检测

遍历每行，检测包含以下关键词的行作为表头行：
- "事件名" 出现在任意单元格

一个 sheet 中可能有**多个表头行**（多个分区），每遇到一个新表头行就切换列映射。

### 表头列映射

检测到表头行后，遍历该行所有单元格：

```python
column_map = {}
for cell in header_row:
    value = str(cell.value).strip()
    if value == '事件名':
        column_map['event_name'] = cell.column - 1
    elif value == '事件中文名':
        column_map['event_cn_name'] = cell.column - 1
    elif value == '字段名':
        column_map['field_name'] = cell.column - 1
    elif value == '字段id':
        column_map['field_id'] = cell.column - 1
    elif value == '类型':
        column_map['field_type'] = cell.column - 1
    elif value in ('备注', '字段内容'):
        column_map['remark'] = cell.column - 1
    elif value == '描述':
        column_map['description'] = cell.column - 1
    elif value == '触发规则':
        column_map['trigger_rule'] = cell.column - 1
```

### 事件分组

- 当 `event_name` 列有值时，开始一个新事件
- 后续行如果 `event_name` 列为空但 `field_id` 列有值，则属于同一事件的字段
- 跳过纯空行和分区标题行（如"新增页面"、"新增埋点"等无表头结构的行）

### 分区标题行识别

以下模式的行视为分区标题（非数据行）：
- 只有 A 列有值，且值为中文描述（如"新增页面"、"新增埋点"、"修改客户端埋点"）
- 不包含字段 id 值
- 行中非空单元格数量 <= 2

## content JSON 字段映射

log.db 中 `local_logs_http.content` 解析后的 JSON 结构：

```json
{
  "f": "事件名",
  "content": "{内层JSON，包含业务字段}",
  "gameid": "...",
  "app_ver": "...",
  "user_uid": "...",
  ...公共字段
}
```

业务字段可能在：
1. **顶层** JSON 中（当 `info_append_way` 不存在或为 `delayed` 时）
2. **`content` 内层** JSON 中（当 `info_append_way=immediately` 时，业务字段在内层 content 中）

验证时应同时检查两层。
