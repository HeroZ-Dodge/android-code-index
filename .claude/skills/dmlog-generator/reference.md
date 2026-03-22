# DM 埋点日志代码生成器 - 参考文档

## 文件结构模板

```kotlin
package com.netease.gl.{模块名}

import com.netease.gl.glbase.log.page.PageConstants
import com.netease.gl.glbase.util.JsonUtil
import com.netease.gl.service.base.componnet.Sdks
import com.netease.gl.servicelog.interfaces.IEventTracker

/**
 * {功能名}埋点日志类
 * 用于记录{功能描述}的用户行为数据
 *
 * @author Claude Code Generator
 * @since {生成日期}
 */
object {功能名}DmLog {

    fun {方法名}(pageId: String?, {其他参数}: Type?) {
        // 方法实现
    }
}
```

## 方法实现模板

```kotlin
fun {methodName}(
    pageId: String?,
    {param1}: String? = null,
    {param2}: Int? = null
) {
    val mapBuilder = IEventTracker.MapBuilder()

    // 如果有复杂信息，构建 info 字段
    val infoMap = mutableMapOf<String, Any?>()
    infoMap["字段名1"] = param1
    infoMap["字段名2"] = param2

    if (infoMap.isNotEmpty()) {
        mapBuilder.put("info", JsonUtil.toJsonString(infoMap))
    }

    // 添加简单字段
    mapBuilder.put("button_name", buttonName)
    mapBuilder.put(PageConstants.PAGE_ID, pageId)

    // 上报事件
    Sdks.serviceLogSdk.eventTracker().trackEvent("{事件名}", mapBuilder.build())
}
```

## 安全的参数处理

```kotlin
val infoMap = mutableMapOf<String, Any?>()
vipId?.let { infoMap["vip_id"] = it }
vipType?.let { infoMap["vip_type"] = it }
benefitList?.takeIf { it.isNotEmpty() }?.let {
    infoMap["benefit_list"] = it
}

if (infoMap.isNotEmpty()) {
    mapBuilder.put("info", JsonUtil.toJsonString(infoMap))
}
```

## 代码组织示例

```kotlin
object VipMypageDmLog {

    // ==================== 曝光埋点 ====================

    fun expVipMypageTop(pageId: String?) { /* ... */ }

    fun expVipBenefitList(pageId: String?) { /* ... */ }

    // ==================== 点击埋点 ====================

    fun clkVipMypageTop(pageId: String?) { /* ... */ }

    fun clkVipBenefitItem(pageId: String?) { /* ... */ }
}
```

## Excel 文档解析规则

查找包含以下关键字的 sheet 页："埋点"、"事件"、"日志"、"事件名"、"eventName"、"触发规则"、"trigger"

提取关键列：

| 字段名 | 可能的列名 | 说明 |
|--------|-----------|------|
| 事件名称 | eventName, 事件名, event_name | 英文事件标识 |
| 事件中文名 | eventCnName, 事件中文名, 中文名称 | 中文描述 |
| 触发规则 | triggerRule, 触发时机, 触发条件 | 何时上报 |
| 字段名 | fieldName, 字段, field | 参数名称 |
| 字段类型 | fieldType, 类型, type | 数据类型 |
| 字段说明 | fieldDesc, 说明, remark | 字段描述 |
| 额外参数 | extra_param, extraParam, 扩展字段 | JSON 结构 |
