# Change: Optimize launch item icon rendering

## Why
Re-enabling icons in `gui/launch_item.py` makes every category tab crawl because each card resolves executable paths and loads pixmaps synchronously on the UI thread. We need to restore the icon experience without blocking rendering when hundreds of items refresh.

## What Changes
- Introduce an icon-loading pipeline that batches lookup/caching off the UI thread with fast fallbacks.
- Avoid repeated disk lookups by persisting a small icon cache (in-memory and optional on-disk) and only recomputing when the target file changes.
- Gate icon painting so cards render immediately with placeholders, then update once the pixmap is available.
- Add telemetry/logging around icon load timing so regressions are visible.

## Impact
- Affected specs: launch-item-display (performance behaviors).
- Affected code: `gui/launch_item.py`, `gui/category_tab.py`, `gui/main_window.py` (batch refresh pipeline), maybe new helper under `utils/` for icon cache, plus tests for the loader scheduling.
