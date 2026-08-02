"""游戏热点插件共享阅读状态 — 三个插件共用同一份分页上下文"""
import threading

_lock = threading.Lock()
_reading = {}  # user_id -> {topic, extra, items, idx, page, total, cmd}


def get_reading(user_id: str):
    with _lock:
        return _reading.get(str(user_id))


def set_reading(user_id: str, ctx: dict):
    with _lock:
        _reading[str(user_id)] = ctx


def clear_reading(user_id: str):
    with _lock:
        _reading.pop(str(user_id), None)
