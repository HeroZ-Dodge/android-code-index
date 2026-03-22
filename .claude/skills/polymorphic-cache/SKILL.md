---
name: polymorphic-cache
description: 使用 JsonPolymorphicUtil 实现页面多态数据的序列化与反序列化，用于 App 冷启动时快速展示页面缓存数据。适用场景：(1) Feed 流列表页面（视频卡片、图文卡片、直播卡片等多种卡片类型）(2) 聊天/消息列表（文本、图片、语音、视频等多种消息类型）(3) 游戏Tab或其他包含多态数据的列表页面。触发词：多态缓存、JsonPolymorphicUtil、页面缓存、冷启动优化、多态序列化、polymorphic cache
---

# 多态数据缓存

使用 JsonPolymorphicUtil 实现页面多态数据的序列化与反序列化，用于 App 冷启动时快速展示上次加载的页面数据。

## 核心工作流

实现多态数据缓存需要 6 个步骤：

1. **⚠️ 深度分析页面数据结构（极其重要）** - **必须全面、彻底地分析业务场景的数据获取和处理逻辑**，识别页面中的所有多态数据类型（基类是什么，有哪些子类实现）。**不能遗漏任何一个可能出现的数据类型，否则会导致序列化失败或反序列化时崩溃**
2. **判断是否需要多态序列化** - 如果页面数据没有多态场景（如只有单一数据类型），使用普通序列化即可
3. **实现 JsonPolymorphicStructure** - 定义多态结构（基类、type 字段名、子类列表）
4. **创建缓存管理类** - 封装序列化/反序列化逻辑，选择正确的Repo保存数据
5. **集成到业务逻辑层** - **在ViewModel/DataSource/Repository等逻辑层集成缓存，不要在View层(Fragment/Activity)处理缓存逻辑**
6. **⚠️ 编译验证** - **完成代码修改后必须进行编译验证，确保没有编译错误、API调用错误等低级问题**

## 快速开始

### 步骤 1: 深度分析识别多态数据（极其重要）

**⚠️ 这是最容易出错的环节，必须投入足够的时间进行全面分析！**

首先**深入、全面地**分析业务场景的数据获取和处理逻辑，识别所有可能的多态数据类型。

#### 为什么必须全面分析？

**遗漏任何一个数据类型都会导致严重问题**：
- ❌ 序列化时遇到未注册的类型会失败或返回空数据
- ❌ 反序列化时无法识别 type 字段，导致崩溃或数据丢失
- ❌ 用户看到空白页面或缓存失效，冷启动优化失败

#### 如何进行全面的数据类型分析？

**多维度分析方法**（必须至少使用 3 种方法交叉验证）：

**方法1: 分析ViewModel/DataSource的数据加载逻辑**
- 查找数据聚合方法（如 `getAllXxx()`, `mergeXxx()`, `fetchXxx()`）
- 分析所有数据来源（LiveData、Observable、Repository）
- 追踪每个数据源可能返回的类型

**方法2: 分析DataSource的数据准备方法**
- 查找 `prepareXxxData()` 或 `convertXxx()` 方法
- 查看 `when (sessionType)` 或 `if (isXxxType())` 分支
- 每个分支可能对应不同的数据类型

**方法3: 使用 Grep 搜索所有子类实现**
```bash
# 搜索实现了基类的所有子类
grep -r "class.*Xxx.*:\s*(BaseClass|BaseInterface)" services/
grep -r ": BaseClass\|extends BaseClass" services/
```

**方法4: 分析Fragment/Activity的适配器**
- 查看 Adapter 的 `getItemViewType()` 方法
- 每个 viewType 可能对应不同的数据类型

**方法5: 搜索数据类型构造器调用**
```bash
# 搜索数据类型的构造调用
grep -r "SubClass1\(|SubClass2\(" services/
```

#### 实战案例：消息Tab页面数据分析

**示例：游戏Tab数据分析（初次分析 - 不完整）**

通过分析 `FeedDiscoveryPageViewModel` 的数据加载和处理逻辑：

