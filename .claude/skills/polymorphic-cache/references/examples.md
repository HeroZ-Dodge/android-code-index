# 多态缓存完整示例

本文档包含三个典型场景的完整实现示例。

## 目录
- [场景 1: Feed 流列表](#场景-1-feed-流列表)
- [场景 2: 聊天/消息列表](#场景-2-聊天消息列表)
- [场景 3: 游戏Tab](#场景-3-游戏tab)
- [进阶: 嵌套多态数据](#进阶-嵌套多态数据)

---

## 场景 1: Feed 流列表

### 业务需求
首页 Feed 流包含多种卡片类型：视频卡片、图文卡片、直播卡片。需要在冷启动时快速展示上次浏览的内容。

### 完整实现

```kotlin
// 1. 定义数据模型
sealed class FeedCard {
    abstract val id: String
    abstract val timestamp: Long
    abstract val authorName: String
}

data class VideoCard(
    override val id: String,
    override val timestamp: Long,
    override val authorName: String,
    val videoUrl: String,
    val coverUrl: String,
    val duration: Int,
    val playCount: Int
) : FeedCard()

data class ImageTextCard(
    override val id: String,
    override val timestamp: Long,
    override val authorName: String,
    val title: String,
    val images: List<String>,
    val content: String,
    val likeCount: Int
) : FeedCard()

data class LiveCard(
    override val id: String,
    override val timestamp: Long,
    override val authorName: String,
    val liveUrl: String,
    val coverUrl: String,
    val viewerCount: Int,
    val isLiving: Boolean
) : FeedCard()

// 2. 定义多态结构
object FeedCardStructure : JsonPolymorphicStructure<FeedCard> {
    override fun baseType() = FeedCard::class.java
    override fun typeFieldName() = "cardType"
    override fun subTypes() = listOf(
        VideoCard::class.java,
        ImageTextCard::class.java,
        LiveCard::class.java
    )
}

// 3. 在 Activity/Fragment 中使用
class FeedFragment : Fragment() {

    private val adapter = FeedAdapter()
    private val cacheKey = "feed_list_cache"

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // 立即加载缓存数据
        loadCacheData()

        // 异步加载网络数据
        loadNetworkData()
    }

    private fun loadCacheData() {
        val cachedJson = PreferenceUtil.getString(cacheKey, "")
        if (cachedJson.isNotEmpty()) {
            val cachedList = JsonPolymorphicUtil.fromJson<List<FeedCard>>(
                cachedJson,
                object : TypeToken<List<FeedCard>>() {},
                FeedCardStructure
            )
            cachedList?.let {
                adapter.submitList(it)
                // 显示缓存标识
                showCacheIndicator()
            }
        }
    }

    private fun loadNetworkData() {
        viewModel.getFeedList().observe(viewLifecycleOwner) { feedList ->
            // 更新 UI
            adapter.submitList(feedList)

            // 保存到缓存
            val json = JsonPolymorphicUtil.toJsonStr(
                feedList,
                object : TypeToken<List<FeedCard>>() {},
                FeedCardStructure
            )
            PreferenceUtil.putString(cacheKey, json)
        }
    }
}
```

### 生成的 JSON 示例

```json
[
  {
    "cardType": "com.example.VideoCard",
    "id": "v_001",
    "timestamp": 1234567890,
    "authorName": "张三",
    "videoUrl": "https://example.com/video.mp4",
    "coverUrl": "https://example.com/cover.jpg",
    "duration": 120,
    "playCount": 1000
  },
  {
    "cardType": "com.example.ImageTextCard",
    "id": "it_002",
    "timestamp": 1234567891,
    "authorName": "李四",
    "title": "美食分享",
    "images": ["img1.jpg", "img2.jpg"],
    "content": "今天做的美食...",
    "likeCount": 500
  },
  {
    "cardType": "com.example.LiveCard",
    "id": "l_003",
    "timestamp": 1234567892,
    "authorName": "王五",
    "liveUrl": "https://example.com/live",
    "coverUrl": "https://example.com/live_cover.jpg",
    "viewerCount": 2000,
    "isLiving": true
  }
]
```

---

## 场景 2: 聊天/消息列表

### 业务需求
聊天页面包含多种消息类型：文本消息、图片消息、语音消息、视频消息。需要缓存最近的聊天记录。

### 完整实现

```kotlin
// 1. 定义数据模型
sealed class Message {
    abstract val msgId: String
    abstract val senderId: String
    abstract val timestamp: Long
    abstract val isFromMe: Boolean
}

data class TextMessage(
    override val msgId: String,
    override val senderId: String,
    override val timestamp: Long,
    override val isFromMe: Boolean,
    val text: String
) : Message()

data class ImageMessage(
    override val msgId: String,
    override val senderId: String,
    override val timestamp: Long,
    override val isFromMe: Boolean,
    val imageUrl: String,
    val thumbnailUrl: String,
    val width: Int,
    val height: Int
) : Message()

data class VoiceMessage(
    override val msgId: String,
    override val senderId: String,
    override val timestamp: Long,
    override val isFromMe: Boolean,
    val voiceUrl: String,
    val duration: Int  // 秒
) : Message()

data class VideoMessage(
    override val msgId: String,
    override val senderId: String,
    override val timestamp: Long,
    override val isFromMe: Boolean,
    val videoUrl: String,
    val coverUrl: String,
    val duration: Int,
    val width: Int,
    val height: Int
) : Message()

// 2. 定义多态结构
object MessageStructure : JsonPolymorphicStructure<Message> {
    override fun baseType() = Message::class.java
    override fun typeFieldName() = "msgType"
    override fun subTypes() = listOf(
        TextMessage::class.java,
        ImageMessage::class.java,
        VoiceMessage::class.java,
        VideoMessage::class.java
    )
}

// 3. 消息缓存管理器
class MessageCacheManager(private val sessionId: String) {

    private val cacheKey get() = "msg_cache_$sessionId"

    fun saveMessages(messages: List<Message>) {
        val json = JsonPolymorphicUtil.toJsonStr(
            messages,
            object : TypeToken<List<Message>>() {},
            MessageStructure
        )
        PreferenceUtil.putString(cacheKey, json)
    }

    fun loadMessages(): List<Message>? {
        val json = PreferenceUtil.getString(cacheKey, "")
        return if (json.isNotEmpty()) {
            JsonPolymorphicUtil.fromJson(
                json,
                object : TypeToken<List<Message>>() {},
                MessageStructure
            )
        } else {
            null
        }
    }

    fun clearCache() {
        PreferenceUtil.remove(cacheKey)
    }
}

// 4. 在聊天页面使用
class ChatActivity : AppCompatActivity() {

    private lateinit var cacheManager: MessageCacheManager
    private val adapter = MessageAdapter()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val sessionId = intent.getStringExtra("sessionId") ?: return
        cacheManager = MessageCacheManager(sessionId)

        // 加载缓存消息
        cacheManager.loadMessages()?.let { cachedMessages ->
            adapter.submitList(cachedMessages)
        }

        // 加载历史消息
        loadHistoryMessages(sessionId)
    }

    private fun loadHistoryMessages(sessionId: String) {
        viewModel.getMessageHistory(sessionId).observe(this) { messages ->
            adapter.submitList(messages)
            // 缓存最新 50 条消息
            cacheManager.saveMessages(messages.takeLast(50))
        }
    }
}
```

---

## 场景 3: 游戏Tab

### 业务需求
游戏Tab页面包含多种游戏卡片：推荐游戏、热门游戏、新游预告等。

### 完整实现

```kotlin
// 1. 定义数据模型
sealed class GameItem {
    abstract val gameId: String
    abstract val gameName: String
    abstract val iconUrl: String
}

data class RecommendGame(
    override val gameId: String,
    override val gameName: String,
    override val iconUrl: String,
    val recommendReason: String,
    val score: Float,
    val downloadCount: Int
) : GameItem()

data class HotGame(
    override val gameId: String,
    override val gameName: String,
    override val iconUrl: String,
    val ranking: Int,
    val playerCount: Int,
    val tags: List<String>
) : GameItem()

data class NewGamePreview(
    override val gameId: String,
    override val gameName: String,
    override val iconUrl: String,
    val releaseDate: String,
    val preOrderCount: Int,
    val trailerUrl: String
) : GameItem()

// 2. 定义多态结构
object GameItemStructure : JsonPolymorphicStructure<GameItem> {
    override fun baseType() = GameItem::class.java
    override fun typeFieldName() = "itemType"
    override fun subTypes() = listOf(
        RecommendGame::class.java,
        HotGame::class.java,
        NewGamePreview::class.java
    )
}

// 3. 游戏Tab Fragment
class GameTabFragment : Fragment() {

    private val cacheKey = "game_tab_cache"

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // 快速展示缓存
        loadCachedGames()

        // 刷新数据
        refreshGames()
    }

    private fun loadCachedGames() {
        val json = PreferenceUtil.getString(cacheKey, "")
        if (json.isNotEmpty()) {
            val games = JsonPolymorphicUtil.fromJson<List<GameItem>>(
                json,
                object : TypeToken<List<GameItem>>() {},
                GameItemStructure
            )
            games?.let { displayGames(it, fromCache = true) }
        }
    }

    private fun refreshGames() {
        viewModel.getGameList().observe(viewLifecycleOwner) { games ->
            displayGames(games, fromCache = false)

            // 保存缓存
            val json = JsonPolymorphicUtil.toJsonStr(
                games,
                object : TypeToken<List<GameItem>>() {},
                GameItemStructure
            )
            PreferenceUtil.putString(cacheKey, json)
        }
    }

    private fun displayGames(games: List<GameItem>, fromCache: Boolean) {
        // 根据类型渲染不同的卡片
        games.forEach { game ->
            when (game) {
                is RecommendGame -> renderRecommendCard(game)
                is HotGame -> renderHotCard(game)
                is NewGamePreview -> renderPreviewCard(game)
            }
        }
    }
}
```

---

## 进阶: 嵌套多态数据

### 场景描述
有时数据结构中会嵌套多态数据。例如，Feed 卡片中的"内容"本身也是多态的。

### 示例实现

```kotlin
// 内层多态: 卡片内容
sealed class CardContent {
    abstract val contentId: String
}

data class TextContent(
    override val contentId: String,
    val text: String
) : CardContent()

data class MediaContent(
    override val contentId: String,
    val mediaUrl: String,
    val mediaType: String  // "image" or "video"
) : CardContent()

// 外层多态: Feed 卡片
sealed class FeedCard {
    abstract val cardId: String
    abstract val content: CardContent  // 嵌套多态
}

data class StandardCard(
    override val cardId: String,
    override val content: CardContent,
    val title: String
) : FeedCard()

data class HighlightCard(
    override val cardId: String,
    override val content: CardContent,
    val highlightColor: String
) : FeedCard()

// 定义两个多态结构
object CardContentStructure : JsonPolymorphicStructure<CardContent> {
    override fun baseType() = CardContent::class.java
    override fun typeFieldName() = "contentType"
    override fun subTypes() = listOf(
        TextContent::class.java,
        MediaContent::class.java
    )
}

object FeedCardStructure : JsonPolymorphicStructure<FeedCard> {
    override fun baseType() = FeedCard::class.java
    override fun typeFieldName() = "cardType"
    override fun subTypes() = listOf(
        StandardCard::class.java,
        HighlightCard::class.java
    )
}

// 序列化时传入两个结构
fun saveFeedCards(cards: List<FeedCard>) {
    val json = JsonPolymorphicUtil.toJsonStr(
        cards,
        object : TypeToken<List<FeedCard>>() {},
        FeedCardStructure,
        CardContentStructure  // 同时注册嵌套的多态结构
    )
    PreferenceUtil.putString("feed_cache", json)
}

// 反序列化时也传入两个结构
fun loadFeedCards(): List<FeedCard>? {
    val json = PreferenceUtil.getString("feed_cache", "")
    return JsonPolymorphicUtil.fromJson(
        json,
        object : TypeToken<List<FeedCard>>() {},
        FeedCardStructure,
        CardContentStructure
    )
}
```

### 生成的嵌套 JSON

```json
[
  {
    "cardType": "com.example.StandardCard",
    "cardId": "card_001",
    "content": {
      "contentType": "com.example.TextContent",
      "contentId": "content_001",
      "text": "这是文本内容"
    },
    "title": "标准卡片"
  },
  {
    "cardType": "com.example.HighlightCard",
    "cardId": "card_002",
    "content": {
      "contentType": "com.example.MediaContent",
      "contentId": "content_002",
      "mediaUrl": "https://example.com/video.mp4",
      "mediaType": "video"
    },
    "highlightColor": "#FF5722"
  }
]
```

---

## 最佳实践建议

1. **缓存数量控制**: 不要缓存过多数据，建议只缓存最近 20-50 条记录
2. **缓存时机**: 在数据加载成功后立即缓存，确保缓存数据是最新的
3. **缓存失效**: 可以添加 timestamp 字段，超过一定时间自动清除缓存
4. **异常处理**: fromJson 可能返回 null，务必做 null check
5. **性能优化**: 大数据量时考虑使用文件存储而非 SharedPreferences
