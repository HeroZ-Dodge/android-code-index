package com.netease.god.template

import com.netease.gl.glbase.util.JsonPolymorphicStructure

/**
 * JsonPolymorphicStructure 实现模板
 *
 * 使用步骤:
 * 1. 复制此文件并重命名（例如: FeedCardStructure.kt）
 * 2. 替换 YourBaseClass 为你的基类
 * 3. 替换 "type" 为你想使用的 JSON type 字段名（避免与业务字段冲突）
 * 4. 在 subTypes() 中添加所有子类
 * 5. 删除此注释块
 */
class YourDataStructure : JsonPolymorphicStructure<YourBaseClass> {

    /**
     * 基础类型
     * 返回多态数据的基类或接口
     */
    override fun baseType(): Class<YourBaseClass> {
        return YourBaseClass::class.java
    }

    /**
     * 类型字段名
     * JSON 中用于标识子类型的字段名
     *
     * ⚠️ 极其重要：该字段名不能与基类或任何子类中的字段重名，否则会导致崩溃！
     *
     * 最佳实践 - 使用业务前缀避免冲突：
     * - ❌ 高风险命名: "type", "feedType", "itemType", "msgType" 等常见业务字段名
     * - ✅ 推荐命名: "__moduleName_polyType__", "_poly_type_", "@polymorphicType"
     *
     * 命名规则：
     * 1. 使用双下划线前缀（__）明显区分业务字段
     * 2. 包含业务模块标识（如 gameTab、chatMsg、feedList）
     * 3. 包含多态标识（如 polyType、polymorphic）
     * 4. 可选双下划线后缀进一步降低冲突概率
     *
     * 示例：
     * - "__gameTab_polyType__"  - 游戏Tab页面
     * - "__chatMsg_polyType__"  - 聊天消息
     * - "__feedCard_polyType__" - Feed卡片
     */
    override fun typeFieldName(): String {
        return "__moduleName_polyType__"  // TODO: 将 moduleName 替换为你的业务模块名
    }

    /**
     * 子类型列表
     * 列出所有可能出现的子类型
     * 未注册的子类型会导致序列化/反序列化失败
     */
    override fun subTypes(): List<Class<out YourBaseClass>> {
        return listOf(
            SubClass1::class.java,  // TODO: 替换为实际的子类
            SubClass2::class.java,  // TODO: 替换为实际的子类
            // TODO: 添加更多子类...
        )
    }

    /**
     * 是否识别子类型
     * 通常保持默认 false，不需要覆盖此方法
     */
    override fun recognizeSubtypes(): Boolean {
        return false
    }
}

/**
 * 占位符类定义
 * 请删除这些占位符并使用你实际的数据类
 */
class YourBaseClass {
    abstract val id: String
}

data class SubClass1(
    override val id: String,
    val field1: String
) : YourBaseClass()

data class SubClass2(
    override val id: String,
    val field2: Int
) : YourBaseClass()
