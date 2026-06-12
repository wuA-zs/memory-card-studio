#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""校验 Memory Card Studio 项目的文件结构、卡片库和复习状态。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


# 小功能：定义卡片项目必须存在的核心文件，便于入口校验统一复用。
REQUIRED_FILES = [
    "index.html",
    "styles.css",
    "app.js",
    "data/review-state.json",
]


# 小功能：定义允许出现的卡片类型，防止拼写错误进入卡片库。
VALID_CARD_TYPES = {"qa", "cloze", "choice"}


# 小功能：定义允许出现的复习状态，防止调度字段被写成不可识别的值。
VALID_REVIEW_STATUSES = {"new", "learning", "review", "forgotten"}


class ValidationError(Exception):
    """小功能：承载可读的校验失败信息。"""


# 小功能：用兼容 BOM 的 UTF-8 读取 JSON 文件，并把解析错误转换成带路径的提示。
def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8-sig") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path} 不是合法 JSON：{exc}") from exc


# 小功能：确认一个值是非空字符串，用于必填文本字段校验。
def require_text(value: Any, field: str, location: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{location} 的 {field} 必须是非空字符串")


# 小功能：确认一个值是列表，用于 tags、cards、sourceFiles 等数组字段校验。
def require_list(value: Any, field: str, location: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{location} 的 {field} 必须是数组")
    return value


# 小功能：校验单张选择题的选项和答案下标，避免前端渲染时出现越界答案。
def validate_choice(card: dict[str, Any], location: str) -> None:
    choice = card.get("choice")
    if not isinstance(choice, dict):
        raise ValidationError(f"{location} 是 choice 类型，必须包含 choice 对象")

    question = choice.get("question")
    if question is not None:
        require_text(question, "choice.question", location)

    options = require_list(choice.get("options"), "choice.options", location)
    if len(options) not in (3, 4):
        raise ValidationError(f"{location} 的 choice.options 必须有 3 或 4 个选项")
    for index, option in enumerate(options):
        require_text(option, f"choice.options[{index}]", location)

    answer_index = choice.get("answerIndex")
    if not isinstance(answer_index, int):
        raise ValidationError(f"{location} 的 choice.answerIndex 必须是整数")
    if answer_index < 0 or answer_index >= len(options):
        raise ValidationError(f"{location} 的 choice.answerIndex 超出选项范围")

    require_text(choice.get("explanation"), "choice.explanation", location)


# 小功能：校验单张填空题的 cloze 结构，确保答案数组和文本都可用。
def validate_cloze(card: dict[str, Any], location: str) -> None:
    cloze = card.get("cloze")
    if cloze is None:
        return
    if not isinstance(cloze, dict):
        raise ValidationError(f"{location} 的 cloze 必须是对象")

    require_text(cloze.get("text"), "cloze.text", location)
    answers = require_list(cloze.get("answers"), "cloze.answers", location)
    if not answers:
        raise ValidationError(f"{location} 的 cloze.answers 不能为空")
    for index, answer in enumerate(answers):
        require_text(answer, f"cloze.answers[{index}]", location)


# 小功能：校验单张卡片的公共字段和题型专属字段。
def validate_card(card: Any, library_id: str, index: int) -> str:
    location = f"卡片库 {library_id} 第 {index + 1} 张卡"
    if not isinstance(card, dict):
        raise ValidationError(f"{location} 必须是对象")

    for field in ("id", "type", "front", "back", "source", "createdAt"):
        require_text(card.get(field), field, location)

    tags = require_list(card.get("tags"), "tags", location)
    for tag_index, tag in enumerate(tags):
        require_text(tag, f"tags[{tag_index}]", location)

    card_type = card["type"]
    if card_type not in VALID_CARD_TYPES:
        raise ValidationError(f"{location} 的 type 必须是 qa、cloze 或 choice")
    if card_type == "choice":
        validate_choice(card, location)
    if card_type == "cloze":
        validate_cloze(card, location)

    return card["id"]


# 小功能：校验一个卡片库文件，并返回其中所有卡片 ID。
def validate_library(path: Path) -> list[str]:
    library = load_json(path)
    location = f"卡片库文件 {path}"
    if not isinstance(library, dict):
        raise ValidationError(f"{location} 必须是对象")

    for field in ("id", "name", "createdAt", "updatedAt"):
        require_text(library.get(field), field, location)
    require_list(library.get("sourceFiles"), "sourceFiles", location)
    cards = require_list(library.get("cards"), "cards", location)

    card_ids = []
    for index, card in enumerate(cards):
        card_ids.append(validate_card(card, library["id"], index))
    return card_ids


# 小功能：校验 review-state.json 的基础结构和单卡复习字段。
def validate_review_state(path: Path) -> dict[str, Any]:
    review_state = load_json(path)
    if not isinstance(review_state, dict):
        raise ValidationError(f"{path} 必须是对象")
    if review_state.get("version") != 1:
        raise ValidationError(f"{path} 的 version 必须是 1")
    cards = review_state.get("cards")
    if not isinstance(cards, dict):
        raise ValidationError(f"{path} 的 cards 必须是对象")

    for card_id, review in cards.items():
        location = f"复习状态 {card_id}"
        if not isinstance(review, dict):
            raise ValidationError(f"{location} 必须是对象")
        if not isinstance(review.get("ease"), (int, float)):
            raise ValidationError(f"{location} 的 ease 必须是数字")
        if not isinstance(review.get("intervalDays"), int) or review["intervalDays"] < 1:
            raise ValidationError(f"{location} 的 intervalDays 必须是大于 0 的整数")
        if not isinstance(review.get("reviewCount"), int) or review["reviewCount"] < 0:
            raise ValidationError(f"{location} 的 reviewCount 必须是非负整数")
        if review.get("lastReviewedAt") is not None and not isinstance(review.get("lastReviewedAt"), str):
            raise ValidationError(f"{location} 的 lastReviewedAt 必须是字符串或 null")
        require_text(review.get("nextReviewAt"), "nextReviewAt", location)
        if review.get("status") not in VALID_REVIEW_STATUSES:
            raise ValidationError(f"{location} 的 status 必须是 new、learning、review 或 forgotten")
    return review_state


# 小功能：校验目标项目目录是否具备静态前端所需的核心文件。
def validate_required_files(project_dir: Path) -> None:
    for relative_path in REQUIRED_FILES:
        path = project_dir / relative_path
        if not path.is_file():
            raise ValidationError(f"缺少必要文件：{path}")
    libraries_dir = project_dir / "data" / "libraries"
    if not libraries_dir.is_dir():
        raise ValidationError(f"缺少卡片库目录：{libraries_dir}")
    if not list(libraries_dir.glob("*.json")):
        raise ValidationError(f"卡片库目录中没有 JSON 文件：{libraries_dir}")


# 小功能：校验所有卡片 ID 是否全局唯一，并可选检查复习状态覆盖完整性。
def validate_card_ids(card_ids: list[str], review_state: dict[str, Any], require_review_state: bool) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for card_id in card_ids:
        if card_id in seen:
            duplicates.add(card_id)
        seen.add(card_id)
    if duplicates:
        raise ValidationError("存在重复 card id：" + ", ".join(sorted(duplicates)))

    review_cards = set(review_state.get("cards", {}).keys())
    missing = seen - review_cards
    if require_review_state and missing:
        raise ValidationError("review-state.json 缺少卡片状态：" + ", ".join(sorted(missing)))


# 小功能：执行完整项目校验，供命令行入口和其他脚本复用。
def validate_project(project_dir: Path, require_review_state: bool = True) -> dict[str, int]:
    project_dir = project_dir.resolve()
    validate_required_files(project_dir)

    card_ids: list[str] = []
    libraries_dir = project_dir / "data" / "libraries"
    for library_path in sorted(libraries_dir.glob("*.json")):
        card_ids.extend(validate_library(library_path))

    review_state = validate_review_state(project_dir / "data" / "review-state.json")
    validate_card_ids(card_ids, review_state, require_review_state)

    return {
        "libraries": len(list(libraries_dir.glob("*.json"))),
        "cards": len(card_ids),
        "reviewStates": len(review_state.get("cards", {})),
    }


# 小功能：解析命令行参数，支持在生成流程中放宽 review-state 覆盖检查。
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验 Memory Card Studio 项目")
    parser.add_argument("project_dir", help="目标卡片项目目录")
    parser.add_argument(
        "--allow-missing-review-state",
        action="store_true",
        help="允许部分卡片没有 review-state 条目",
    )
    return parser.parse_args()


# 小功能：命令行入口，输出简洁结果并用退出码表达校验是否通过。
def main() -> int:
    args = parse_args()
    try:
        result = validate_project(
            Path(args.project_dir),
            require_review_state=not args.allow_missing_review_state,
        )
    except ValidationError as exc:
        print(f"校验失败：{exc}", file=sys.stderr)
        return 1

    print(
        "校验通过："
        f"{result['libraries']} 个卡片库，"
        f"{result['cards']} 张卡片，"
        f"{result['reviewStates']} 条复习状态"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
