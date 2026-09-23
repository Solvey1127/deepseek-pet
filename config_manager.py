# -*- coding: utf-8 -*-
"""配置管理：读写 data/config.json"""
import json, os, shutil, sys

# frozen（PyInstaller 打包后）：
#   BASE_DIR = exe 内置资源解压目录（_MEIPASS），只读
#   APP_DIR  = exe 所在目录，用户数据（data/、自定义图片）写在这里
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = APP_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(APP_DIR, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
HISTORY_PATH = os.path.join(DATA_DIR, "history.json")

# 情绪差分：key -> 内置差分文件名（None = 用基础形象）
MOODS = {
    "idle": None,                 # 待机
    "thinking": "mood_thinking",  # 思考
    "happy": "mood_happy",        # 开心
    "sad": "mood_sad",            # 伤心
    "surprised": "mood_surprised",  # 惊讶
    "shy": "mood_shy",            # 害羞
    "afraid": "mood_afraid",      # 害怕
    "speechless": "mood_speechless",  # 无语
}
MOOD_NAMES = {
    "idle": "待机",
    "thinking": "思考",
    "happy": "开心",
    "sad": "伤心",
    "surprised": "惊讶",
    "shy": "害羞",
    "afraid": "害怕",
    "speechless": "无语",
}

DEFAULT_PERSONA = (
    "你是一只住在用户电脑里的软萌猫娘桌宠，名叫小蓝。"
    "说话简短可爱，喜欢用“喵”结尾，语气温柔粘人。"
    "你会认真回答用户的问题，回答问题本身要准确清楚，"
    "不要长篇大论，尽量简洁。"
)

DEFAULT_CONFIG = {
    "model": "deepseek-r1:8b",
    "ollama_host": "http://localhost:11434",
    "pet_image": "assets/pet.png",
    "mood_images": {},   # 自定义情绪图片：{"happy": "assets/moods/xxx.png", ...}
    "persona": DEFAULT_PERSONA,
    "temperature": 0.7,
    "top_p": 0.9,
    "window_pos": [100, 120],
    "pet_scale": 1.0,
    "opacity": 1.0,
    "always_on_top": True,
    "click_through": False,
    "typewriter_speed": 28,      # 每字间隔 ms
    "bubble_max_width": 320,     # 气泡最大宽度 px
}


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def resolve_asset(path):
    """把配置里的相对路径解析为绝对路径；找不到返回 None
    优先用户数据目录（exe 同目录），其次内置资源目录"""
    if not path:
        return None
    p = path if os.path.isabs(path) else os.path.join(APP_DIR, path)
    if os.path.exists(p):
        return p
    if BASE_DIR != APP_DIR and not os.path.isabs(path):
        p2 = os.path.join(BASE_DIR, path)
        if os.path.exists(p2):
            return p2
    return None


def load_config():
    ensure_data_dir()
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg


def save_config(cfg):
    ensure_data_dir()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def list_builtin_images():
    """内置形象列表：[显示名, 路径]"""
    assets = os.path.join(BASE_DIR, "assets")
    out = []
    for name in ("pet.png", "pet2.png", "pet3.png"):
        p = os.path.join(assets, name)
        if os.path.exists(p):
            out.append([name, p])
    return out


def copy_to_assets(src_path, subdir="", prefix="user"):
    """把用户选择的形象复制进 assets[/subdir]/<prefix>_<时间戳>.<ext>，返回相对路径
    始终复制到 exe 同目录（持久保存）"""
    ensure_data_dir()
    base = os.path.join(APP_DIR, "assets")
    if subdir:
        base = os.path.join(base, subdir)
    os.makedirs(base, exist_ok=True)
    ext = os.path.splitext(src_path)[1].lower() or ".png"
    if ext not in (".png", ".jpg", ".jpeg", ".gif"):
        ext = ".png"
    import time
    dst = os.path.join(base, f"{prefix}_{int(time.time())}{ext}")
    shutil.copy2(src_path, dst)
    return os.path.relpath(dst, APP_DIR).replace("\\", "/")


def mood_image_path(cfg, mood):
    """返回某情绪当前应使用的图片绝对路径（自定义 > 内置差分 > None）
    返回 None 表示用基础形象"""
    mood_imgs = cfg.get("mood_images", {}) or {}
    custom = mood_imgs.get(mood)
    if custom:
        p = resolve_asset(custom)
        if p:
            return p
    fname = MOODS.get(mood)
    if fname:
        p = os.path.join(BASE_DIR, "assets", "moods", f"{fname}.png")
        if os.path.exists(p):
            return p
    return None
