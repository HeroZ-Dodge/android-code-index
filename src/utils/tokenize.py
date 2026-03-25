"""标识符分词：camelCase 拆分 + Android 专用术语保留。"""

import re

# Android / Kotlin / Java 专用术语表（小写），贪心合并阶段用于识别不拆分的完整单元。
ANDROID_KNOWN_TERMS: frozenset[str] = frozenset({
    # Android 核心组件
    "activity",
    "fragment",
    "service",
    "broadcastreceiver",
    "contentprovider",
    "view",
    "viewgroup",
    "recyclerview",
    "listview",
    "intent",
    "bundle",
    "context",
    "resources",
    "drawable",
    "bitmap",
    "handler",
    "looper",
    "asynctask",
    "sharedpreferences",
    "cursor",
    "uri",
    "parcel",
    # 生命周期方法
    "oncreate",
    "onstart",
    "onresume",
    "onpause",
    "onstop",
    "ondestroy",
    "onsaveinstancestate",
    "onrestoreinstancestate",
    "onattach",
    "ondetach",
    "onbind",
    "onunbind",
    "onreceive",
    "onactivityresult",
    "onrequestpermissionsresult",
    "onviewcreated",
    # 常用 Android API 方法
    "findviewbyid",
    "setcontentview",
    "startactivity",
    "startservice",
    "bindservice",
    "sendbroadcast",
    "registerreceiver",
    "unregisterreceiver",
    "inflate",
    "postdelayed",
    "observe",
    "settext",
    "setimageresource",
    "getsystemservice",
    # Jetpack 类
    "livedata",
    "viewmodel",
    "mutablelivedata",
    "stateflow",
    "flow",
    "navcontroller",
    "databinding",
    "viewbinding",
    "room",
    "workmanager",
    "paging",
    # Gradle DSL 关键字
    "compilesdkversion",
    "minsdkversion",
    "targetsdkversion",
    "applicationid",
    "versioncode",
    "versionname",
})


def split_identifier(name: str) -> str:
    """
    将驼峰/Pascal 命名拆分为空格分隔的小写 token 序列，Android 专用术语保持完整。

    两步算法：
      1. 正则 camelCase 拆分
      2. 贪心左向合并：相邻片段拼合后若命中 ANDROID_KNOWN_TERMS，则合并为单一 token

    示例：
      getUserById      → "get user by id"
      OnClickListener  → "on click listener"
      ViewModelFactory → "viewmodel factory"       (ViewModel 保留)
      onCreateView     → "oncreate view"            (onCreate 保留)
      BaseActivity     → "base activity"            (Activity 保留)
      LiveDataObserver → "livedata observer"        (LiveData 保留)
      RecyclerViewAdapter → "recyclerview adapter" (RecyclerView 保留)
      parseJSON2XML    → "parse json 2 xml"
    """
    # 步骤 1：正则拆分
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", name)  # XMLParser → XML Parser
    s = re.sub(r"([a-z\d])([A-Z])", r"\1 \2", s)          # camelCase → camel Case
    s = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", s)            # rgb2hex → rgb 2 hex
    s = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", s)
    parts = [p.lower() for p in s.split() if p]

    # 步骤 2：贪心左向合并（尽量取最长命中字典的合并结果）
    merged: list[str] = []
    i = 0
    while i < len(parts):
        best_end = i  # 默认：不合并
        combined = parts[i]
        for j in range(i + 1, len(parts)):
            combined += parts[j]
            if combined in ANDROID_KNOWN_TERMS:
                best_end = j  # 命中字典，记录最远位置
        merged.append("".join(parts[i : best_end + 1]))
        i = best_end + 1

    return " ".join(merged)
