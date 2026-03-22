# 游戏Tab页面缓存集成案例

> **📱 Feed流场景实战**：展示了如何为 Feed 流列表页面实现多态数据缓存，包括配置数据、广告、推荐内容等多种卡片类型的混合场景。

## 📖 快速导航

**核心章节**：
- [已创建的文件](#已创建的文件) - 3个关键文件说明
- [ViewModel集成方案](#需要在-feeddiscoverypageviewmodel-中集成) - 如何在现有 ViewModel 中集成缓存
- [使用方式](#使用方式) - Fragment 中的使用示例
- [注意事项](#注意事项) - 关键要点和常见问题
- [测试验证](#测试验证) - 完整的测试清单
- [故障排查](#故障排查) - 常见问题解决方案

**案例特点**：
- **Feed流场景**：多种卡片类型混合展示（配置、广告、推荐、实体）
- **兼容性设计**：支持新旧缓存方案平滑过渡
- **嵌套多态**：处理 sealed class 的嵌套多态序列化
- **大小控制**：缓存数据量控制策略

**适合场景**：
- Feed 流、动态列表、内容聚合页面
- 需要缓存多种卡片类型的混合场景
- 需要兼容旧版本缓存的升级场景

---

## 已创建的文件

### 1. GameTabFeedStructure.kt
路径: `compfeed-game/src/main/java/com/netease/gl/compfeed/game/discovery/cache/GameTabFeedStructure.kt`

定义了游戏Tab的多态数据结构：
- 基类：IFeed
- 子类：RecommendGameMemorabiliaWrapper、RecommendTitleData、DiscoveryGameLibWrapper、AppConfigWrapData、GameUpdateModuleWrapData、FeedEntity
- typeFieldName：使用 "feedType"（已验证不与现有字段冲突）

### 2. GameTabCacheManager.kt
路径: `compfeed-game/src/main/java/com/netease/gl/compfeed/game/discovery/cache/GameTabCacheManager.kt`

提供了缓存管理方法：
- `saveFeedCache(feedList)`: 保存缓存
- `loadFeedCache()`: 加载缓存
- `clearCache()`: 清除缓存
- `hasCached()`: 检查是否有缓存

### 3. 修改 GLUserConstants.java
添加了缓存 key 常量：
```java
String GAME_TAB_FEED_CACHE = "game_tab_feed_cache";  // 游戏tab Feed列表缓存（多态数据）
```

---

## 需要在 FeedDiscoveryPageViewModel 中集成

### 修改点 1: 添加导入
在文件头部添加：
```java
import com.netease.gl.compfeed.game.discovery.cache.GameTabCacheManager;
```

### 修改点 2: 在 hookAfterFetchData 中保存缓存
在 `hookAfterFetchData` 方法的最后，添加缓存保存逻辑：

```java
@Override
public List<IFeed> hookAfterFetchData(List<IFeed> source, boolean isRefresh) {
    List<IFeed> list = super.hookAfterFetchData(source, isRefresh);
    if (isRefresh) {
        if (CollectionUtil.isNoEmpty(list)) {
            list.add(0, new RecommendTitleData("精品和推荐"));
        }
        if (CollectionUtil.isNoEmpty(mWrapDataList)) {
            list.addAll(0, mWrapDataList);
        }
    }

    // ... 现有的配置位置处理逻辑 ...

    // ✅ 新增：保存缓存数据（仅在刷新时保存）
    if (isRefresh && CollectionUtil.isNoEmpty(list)) {
        // 在后台线程保存缓存
        getExecutors().diskIO().execute(() -> {
            GameTabCacheManager.INSTANCE.saveFeedCache(list);
        });
    }

    return list;
}
```

### 修改点 3: 修改 loadCacheData 方法，加载多态缓存
修改现有的 `loadCacheData()` 方法：

```java
/**
 * 加载缓存数据
 * 优先加载多态缓存，如果不存在则加载旧的单独配置缓存
 */
public Disposable loadCacheData() {
    return Rx2Creator.createObservable(() -> {
        // 优先尝试加载多态缓存
        List<IFeed> cachedFeeds = GameTabCacheManager.INSTANCE.loadFeedCache();
        if (cachedFeeds != null && !cachedFeeds.isEmpty()) {
            return cachedFeeds;
        }

        // 如果多态缓存不存在，fallback到旧的缓存逻辑
        return loadOldCacheData();
    })
    .compose(Rx2Schedulers.observableIoToMain())
    .subscribe(iFeeds -> {
        // 缓存结果
        mCacheDataLd.postValue(iFeeds);
    }, Throwable::printStackTrace);
}

/**
 * 加载旧的缓存数据（兼容旧版本）
 */
private List<IFeed> loadOldCacheData() {
    // 原有的 loadCacheData 逻辑
    Observable<List<AppConfigEntity>> loadConfig = loadCacheConfigList();
    Observable<Pair<AdData, GameInfoEntity>> loadGameAd = loadCacheGameAd();
    return Observable
            .zip(loadConfig, loadGameAd, (configList, adDataPair) -> {
                List<IFeed> result = new ArrayList<>();
                handleConfigList(result, configList, null);
                return result;
            })
            .blockingFirst(new ArrayList<>());
}
```

---

## 使用方式

### 在 Activity/Fragment 中使用

```kotlin
class GameTabFragment : Fragment() {

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // 1. 立即加载缓存数据（冷启动优化）
        viewModel.loadCacheData()

        // 2. 观察缓存数据
        viewModel.cacheDataLd.observe(viewLifecycleOwner) { cachedFeeds ->
            if (cachedFeeds != null && cachedFeeds.isNotEmpty()) {
                // 展示缓存数据
                adapter.submitList(cachedFeeds)
                showCacheIndicator() // 显示"正在加载最新数据"提示
            }
        }

        // 3. 刷新网络数据
        viewModel.refresh()

        // 4. 观察最新数据
        viewModel.dataListLd.observe(viewLifecycleOwner) { newFeeds ->
            // 更新UI，显示最新数据
            adapter.submitList(newFeeds)
            hideCacheIndicator()
        }
    }
}
```

---

## 注意事项

### 1. ⚠️ typeFieldName 冲突检查
已经检查确认：
- IFeed 接口只有方法，无字段 ✅
- 使用 "feedType" 作为类型标识字段

如果未来添加新的 IFeed 子类，请确保该子类没有 "feedType" 字段。

### 2. 子类型注册
当前已注册的子类型：
- RecommendGameMemorabiliaWrapper
- RecommendTitleData
- DiscoveryGameLibWrapper
- AppConfigWrapData
- GameUpdateModuleWrapData
- FeedEntity

**如果未来添加新的子类型，必须在 GameTabFeedStructure.subTypes() 中注册！**

### 3. 嵌套多态数据
`GameMemorabiliaData` 是一个 sealed class，包含：
- `FromAiAd`
- `FromRedDotAdData`

如果需要序列化 `GameMemorabiliaData`，需要创建额外的 JsonPolymorphicStructure：

```kotlin
object GameMemorabiliaDataStructure : JsonPolymorphicStructure<GameMemorabiliaData> {
    override fun baseType() = GameMemorabiliaData::class.java
    override fun typeFieldName() = "memorabiliaType"
    override fun subTypes() = listOf(
        GameMemorabiliaData.FromAiAd::class.java,
        GameMemorabiliaData.FromRedDotAdData::class.java
    )
}
```

然后在序列化时传入两个结构：
```kotlin
JsonPolymorphicUtil.toJsonStr(
    feedList,
    object : TypeToken<List<IFeed>>() {},
    GameTabFeedStructure,
    GameMemorabiliaDataStructure  // 嵌套结构
)
```

### 4. 缓存大小控制
建议只缓存前 20-50 条数据，避免缓存过大：

```kotlin
// 在 hookAfterFetchData 中
if (isRefresh && CollectionUtil.isNoEmpty(list)) {
    getExecutors().diskIO().execute(() -> {
        // 只缓存前50条
        val cacheList = list.take(50)
        GameTabCacheManager.INSTANCE.saveFeedCache(cacheList)
    })
}
```

---

## 测试验证

### 1. 功能测试
- [ ] 冷启动时能否快速展示缓存数据
- [ ] 缓存数据能否正确反序列化
- [ ] 网络数据加载后能否正确替换缓存
- [ ] 各种卡片类型是否都能正确显示

### 2. 边界测试
- [ ] 没有缓存时的行为
- [ ] 缓存数据损坏时的降级处理
- [ ] 新增子类型后是否需要清除旧缓存

### 3. 性能测试
- [ ] 序列化耗时（建议 < 100ms）
- [ ] 反序列化耗时（建议 < 50ms）
- [ ] 缓存文件大小（建议 < 500KB）

---

## 故障排查

### 问题1: 序列化返回空字符串
**原因**: 某个子类型未注册或字段名冲突
**解决**:
1. 检查 GameTabFeedStructure.subTypes() 是否包含所有子类
2. 检查是否有字段名与 "feedType" 冲突

### 问题2: 反序列化返回 null
**原因**: JSON 格式错误或子类型变化
**解决**:
1. 添加日志查看 JSON 内容
2. 检查子类定义是否变更
3. 考虑清除旧缓存重新生成

### 问题3: 某些卡片类型显示异常
**原因**: 该类型未在 subTypes() 中注册
**解决**:
1. 在 GameTabFeedStructure.subTypes() 中添加该类型
2. 清除旧缓存重新生成

---

## 参考文档
- Skill 文档: `.claude/skills/polymorphic-cache/SKILL.md`
- API 参考: `.claude/skills/polymorphic-cache/references/api-reference.md`
- 示例代码: `.claude/skills/polymorphic-cache/references/examples.md`
