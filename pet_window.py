# -*- coding: utf-8 -*-
"""桌宠透明窗口：形象 + 情绪差分 + 气泡对话框 + 输入框 + 拖拽/右键交互"""
import os, re, random, time
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QPointF
from PySide6.QtGui import QPixmap, QMovie, QFont, QAction, QFontMetrics, QPainter, QColor, QPolygonF
from PySide6.QtWidgets import (QWidget, QLabel, QLineEdit, QVBoxLayout,
                               QHBoxLayout, QMenu, QGraphicsDropShadowEffect)

import config_manager as cm
from config_manager import MOODS, MOOD_NAMES
from chat_client import OllamaClient

MOOD_LABELS = {
    "开心": "happy", "高兴": "happy", "喜悦": "happy", "兴奋": "happy",
    "伤心": "sad", "难过": "sad", "悲伤": "sad", "委屈": "sad",
    "惊讶": "surprised", "震惊": "surprised", "吃惊": "surprised",
    "害羞": "shy", "羞涩": "shy", "脸红": "shy",
    "害怕": "afraid", "恐惧": "afraid", "紧张": "afraid",
    "无语": "speechless", "无奈": "speechless", "汗": "speechless", "嫌弃": "speechless",
    "平静": "idle", "正常": "idle", "温柔": "idle",
}
MOOD_RE = re.compile(r"^\s*【情绪[:：]?\s*(.*?)】\s*", re.S)
IDLE_LINES = [
    "……",
    "好无聊喵～",
    "点我聊天嘛！",
    "（伸了个懒腰）",
    "今天想聊点什么呢？",
    "（打了个哈欠）",
]


def visible_prefix(text, k):
    """取 text 中前 k 个『可见』字符（跳过 <think> 思维链块）"""
    out, i, n, in_think, count = [], 0, len(text), False, 0
    while i < n:
        if text.startswith("<think>", i):
            in_think = True
            i += 7
            continue
        if text.startswith("</think>", i):
            in_think = False
            i += 8
            continue
        if not in_think:
            out.append(text[i])
            count += 1
            if count >= k:
                break
        i += 1
    return "".join(out)


class BubbleTail(QLabel):
    """气泡尾巴：QPainter 画小三角（QSS 不支持 transform）"""

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QColor("#cfe0f0"))
        p.setBrush(QColor("#ffffff"))
        tri = QPolygonF([
            QPointF(0, 0),
            QPointF(self.width(), 0),
            QPointF(self.width() / 2, self.height()),
        ])
        p.drawPolygon(tri)


class ChatWorker(QThread):
    delta = Signal(str)
    done = Signal(str)
    error = Signal(str)

    def __init__(self, client, messages, temperature, top_p):
        super().__init__()
        self.client = client
        self.messages = messages
        self.temperature = temperature
        self.top_p = top_p

    def run(self):
        full = ""
        try:
            for d in self.client.stream_chat(self.messages, self.temperature, self.top_p):
                full += d
                self.delta.emit(d)
        except Exception as e:
            self.error.emit(str(e))
            return
        self.done.emit(full)


