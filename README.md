# Memory Card Studio

Memory Card Studio is an Agent Skill for creating local, zero-install memory-card projects. It helps an agent generate grounded flashcards from source files, maintain review-state JSON, and provide a static browser review app that can run directly from `file://`.

## What It Does

- Initializes or repairs a static memory-card review project.
- Generates `qa`, `cloze`, and `choice` card libraries from user-provided files.
- Keeps card data in JSON as the source of truth.
- Regenerates `data/app-data.js` so the browser app works without a local server.
- Updates spaced-repetition state after each review feedback with a deterministic script.

## Structure

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

## Validation

From this repository root:

```powershell
cd memory-card-studio
python scripts/validate_project.py assets/static-card-project
python -m py_compile scripts/refresh_app_data.py scripts/update_review_state.py scripts/validate_project.py
```

Use `python3` instead of `python` if that is how Python is exposed on your system.

## Install From GitHub

After publishing this repository, install it with any Agent Skills-compatible tool that supports GitHub sources. This repository stores the skill in the `memory-card-studio/` directory so publishing tools can match the directory name to the skill name.

## Notes

- The generated card projects stay zero-install: no Node, npm, React, Vite, database, server, or cloud dependency.
- Browser `localStorage` is only temporary interaction state. Persistent review state lives in `data/review-state.json`.
- Use `scripts/update_review_state.py` after each card feedback to avoid losing review progress.
