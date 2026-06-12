#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""根据单张卡片的复习反馈，确定性更新 review-state.json 并刷新浏览器快照。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from refresh_app_data import build_snapshot, write_snapshot
from validate_project import ValidationError, load_json, validate_project


# 小功能：定义固定的复习间隔阶梯，避免每次由模型临时推断下一次复习时间。
INTERVAL_STEPS = [1, 2, 4, 7, 15, 30, 60]


# 小功能：统一复习反馈的英文值和中文别名，便于聊天复习和命令行调用使用同一套规则。
FEEDBACK_ALIASES = {
    "remembered": "remembered",
    "remember": "remembered",
    "记得": "remembered",
    "fuzzy": "fuzzy",
    "模糊": "fuzzy",
    "forgotten": "forgotten",
    "forgot": "forgotten",
    "忘记": "forgotten",
}


# 小功能：把用户传入的复习反馈归一化为脚本内部使用的固定枚举值。
def normalize_feedback(raw_feedback: str) -> str:
    feedback = FEEDBACK_ALIASES.get(raw_feedback.strip().lower())
    if feedback is None:
        valid_values = ", ".join(sorted(FEEDBACK_ALIASES))
        raise ValidationError(f"未知复习反馈：{raw_feedback}。可用值：{valid_values}")
    return feedback


# 小功能：生成带本地时区的当前时间，确保写入 JSON 的时间格式稳定且可排序。
def current_time() -> datetime:
    return datetime.now().astimezone()


# 小功能：把时间对象转换为秒级 ISO 字符串，避免微秒导致快照频繁产生无意义变化。
def format_time(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat()


# 小功能：读取项目中所有卡片 ID，用于在写入复习状态前确认目标卡片真实存在。
def load_card_ids(project_dir: Path) -> set[str]:
    card_ids: set[str] = set()
    libraries_dir = project_dir / "data" / "libraries"
    for library_path in sorted(libraries_dir.glob("*.json")):
        library = load_json(library_path)
        for card in library.get("cards", []):
            card_id = card.get("id")
            if isinstance(card_id, str):
                card_ids.add(card_id)
    return card_ids


# 小功能：查找当前间隔在固定阶梯中的位置；未知间隔按不超过它的最大阶梯处理，增强旧数据兼容性。
def find_interval_index(interval_days: int) -> int:
    index = 0
    for step_index, step in enumerate(INTERVAL_STEPS):
        if interval_days >= step:
            index = step_index
    return index


# 小功能：根据反馈计算下一次复习间隔和状态，集中封装调度规则，避免散落手写 JSON。
def schedule_next_review(review: dict[str, Any], feedback: str, reviewed_at: datetime) -> dict[str, Any]:
    previous_interval = review.get("intervalDays", 1)
    if not isinstance(previous_interval, int) or previous_interval < 1:
        previous_interval = 1

    interval_index = find_interval_index(previous_interval)
    if feedback == "remembered":
        interval_days = INTERVAL_STEPS[min(interval_index + 1, len(INTERVAL_STEPS) - 1)]
        status = "review"
        next_review_at = reviewed_at + timedelta(days=interval_days)
    elif feedback == "fuzzy":
        interval_days = INTERVAL_STEPS[max(interval_index - 1, 0)]
        status = "learning"
        next_review_at = reviewed_at + timedelta(days=interval_days)
    else:
        interval_days = 1
        status = "forgotten"
        next_review_at = reviewed_at

    review_count = review.get("reviewCount", 0)
    if not isinstance(review_count, int) or review_count < 0:
        review_count = 0

    return {
        "ease": review.get("ease", 2.5),
        "intervalDays": interval_days,
        "reviewCount": review_count + 1,
        "lastReviewedAt": format_time(reviewed_at),
        "nextReviewAt": format_time(next_review_at),
        "status": status,
    }


# 小功能：确保 review-state.json 具备基础结构，旧项目缺字段时给出清晰错误。
def require_review_state_shape(review_state: Any, path: Path) -> dict[str, Any]:
    if not isinstance(review_state, dict):
        raise ValidationError(f"{path} 必须是 JSON 对象")
    if review_state.get("version") != 1:
        raise ValidationError(f"{path} 的 version 必须是 1")
    cards = review_state.get("cards")
    if not isinstance(cards, dict):
        raise ValidationError(f"{path} 的 cards 必须是 JSON 对象")
    return review_state


# 小功能：把单张卡片的复习结果写回 review-state.json，并返回更新后的单卡状态。
def update_review_state(project_dir: Path, card_id: str, feedback: str, reviewed_at: datetime) -> dict[str, Any]:
    project_dir = project_dir.resolve()
    validate_project(project_dir, require_review_state=False)

    card_ids = load_card_ids(project_dir)
    if card_id not in card_ids:
        raise ValidationError(f"卡片不存在：{card_id}")

    review_state_path = project_dir / "data" / "review-state.json"
    review_state = require_review_state_shape(load_json(review_state_path), review_state_path)
    cards = review_state["cards"]
    previous_review = cards.get(card_id, {})
    if not isinstance(previous_review, dict):
        previous_review = {}

    updated_review = schedule_next_review(previous_review, feedback, reviewed_at)
    cards[card_id] = updated_review
    review_state_path.write_text(
        json.dumps(review_state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    validate_project(project_dir)
    write_snapshot(project_dir, build_snapshot(project_dir))
    validate_project(project_dir)
    return updated_review


# 小功能：解析可选的 reviewed-at 时间；未传入时使用当前本地时间。
def parse_reviewed_at(raw_value: str | None) -> datetime:
    if raw_value is None:
        return current_time()
    normalized = raw_value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValidationError(f"--reviewed-at 不是合法 ISO 时间：{raw_value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc).astimezone()
    return parsed.astimezone()


# 小功能：解析命令行参数，让 Codex 可以用确定性命令记录每一次复习反馈。
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="更新 Memory Card Studio 的单卡复习状态")
    parser.add_argument("project_dir", help="目标卡片项目目录")
    parser.add_argument("card_id", help="要更新复习状态的卡片 ID")
    parser.add_argument("feedback", help="复习反馈：remembered/fuzzy/forgotten 或 记得/模糊/忘记")
    parser.add_argument(
        "--reviewed-at",
        help="可选 ISO 时间；不传则使用当前本地时间",
    )
    return parser.parse_args()


# 小功能：命令行入口，负责串联参数解析、复习状态更新、快照刷新和结果输出。
def main() -> int:
    args = parse_args()
    try:
        feedback = normalize_feedback(args.feedback)
        reviewed_at = parse_reviewed_at(args.reviewed_at)
        updated_review = update_review_state(
            Path(args.project_dir),
            args.card_id,
            feedback,
            reviewed_at,
        )
    except ValidationError as exc:
        print(f"更新失败：{exc}", file=sys.stderr)
        return 1

    print(
        "更新成功："
        f"{args.card_id} -> {feedback}，"
        f"intervalDays={updated_review['intervalDays']}，"
        f"nextReviewAt={updated_review['nextReviewAt']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
