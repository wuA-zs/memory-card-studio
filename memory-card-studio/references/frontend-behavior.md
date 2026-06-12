# Frontend Behavior Reference

Use this reference before editing the static frontend template in `assets/static-card-project/`.

## Runtime Model

- The frontend is zero-install and must run from `file://` when `data/app-data.js` exists.
- `data/app-data.js` is generated from JSON source files and is not a source of truth.
- Browser review clicks may update in-memory state and `localStorage` for immediate interaction, but they do not write JSON files.
- Persistent review changes require Codex to update `data/review-state.json` and run `scripts/refresh_app_data.py`.

## Forgetting-Curve Priority

The frontend sorts due cards by `forgettingCurvePriority()` before grouping.

The score combines:

- Overdue factor: cards past `nextReviewAt` get higher priority.
- Interval factor: shorter intervals mean weaker memory and higher priority.
- Review count factor: fewer prior reviews means higher priority.
- Status bonus: `forgotten` cards receive extra priority.
- New cards without review state receive the highest base score.

Preserve `forgettingCurvePriority()` as the sorting key for `state.allDueCards`.

## Group Review

- `GROUP_SIZE` is a top-level constant in `app.js`; default is 5.
- Due cards are sorted first, then split sequentially into groups.
- `loadGroup()` resets the current group, answer visibility, selected choice, and group results.
- `handleGrade()` records one card result, advances within the group, and opens the completion overlay after the last card.
- The group progress bar shows current group number and per-card dots:
  - gray = pending
  - orange = current
  - green = done
- The completion overlay shows a random message from `CHEERS`, remembered/fuzzy/forgotten counts, and a button to continue or finish.
- After the last group, the card area shows final completion text.

## Hidden Element Safety

Elements that combine the `hidden` attribute with CSS display rules must stay hidden reliably. Keep this CSS rule:

```css
[hidden] {
  display: none !important;
}
```

This is required because `.celebration-overlay` uses `display: flex`, which can otherwise override `hidden`.

## Editing Checks

After editing frontend assets:

1. Run `node --check app.js`.
2. Run `node --check data/app-data.js`.
3. Run `scripts/validate_project.py <target-folder>`.
   - On this Windows environment, prefer `& 'd:/code/uv/uv3/Scripts/python.exe' scripts/validate_project.py <target-folder>`.
4. Open the page in a browser or local server when possible and check:
   - initial card renders
   - answer reveal works
   - grading advances progress dots
   - final group completion overlay appears