```java
// FeedDiscoveryPageViewModel.java
private void doRefreshData(...) {
    // 加载配置、游戏大事记、红点等数据
    Observable.zip(loadConfig, loadGameMemorabiliaRecommend, loadRedDot, ...)
        .map(appKeyList -> {
            mWrapDataList.clear();
            handleGameMemorabilia(mWrapDataList, ...);  // 添加游戏大事记
            handleConfigList(mWrapDataList, ...);       // 添加配置数据
            return ...;
        })
}

public List<IFeed> hookAfterFetchData(List<IFeed> source, boolean isRefresh) {
    if (isRefresh) {
        list.add(0, new RecommendTitleData(...));           // 标题
        list.addAll(0, mWrapDataList);                      // 多种类型数据
    }
    // 添加 DiscoveryGameLibWrapper、AppConfigWrapData、GameUpdateModuleWrapData...
}
```

**分析结果**：
- **基类**: `IFeed` 接口
- **子类**: `RecommendGameMemorabiliaWrapper`、`RecommendTitleData`、`DiscoveryGameLibWrapper`、`AppConfigWrapData`、`GameUpdateModuleWrapData`、`FeedEntity` 等
- **结论**: 这是典型的多态场景，需要使用多态序列化

---

**示例：消息Tab数据分析（完整分析）**

**❌ 错误的分析方法**：只看 MessageHomeViewModel.getAllRecentContacts() 方法中直接创建的类型
```kotlin
// 只分析了这些直接创建的类型（不完整！）
InteractionNotifyRecentContact(...)      // ✓ 发现
AggregateMessageRecentContact(...)       // ✓ 发现
ChatRoomSystemRecentContact(...)         // ✓ 发现
```
结果：**遗漏了 privateTeam 数据源中的所有类型！**

**✅ 正确的分析方法**：多维度交叉验证

1. **分析 ViewModel 的数据聚合逻辑** (MessageHomeViewModel.kt:1859-1908)
```kotlin
private fun getAllRecentContacts(): MutableList<RecentContact> {
    val privateTeam = privateTeamLd.value.orEmpty()          // 数据源1
    val chatroomContacts = _chatroomLatestMsgLd.value.orEmpty()  // 数据源2
    val channelContacts = _channelLatestMsgLd.value.orEmpty()    // 数据源3

    val allContacts = mutableListOf<RecentContact>().apply {
        addAll(privateTeam)  // ⚠️ 这里包含多种类型，需要深入分析！
        add(InteractionNotifyRecentContact(...))
        add(AggregateMessageRecentContact(...))
        add(ChatRoomSystemRecentContact(...))
        addAll(channelContacts)
        addAll(chatroomContacts)
    }
}
```
**发现**: privateTeam、chatroomContacts、channelContacts 都是 List，需要进一步分析

2. **追踪数据源的类型** (PrivateTeamMessageDataSource.kt)
```kotlin
// 搜索 "private fun prepare.*RecentContact" 找到所有数据准备方法
private fun prepareP2PUserRecentContact(recent: RecentContact): UserRecentContact {
    return UserRecentContact(recent, userInfo)  // ✓ 发现 UserRecentContact
}

private fun prepareFunctionServiceRecentContact(recent: RecentContact): FunctionServiceRecentContact {
    return FunctionServiceRecentContact(recent, info)  // ✓ 发现 FunctionServiceRecentContact
}

private fun prepareGameGroupRecentContact(recent: RecentContact): RoleRecentContact {
    return RoleRecentContact(recent)  // ✓ 发现 RoleRecentContact
}

private fun prepareGameGangRecentContact(recent: RecentContact): RoleRecentContact {
    return RoleRecentContact(...)  // ✓ 已发现
}

private fun prepareGameRecentContact(recent: RecentContact): RoleRecentContact {
    return RoleRecentContact(...)  // ✓ 已发现
}
```

