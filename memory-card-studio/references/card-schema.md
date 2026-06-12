# Memory Card Schema

Use this reference before creating or updating card libraries or review state files.

## Project Layout

```text
target-folder/
  index.html
  styles.css
  app.js
  data/
    app-data.js
    libraries/
      default.json
      <library-name>.json
    review-state.json
```

## Library File

Each file in `data/libraries/*.json` is one card library.

```json
{
  "id": "library-example",
  "name": "示例卡片库",
  "sourceFiles": ["D:/docs/example.md"],
  "createdAt": "2026-06-11T00:00:00+08:00",
  "updatedAt": "2026-06-11T00:00:00+08:00",
  "cards": [
    {
      "id": "card-example-qa",
      "type": "qa",
      "front": "间隔复习主要解决什么问题？",
      "back": "它通过在遗忘前重新激活记忆，降低重复学习的成本。",
      "source": "来源：example.md，记忆策略小节",
      "tags": ["记忆", "复习"],
      "createdAt": "2026-06-11T00:00:00+08:00"
    }
  ]
}
```

Required library fields:

- `id`: stable kebab-case or slug-like library id.
- `name`: human-readable library name.
- `sourceFiles`: absolute or user-provided source file paths.
- `createdAt`: ISO-like timestamp.
- `updatedAt`: ISO-like timestamp.
- `cards`: array of card objects.

Required common card fields:

- `id`: stable unique id across all libraries when possible.
- `type`: `qa`, `cloze`, or `choice`.
- `front`: the visible prompt.
- `back`: the answer, explanation, or complete text.
- `source`: short source note or excerpt.
- `tags`: short topic labels.
- `createdAt`: ISO-like timestamp.

## QA Card

Use `qa` for definitions, reasons, steps, principles, tradeoffs, examples, and constraints.

```json
{
  "id": "card-memory-qa-001",
  "type": "qa",
  "front": "为什么记忆卡片要保持原子化？",
  "back": "原子化卡片只测试一个知识点，便于快速判断是否掌握，也能降低复习时的认知负担。",
  "source": "来源：学习方法说明，卡片设计原则",
  "tags": ["卡片设计", "原子化"],
  "createdAt": "2026-06-11T00:00:00+08:00"
}
```

## Cloze Card

Use `cloze` for key terms, short facts, named conclusions, important numbers, formulas, and compact definitions.

```json
{
  "id": "card-memory-cloze-001",
  "type": "cloze",
  "front": "艾宾浩斯遗忘曲线描述的是 {{c1::记忆保持量}} 随时间下降的规律。",
  "back": "艾宾浩斯遗忘曲线描述的是记忆保持量随时间下降的规律。",
  "cloze": {
    "text": "艾宾浩斯遗忘曲线描述的是 {{c1::记忆保持量}} 随时间下降的规律。",
    "answers": ["记忆保持量"]
  },
  "source": "来源：记忆理论小节",
  "tags": ["艾宾浩斯", "填空"],
  "createdAt": "2026-06-11T00:00:00+08:00"
}
```

## Choice Card

Use `choice` for confusable concepts, classifications, best practices, and decision points.

```json
{
  "id": "card-memory-choice-001",
  "type": "choice",
  "front": "下面哪种方式更适合长期记忆？",
  "back": "正确答案：间隔复习。它能在遗忘前重新激活记忆。",
  "choice": {
    "question": "下面哪种方式更适合长期记忆？",
    "options": ["一次性通读", "间隔复习", "只看摘要", "跳过复盘"],
    "answerIndex": 1,
    "explanation": "间隔复习能在遗忘前重新激活记忆，比一次性通读更适合长期保持。"
  },
  "source": "来源：记忆策略小节",
  "tags": ["选择题", "复习策略"],
  "createdAt": "2026-06-11T00:00:00+08:00"
}
```

Choice rules:

- Provide 3 or 4 options.
- `answerIndex` is zero-based.
- Distractors must be plausible but clearly wrong from the source material.
- Do not create trick questions.

## Review State

`data/review-state.json` tracks scheduling for cards.

```json
{
  "version": 1,
  "cards": {
    "card-memory-qa-001": {
      "ease": 2.5,
      "intervalDays": 1,
      "reviewCount": 0,
      "lastReviewedAt": null,
      "nextReviewAt": "2026-06-11T00:00:00+08:00",
      "status": "new"
    }
  }
}
```

Required state fields:

