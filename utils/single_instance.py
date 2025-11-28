#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import socket
import tempfile
import threading
from contextlib import closing
from typing import Callable, Optional

from utils.logger import get_logger

logger = get_logger("single_instance")


class SingleInstanceManager:
    """Coordinates a single running instance with local socket activation."""

    def __init__(self, app_id: str = "work-stack", port: Optional[int] = None):
        self.app_id = app_id
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.listener_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._activation_handler: Optional[Callable[[], None]] = None
        self._lock_file_handle: Optional[object] = None

    def _build_port_file(self) -> str:
        directory = tempfile.gettempdir()
        return os.path.join(directory, f"{self.app_id}.port")

    def _build_lock_file(self) -> str:
        directory = tempfile.gettempdir()
        return os.path.join(directory, f"{self.app_id}.lock")

    def _write_port_file(self, port: int):
        try:
            with open(self._build_port_file(), "w", encoding="utf-8") as f:
                f.write(str(port))
        except Exception as exc:
            logger.error(f"写入端口文件失败: {exc}")

    def _read_port_file(self) -> Optional[int]:
        path = self._build_port_file()
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                value = int(f.read().strip())
                return value if 0 < value < 65535 else None
        except Exception as exc:
            logger.warning(f"读取端口文件失败: {exc}")
            return None

    def _remove_port_file(self):
        path = self._build_port_file()
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as exc:
            logger.warning(f"移除端口文件失败: {exc}")

    def _acquire_file_lock(self) -> bool:
        """Attempt to lock application instance."""
        lock_path = self._build_lock_file()
        try:
            handle = open(lock_path, "w")
        except OSError as exc:
            logger.error(f"创建锁文件失败: {exc}")
            return False

        try:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                handle.seek(0)
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            handle.seek(0)
            handle.write(str(os.getpid()))
            handle.flush()
            self._lock_file_handle = handle
            return True
        except (OSError, IOError) as exc:
            logger.info(f"无法获取单实例锁: {exc}")
            try:
                handle.close()
            except Exception:
                pass
            self._lock_file_handle = None
            return False

    def _release_file_lock(self):
        if not self._lock_file_handle:
            return
        try:
            self._lock_file_handle.seek(0)
        except Exception:
            pass
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self._lock_file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._lock_file_handle.fileno(), fcntl.LOCK_UN)
        except Exception as exc:
            logger.warning(f"释放单实例锁失败: {exc}")
        finally:
            try:
                self._lock_file_handle.close()
            except Exception:
                pass
            self._lock_file_handle = None
            try:
                os.remove(self._build_lock_file())
            except OSError:
                pass

    def acquire(self, activation_handler: Callable[[], None]) -> bool:
        """尝试成为主实例，返回True表示成功"""
        self._activation_handler = activation_handler
        self._stop_event.clear()

        if not self._acquire_file_lock():
            return False

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(("127.0.0.1", 0))
            self.server_socket.listen(1)
            self.port = self.server_socket.getsockname()[1]
            self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listener_thread.start()
            self._write_port_file(self.port)
            logger.info(f"单实例锁成功，监听端口{self.port}")
            return True
        except OSError as exc:
            logger.info(f"无法绑定端口成为主实例: {exc}")
            self._close_server()
            self._release_file_lock()
            return False

    def _listen_loop(self):
        while not self._stop_event.is_set():
            try:
                if not self.server_socket:
                    break
                self.server_socket.settimeout(0.5)
                client, _ = self.server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with closing(client):
                try:
                    data = client.recv(1024)
                    if data.strip() == b"activate":
                        logger.info("收到激活请求")
                        if self._activation_handler:
                            self._activation_handler()
                        client.sendall(b"ok")
                except Exception as exc:
                    logger.error(f"处理激活请求失败: {exc}")

    def _close_server(self):
        self._stop_event.set()
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=1.0)
            self.listener_thread = None
        self._remove_port_file()
        self._stop_event.clear()

    def release(self):
        """关闭监听，释放单实例锁"""
        self._close_server()
        self._release_file_lock()
        logger.info("单实例锁已释放")

    def activate_existing(self, timeout: float = 1.0) -> bool:
        """通知现有实例显示窗口"""
        port = self.port or self._read_port_file()
        if not port:
            logger.warning("未找到现有实例端口")
            return False
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as client:
            client.settimeout(timeout)
            try:
                client.connect(("127.0.0.1", port))
                client.sendall(b"activate")
                data = client.recv(16)
                return data.strip() == b"ok"
            except Exception as exc:
                logger.error(f"向现有实例发送激活失败: {exc}")
                return False