class PetWindow(QWidget):
    open_settings = Signal()

    PET_H = 300          # 形象显示高度基准
    BUBBLE_MARGIN = 16   # 气泡距形象顶部间距

    def __init__(self):
        super().__init__(None)
        self.cfg = cm.load_config()
        self.client = OllamaClient(self.cfg["ollama_host"], self.cfg["model"])
        self.worker = None
        self._full_text = ""
        self._display_full = ""
        self._shown_chars = 0
        self._drag_offset = None
        self._press_pos = None
        self._input_visible = False
        self._chatting = False
        self._mood = "idle"
        self._base_image = self.cfg.get("pet_image", "assets/pet.png")
        self._mood_parsed = False
        self._last_activity = time.time()

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("DeepSeek 桌宠")

        # ---- UI ----
        self.inner = QWidget(self)   # 浮动层（上下浮动动画作用于此）
        self.inner.setAttribute(Qt.WA_TranslucentBackground)
        lay = QVBoxLayout(self.inner)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # 气泡（含小三角）
        self.bubble_wrap = QWidget(self.inner)
        self.bubble_wrap.setAttribute(Qt.WA_TranslucentBackground)
        bw_lay = QVBoxLayout(self.bubble_wrap)
        bw_lay.setContentsMargins(0, 0, 0, 0)
        bw_lay.setSpacing(-1)

        self.bubble = QLabel()
        self.bubble.setWordWrap(True)
        self.bubble.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.bubble.setMaximumWidth(self.cfg.get("bubble_max_width", 320))
        self.bubble.setStyleSheet(
            "QLabel{background:#ffffff;border:1px solid #cfe0f0;"
            "border-radius:14px;padding:10px 14px;color:#2b3a4a;font-size:13px;}"
        )
        self.bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.bubble.hide()

        self.bubble_tail = BubbleTail()
        self.bubble_tail.setFixedSize(16, 14)
        self.bubble_tail.hide()

        bw_lay.addWidget(self.bubble, alignment=Qt.AlignHCenter)
        bw_lay.addWidget(self.bubble_tail, alignment=Qt.AlignHCenter)

        # 输入框
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("和她说点什么…（回车发送）")
        self.input_edit.setMaximumWidth(self.cfg.get("bubble_max_width", 320))
        self.input_edit.setStyleSheet(
            "QLineEdit{background:#ffffff;border:1px solid #9fc4e8;"
            "border-radius:14px;padding:8px 14px;color:#2b3a4a;font-size:13px;}"
            "QLineEdit:focus{border:1px solid #4a90d9;}"
        )
        self.input_edit.hide()
        self.input_edit.returnPressed.connect(self.on_send)

        # 形象
        self.pet_label = QLabel()
        self.pet_label.setAlignment(Qt.AlignCenter)
        self.pet_label.setCursor(Qt.PointingHandCursor)

        lay.addWidget(self.bubble_wrap, alignment=Qt.AlignHCenter)
        lay.addSpacing(2)
        lay.addWidget(self.input_edit, alignment=Qt.AlignHCenter)
        lay.addSpacing(12)
        lay.addWidget(self.pet_label, alignment=Qt.AlignHCenter)

        # 打字机
        self.type_timer = QTimer(self)
        self.type_timer.timeout.connect(self._type_tick)

        # 待机小动作：每隔一段时间换一句待机台词，形象回待机
        self.idle_timer = QTimer(self)
        self.idle_timer.setInterval(20000)
        self.idle_timer.timeout.connect(self._on_idle_tick)
        self.idle_timer.start()

        self._apply_config()
        self._set_mood("idle")
        self._show_idle_text()

    # ---------- 配置重载 ----------
    def reload_config(self):
        self.cfg = cm.load_config()
        self.client = OllamaClient(self.cfg.get("ollama_host", "http://localhost:11434"),
                                   self.cfg.get("model", "deepseek-r1:8b"))
        self._apply_config()
        self._base_image = self.cfg.get("pet_image", "assets/pet.png")
        self._set_mood(self._mood)
        self._last_activity = time.time()
        self.show()

    # ---------- 形象 / 情绪差分 ----------
    def _apply_config(self):
        self.setWindowOpacity(max(0.3, min(1.0, self.cfg.get("opacity", 1.0))))
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.cfg.get("always_on_top", True))
        self.setWindowFlag(Qt.WindowTransparentForInput, self.cfg.get("click_through", False))
        pos = self.cfg.get("window_pos", [100, 120])
        self.move(pos[0], pos[1])
        self._type_speed = max(5, self.cfg.get("typewriter_speed", 28))

    def _set_mood(self, mood):
        """切换情绪形象：自定义图 > 内置差分图 > 基础形象"""
        self._mood = mood
        path = cm.mood_image_path(self.cfg, mood)
        if not path:
            path = cm.resolve_asset(self._base_image)
        if not path:
            path = cm.resolve_asset("assets/pet.png")
        self._show_image(path)

    def _show_image(self, abs_path):
        if not abs_path or not os.path.exists(abs_path):
            self.pet_label.setText("(无形象)")
            return
        scale = self.cfg.get("pet_scale", 1.0)
        pet_h = int(self.PET_H * scale)
        if abs_path.lower().endswith(".gif"):
            self._movie = QMovie(abs_path)
            self._movie.setScaledSize(self._movie.currentPixmap().size().scaled(
                pet_h, pet_h, Qt.KeepAspectRatio))
            self.pet_label.setMovie(self._movie)
            self._movie.start()
            self._pix_size = self._movie.currentPixmap().size().scaled(
                pet_h, pet_h, Qt.KeepAspectRatio)
        else:
            pix = QPixmap(abs_path)
            if pix.isNull():
                self.pet_label.setText("(图片无法加载)")
                return
            self._pix_size = pix.size().scaled(pet_h, pet_h, Qt.KeepAspectRatio)
            self.pet_label.setPixmap(pix.scaled(self._pix_size, Qt.KeepAspectRatio,
                                                Qt.SmoothTransformation))
        self._resize_window()

    def _resize_window(self):
        w = self._pix_size.width()
        h = self._pix_size.height()
        bubble_h = self.bubble_wrap.sizeHint().height() if self.bubble.isVisible() else 0
        input_h = self.input_edit.sizeHint().height() if self.input_edit.isVisible() else 0
        total_h = bubble_h + input_h + self.BUBBLE_MARGIN + h
        self.inner.resize(max(w, self.cfg.get("bubble_max_width", 320)), total_h)
        self.resize(max(w, self.cfg.get("bubble_max_width", 320)) + 8, total_h + 8)

    # ---------- 气泡 ----------
    def _show_idle_text(self):
        self._set_bubble("你好呀～我是你的 AI 桌宠，点我就能聊天喵！")

    def _set_bubble(self, text):
        self.bubble.setText(text)
        # 用字体度量精确计算气泡宽度：单行文本宽度 clamp 到 [120, max_width]
        fm = QFontMetrics(self.bubble.font())
        tw = fm.horizontalAdvance(text) + 32  # 32 = 左右 padding + 边框
        max_w = self.cfg.get("bubble_max_width", 320)
        w = max(120, min(int(tw), max_w))
        self.bubble.setFixedWidth(w)
        self.bubble.show()
        self.bubble_tail.show()
        self._resize_window()

    def _hide_bubble(self):
        self.bubble.hide()
        self.bubble_tail.hide()
        self._resize_window()

    # ---------- 打字机 ----------
    def _type_tick(self):
        if not self._display_full:
            return  # 模型内容还没出现，保留"少女思考中…"提示
        self._shown_chars += 2
        if self._shown_chars >= len(self._display_full):
            self._shown_chars = len(self._display_full)
            self.type_timer.stop()
        self._set_bubble(self._display_full[:self._shown_chars])

    def _update_display(self):
        """从原始文本剥离 think 块与情绪标签，得到显示文本；解析到情绪则切换差分表情"""
        vis = visible_prefix(self._full_text, len(self._full_text))
        m = MOOD_RE.match(vis)
        if m:
            label = m.group(1).strip()
            key = MOOD_LABELS.get(label)
            if key:
                self._set_mood(key)
                self._mood_parsed = True
            vis = vis[m.end():]
        self._display_full = vis.strip()

    def _begin_stream(self, user_text):
        self._full_text = ""
        self._display_full = ""
        self._shown_chars = 0
        self._mood_parsed = False
        self._chatting = True
        self._set_mood("thinking")
        self._set_bubble("（少女思考中…）")
        # 打字机等第一条内容到达后再启动，思考中提示保持显示

        persona = self.cfg.get("persona", "")
        mood_instr = (
            "\n\n【回复格式要求】每次回复前，先单独输出一行情绪标签，"
            "格式为【情绪:开心】/【情绪:伤心】/【情绪:惊讶】/【情绪:害羞】/"
            "【情绪:害怕】/【情绪:无语】/【情绪:平静】，"
            "然后换行输出正式回复内容。情绪标签行不要包含其他内容。"
        )
        msgs = [{"role": "system", "content": persona + mood_instr}]
        msgs.append({"role": "user", "content": user_text})
        self.worker = ChatWorker(self.client, msgs,
                                 self.cfg.get("temperature", 0.7),
                                 self.cfg.get("top_p", 0.9))
        self.worker.delta.connect(self._on_delta)
        self.worker.done.connect(self._on_done)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_delta(self, text):
        self._full_text += text
        self._update_display()
        if self._display_full and not self.type_timer.isActive():
            self.type_timer.start(self._type_speed)

    def _on_done(self, full):
        self._full_text = full
        self._update_display()
        self._shown_chars = len(self._display_full)
        self.type_timer.stop()
        clean = self._display_full or self.client.strip_think(full)
        self._set_bubble(clean)
        import history_manager as hm
        hm.add("assistant", clean)
        self._chatting = False
        self._last_activity = time.time()
        if not self._mood_parsed:
            self._set_mood("idle")

    def _on_error(self, msg):
        self.type_timer.stop()
        self._set_bubble(f"呜呜，连接出问题了：{msg}\n（检查 Ollama 是否在运行）")
        self._chatting = False
        self._set_mood("sad")

    # ---------- 待机 ----------
    def _on_idle_tick(self):
        # 距上次活动超过 25 秒才切换待机台词，避免覆盖刚回复的内容
        if not self._chatting and time.time() - self._last_activity > 25:
            self._set_mood("idle")
            self._set_bubble(random.choice(IDLE_LINES))

    # ---------- 交互 ----------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and not self.cfg.get("click_through", False):
            self._drag_offset = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._press_pos = e.globalPosition().toPoint()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag_offset is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._drag_offset is not None:
            self._drag_offset = None
            # 位移很小 -> 视为单击，弹出输入框
            if (self._press_pos
                    and (e.globalPosition().toPoint() - self._press_pos).manhattanLength() < 6):
                self._toggle_input()
            else:
                pos = self.pos()
                self.cfg["window_pos"] = [pos.x(), pos.y()]
                cm.save_config(self.cfg)
            self._press_pos = None
            self._last_activity = time.time()
        super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.open_settings.emit()
        super().mouseDoubleClickEvent(e)

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        act_settings = QAction("⚙ 设置面板", self)
        act_chat = QAction("💬 聊天", self)
        act_through = QAction("🖱 鼠标穿透：开" if not self.cfg.get("click_through") else "🖱 鼠标穿透：关", self)
        act_top = QAction("📌 置顶：开" if self.cfg.get("always_on_top") else "📌 置顶：关", self)
        act_quit = QAction("✕ 退出", self)
        menu.addAction(act_settings)
        menu.addAction(act_chat)
        menu.addSeparator()
        menu.addAction(act_through)
        menu.addAction(act_top)
        menu.addSeparator()
        menu.addAction(act_quit)

        act_settings.triggered.connect(self.open_settings.emit)
        act_chat.triggered.connect(self._toggle_input)
        act_through.triggered.connect(lambda: self._toggle_flag("click_through"))
        act_top.triggered.connect(lambda: self._toggle_flag("always_on_top"))
        act_quit.triggered.connect(self._quit)
        menu.exec(e.globalPos())

    def _toggle_flag(self, key):
        self.cfg[key] = not self.cfg.get(key)
        cm.save_config(self.cfg)
        self._apply_config()
        self.show()

    def _quit(self):
        from PySide6.QtWidgets import QApplication
        QApplication.instance().quit()

    def _toggle_input(self):
        self._last_activity = time.time()
        self._input_visible = not self._input_visible
        if self._input_visible:
            self.input_edit.show()
            self.input_edit.setFocus()
        else:
            self.input_edit.hide()
        self._resize_window()

    def on_send(self):
        text = self.input_edit.text().strip()
        if not text or self._chatting:
            return
        self._last_activity = time.time()
        self.input_edit.clear()
        self._input_visible = False
        self.input_edit.hide()
        self._resize_window()
        import history_manager as hm
        hm.add("user", text)
        self._begin_stream(text)
