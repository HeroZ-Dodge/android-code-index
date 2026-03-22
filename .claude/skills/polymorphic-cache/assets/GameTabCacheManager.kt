package com.netease.god.template


object GameTabCacheManager {

    private const val CACHE_KEY = GLUserConstants.DiscoveryPage.GAME_TAB_FEED_CACHE

    /**
     * 保存游戏Tab数据到缓存
     * @param feedList 待缓存的 Feed 列表
     * @return 是否保存成功
     */
    fun saveFeedCache(feedList: List<IFeed>?): Boolean {
        if (feedList.isNullOrEmpty()) {
            return false
        }

        return try {
            val json = JsonPolymorphicUtil.toJsonStr(
                feedList,
                object : TypeToken<List<IFeed>>() {},
                GameTabFeedStructure
            )

            if (json.isNotEmpty()) {
                val homeRepo = RepoHelper.getHomeRepo()
                homeRepo?.updateSetting(CACHE_KEY, json)
                true
            } else {
                false
            }
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    /**
     * 从缓存加载游戏Tab数据
     * @return 缓存的 Feed 列表，如果缓存不存在或加载失败则返回 null
     */
    fun loadFeedCache(): List<IFeed>? {
        return try {
            val homeRepo = RepoHelper.getHomeRepo() ?: return null
            val json = homeRepo.querySettingBlock(CACHE_KEY)

            if (json.isNullOrEmpty()) {
                return null
            }

            JsonPolymorphicUtil.fromJson(
                json,
                object : TypeToken<List<IFeed>>() {},
                GameTabFeedStructure
            )
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * 清除游戏Tab缓存
     */
    fun clearCache() {
        val homeRepo = RepoHelper.getHomeRepo()
        homeRepo?.updateSetting(CACHE_KEY, "")
    }

    /**
     * 检查是否有缓存数据
     */
    fun hasCached(): Boolean {
        val homeRepo = RepoHelper.getHomeRepo() ?: return false
        val json = homeRepo.querySettingBlock(CACHE_KEY)
        return !json.isNullOrEmpty()
    }
}
