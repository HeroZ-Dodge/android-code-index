#!/usr/bin/env python3
"""搜索文档并返回匹配结果"""

import os
import sys
import json
import re
from pathlib import Path

def get_docs_site_dir():
    """获取 docs-site 目录路径"""
    script_dir = Path(__file__).parent
    return script_dir.parent.parent.parent.parent / "docs-site"

def load_structure():
    """加载 structure.json"""
    docs_site = get_docs_site_dir()
    structure_file = docs_site / "structure.json"
    if structure_file.exists():
        with open(structure_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def search_in_file(file_path, keywords):
    """在文件中搜索关键词，路径匹配权重更高"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().lower()

        # 计算匹配度（路径权重 = 10，内容权重 = 1）
        path_str = str(file_path).lower()
        score = 0
        path_matches = 0
        content_matches = 0

        for keyword in keywords:
            kw = keyword.lower()
            # 路径/文件名匹配（高权重）
            if kw in path_str:
                path_matches += 1
                score += 10
            # 内容匹配（低权重）
            if kw in content:
                content_matches += 1
                score += 1

        if score > 0:
            # 提取标题
            title = None
            lines = content.split("\n")
            for line in lines:
                if line.startswith("# "):
                    title = line[2:].strip()
                    break

            return {
                "score": score,
                "path_matches": path_matches,
                "content_matches": content_matches,
                "title": title or file_path.stem
            }
    except Exception:
        pass
    return None

def get_url_from_path(file_path, docs_site, base_url="http://localhost:3000/docs-site"):
    """将文件路径转换为 URL"""
    rel_path = file_path.relative_to(docs_site)
    # 移除 .md 扩展名，添加 .html
    url_path = str(rel_path).replace(".md", ".html")
    return f"{base_url}/{url_path}"

def search_docs(keywords, port=3000):
    """搜索文档"""
    docs_site = get_docs_site_dir()
    base_url = f"http://localhost:{port}/docs-site"

    results = []

    # 搜索所有 .md 文件
    for md_file in docs_site.rglob("*.md"):
        # 跳过 node_modules 和 .vitepress
        if "node_modules" in str(md_file) or ".vitepress" in str(md_file):
            continue

        match_result = search_in_file(md_file, keywords)
        if match_result:
            results.append({
                "file": str(md_file.relative_to(docs_site)),
                "title": match_result["title"],
                "score": match_result["score"],
                "path_matches": match_result["path_matches"],
                "content_matches": match_result["content_matches"],
                "url": get_url_from_path(md_file, docs_site, base_url)
            })

    # 按综合评分排序（路径匹配优先）
    results.sort(key=lambda x: (x["score"], x["path_matches"]), reverse=True)

    return results[:10]  # 返回前10个结果

def main():
    if len(sys.argv) < 2:
        print("Usage: search_docs.py <keyword1> [keyword2] ...")
        sys.exit(1)

    keywords = sys.argv[1:]
    port = 3000

    # 检查是否有 --port 参数
    if "--port" in keywords:
        port_idx = keywords.index("--port")
        if port_idx + 1 < len(keywords):
            port = int(keywords[port_idx + 1])
            keywords = keywords[:port_idx] + keywords[port_idx + 2:]

    results = search_docs(keywords, port)

    if results:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("[]")

if __name__ == "__main__":
    main()
