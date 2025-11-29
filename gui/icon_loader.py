#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import time
import uuid
from collections import deque, OrderedDict, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple

from PyQt5.QtCore import QObject, pyqtSignal, QSize, Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFileIconProvider
from PyQt5.QtCore import QFileInfo

from utils.logger import get_logger
from utils.platform_settings import is_windows, is_mac
from utils.path_utils import resource_path

RESOURCE_DIR = resource_path("resources")
APP_ICON_DIR = os.path.join(RESOURCE_DIR, "app-icons")
DEFAULT_ICON_PATH = os.path.join(RESOURCE_DIR, "icon.png")

_builtin_icons = {
    "edge": os.path.join(APP_ICON_DIR, "edge.png"),
    "msedge": os.path.join(APP_ICON_DIR, "edge.png"),
    "microsoftedge": os.path.join(APP_ICON_DIR, "edge.png"),
    "vscode": os.path.join(APP_ICON_DIR, "vscode.png"),
    "code": os.path.join(APP_ICON_DIR, "vscode.png"),
    "cursor": os.path.join(APP_ICON_DIR, "cursor.png"),
    "obsidian": os.path.join(APP_ICON_DIR, "obsidian.png"),
    "navicat": os.path.join(APP_ICON_DIR, "navicat.png"),
}

ICONS_PER_BATCH = 4


@dataclass
class IconRequest:
    key: str
    app_value: str
    size: QSize


