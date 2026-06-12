#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从 JSON 源文件确定性生成浏览器可直接读取的 data/app-data.js。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_project import ValidationError, load_json, validate_project


# 小功能：读取所有卡片库 JSON，并按文件名排序保证输出顺序稳定。
def load_libraries(project_dir: Path) -> list[dict]:
    libraries_dir = project_dir / "data" / "libraries"
    return [load_json(path) for path in sorted(libraries_dir.glob("*.json"))]


# 小功能：把卡片库和复习状态序列化成固定格式的浏览器快照脚本。
def build_snapshot(project_dir: Path) -> str:
    libraries = load_libraries(project_dir)
    review_state = load_json(project_dir / "data" / "review-state.json")
    payload = {
        "libraries": libraries,
        "reviewState": review_state,
    }
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    return f"window.MEMORY_CARD_STUDIO_DATA = {json_text};\n"


# 小功能：写入 app-data.js，并确保目标目录存在。
def write_snapshot(project_dir: Path, snapshot: str) -> Path:
    output_path = project_dir / "data" / "app-data.js"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(snapshot, encoding="utf-8", newline="\n")
    return output_path


# 小功能：解析命令行参数，支持生成后再次校验。
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="刷新 Memory Card Studio 的 data/app-data.js")
    parser.add_argument("project_dir", help="目标卡片项目目录")
    parser.add_argument(
        "--allow-missing-review-state",
        action="store_true",
        help="允许部分卡片没有 review-state 条目",
    )
    return parser.parse_args()


# 小功能：命令行入口，先校验 JSON 源文件，再生成浏览器快照。
def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).resolve()
    try:
        validate_project(
            project_dir,
            require_review_state=not args.allow_missing_review_state,
        )
        output_path = write_snapshot(project_dir, build_snapshot(project_dir))
    except ValidationError as exc:
        print(f"刷新失败：{exc}", file=sys.stderr)
        return 1

    print(f"已刷新：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
