---
name: memory-card-studio
description: Use when the user asks to create or update persistent local memory-card projects, generate flashcards or spaced-repetition card libraries from files, URLs, web pages, or other readable sources, create a zero-install card-review frontend, start today's due-card review, or study an existing local card library in conversation.
license: MIT
---

# Memory Card Studio

Create local zero-install memory-card projects, generate grounded card libraries from files, and run lightweight review sessions in chat. The frontend is copied from `assets/static-card-project/`; Codex parses source files and updates JSON data.

## Required References And Tools

- Read `references/card-schema.md` before creating or updating card JSON.
- Read `references/frontend-behavior.md` before editing frontend assets or explaining browser review behavior.
- Use `scripts/refresh_app_data.py <target-folder>` after every card library or review-state change.
- Use `scripts/update_review_state.py <target-folder> <card-id> <feedback>` for every interactive review feedback before moving to the next card.
- Use `scripts/validate_project.py <target-folder>` before reporting initialization, generation, repair, or review-state updates as complete.
- Store all generated files as UTF-8.

## Core Rules

- Keep the frontend zero-install: only static HTML, CSS, JavaScript, JSON files, and `data/app-data.js`.
- Do not introduce Node, npm, React, Vite, databases, local servers, or cloud services into generated card projects.
- Do not overwrite existing card libraries or `data/review-state.json` unless the user explicitly asks to rebuild them.
- If target project files already exist, copy only missing frontend files and append or update the requested card library.
- Preserve all files under `data/libraries/` and `data/review-state.json` when repairing old projects.
- Browser feedback stored in `localStorage` is only a temporary in-page interaction record; it does not write back to JSON. Persistent review state must be updated by Codex in `data/review-state.json`, then refreshed into `data/app-data.js`.
- Do not edit `data/app-data.js` as source data. Regenerate it from JSON with `scripts/refresh_app_data.py <target-folder>`.
- Do not rely on memory or end-of-session summaries to persist review feedback. After each `忘记`, `模糊`, or `记得` answer, immediately run `scripts/update_review_state.py` for that card.
- Do not treat ordinary learning questions as card-project work unless the user asks for persistent cards, a local card library, spaced repetition, or a review session.
- End every initialization, generation, repair, or review response with a clickable absolute link to the target `index.html`.

## Workflow Decision

Choose one workflow:

1. **Initialize or repair project**: user asks to create a memory-card frontend, local review app, card project, or gives a folder where cards should live.
2. **Generate cards from sources**: user asks to generate memory cards, flashcards, Q&A cards, cloze cards, choice cards, or review cards from files, URLs, web pages, pasted text, or other readable sources.
3. **Start today's review**: user asks to begin memory, review due cards, study cards, or start card memory for an existing local card project.

If generating cards for a folder that is not initialized, initialize first.

## Target Folder

- Use the folder explicitly named by the user.
- If the user gives only a source file, prefer that file's parent folder unless another card project folder is already established in the conversation.
- If no safe target folder can be inferred, ask one concise question for the folder path before writing files.
- Treat a folder as initialized when `index.html`, `app.js`, `styles.css`, and `data/libraries/` exist.

## Initialize Or Repair Project

1. Confirm or infer the target folder.
2. Create the target folder if needed.
3. Copy missing files from `assets/static-card-project/`.
4. If `index.html` or `app.js` is an older generated template that does not load `data/app-data.js`, replace those frontend runtime files with the current template.
5. Preserve existing user libraries and review state unless replacement was explicitly requested.
6. Run `scripts/refresh_app_data.py <target-folder>`.
7. Run `scripts/validate_project.py <target-folder>`.
8. Report created files, repaired frontend files, preserved data files, and the absolute `index.html` link.

## Generate Cards From Sources

1. Read `references/card-schema.md`.
2. Resolve and initialize the target project folder if needed.
3. Extract meaningful source content using local tools. Any file type, URL, web page, pasted text, or other source is acceptable when Codex can extract grounded text or structured data.
4. Generate atomic cards that test one idea each:
   - `qa` for concepts, reasons, steps, tradeoffs, principles, examples, and constraints.
   - `cloze` for key terms, short facts, numbers, formulas, named conclusions, and compact definitions.
   - `choice` for confusable concepts, classifications, best practices, and decision points.
5. Enforce quality and deduplication:
   - Do not create duplicate cards for the same test point.
   - Use the same source excerpt for at most 1-2 cards unless the excerpt contains clearly separate ideas.
   - Keep cloze blanks short; do not hide long clauses or entire sentences.
   - Choice distractors must be plausible neighboring concepts grounded in the source, not invented trivia.
   - Do not create trick questions.
6. Include a short source note or source excerpt for each card.
7. Write or append to `data/libraries/<library-name>.json`.
8. Add default review state entries for every new card in `data/review-state.json`.
9. Run `scripts/refresh_app_data.py <target-folder>`.
10. Run `scripts/validate_project.py <target-folder>`.
11. Report library name, card count, card type counts, validation result, and the absolute `index.html` link.

## Start Today's Review

1. Read `references/card-schema.md`.
2. Locate the target project folder from the user's path or conversation context. If it cannot be inferred, ask for the folder path.
3. Load all `data/libraries/*.json` files and `data/review-state.json`.
4. Select at most 10 cards in this priority order unless the user asks for more:
   - Cards with `nextReviewAt` at or before today.
   - New cards without review state.
   - Recently created cards if too few due cards exist.
5. Review interactively:
   - For `qa`, show the question first, wait for the user's answer, then reveal or grade.
   - For `cloze`, show the sentence with blanks first, then reveal the answers.
   - For `choice`, show options and ask the user to choose before revealing the explanation.
6. After each card, ask the user to mark `忘记`, `模糊`, or `记得`.
7. Immediately persist that feedback before showing the next card:
   - Run `scripts/update_review_state.py <target-folder> <card-id> remembered` for `记得`.
   - Run `scripts/update_review_state.py <target-folder> <card-id> fuzzy` for `模糊`.
   - Run `scripts/update_review_state.py <target-folder> <card-id> forgotten` for `忘记`.
8. Confirm the command succeeded. If it fails, stop the review and report the persistence error instead of continuing.
9. Run `scripts/validate_project.py <target-folder>` at the end of the review session.
10. End with progress, validation result, and the absolute frontend link.

## Frontend Assets

- The browser frontend loads `data/app-data.js` first because local JSON fetch commonly fails under `file://`.
- JSON files are the source of truth. `data/app-data.js` is a generated browser snapshot.
- The browser does not parse user documents and does not persist review feedback back to JSON.
- Preserve the frontend behavior invariants documented in `references/frontend-behavior.md` when editing `index.html`, `styles.css`, or `app.js`.