3. **使用 Grep 搜索所有 RecentContact 子类**
```bash
grep -r "class.*RecentContact.*:" services/communication/im | grep "RecentContact\|RecentContactImpl"
```
发现额外的类型：
- SystemRecentContact.kt  # ✓ 发现可能的系统消息类型
- ChatroomRecentContact.kt  # ✓ 已知
- ChannelRecentContact.kt  # ✓ 已知

4. **交叉验证：检查是否有遗漏**
```bash
# 搜索 RecentContact 的直接子类
grep "extends RecentContactImpl\|: RecentContactImpl\|extends RecentContact\|: RecentContact" -r services/communication/im
```

**最终完整的类型列表**：
```kotlin
override fun subTypes(): List<Class<out RecentContact>> {
    return listOf(
        // 基础实现类
        RecentContactImpl::class.java,

        // PrivateTeam 中的P2P用户/角色/功能服务类型
        UserRecentContact::class.java,           // ✓ 深入分析发现
        RoleRecentContact::class.java,           // ✓ 深入分析发现
        FunctionServiceRecentContact::class.java, // ✓ 深入分析发现

        // 系统消息类型
        SystemRecentContact::class.java,         // ✓ Grep搜索发现

        // 聊天室/频道类型
        ChatroomRecentContact::class.java,       // ✓ 直接分析发现
        ChannelRecentContact::class.java,        // ✓ 直接分析发现

        // 特殊交互类型
        InteractionNotifyRecentContact::class.java,  // ✓ 直接分析发现
        AggregateMessageRecentContact::class.java,   // ✓ 直接分析发现
        ChatRoomSystemRecentContact::class.java,     // ✓ 直接分析发现

        // 广告类型
        ADRecentContact::class.java              // ✓ 额外分析发现
    )
}
```

**经验教训**：
1. ❌ 不能只看直接创建的对象，必须追踪所有数据源
2. ✅ 使用多种方法交叉验证（代码分析 + Grep搜索 + 数据源追踪）
3. ✅ 对于 List 类型的数据源，必须深入分析其来源和可能包含的类型
4. ✅ 检查 DataSource 的所有 `prepareXxx()` 或 `convertXxx()` 方法

