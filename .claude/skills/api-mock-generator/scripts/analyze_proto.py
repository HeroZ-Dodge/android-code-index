#!/usr/bin/env python3
"""
分析 Kotlin Proto 类，提取接口信息
"""
import re
import sys
import json
from pathlib import Path


def analyze_proto_class(file_path: str) -> dict:
    """
    分析 Proto 类文件，提取关键信息

    返回：
    {
        "class_name": "GetRecommentRankingAndItemsProto",
        "api_path": "/game-creation/game-ranking/recommend/getRankingAndItems",
        "result_type": "SquareRankingTabResult",
        "package": "com.netease.gl.servicefeed.feed.proto.creation",
        "params": ["colorConfig", "count", "page", "groupId", "squareId"]
    }
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    result = {}

    # 提取包名
    package_match = re.search(r'package\s+([\w.]+)', content)
    result['package'] = package_match.group(1) if package_match else ''

    # 提取类名
    class_match = re.search(r'class\s+(\w+)\s*\(', content)
    result['class_name'] = class_match.group(1) if class_match else ''

    # 提取 API 路径
    api_match = re.search(r'return\s+"([^"]+)"', content)
    result['api_path'] = api_match.group(1) if api_match else ''

    # 提取返回类型（从 result 变量声明或 JsonUtil.fromJson）
    result_type_match = re.search(r'JsonUtil\.fromJson\([^,]+,\s*(\w+)::class\.java\)', content)
    if result_type_match:
        result['result_type'] = result_type_match.group(1)
    else:
        # 尝试从 result 变量声明中提取
        result_var_match = re.search(r'private\s+var\s+result:\s*(\w+)\?', content)
        result['result_type'] = result_var_match.group(1) if result_var_match else 'JsonObject'

    # 提取参数（从构造函数）
    params = []
    constructor_match = re.search(r'class\s+\w+\s*\((.*?)\)\s*:', content, re.DOTALL)
    if constructor_match:
        param_text = constructor_match.group(1)
        param_matches = re.findall(r'private\s+val\s+(\w+):', param_text)
        params = param_matches
    result['params'] = params

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_proto.py <proto_file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    result = analyze_proto_class(file_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()