- `ease`: keep `2.5` by default for future compatibility.
- `intervalDays`: current review interval.
- `reviewCount`: number of completed reviews.
- `lastReviewedAt`: timestamp or `null`.
- `nextReviewAt`: timestamp for due selection.
- `status`: `new`, `learning`, `review`, or `forgotten`.

## Scheduling

- New cards: `intervalDays = 1`, `reviewCount = 0`, `status = "new"`, and `nextReviewAt` is today.
- `记得`: move forward through `1, 2, 4, 7, 15, 30, 60` days.
- `模糊`: move back one interval level, minimum 1 day.
- `忘记`: schedule again today, set `intervalDays = 1`, set `status = "forgotten"`.
- Always update `lastReviewedAt` and increment `reviewCount` when the user gives review feedback.

## Persistent Review Update Command

Prefer the deterministic script instead of manually editing `review-state.json` during interactive review:

```powershell
& 'd:/code/uv/uv3/Scripts/python.exe' scripts/update_review_state.py <target-folder> <card-id> remembered
& 'd:/code/uv/uv3/Scripts/python.exe' scripts/update_review_state.py <target-folder> <card-id> fuzzy
& 'd:/code/uv/uv3/Scripts/python.exe' scripts/update_review_state.py <target-folder> <card-id> forgotten
```

The script must run immediately after each card feedback. It updates `data/review-state.json`, regenerates `data/app-data.js`, and validates the project. Do not wait until the end of a review session to reconstruct feedback from chat history.

Use the feedback rules mechanically:

```json
{
  "before": {
    "ease": 2.5,
    "intervalDays": 2,
    "reviewCount": 3,
    "lastReviewedAt": "2026-06-10T09:00:00+08:00",
    "nextReviewAt": "2026-06-12T00:00:00+08:00",
    "status": "review"
  },
  "afterRemembered": {
    "ease": 2.5,
    "intervalDays": 4,
    "reviewCount": 4,
    "lastReviewedAt": "2026-06-12T10:30:00+08:00",
    "nextReviewAt": "2026-06-16T10:30:00+08:00",
    "status": "review"
  },
  "afterFuzzy": {
    "ease": 2.5,
    "intervalDays": 1,
    "reviewCount": 4,
    "lastReviewedAt": "2026-06-12T10:30:00+08:00",
    "nextReviewAt": "2026-06-13T10:30:00+08:00",
    "status": "learning"
  },
  "afterForgotten": {
    "ease": 2.5,
    "intervalDays": 1,
    "reviewCount": 4,
    "lastReviewedAt": "2026-06-12T10:30:00+08:00",
    "nextReviewAt": "2026-06-12T10:30:00+08:00",
    "status": "forgotten"
  }
}
```

Status rules:

- Use `review` when the user marks `记得`.
- Use `learning` when the user marks `模糊`.
- Use `forgotten` when the user marks `忘记`.
- Keep `ease` unchanged unless a future version explicitly defines an ease algorithm.

## Browser Data Snapshot

Browsers commonly block `fetch("data/*.json")` when the page is opened directly from `file://`. Keep JSON files for Codex, but also generate `data/app-data.js` for the frontend.

```javascript
window.MEMORY_CARD_STUDIO_DATA = {
  "libraries": [
    {
      "id": "library-example",
      "name": "示例卡片库",
      "sourceFiles": ["D:/docs/example.md"],
      "createdAt": "2026-06-11T00:00:00+08:00",
      "updatedAt": "2026-06-11T00:00:00+08:00",
      "cards": []
    }
  ],
  "reviewState": {
    "version": 1,
    "cards": {}
  }
};
```

Snapshot rules:

- Include every library from `data/libraries/*.json`.
- Include the full contents of `data/review-state.json` as `reviewState`.
- Regenerate `data/app-data.js` after adding cards or updating review feedback.
- Validate the snapshot with `node --check data/app-data.js` when Node is available.
- Do not treat `app-data.js` as a second source of truth; regenerate it from JSON.

## Generation Quality Rules

- Keep each card focused on one idea.
- Generate a mix of `qa`, `cloze`, and `choice` unless the source does not support one type.
- Preserve source grounding; do not invent facts outside the user-provided file.
- Prefer clear Chinese prompts when the source is Chinese.
- Use concise answers that can be reviewed quickly.
- Avoid duplicate cards with the same test point.
- If writing or modifying functional code for a generated project, add complete Chinese comments for each small functional block.