**💡 完整案例参考**：参见 [消息Tab页面缓存案例](references/case-message-tab.md#数据类型分析过程) 了解详细的分析过程和经验教训。

---

识别出多态结构后，定义多态配置：

```kotlin
object FeedDataStructure : JsonPolymorphicStructure<IFeed> {
    override fun baseType() = IFeed::class.java

    /**
     * ⚠️ 极其重要：typeFieldName 的命名规范
     *
     * 问题：如果与基类或任何子类中的字段重名，会导致序列化/反序列化时数据覆盖或崩溃
     *
     * 示例：DiscoveryGameLibWrapper 类有 `val feedType: Int` 字段
     *       如果使用 "feedType" 作为 typeFieldName，会导致冲突！
     *
     * 最佳实践：使用带业务前缀的字段名避免冲突
     * - ❌ "feedType" / "type" / "itemType" - 容易与业务字段冲突
     * - ✅ "__gameTab_polyType__" - 使用双下划线前缀 + 业务模块名 + polyType 标识
     * - ✅ "_poly_type_" - 使用下划线包围，明显区分业务字段
     * - ✅ "@polymorphicType" - 使用特殊字符前缀
     */
    override fun typeFieldName() = "__gameTab_polyType__"

    override fun subTypes() = listOf(
        RecommendGameMemorabiliaWrapper::class.java,
        RecommendTitleData::class.java,
        DiscoveryGameLibWrapper::class.java,
        AppConfigWrapData::class.java,
        GameUpdateModuleWrapData::class.java,
        FeedEntity::class.java
    )
}
```

### 步骤 3: 序列化与反序列化

```kotlin
// 保存缓存
val feedList: List<IFeed> = mWrapDataList
val json = JsonPolymorphicUtil.toJsonStr(
    feedList,
    object : TypeToken<List<IFeed>>() {},
    FeedDataStructure
)
PreferenceUtil.putString("feed_cache", json)

// 读取缓存
val cachedJson = PreferenceUtil.getString("feed_cache", "")
val cachedList = JsonPolymorphicUtil.fromJson<List<IFeed>>(
    cachedJson,
    object : TypeToken<List<IFeed>>() {},
    FeedDataStructure
)
```

---

### 完整示例：Feed 流卡片缓存

如果你的业务中**还没有数据模型**，需要先创建：

```kotlin
// 1. 定义数据模型
sealed class FeedCard {
    abstract val id: String
    abstract val timestamp: Long
}

data class VideoCard(
    override val id: String,
    override val timestamp: Long,
    val videoUrl: String,
    val coverUrl: String,
    val duration: Int
) : FeedCard()

data class ImageTextCard(
    override val id: String,
    override val timestamp: Long,
    val title: String,
    val images: List<String>,
    val content: String
) : FeedCard()

// 2. 定义多态结构
object FeedCardStructure : JsonPolymorphicStructure<FeedCard> {
    override fun baseType() = FeedCard::class.java
    override fun typeFieldName() = "cardType"  // JSON 中的 type 字段名
    override fun subTypes() = listOf(
        VideoCard::class.java,
        ImageTextCard::class.java
    )
}

// 3. 序列化：保存 Feed 列表
val feedList = listOf(
    VideoCard("1", 1234567890, "https://...", "https://...", 120),
    ImageTextCard("2", 1234567891, "标题", listOf("img1", "img2"), "内容")
)
val json = JsonPolymorphicUtil.toJsonStr(
    feedList,
    object : TypeToken<List<FeedCard>>() {},
    FeedCardStructure
)
// 保存到 SharedPreferences 或文件
PreferenceUtil.putString("feed_cache", json)

// 4. 反序列化：读取 Feed 列表
val cachedJson = PreferenceUtil.getString("feed_cache", "")
val cachedFeedList = JsonPolymorphicUtil.fromJson<List<FeedCard>>(
    cachedJson,
    object : TypeToken<List<FeedCard>>() {},
    FeedCardStructure
)
// 在 UI 加载完成前展示缓存数据
cachedFeedList?.let { adapter.submitList(it) }
```

## 使用 Asset 模板快速开始

Skill 提供了两个模板文件：

### 1. PolymorphicStructureTemplate.kt
快速创建 JsonPolymorphicStructure 实现：
```kotlin
// 复制 assets/PolymorphicStructureTemplate.kt 并修改
object YourDataStructure : JsonPolymorphicStructure<YourBaseClass> {
    override fun baseType() = YourBaseClass::class.java
    override fun typeFieldName() = "type"
    override fun subTypes() = listOf(
        SubClass1::class.java,
        SubClass2::class.java
    )
}
```

### 2. PageCacheHelper.kt
页面缓存辅助类，封装了序列化/反序列化逻辑：
```kotlin
// 使用示例
val cacheHelper = PageCacheHelper<FeedCard>(
    cacheKey = "feed_cache",
    polymorphicStructure = FeedCardStructure
)

// 保存缓存
cacheHelper.saveCache(feedList)

// 读取缓存
val cachedData = cacheHelper.loadCache()
```

## 进阶示例和场景

详细的使用示例请参考 [examples.md](references/examples.md)，包含：
- Feed 流场景（视频卡片、图文卡片、直播卡片）
- 聊天/消息列表场景（文本、图片、语音消息）
- 游戏Tab场景
- 嵌套多态数据处理

### ⭐ 完整实战案例

#### 案例1：消息Tab页面缓存（数据类型分析）

**强烈推荐阅读**：[消息Tab页面缓存集成案例](references/case-message-tab.md)

这是一个完整的生产环境实战案例，展示了：
- ✅ 完整的数据类型分析过程（11种RecentContact子类型）
- ✅ 如何使用多维度方法发现所有数据类型（ViewModel + DataSource + Grep）
- ✅ 正确的架构设计（ViewModel层缓存 + UInfoRepo用户隔离）
- ✅ 从错误中学习（记录了遗漏类型的错误及修复过程）
- ✅ 完整的测试和验证方法

**核心亮点**：
- 数据类型分析方法论（多维度交叉验证）
- 常见错误对比（错误 vs 正确的分析方法）
- 类型清单表格（每个类型的来源和发现方法）
- 更新历史记录（问题、原因、修复、教训）

**适合场景**：
- 第一次使用 polymorphic-cache 的开发者
- 需要分析复杂业务数据结构的场景
- IM/聊天/消息列表页面

#### 案例2：游戏Tab页面缓存（Feed流场景）

**推荐阅读**：[游戏Tab页面缓存集成方案](references/case-game-tab.md)

这是一个 Feed 流场景的实战案例，展示了：
- ✅ Feed流多种卡片类型混合展示（配置、广告、推荐、实体）
- ✅ 新旧缓存方案的兼容性设计（平滑升级）
- ✅ 嵌套多态数据的处理（sealed class）
- ✅ 缓存大小控制策略（限制前50条）
- ✅ 完整的故障排查指南

**核心亮点**：
- ViewModel 集成方案（hookAfterFetchData + loadCacheData）
- 兼容性设计（优先新缓存，fallback到旧缓存）
- 嵌套多态结构处理（GameMemorabiliaData）
- 详细的测试清单和性能指标

**适合场景**：
- Feed流、动态列表、内容聚合页面
- 需要缓存多种卡片类型的混合场景
- 需要兼容旧版本缓存的升级场景


## 架构设计最佳实践

### 1. 缓存逻辑应该在哪一层？

**✅ 正确做法 - 在逻辑层处理缓存**:
- **ViewModel**: MVVM架构中的首选位置，负责数据获取、转换、缓存
- **Repository**: 数据仓库模式中的合适位置
- **DataSource**: 可以在数据源层处理缓存

**❌ 错误做法 - 不要在View层处理缓存**:
- **Fragment/Activity**: View层只负责UI展示和用户交互，不应包含缓存逻辑
- **Adapter/ViewHolder**: 同样属于View层，职责是数据绑定，不是数据管理

**示例对比**:
```kotlin
// ❌ 错误：在Fragment中处理缓存
class MyFragment : Fragment() {
    override fun initView() {
        // 错误：缓存逻辑不应该在View层
        loadCachedData()
    }

    private fun loadCachedData() {
        val cachedData = CacheManager.loadCache()
        adapter.submitList(cachedData)
    }
}

// ✅ 正确：在ViewModel中处理缓存
class MyViewModel : ViewModel() {
    private val _dataLd = MutableLiveData<List<Data>>()
    val dataLd: LiveData<List<Data>> = _dataLd

    init {
        // 正确：在ViewModel初始化时加载缓存
        loadCachedData()
    }

    private fun loadCachedData() {
        viewModelScope.launch {
            val cachedData = CacheManager.loadCache()
            _dataLd.postValue(cachedData)
        }
    }
}

// Fragment只负责观察数据
class MyFragment : Fragment() {
    override fun initView() {
        viewModel.dataLd.observe(this) { data ->
            adapter.submitList(data)
        }
    }
}
```

### 2. 如何选择正确的Repo?

**用户相关数据** (如聊天消息、个人设置)：
- ✅ 使用 **UInfoRepo** - 确保用户切换时数据隔离
- ❌ 不使用 **HomeRepo** - 全局共享，用户切换会串数据

**全局配置数据** (如App配置、游戏列表)：
- ✅ 使用 **HomeRepo** - 所有用户共享
- ❌ 不使用 **UInfoRepo** - 会造成重复缓存

**示例**:
```kotlin
// IM消息数据 - 用户相关
object MessageCacheManager {
    fun saveCache(data: List<Message>) {
        val uInfoRepo = RepoHelper.getUInfoRepo()  // ✅ 正确
        uInfoRepo?.updateSetting(CACHE_KEY, json)
    }
}

// 游戏Tab配置 - 全局共享
object GameTabCacheManager {
    fun saveCache(data: List<GameConfig>) {
        val homeRepo = RepoHelper.getHomeRepo()  // ✅ 正确
        homeRepo?.updateSetting(CACHE_KEY, json)
    }
}
```

### 3. 缓存集成的完整流程

#### 步骤1: 创建多态结构定义
```kotlin
object DataStructure : JsonPolymorphicStructure<BaseType> {
    override fun baseType() = BaseType::class.java
    override fun typeFieldName() = "__module_polyType__"
    override fun subTypes() = listOf(SubType1::class.java, SubType2::class.java)
}
```

#### 步骤2: 创建缓存管理类
```kotlin
object CacheManager {
    fun saveCache(data: List<BaseType>): Boolean {
        val json = JsonPolymorphicUtil.toJsonStr(data, ..., DataStructure)
        // 根据数据性质选择Repo
        val repo = RepoHelper.getUInfoRepo() // 或 getHomeRepo()
        repo?.updateSetting(CACHE_KEY, json)
        return true
    }

    fun loadCache(): List<BaseType>? {
        val repo = RepoHelper.getUInfoRepo() // 或 getHomeRepo()
        val json = repo?.querySettingBlock(CACHE_KEY)
        return JsonPolymorphicUtil.fromJson(json, ..., DataStructure)
    }
}
```

#### 步骤3: 在ViewModel中集成
```kotlin
class MyViewModel : ViewModel() {
    private val _dataLd = MutableLiveData<List<BaseType>>()
    val dataLd: LiveData<List<BaseType>> = _dataLd

    init {
        // 冷启动时加载缓存
        loadCachedData()
    }

    private fun loadCachedData() {
        viewModelScope.launch(Dispatchers.IO) {
            val cachedData = CacheManager.loadCache()
            if (!cachedData.isNullOrEmpty()) {
                _dataLd.postValue(cachedData)
            }
        }
    }

    fun loadRealData() {
        viewModelScope.launch {
            val realData = repository.fetchData()
            _dataLd.postValue(realData)
            // 异步保存缓存
            withContext(Dispatchers.IO) {
                CacheManager.saveCache(realData)
            }
        }
    }
}
```

#### 步骤4: Fragment只负责观察
```kotlin
class MyFragment : Fragment() {
    override fun initView() {
        // View层只负责UI展示
        viewModel.dataLd.observe(this) { data ->
            adapter.submitList(data)
        }

        // 触发真实数据加载
        viewModel.loadRealData()
    }
}
```

### 4. 常见错误示例

**❌ 错误1: 在Fragment中直接调用缓存API**
```kotlin
class MyFragment : Fragment() {
    private fun loadData() {
        // 错误：View层不应该处理缓存逻辑
        val cachedData = JsonPolymorphicUtil.fromJson(...)
        adapter.submitList(cachedData)
    }
}
```

**❌ 错误2: 用户数据使用全局Repo**
```kotlin
object IMCacheManager {
    fun saveMessages(messages: List<Message>) {
        // 错误：IM消息是用户相关的，应该用UInfoRepo
        val homeRepo = RepoHelper.getHomeRepo()
        homeRepo?.updateSetting(key, json)
    }
}
```

**❌ 错误3: 在DataSource中处理UI相关逻辑**
```kotlin
class MyDataSource {
    fun loadData() {
        val data = fetchFromNetwork()
        // 错误：DataSource不应该知道Adapter的存在
        adapter?.submitList(data)
    }
}
```

## API 参考

**重要提示**: JsonPolymorphicUtil 和 JsonPolymorphicStructure 是已存在的工具类，位于 base 库中（`com.netease.gl.glbase.util` 包）。

JsonPolymorphicUtil 完整 API 说明请参考 [api-reference.md](references/api-reference.md)，该文档详细说明了：
- JsonPolymorphicUtil 的所有序列化/反序列化方法
- JsonPolymorphicStructure 接口的实现要求
- typeFieldName 字段名冲突问题及解决方案
- 常见用法模式和最佳实践

## 常见问题

**Q: ⚠️ 如何确保没有遗漏任何数据类型？（最常见的错误）**

A: **这是实现多态缓存时最容易犯的错误！** 遗漏数据类型会导致序列化失败或反序列化崩溃。

**必须使用的完整检查流程**：

1. **多维度分析（至少3种方法）**：
   - ViewModel/DataSource 的数据聚合方法分析
   - DataSource 的 `prepareXxx()` 方法分析
   - Grep 搜索所有基类实现
   - 追踪所有 LiveData/Observable 数据源
   - 检查 Adapter 的 viewType 分支

2. **关键搜索命令**：
   ```bash
   # 搜索基类的所有实现
   grep -r "class.*: YourBaseClass\|extends YourBaseClass" services/

   # 搜索数据准备方法
   grep -r "private fun prepare.*RecentContact\|fun convert.*Data" services/

   # 搜索构造器调用
   grep -r "SubClassName(" services/module/
   ```

3. **交叉验证清单**：
   - [ ] 分析了所有数据源（LiveData、Observable、Repository）
   - [ ] 检查了所有 `when` 或 `if` 分支的数据类型
   - [ ] 搜索了基类的所有子类实现
   - [ ] 追踪了 List 类型数据源的实际内容
   - [ ] 查看了 DataSource 的所有数据准备方法
   - [ ] 检查了 Adapter 的所有 ViewHolder 类型

4. **实战案例：消息Tab数据类型完整分析**

   **错误的分析（遗漏类型）**：
   ```kotlin
   // ❌ 只看了 ViewModel 中直接创建的类型
   InteractionNotifyRecentContact
   AggregateMessageRecentContact
   ChatRoomSystemRecentContact
   // 结果：遗漏了 UserRecentContact、RoleRecentContact、FunctionServiceRecentContact 等！
   ```

   **正确的分析（完整分析）**：
   ```kotlin
   // 1. ViewModel 直接创建的类型
   InteractionNotifyRecentContact
   AggregateMessageRecentContact
   ChatRoomSystemRecentContact

   // 2. 追踪 privateTeamLd 数据源，发现来自 PrivateTeamMessageDataSource
   // 3. 分析 PrivateTeamMessageDataSource.prepareXxx() 方法
   UserRecentContact           // 从 prepareP2PUserRecentContact 发现
   RoleRecentContact           // 从 prepareGameXxxRecentContact 发现
   FunctionServiceRecentContact // 从 prepareFunctionServiceRecentContact 发现

   // 4. 分析 chatroomContacts 和 channelContacts 数据源
   ChatroomRecentContact
   ChannelRecentContact

   // 5. Grep 搜索发现额外的类型
   SystemRecentContact  // 可能在某些场景使用
   ADRecentContact      // 广告消息

   // 6. 基础实现类
   RecentContactImpl    // 其他普通会话
   ```

5. **验证方法**：
   ```kotlin
   // 在开发环境添加日志验证
   val json = JsonPolymorphicUtil.toJsonStr(data, ...)
   if (json.isEmpty()) {
       Log.e(TAG, "序列化失败！可能遗漏了某个数据类型")
       // 打印 data 中每个对象的实际类型
       data.forEach { Log.e(TAG, "Type: ${it.javaClass.simpleName}") }
   }
   ```

6. **错误症状识别**：
   - 缓存保存后为空字符串 → 序列化失败，遗漏了某个类型
   - 反序列化返回 null 或空列表 → JSON 中有未注册的 type 字段值
   - 启动时崩溃 ClassCastException → type 字段映射错误

**总结**: 数据类型分析必须投入足够时间，使用多种方法交叉验证，不能只看表面逻辑。

**💡 完整案例**：[消息Tab页面缓存案例](references/case-message-tab.md) 中详细记录了从错误到修复的完整过程，包括遗漏4个类型的错误、根本原因分析、多维度验证方法等。

---

**Q: typeFieldName 为什么不能与业务字段重名？会导致什么问题？**

A: **非常重要！** RuntimeTypeAdapterFactory 会在 JSON 中插入一个 type 字段来标识子类型。如果 `typeFieldName()` 返回的字段名与基类或任何子类中已有的字段重名，会导致：
- **序列化崩溃**: Gson 尝试写入两个同名字段
- **反序列化崩溃**: Gson 无法区分业务字段和类型标识字段
- **数据覆盖**: 业务字段值被类型标识覆盖或反之

**解决方案**：
1. 使用不会冲突的字段名，如 `"_type"`、`"itemType"`、`"cardType"`、`"msgType"` 等
2. 检查基类和所有子类的字段，确保没有重名
3. 推荐使用带前缀或后缀的命名（如 `"_type"`、`"__typename"`）

**示例**：
```kotlin
// ❌ 错误：假设 FeedCard 中已有 type 字段
data class VideoCard(
    val type: String,  // 业务字段
    val videoUrl: String
) : FeedCard()

object FeedCardStructure : JsonPolymorphicStructure<FeedCard> {
    override fun typeFieldName() = "type"  // ❌ 与业务字段重名，会崩溃
    ...
}

// ✅ 正确：使用不冲突的字段名
object FeedCardStructure : JsonPolymorphicStructure<FeedCard> {
    override fun typeFieldName() = "cardType"  // ✅ 不冲突
    ...
}
```

**Q: 何时需要设置 recognizeSubtypes() 为 true？**

A: 当你需要在声明为具体子类型的字段上也使用多态序列化时。默认 `false` 时，只有声明为基类型的字段才会使用多态适配器（添加 type 字段）。设置为 `true` 后，即使字段声明为 `Cat` 而非 `Animal`，也会添加 type 字段。通常保持默认 false 即可。

**Q: 序列化失败返回空字符串，如何调试？**
A: JsonPolymorphicUtil 捕获了异常。建议在开发阶段移除 try-catch 或添加日志，查看具体错误信息。常见问题：
- 忘记注册某个子类型
- type 字段名冲突
- 数据类字段缺少默认值导致反序列化失败

**Q: 完成代码后如何验证？**
A: **必须进行编译验证，这是避免低级错误的最后防线**：

1. **编译验证** - 确保代码能够编译通过
   ```bash
   # Android项目
   ./gradlew :module-name:compileDebugKotlin

   # 检查是否有编译错误
   # ✅ BUILD SUCCESSFUL - 通过
   # ❌ BUILD FAILED - 检查错误信息并修复
   ```

2. **常见编译错误**：
   - ❌ API调用错误：方法名错误、参数类型不匹配
     - 示例：`querySettingBlock()` 不存在，应该用 `getSettingSync()`
   - ❌ 导入缺失：忘记导入必要的类
   - ❌ 类型不匹配：泛型使用错误、返回类型错误
   - ❌ 空安全问题：Kotlin的null检查不完整

3. **检查清单**：
   - [ ] 所有新创建的类能否编译通过
   - [ ] 修改的类是否引入编译错误
   - [ ] API调用是否使用了正确的方法名和参数
   - [ ] 导入语句是否完整
   - [ ] Kotlin空安全检查是否正确

4. **最佳实践**：
   - ✅ 每完成一个文件立即编译验证
   - ✅ 修改API调用前先检查方法签名
   - ✅ 使用IDE的自动补全避免方法名错误
   - ✅ 提交代码前再次全量编译验证

**示例：正确的开发流程**
```kotlin
// 1. 创建文件
object MyCacheManager {
    fun saveCache() {
        // 使用IDE补全，避免方法名错误
        val repo = RepoHelper.getUInfoRepo()
        // ⚠️ 这里应该检查UInfoRepo有哪些方法
        repo?.updateSetting(key, value)  // ✅ 正确
        // repo?.saveSetting(key, value) // ❌ 错误，方法不存在
    }
}

// 2. 立即编译验证
// ./gradlew :module:compileDebugKotlin

// 3. 发现错误，立即修复
// error: Unresolved reference: saveSetting
// 修复：查看UInfoRepo的实际方法，使用updateSetting

// 4. 再次验证直到编译通过
```