class IconLoader(QObject):
    """Queue-based icon loader that throttles work per event loop iteration."""
    icon_ready = pyqtSignal(str, QPixmap)
    stats_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.logger = get_logger("icon_loader")
        self._queue: deque[IconRequest] = deque()
        self._queued_keys = set()
        self._pending: Dict[str, List[Tuple[str, QSize]]] = defaultdict(list)
        self._cache: OrderedDict[str, QPixmap] = OrderedDict()
        self._placeholder_cache: Dict[str, QPixmap] = {}
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._process_queue)
        self._cache_capacity = 128
        self._icons_enabled = True
        self._stats = {"requests": 0, "cache_hits": 0, "loads": 0}

    def set_enabled(self, enabled: bool):
        if self._icons_enabled == enabled:
            return
        self._icons_enabled = enabled
        if not enabled:
            self.clear_queue()
        self.logger.info(f"Icon loader enabled={enabled}")

    def set_cache_capacity(self, capacity: int):
        capacity = max(16, int(capacity))
        self._cache_capacity = capacity
        while len(self._cache) > self._cache_capacity:
            self._cache.popitem(last=False)
        self.logger.debug(f"Icon cache capacity set to {capacity}")

    def clear_queue(self):
        self._queue.clear()
        self._queued_keys.clear()
        self._pending.clear()
        self._timer.stop()

    def clear_cache(self):
        self._cache.clear()

    def request_icon(self, app_value: str, size: QSize) -> str:
        ticket = uuid.uuid4().hex
        if not self._icons_enabled:
            return ticket
        key = self._make_cache_key(app_value, size)
        cached = self._cache.get(key)
        if cached:
            self._stats["cache_hits"] += 1
            self._touch_cache(key)
            QTimer.singleShot(0, lambda k=ticket, pix=QPixmap(cached): self.icon_ready.emit(k, pix))
            return ticket
        self._stats["requests"] += 1
        self._pending[key].append((ticket, QSize(size)))
        if key not in self._queued_keys:
            self._queue.append(IconRequest(key, app_value, QSize(size)))
            self._queued_keys.add(key)
        self._schedule_processing()
        return ticket

    def get_placeholder_pixmap(self, size: QSize) -> QPixmap:
        key = f"{size.width()}x{size.height()}"
        cached = self._placeholder_cache.get(key)
        if cached:
            return QPixmap(cached)
        fallback = DEFAULT_ICON_PATH if os.path.exists(DEFAULT_ICON_PATH) else ""
        pixmap = QPixmap(fallback) if fallback else QPixmap(size)
        if pixmap.isNull():
            pixmap = QPixmap(size)
            pixmap.fill(Qt.lightGray)
        scaled = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._placeholder_cache[key] = QPixmap(scaled)
        return scaled

    def prime_icon(self, app_value: str, size: QSize):
        """Warm the cache without tracking a specific ticket."""
        if not self._icons_enabled:
            return
        key = self._make_cache_key(app_value, size)
        if key in self._cache or key in self._queued_keys:
            return
        self._pending.setdefault(key, [])
        self._queue.append(IconRequest(key, app_value, QSize(size)))
        self._queued_keys.add(key)
        self._schedule_processing()

    def _schedule_processing(self):
        if not self._timer.isActive():
            self._timer.start(0)

    def _process_queue(self):
        if not self._queue:
            return
        start = time.time()
        processed = 0
        provider = QFileIconProvider()
        while self._queue and processed < ICONS_PER_BATCH:
            request = self._queue.popleft()
            self._queued_keys.discard(request.key)
            pixmap = self._load_pixmap(provider, request.app_value, request.size)
            if pixmap is None:
                pixmap = self.get_placeholder_pixmap(request.size)
            self._store_cache(request.key, pixmap)
            pending = self._pending.pop(request.key, [])
            for ticket, _ in pending:
                self.icon_ready.emit(ticket, QPixmap(pixmap))
            processed += 1
            self._stats["loads"] += 1
        duration = (time.time() - start) * 1000.0
        self.logger.debug(f"Processed {processed} icon requests in {duration:.2f}ms (queue={len(self._queue)})")
        self.stats_updated.emit(self._stats.copy())
        if self._queue:
            self._timer.start(0)

    def _store_cache(self, key: str, pixmap: QPixmap):
        self._cache[key] = QPixmap(pixmap)
        self._touch_cache(key)
        while len(self._cache) > self._cache_capacity:
            self._cache.popitem(last=False)

    def _touch_cache(self, key: str):
        if key not in self._cache:
            return
        pix = self._cache.pop(key)
        self._cache[key] = pix

    def _make_cache_key(self, app_value: str, size: QSize) -> str:
        normalized = (app_value or "").strip().lower()
        return f"{normalized}::{size.width()}x{size.height()}"

    def _load_pixmap(self, provider: QFileIconProvider, app_value: str, size: QSize) -> QPixmap:
        target = self._resolve_icon_target(app_value)
        if target:
            file_info = QFileInfo(target)
            icon = provider.icon(file_info)
            if icon and not icon.isNull():
                pixmap = icon.pixmap(size)
                if not pixmap.isNull():
                    return pixmap
            direct_pixmap = QPixmap(target)
            if not direct_pixmap.isNull():
                return direct_pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if target.lower().endswith(".app") and os.path.isdir(target):
                executable_name = os.path.splitext(os.path.basename(target))[0]
                bundle_exec = os.path.join(target, "Contents", "MacOS", executable_name)
                if os.path.exists(bundle_exec):
                    icon = provider.icon(QFileInfo(bundle_exec))
                    pixmap = icon.pixmap(size)
                    if not pixmap.isNull():
                        return pixmap
        builtin = self._get_builtin_icon_path(app_value)
        if builtin and os.path.exists(builtin):
            pix = QPixmap(builtin)
            if not pix.isNull():
                return pix.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return None

    def _get_builtin_icon_path(self, app_value: str) -> str:
        normalized = self._normalize_app_name(app_value)
        if not normalized:
            return ""
        path = _builtin_icons.get(normalized)
        return path if path and os.path.exists(path) else ""

    def _normalize_app_name(self, app_value: str) -> str:
        if not app_value:
            return ""
        lowered = app_value.strip().lower()
        if not lowered:
            return ""
        base = os.path.basename(lowered)
        base = base or lowered
        root, _ = os.path.splitext(base)
        return root or base

    def _resolve_icon_target(self, app_value: str) -> str:
        app_value = app_value or ""
        if not app_value:
            return ""
        expanded = os.path.expandvars(os.path.expanduser(app_value))
        if os.path.isabs(expanded) and os.path.exists(expanded):
            return expanded
        if os.path.exists(expanded):
            return os.path.abspath(expanded)
        if is_windows():
            candidate = expanded
            exe_candidate = candidate if candidate.lower().endswith(".exe") else candidate + ".exe"
            if os.path.exists(exe_candidate):
                return os.path.abspath(exe_candidate)
        resolved = shutil.which(expanded)
        if resolved:
            return resolved
        for path in self._build_known_app_paths(expanded):
            if path and os.path.exists(path):
                return path
        return ""

    def _build_known_app_paths(self, app_name: str):
        candidates = []
        normalized = (app_name or "").lower()
        if not normalized:
            return candidates
        if is_windows():
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            program_files = os.environ.get("ProgramW6432") or os.environ.get("ProgramFiles")
            program_files_x86 = os.environ.get("ProgramFiles(x86)")

            def _append(path):
                if path and path not in candidates:
                    candidates.append(path)

            if normalized in {"edge", "msedge"}:
                for base in filter(None, [program_files, program_files_x86]):
                    _append(os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe"))
            elif normalized in {"chrome", "google-chrome"}:
                for base in filter(None, [program_files, program_files_x86]):
                    _append(os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"))
            elif normalized in {"vscode", "code"}:
                if local_appdata:
                    _append(os.path.join(local_appdata, "Programs", "Microsoft VS Code", "Code.exe"))
                for base in filter(None, [program_files, program_files_x86]):
                    _append(os.path.join(base, "Microsoft VS Code", "Code.exe"))
            elif normalized == "cursor":
                if local_appdata:
                    _append(os.path.join(local_appdata, "Programs", "Cursor", "Cursor.exe"))
            elif normalized == "obsidian":
                if local_appdata:
                    _append(os.path.join(local_appdata, "Programs", "obsidian", "Obsidian.exe"))
                for base in filter(None, [program_files, program_files_x86]):
                    _append(os.path.join(base, "Obsidian", "Obsidian.exe"))
        elif is_mac():
            app_mapping = {
                "edge": "/Applications/Microsoft Edge.app",
                "msedge": "/Applications/Microsoft Edge.app",
                "chrome": "/Applications/Google Chrome.app",
                "google-chrome": "/Applications/Google Chrome.app",
                "vscode": "/Applications/Visual Studio Code.app",
                "code": "/Applications/Visual Studio Code.app",
                "cursor": "/Applications/Cursor.app",
                "obsidian": "/Applications/Obsidian.app",
            }
            candidate = app_mapping.get(normalized)
            if candidate:
                candidates.append(candidate)
        return candidates


_icon_loader_instance: IconLoader = None


def get_icon_loader() -> IconLoader:
    global _icon_loader_instance
    if _icon_loader_instance is None:
        _icon_loader_instance = IconLoader()
    return _icon_loader_instance
