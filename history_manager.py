# -*- coding: utf-8 -*-
"""历史记录管理：data/history.json，消息按时间追加"""
import json, os, time
from config_manager import HISTORY_PATH, ensure_data_dir

MAX_ITEMS = 2000   # 最多保留条数


def _load():
    ensure_data_dir()
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save(items):
    ensure_data_dir()
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def add(role, content):
    """role: user / assistant / system；返回该条记录 dict"""
    items = _load()
    rec = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "role": role,
        "content": content,
    }
    items.append(rec)
    if len(items) > MAX_ITEMS:
        items = items[-MAX_ITEMS:]
    _save(items)
    return rec


def all_items():
    return _load()


def delete(index):
    """按展示列表的序号删除（倒序列表的第 index 条）"""
    items = _load()
    if 0 <= index < len(items):
        items.pop(index)
        _save(items)
        return True
    return False


def clear():
    _save([])
