"""
真实数据样本库
从 FeedMockJson.kt 提取的有效数据，用于生成更真实的 mock 数据
"""

# 真实的图片链接样本
IMAGE_URLS = [
    "https://ok.166.net/reunionpub/3_20190909_16d14a2ef2d502024.png",
    "https://ok.166.net/reunionpub/3_20201209_17647756d4a543831.png",
    "https://ok.166.net/reunionpub/3_20250212_194f93c6602765239.jpeg",
    "https://ok.166.net/reunionpub/3_20240914_191efddfc10522017.jpeg",
    "https://ok.166.net/reunionpub/1_kol_20250225_e31bf25e466d0aff2d61a1be4ac6dc17.png",
    "https://ok.166.net/reunionpub/1_20250227_195448a7089920237.png",
    "https://ok.166.net/reunionpub/1_20250508_18f56310f72629283.jpeg",
    "http://cc.fp.ps.netease.com/file/67c15a574ab01385aaf74116FQmVjxX006",
    "http://cc.fp.ps.netease.com/file/6742bbb1d2f0d79c6ea39b58cO0kvsNC05",
    "http://cc.fp.ps.netease.com/file/691582503ca189228be14ff17cETbp2o06",
]

# 真实的视频链接样本
VIDEO_URLS = [
    "https://vod.cc.163.com/file/67bd98e167f6763753179515.mp4?client_type=ios&protocol=https",
    "https://vod.cc.163.com/file/67bfa05e67f676375319d33a.mp4?client_type=android&protocol=https",
    "https://vod.cc.163.com/file/67be689767f67637531876c0.mp4?client_type=android&protocol=https",
    "https://vod.cc.163.com/file/678dfdc0d55230f11c90ccf2.mp4?client_type=android&protocol=https",
]

# 真实的 Feed ID 样本
FEED_IDS = [
    "67bd9c3cc2c28b7eee504ff1",
    "67bfa0e1c2c28b7eee57c055",
    "67be692d4c206e55944ea126",
    "663df65719ad834e551fc840",
    "67b2ed665782e7446950b118",
    "67b2ed635782e7446950b10f",
    "67b2ed605782e7446950b10b",
    "67b2ed5f5782e7446950b107",
    "67b2ed5d5782e7446950b103",
    "67b2ed595782e7446950b0fb",
    "67b2ed445782e7446950b0d2",
    "67b2ed295782e7446950b05d",
    "67bee15c5782e7446950b45b",
    "67beb87c5782e7446950b3f6",
]

# 真实的 UID 样本
USER_UIDS = [
    "f9946ffd4fcb4fd5999929f715b3c98c",
    "66cda0a2b40346108cda1f3b77384a86",
    "41ab5c0111094d2daa9fdf30a6e37a0c",
    "3a782c52c5d54a4b9fcd1dadd39d6c44",
    "653866f1a44147b8823658b4d018402f",
    "b7a91f6362ee4b98be3bd7679b638a33",
    "e2703a9f55b041ef8d948db5ad1b0208",
    "260a4d303edc48a78fb48aa89d9710f2",
]

