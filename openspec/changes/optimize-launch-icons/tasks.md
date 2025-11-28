## 1. Icon loader architecture
- [x] 1.1 Measure current synchronous icon load path and document hotspots (path resolution, pixmap creation, per-item scheduling).
- [x] 1.2 Design lightweight worker + cache helper (threaded or queued) that can return stale/fallback pixmaps instantly and refresh asynchronously.

## 2. Implementation
- [x] 2.1 Add icon loader module (shared helper or class) that accepts load requests, deduplicates by target path, and emits results back to the UI thread.
- [x] 2.2 Update `LaunchItem` to request icons via the loader, render placeholders immediately, and repaint when the pixmap arrives; ensure preload hooks (`preload_icons`) and batch refreshes reuse the same pipeline.
- [x] 2.3 Ensure category/all-tab rebuilds wait on nothing: hooking into loader callbacks should not block `update_all_category`.

## 3. Telemetry & configuration
- [x] 3.1 Add logging counters/timing for icon loads; provide a config flag to disable icons entirely for troubleshooting.
- [x] 3.2 Document cache size/eviction strategy and make it configurable if needed.

## 4. Testing & validation
- [x] 4.1 Create targeted tests (unit or integration) verifying the loader caches results, coalesces duplicate requests, and does not block the GUI thread.
- [x] 4.2 Manual QA: enable icons, load tabs with >50 entries, confirm scroll/refresh stays responsive while icons appear progressively.
