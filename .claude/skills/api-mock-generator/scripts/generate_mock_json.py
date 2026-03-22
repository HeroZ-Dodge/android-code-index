#!/usr/bin/env python3
"""
基于数据模型生成 mock JSON 数据（使用真实数据样本）
"""
import json
import sys
import random
from typing import Any
from real_data_samples import (
    IMAGE_URLS, VIDEO_URLS, FEED_IDS, USER_UIDS,
    USER_SAMPLES, FEED_SAMPLES, RECORD_SAMPLES,
    SQUARE_IDS, IP_LOCATIONS, LIVE_ROOM_SAMPLES,
    MEDIA_SAMPLES, TOPIC_SAMPLES, TAG_IDS
)


def get_random_image() -> str:
    """随机获取一个真实的图片URL"""
    return random.choice(IMAGE_URLS)


def get_random_video() -> str:
    """随机获取一个真实的视频URL"""
    return random.choice(VIDEO_URLS)


def get_random_feed_id() -> str:
    """随机获取一个真实的Feed ID"""
    return random.choice(FEED_IDS)


def get_random_uid() -> str:
    """随机获取一个真实的UID"""
    return random.choice(USER_UIDS)


def get_random_square_id() -> str:
    """随机获取一个真实的Square ID"""
    return random.choice(SQUARE_IDS)


def get_random_user() -> dict:
    """随机获取一个真实的用户对象"""
    return random.choice(USER_SAMPLES).copy()


def get_random_feed() -> dict:
    """随机获取一个真实的Feed对象"""
    return random.choice(FEED_SAMPLES).copy()


def get_random_record() -> dict:
    """随机获取一个真实的Record对象"""
    return random.choice(RECORD_SAMPLES).copy()


def generate_mock_for_type(type_name: str, field_name: str = "") -> Any:
    """
    根据类型名称生成 mock 数据（优先使用真实数据）
    """
    # 基于字段名识别特定类型
    field_lower = field_name.lower()

    # 图片相关
    if 'icon' in field_lower or 'cover' in field_lower or 'image' in field_lower or 'avatar' in field_lower:
        return get_random_image()

    # 视频相关
    if 'video' in field_lower or 'media' in field_lower:
        return get_random_video()

    # ID 相关
    if 'feedid' in field_lower or (field_lower == 'id' and 'feed' in type_name.lower()):
        return get_random_feed_id()

    if 'uid' in field_lower or 'userid' in field_lower:
        return get_random_uid()

    if 'squareid' in field_lower:
        return get_random_square_id()

    # 位置相关
    if 'location' in field_lower or 'iplocation' in field_lower:
        return random.choice(IP_LOCATIONS)

    # 基础类型映射
    type_mapping = {
        'String': f"test_{field_name}" if field_name else "test_string",
        'Int': random.randint(1, 1000),
        'Long': random.randint(1000000000, 1999999999),
        'Boolean': random.choice([True, False]),
        'Double': round(random.uniform(1, 1000), 2),
        'Float': round(random.uniform(1, 1000), 2),
    }

    # 列表类型
    if type_name.startswith('List<') or type_name.startswith('ArrayList<'):
        inner_type = type_name.split('<')[1].rstrip('>')
        return [generate_mock_for_type(inner_type, field_name) for _ in range(2)]

    # Map 类型
    if type_name.startswith('Map<'):
        return {"key1": "value1", "key2": "value2"}

    # 基础类型
    if type_name in type_mapping:
        return type_mapping[type_name]

    # 对象类型 - 使用真实数据或生成默认结构
    return generate_default_object_mock(type_name)


def generate_default_object_mock(type_name: str) -> dict:
    """
    为自定义对象类型生成 mock 结构（优先使用真实数据样本）
    """
    type_lower = type_name.lower()

    # 使用真实的用户数据
    if 'user' in type_lower and 'info' in type_lower:
        return get_random_user()

    # 使用真实的 Feed 数据
    if 'feed' in type_lower and not 'content' in type_lower:
        return get_random_feed()

    # 使用真实的 Record 数据
    if 'record' in type_lower:
        return get_random_record()

    # 直播相关 - 使用真实直播间数据
    if 'live' in type_lower or 'room' in type_lower:
        return random.choice(LIVE_ROOM_SAMPLES).copy()

    # 媒体相关 - 使用真实媒体数据
    if 'media' in type_lower:
        return random.choice(MEDIA_SAMPLES).copy()

    # 话题相关 - 使用真实话题数据
    if 'topic' in type_lower:
        return random.choice(TOPIC_SAMPLES).copy()

    # 榜单相关
    if 'ranking' in type_lower or 'rank' in type_lower:
        return {
            "id": get_random_feed_id(),
            "name": "热门榜单",
            "icon": get_random_image(),
            "items": [
                {
                    "id": get_random_feed_id(),
                    "title": "榜单项目1",
                    "score": random.randint(1000, 10000)
                },
                {
                    "id": get_random_feed_id(),
                    "title": "榜单项目2",
                    "score": random.randint(1000, 10000)
                }
            ]
        }

    # 默认结构
    return {
        "id": get_random_feed_id(),
        "name": "test_name",
        "value": "test_value"
    }


def generate_mock_json(result_type: str, api_path: str = "", result_key: str = None) -> dict:
    """
    生成完整的 mock JSON 响应（使用真实数据）

    参数：
        result_type: 返回数据类型（如 SquareRankingTabResult）
        api_path: API 路径（用于推断数据结构）
        result_key: result 内部的实际数据 key，如 "schemeAccountList"

    返回：
        完整的 mock JSON 对象，格式为：
        {
          "result": {
            "actualData": ...
          },
          "code": 200,
          "errmsg": "OK"
        }
    """
    # 基于结果类型生成 mock 数据
    if 'List' in result_type or result_type.endswith('s'):
        # 列表类型的结果
        inner_type = result_type.replace('List', '').rstrip('s')
        result_data = [
            generate_default_object_mock(inner_type),
            generate_default_object_mock(inner_type)
        ]
    else:
        # 对象类型的结果
        result_data = generate_default_object_mock(result_type)

    # 如果指定了 result_key，将数据放在该 key 下
    if result_key:
        return {
            "result": {
                result_key: result_data
            },
            "code": 200,
            "errmsg": "OK"
        }
    else:
        # 否则直接作为 result
        return {
            "result": result_data,
            "code": 200,
            "errmsg": "OK"
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_mock_json.py <result_type> [api_path] [result_key]")
        sys.exit(1)

    result_type = sys.argv[1]
    api_path = sys.argv[2] if len(sys.argv) > 2 else ""
    result_key = sys.argv[3] if len(sys.argv) > 3 else None

    mock_data = generate_mock_json(result_type, api_path, result_key)
    print(json.dumps(mock_data, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()