# 真实的用户信息样本
USER_SAMPLES = [
    {
        "uid": "f9946ffd4fcb4fd5999929f715b3c98c",
        "nick": "玲珑紫嫣",
        "icon": "https://ok.166.net/reunionpub/3_20190909_16d14a2ef2d502024.png",
        "intro": "",
        "gender": 1,
        "birth": "1985-10-15",
        "deleteTime": 0,
        "createTime": 1548169428622,
        "updateTime": 1568009286671
    },
    {
        "uid": "66cda0a2b40346108cda1f3b77384a86",
        "nick": "你们亲爱的大明哥",
        "icon": "https://ok.166.net/reunionpub/3_20201209_17647756d4a543831.png",
        "intro": "善言结善缘🙏 开心每一天 😁😁😁",
        "gender": 1,
        "birth": "1991-01-31",
        "location": "深圳市",
        "identityAuthenticInfo": "大话手游攻略达人，估号师",
        "identityType": "3",
        "followerLevel": 1,
        "state": "NORMAL",
        "medal": "5e7ab776a54a0030783fa3aa",
        "deleteTime": 0,
        "createTime": 1531847762788,
        "updateTime": 1719890851050
    },
    {
        "uid": "3a782c52c5d54a4b9fcd1dadd39d6c44",
        "nick": "落月Amor",
        "icon": "https://ok.166.net/reunionpub/3_20250212_194f93c6602765239.jpeg",
        "intro": "当时只道是寻常。",
        "gender": 1,
        "identityAuthenticInfo": "大话西游手游视频达人",
        "identityType": "3",
        "followerLevel": 1,
        "state": "NORMAL",
        "frame": "668e43acc50e3f6163c2a203",
        "medal": "5e7ab776a54a0030783fa3aa",
        "deleteTime": 0,
        "createTime": 1685627641639,
        "updateTime": 1739348276066
    },
    {
        "uid": "41ab5c0111094d2daa9fdf30a6e37a0c",
        "nick": "大话西游妹夫仔",
        "icon": "https://ok.166.net/reunionpub/3_20240914_191efddfc10522017.jpeg",
        "intro": "妹夫仔",
        "gender": 1,
        "birth": "1982-12-03",
        "identityAuthenticInfo": "大话手游视频达人\\n大话西游手游攻略达人",
        "identityType": "3",
        "followerLevel": 1,
        "frame": "5ea7d74bbc54b71683eeb6d2",
        "medal": "66d58ba672996d0c86b8a989",
        "deleteTime": 0,
        "createTime": 1540712711131,
        "updateTime": 1726306190223
    },
    {
        "uid": "b7a91f6362ee4b98be3bd7679b638a33",
        "nick": "哈利波特和他的猫",
        "icon": "https://ok.166.net/reunionpub/3_20240628_1905dfc46dd164138.jpeg",
        "intro": "Hahaha",
        "gender": 2,
        "birth": "1995-01-01",
        "identityAuthenticInfo": "地图创作者",
        "identityType": "3",
        "state": "NORMAL",
        "deleteTime": 0,
        "createTime": 1659086475474,
        "updateTime": 1719563733890
    }
]

# 真实的 Feed Entity 样本
FEED_SAMPLES = [
    {
        "id": "67bd9c3cc2c28b7eee504ff1",
        "uid": "66cda0a2b40346108cda1f3b77384a86",
        "type": 3,
        "deleteTime": 0,
        "createTime": 1740479253766,
        "updateTime": 1740479548333,
        "clientType": 72,
        "squareId": "5bed7223d545682b8bb8b732",
        "like": False,
        "record": {
            "id": "67bd9c3cc2c28b7eee504ff1",
            "repostCount": 3,
            "commentCount": 48,
            "likeCount": 68,
            "shareCount": 13,
            "favCount": 2,
            "createTime": 1740479691847
        },
        "displayIpInfo": {
            "ipLocationName": "山东"
        }
    },
    {
        "id": "67bfa0e1c2c28b7eee57c055",
        "uid": "41ab5c0111094d2daa9fdf30a6e37a0c",
        "type": 3,
        "visibility": 0,
        "deleteTime": 0,
        "createTime": 1740611806883,
        "updateTime": 1740611809928,
        "clientType": 50,
        "squareId": "5bed7223d545682b8bb8b732",
        "like": False,
        "record": {
            "id": "67bfa0e1c2c28b7eee57c055",
            "repostCount": 2,
            "commentCount": 45,
            "likeCount": 21,
            "shareCount": 4,
            "favCount": 11,
            "createTime": 1740611899342
        },
        "displayIpInfo": {
            "ipLocationName": "江西"
        }
    },
    {
        "id": "67be692d4c206e55944ea126",
        "uid": "3a782c52c5d54a4b9fcd1dadd39d6c44",
        "type": 3,
        "visibility": 0,
        "deleteTime": 0,
        "createTime": 1740532011437,
        "updateTime": 1740532013445,
        "clientType": 50,
        "squareId": "5bed7223d545682b8bb8b732",
        "like": False,
        "record": {
            "id": "67be692d4c206e55944ea126",
            "repostCount": 2,
            "commentCount": 43,
            "likeCount": 21,
            "shareCount": 4,
            "favCount": 1,
            "createTime": 1740532371095
        },
        "displayIpInfo": {
            "ipLocationName": "辽宁"
        }
    }
]

