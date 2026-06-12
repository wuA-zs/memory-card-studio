# Memory Card Studio

Memory Card Studio 是一个 Agent Skill，用来让 AI 助手从本地文件、网页链接或其他可读取资料中生成记忆卡片，并创建一个零安装的本地复习前端。

它适合这些场景：

- 把 Markdown、笔记、课程资料、网页链接、技术文档整理成问答卡、填空卡、选择题卡。
- 在本地生成可直接打开的复习页面，不需要 Node、npm、数据库或云服务。
- 用 JSON 保存卡片库和复习状态，方便备份、迁移和继续加工。
- 在聊天中进行今日复习，并把每张卡的 `记得 / 模糊 / 忘记` 反馈持久化到本地文件。

## 核心特点

- **多来源资料友好**：可以根据本地文件、网页链接等资料生成对应语言的卡片，适合笔记、课程资料和技术文档。
- **本地优先**：生成的卡片项目是静态 HTML、CSS、JavaScript 和 JSON 文件。
- **零安装前端**：用户可以直接打开 `index.html` 复习。
- **可验证**：内置脚本校验卡片库、复习状态和浏览器快照。
- **防丢进度**：复习反馈通过 `update_review_state.py` 立即写入 `review-state.json`。

## 目录结构

```text
memory-card-studio/
  README.md
  LICENSE
  memory-card-studio/
    SKILL.md
    agents/openai.yaml
    assets/static-card-project/
    references/card-schema.md
    references/frontend-behavior.md
    scripts/refresh_app_data.py
    scripts/update_review_state.py
    scripts/validate_project.py
```

## 安装

如果你使用 GitHub CLI 的 Agent Skills 预览功能：

```powershell
gh skill install wuA-zs/memory-card-studio
```

如果你使用 `skills` CLI：

```powershell
npx skills add wuA-zs/memory-card-studio --list
npx skills add wuA-zs/memory-card-studio --skill memory-card-studio
```

## 典型用法

安装后，可以这样对 AI 助手说：

```text
用 memory-card-studio 把 D:\notes\python.md 生成记忆卡片，并创建一个本地复习项目。
```

或者：

```text
用 memory-card-studio 把 https://example.com/article 生成记忆卡片，并创建一个本地复习项目。
```

或者：

```text
开始今天的记忆卡片复习。
```

## 数据模型

生成的卡片项目会包含：

- `data/libraries/*.json`：卡片库，是卡片内容的来源。
- `data/review-state.json`：复习状态，是间隔复习进度的来源。
- `data/app-data.js`：浏览器快照，由 JSON 生成，不是源数据。

浏览器里的 `localStorage` 只用于临时交互记录，不会自动写回 JSON。真正的复习状态必须由 AI 助手调用脚本写入：

```powershell
python scripts/update_review_state.py <target-folder> <card-id> remembered
python scripts/update_review_state.py <target-folder> <card-id> fuzzy
python scripts/update_review_state.py <target-folder> <card-id> forgotten
```

对应中文反馈：

- `remembered`：记得
- `fuzzy`：模糊
- `forgotten`：忘记

## 本地验证

从仓库根目录执行：

```powershell
cd memory-card-studio
python scripts/validate_project.py assets/static-card-project
python -m py_compile scripts/refresh_app_data.py scripts/update_review_state.py scripts/validate_project.py
```

如果你的系统用 `python3` 命令启动 Python，可以把上面的 `python` 替换成 `python3`。

## 设计边界

- 不引入 Node、npm、React、Vite、数据库、本地服务器或云服务到生成项目中。
- 不覆盖已有卡片库或 `review-state.json`，除非用户明确要求重建。
- 不把 `data/app-data.js` 当作源数据手改，它应该由 `refresh_app_data.py` 从 JSON 重新生成。
- 不把普通学习问答误判成卡片项目，除非用户明确要求生成持久卡片、卡片库或复习会话。

## License

MIT

---

## English

Memory Card Studio is an Agent Skill that helps an AI assistant generate memory cards from local files, web links, pasted text, or other readable sources, then create a zero-install local review frontend.

It is useful for:

- Turning Markdown files, notes, course materials, web pages, and technical documents into QA, cloze, and multiple-choice cards.
- Creating a review page that can be opened locally without Node, npm, a database, or a cloud service.
- Storing card libraries and spaced-repetition state as JSON for backup, migration, and further editing.
- Running daily review sessions in chat while persisting each card result to local files.

## Key Features

- **Multiple source types**: Generate cards from local files, URLs, web pages, pasted text, or any source the agent can read.
- **Local-first output**: Generated projects are static HTML, CSS, JavaScript, and JSON files.
- **Zero-install frontend**: Open `index.html` directly to review cards.
- **Verifiable data**: Built-in scripts validate card libraries, review state, and browser snapshots.
- **Persistent review progress**: `update_review_state.py` writes each `remembered / fuzzy / forgotten` result into `review-state.json`.

## Install

With GitHub CLI Agent Skills preview:

```powershell
gh skill install wuA-zs/memory-card-studio
```

With the `skills` CLI:

```powershell
npx skills add wuA-zs/memory-card-studio --list
npx skills add wuA-zs/memory-card-studio --skill memory-card-studio
```

## Example Prompts

```text
Use memory-card-studio to generate memory cards from D:\notes\python.md and create a local review project.
```

```text
Use memory-card-studio to generate memory cards from https://example.com/article and create a local review project.
```

```text
Start today's memory-card review.
```

## Data Model

Generated card projects include:

- `data/libraries/*.json`: card libraries and card content.
- `data/review-state.json`: spaced-repetition progress.
- `data/app-data.js`: a browser snapshot generated from JSON. It is not the source of truth.

Browser `localStorage` is only temporary interaction state. Persistent review progress must be written by the agent through:

```powershell
python scripts/update_review_state.py <target-folder> <card-id> remembered
python scripts/update_review_state.py <target-folder> <card-id> fuzzy
python scripts/update_review_state.py <target-folder> <card-id> forgotten
```

Feedback meanings:

- `remembered`: remembered
- `fuzzy`: partially remembered
- `forgotten`: forgotten

## Validation

From the repository root:

```powershell
cd memory-card-studio
python scripts/validate_project.py assets/static-card-project
python -m py_compile scripts/refresh_app_data.py scripts/update_review_state.py scripts/validate_project.py
```

Use `python3` instead of `python` if that is how Python is exposed on your system.

## Design Boundaries

- Do not introduce Node, npm, React, Vite, databases, local servers, or cloud services into generated projects.
- Do not overwrite existing card libraries or `review-state.json` unless the user explicitly asks to rebuild them.
- Do not edit `data/app-data.js` as source data; regenerate it from JSON with `refresh_app_data.py`.
- Do not treat ordinary study questions as card-project work unless the user explicitly asks for persistent cards, a card library, or a review session.