# 真实的 Record 样本
RECORD_SAMPLES = [
    {
        "uid": "f9946ffd4fcb4fd5999929f715b3c98c",
        "feedCount": 1,
        "followerCount": 83,
        "followingCount": 66,
        "roleCount": 0,
        "squareCount": 1,
        "likeCount": 0
    },
    {
        "uid": "66cda0a2b40346108cda1f3b77384a86",
        "feedCount": 5092,
        "followerCount": 39203,
        "followingCount": 114,
        "roleCount": 31,
        "columnCount": 3,
        "squareCount": 8,
        "likeCount": 202015,
        "lastPostIpLocation": "山东"
    },
    {
        "uid": "3a782c52c5d54a4b9fcd1dadd39d6c44",
        "feedCount": 1449,
        "followerCount": 9592,
        "followingCount": 92,
        "roleCount": 1,
        "columnCount": 5,
        "squareCount": 9,
        "likeCount": 56318,
        "lastPostIpLocation": "辽宁"
    },
    {
        "uid": "41ab5c0111094d2daa9fdf30a6e37a0c",
        "feedCount": 778,
        "followerCount": 4259,
        "followingCount": 1789,
        "roleCount": 1,
        "columnCount": 9,
        "squareCount": 10,
        "likeCount": 30278,
        "lastPostIpLocation": "江西"
    }
]

# 真实的直播信息样本
LIVE_ROOM_SAMPLES = [
    {
        "roomType": "-1",
        "purl": "http://cc.fp.ps.netease.com/file/6742bbb1d2f0d79c6ea39b58cO0kvsNC05",
        "ccId": "3169730",
        "roomId": "917",
        "channelId": "4930040",
        "title": "玩新区就来领专属礼包",
        "cover": "http://cc.fp.ps.netease.com/file/67c15a574ab01385aaf74116FQmVjxX006",
        "hotScore": "210428",
        "ccUid": "2764593",
        "nickname": "917-伴永久",
        "gameType": "28"
    },
    {
        "roomType": "-1",
        "purl": "http://cc.fp.ps.netease.com/file/6600e845633bdda3091d46649QSGZiqe05",
        "ccId": "249161",
        "roomId": "24",
        "channelId": "6748954",
        "title": "【重播】永劫无间手游S8前瞻特别节目",
        "cover": "http://cc.fp.ps.netease.com/file/691582503ca189228be14ff17cETbp2o06",
        "hotScore": "39854",
        "ccUid": "289952844",
        "nickname": "永劫无间手游",
        "gameType": "9161"
    }
]

# Square ID 样本
SQUARE_IDS = [
    "5bed7223d545682b8bb8b732",
    "62860a7ad97e1c02a80eaf02",
    "61e8de8323939b00018093ae",
    "5d318688550f0256f7d80262",
]

# Tag ID 样本
TAG_IDS = [
    "63bd0a66f22be80001afea59",
    "66f8c4e47e8fde63aa2778e7",
    "6704a85af497633e942e9bca",
    "5b026effd545685882af802d",
    "65af9f85210b0b688af758ef",
    "66f695b35aeba81a829379ee",
]

# IP 位置样本
IP_LOCATIONS = ["山东", "江西", "辽宁", "浙江", "广东", "宁夏", "深圳市", "北京", "上海"]

# 真实的媒体样本（包含完整信息）
MEDIA_SAMPLES = [
    {
        "name": "普通克、赤焰妖克、朱雀克与符咒的伤害对比！.mp4",
        "url": "https://vod.cc.163.com/file/67bd98e167f6763753179515.mp4?client_type=ios&protocol=https",
        "text": "没想到符咒的增伤这么强！",
        "mimeType": "video/mp4",
        "size": 123097285,
        "duration": 140990,
        "cover": "https://ok.166.net/reunionpub/1_kol_20250225_e31bf25e466d0aff2d61a1be4ac6dc17.png",
        "mediaId": "67bd98e167f6763753179515",
        "sourceMediaId": "67bd98e167f6763753179515"
    },
    {
        "url": "https://vod.cc.163.com/file/67bfa05e67f676375319d33a.mp4?client_type=android&protocol=https",
        "mimeType": "video/mp4",
        "size": 16198955,
        "duration": 38359,
        "width": 1920,
        "height": 1080,
        "cover": "https://ok.166.net/reunionpub/1_20250227_195448a7089920237.png",
        "mediaId": "67bfa05e67f676375319d33a",
        "sourceMediaId": "67bfa05e67f676375319d33a"
    }
]

# 真实的话题信息样本
TOPIC_SAMPLES = [
    {"topicName": "大话西游手游", "type": "DEFAULT"},
    {"topicName": "大话西游手游大神繁星计划", "type": "DEFAULT"},
    {"topicName": "大话手游大神创作者激励计划", "type": "DEFAULT"},
    {"topicName": "永劫手游大神创作激励", "type": "DEFAULT"},
    {"topicName": "测试正常话题", "type": "DEFAULT"},
    {"topicName": "test", "type": "DEFAULT"},
]