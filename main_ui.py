# -*- coding: utf-8 -*-
"""主设置面板：外观 / 人设 / 历史 / 通用，淡蓝白简约风格"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QMovie, QFont
from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QListWidget,
                               QListWidgetItem, QStackedWidget, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QTextEdit, QSlider,
                               QCheckBox, QComboBox, QFileDialog, QMessageBox,
                               QLineEdit, QSplitter, QFrame, QScrollArea)

import config_manager as cm
from chat_client import OllamaClient

QSS = """
QWidget { font-family: "Microsoft YaHei"; font-size: 13px; color: #2b3a4a; }
#root { background: #f2f7fc; }
#nav { background: #ffffff; border-right: 1px solid #dce8f2; }
#nav QListWidget {
    background: transparent; border: none; outline: none; padding: 12px 8px;
}
#nav QListWidget::item {
    padding: 11px 18px; border-radius: 10px; margin: 2px 4px; color: #5a6b7d;
}
#nav QListWidget::item:selected {
    background: #e3f0fb; color: #1e6fd9; font-weight: bold;
}
#nav QListWidget::item:hover { background: #eef6fc; }
#content { background: #f2f7fc; }
#card {
    background: #ffffff; border: 1px solid #dce8f2; border-radius: 14px;
}
QLabel#title { font-size: 17px; font-weight: bold; color: #1c3b57; }
QLabel#sub { color: #7d8fa3; font-size: 12px; }
QLabel#hint { color: #9aacbe; font-size: 11px; }
QPushButton {
    background: #ffffff; border: 1px solid #c3d8ea; border-radius: 8px;
    padding: 7px 16px; color: #2b3a4a;
}
QPushButton:hover { border-color: #7fb0dd; background: #f4faff; }
QPushButton#primary {
    background: #4a90d9; color: #ffffff; border: none; font-weight: bold;
}
QPushButton#primary:hover { background: #3c7fc7; }
QPushButton#danger { color: #c0392b; border-color: #e5b8b3; }
QPushButton#danger:hover { background: #fdf1f0; }
QTextEdit, QLineEdit {
    background: #ffffff; border: 1px solid #c3d8ea; border-radius: 10px;
    padding: 8px 10px; selection-background-color: #cfe4f7;
}
QTextEdit:focus, QLineEdit:focus { border: 1px solid #4a90d9; }
QSlider::groove:horizontal { height: 6px; background: #d7e6f3; border-radius: 3px; }
QSlider::handle:horizontal {
    width: 16px; height: 16px; margin: -5px 0; border-radius: 8px;
    background: #4a90d9;
}
QCheckBox::indicator { width: 17px; height: 17px; border-radius: 5px;
    border: 1px solid #b9cfE2; background: #ffffff; }
QCheckBox::indicator:checked { background: #4a90d9; border-color: #4a90d9; }
QComboBox {
    background: #ffffff; border: 1px solid #c3d8ea; border-radius: 8px;
    padding: 5px 12px;
}
QComboBox::drop-down { border: none; width: 22px; }
QListWidget#history {
    background: #ffffff; border: 1px solid #dce8f2; border-radius: 10px;
    padding: 4px;
}
QListWidget#history::item { padding: 8px 10px; border-radius: 8px; }
QListWidget#history::item:selected { background: #e3f0fb; }
QSplitter::handle { background: transparent; }
"""

PERSONA_PRESETS = {
    "软萌猫娘": "你是一只住在用户电脑里的软萌猫娘桌宠，名叫小蓝。说话简短可爱，喜欢用“喵”结尾，语气温柔粘人。你会认真回答用户的问题，回答问题本身要准确清楚，不要长篇大论，尽量简洁。",
    "毒舌助手": "你是一个嘴硬心软的毒舌 AI 助手，说话带点傲娇和调侃，但给出的信息准确可靠。回答尽量简短犀利，偶尔吐槽，让聊天变得有趣。",
    "正经学霸": "你是一个认真严谨的学霸型 AI 助手，回答问题条理清晰、结构分明，用简洁的要点呈现，绝不废话。",
    "温柔知心": "你是一个温柔耐心的知心伙伴，善于倾听、共情，回答温和有温度，同时给出实在的建议。",
}


class MainUI(QWidget):
    config_changed = Signal()      # 通知桌宠重载

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeepSeek 桌宠 · 设置")
        self.resize(760, 540)
        self.setMinimumSize(680, 480)
        self.setStyleSheet(QSS)
        self.cfg = cm.load_config()
        self.client = OllamaClient(self.cfg.get("ollama_host", "http://localhost:11434"))
        self._current_image_path = self.cfg.get("pet_image", "assets/pet.png")

        self._build_ui()
        self._load_models()
        self._fill_persona()
        self._refresh_history()

    # ---------- UI 骨架 ----------
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)        # 左侧导航
        nav = QWidget()
        nav.setObjectName("nav")
        nav.setFixedWidth(168)
        nav_lay = QVBoxLayout(nav)
        nav_lay.setContentsMargins(0, 16, 0, 0)
        self.nav_list = QListWidget()
        for t in ("🎨 外观", "💬 人设", "📜 历史记录", "⚙ 通用"):
            QListWidgetItem(t, self.nav_list)
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._switch_page)
        nav_lay.addWidget(self.nav_list)
        nav_lay.addStretch()

        # 右侧内容
        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_appearance())
        self.stack.addWidget(self._page_persona())
        self.stack.addWidget(self._page_history())
        self.stack.addWidget(self._page_general())

        root.addWidget(nav)
        root.addWidget(self.stack, 1)

    def showEvent(self, event):
        """每次显示面板时刷新历史列表（聊天过程中会新增记录）"""
        super().showEvent(event)
        self._refresh_history()

    def _switch_page(self, row):
        self.stack.setCurrentIndex(max(0, row))

    def _card(self, title, sub=""):
        card = QFrame()
        card.setObjectName("card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        t = QLabel(title)
        t.setObjectName("title")
        lay.addWidget(t)
        if sub:
            s = QLabel(sub)
            s.setObjectName("sub")
            s.setWordWrap(True)
            lay.addWidget(s)
        return card, lay

    # ---------- 外观页 ----------
    def _page_appearance(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}"
                             "QScrollBar:vertical{width:8px;background:transparent;}"
                             "QScrollBar::handle:vertical{background:#c3d8ea;border-radius:4px;}"
                             "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}")
        body = QWidget()
        body.setStyleSheet("background:transparent;")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(24, 20, 24, 20)
        body_lay.setSpacing(14)

        # 基础形象卡片
        card, lay = self._card("桌宠形象", "内置了几只形象，也可以选择你自己的图片（推荐透明底 PNG，支持 GIF 动图）")
        body_lay.addWidget(card)

        row = QHBoxLayout()
        # 预览
        self.preview = QLabel()
        self.preview.setFixedSize(150, 180)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet(
            "QLabel{background:#f7fbfe;border:1px dashed #b9cfe2;border-radius:12px;}")
        row.addWidget(self.preview, 0)
        # 选择区
        right = QVBoxLayout()
        right.setSpacing(10)
        self.builtin_row = QHBoxLayout()
        self.builtin_row.setSpacing(10)
        right.addLayout(self.builtin_row)
        self.btn_local = QPushButton("选择本地图片 / GIF…")
        self.btn_local.clicked.connect(self._pick_local_image)
        right.addWidget(self.btn_local)
        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("形象大小"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(60, 160)
        self.scale_slider.setValue(int(self.cfg.get("pet_scale", 1.0) * 100))
        self.scale_slider.valueChanged.connect(self._on_scale)
        self.scale_val = QLabel(f"{self.scale_slider.value()}%")
        self.scale_val.setObjectName("hint")
        scale_row.addWidget(self.scale_slider, 1)
        scale_row.addWidget(self.scale_val)
        right.addLayout(scale_row)
        right.addStretch()
        row.addLayout(right, 1)
        lay.addLayout(row)

        # 表情差分卡片
        card2, lay2 = self._card("表情差分", "为每个情绪状态单独设置形象图片；不改则用内置表情")
        body_lay.addWidget(card2)
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        self.mood_cells = {}
        for i, (key, name) in enumerate(cm.MOOD_NAMES.items()):
            cell = self._mood_cell(key, name)
            grid.addWidget(cell, i // 2, i % 2)
        lay2.addLayout(grid)

        body_lay.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll)

        self._refresh_builtin_buttons()
        self._refresh_preview()
        self._refresh_mood_cards()
        return page

    def _mood_cell(self, key, name):
        """单个情绪状态的换图小卡片"""
        frame = QFrame()
        frame.setObjectName("card")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)
        prev = QLabel()
        prev.setFixedSize(56, 72)
        prev.setAlignment(Qt.AlignCenter)
        prev.setStyleSheet(
            "QLabel{background:#f7fbfe;border:1px dashed #b9cfe2;border-radius:8px;}")
        name_l = QLabel(name)
        name_l.setAlignment(Qt.AlignCenter)
        name_l.setStyleSheet("font-weight:bold;color:#2b3a4a;")
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_set = QPushButton("更换")
        btn_set.setFixedHeight(24)
        btn_reset = QPushButton("恢复默认")
        btn_reset.setFixedHeight(24)
        btn_set.clicked.connect(lambda _, k=key: self._pick_mood_image(k))
        btn_reset.clicked.connect(lambda _, k=key: self._reset_mood_image(k))
        btn_row.addWidget(btn_set, 1)
        btn_row.addWidget(btn_reset, 1)
        lay.addWidget(prev, alignment=Qt.AlignHCenter)
        lay.addWidget(name_l)
        lay.addLayout(btn_row)
        self.mood_cells[key] = {"preview": prev, "btn_reset": btn_reset}
        return frame

    def _pick_mood_image(self, key):
        name = cm.MOOD_NAMES.get(key, key)
        path, _ = QFileDialog.getOpenFileName(
            self, f"选择「{name}」表情图片", "", "图片文件 (*.png *.jpg *.jpeg *.gif)")
        if path:
            rel = cm.copy_to_assets(path, subdir="moods", prefix=f"mood_{key}")
            self.cfg.setdefault("mood_images", {})[key] = rel
            cm.save_config(self.cfg)
            self._refresh_mood_cards()
            self.config_changed.emit()

    def _reset_mood_image(self, key):
        self.cfg.setdefault("mood_images", {}).pop(key, None)
        cm.save_config(self.cfg)
        self._refresh_mood_cards()
        self.config_changed.emit()

    def _refresh_mood_cards(self):
        for key, cell in self.mood_cells.items():
            prev = cell["preview"]
            path = cm.mood_image_path(self.cfg, key)
            if path:
                if path.lower().endswith(".gif"):
                    mv = QMovie(path)
                    mv.setScaledSize(mv.currentPixmap().size().scaled(
                        56, 72, Qt.KeepAspectRatio))
                    prev.setMovie(mv)
                    mv.start()
                    setattr(self, f"_mood_movie_{key}", mv)
                else:
                    pix = QPixmap(path)
                    prev.setPixmap(pix.scaled(56, 72, Qt.KeepAspectRatio,
                                              Qt.SmoothTransformation))
            else:
                prev.clear()
                prev.setText("默认")
            # 自定义时恢复默认按钮可用
            custom = (self.cfg.get("mood_images", {}) or {}).get(key)
            cell["btn_reset"].setEnabled(bool(custom))

    def _refresh_builtin_buttons(self):
        # 清空旧的
        while self.builtin_row.count():
            item = self.builtin_row.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for name, path in cm.list_builtin_images():
            btn = QPushButton(name.replace(".png", "").replace("pet", "形象"))
            btn.setCheckable(True)
            btn.setChecked(cm.resolve_asset(self._current_image_path) == path)
            btn.clicked.connect(lambda _, p=path: self._select_image(p))
            self.builtin_row.addWidget(btn)

    def _select_image(self, path):
        self._current_image_path = path
        self.cfg["pet_image"] = path
        cm.save_config(self.cfg)
        self._refresh_builtin_buttons()
        self._refresh_preview()
        self.config_changed.emit()

    def _pick_local_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择桌宠形象", "", "图片文件 (*.png *.jpg *.jpeg *.gif)")
        if path:
            rel = cm.copy_to_assets(path)
            self._select_image(rel)

    def _on_scale(self, v):
        self.scale_val.setText(f"{v}%")
        self.cfg["pet_scale"] = v / 100.0
        cm.save_config(self.cfg)
        self.config_changed.emit()

    def _refresh_preview(self):
        p = cm.resolve_asset(self._current_image_path)
        if not p:
            self.preview.setText("无图片")
            return
        if p.lower().endswith(".gif"):
            self._prev_movie = QMovie(p)
            self._prev_movie.setScaledSize(self._prev_movie.currentPixmap().size().scaled(
                150, 180, Qt.KeepAspectRatio))
            self.preview.setMovie(self._prev_movie)
            self._prev_movie.start()
        else:
            pix = QPixmap(p)
            self.preview.setPixmap(pix.scaled(150, 180, Qt.KeepAspectRatio,
                                              Qt.SmoothTransformation))

    # ---------- 人设页 ----------
    def _page_persona(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        card, lay = self._card("人设设定", "决定桌宠的性格与口吻，会作为系统提示词发给模型")
        outer.addWidget(card)

        presets = QHBoxLayout()
        presets.addWidget(QLabel("预设"))
        self.preset_box = QComboBox()
        self.preset_box.addItem("自定义…")
        self.preset_box.addItems(list(PERSONA_PRESETS.keys()))
        self.preset_box.currentTextChanged.connect(self._on_preset)
        presets.addWidget(self.preset_box, 1)
        lay.addLayout(presets)

        self.persona_edit = QTextEdit()
        self.persona_edit.setMinimumHeight(160)
        self.persona_edit.setPlaceholderText("在这里写桌宠的人设…")
        lay.addWidget(self.persona_edit)

        btn_row = QHBoxLayout()
        self.btn_save_persona = QPushButton("保存人设")
        self.btn_save_persona.setObjectName("primary")
        self.btn_save_persona.clicked.connect(self._save_persona)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_save_persona)
        lay.addLayout(btn_row)
        return page

    def _fill_persona(self):
        self.persona_edit.setPlainText(self.cfg.get("persona", ""))

    def _on_preset(self, name):
        if name in PERSONA_PRESETS:
            self.persona_edit.setPlainText(PERSONA_PRESETS[name])

    def _save_persona(self):
        self.cfg["persona"] = self.persona_edit.toPlainText().strip()
        cm.save_config(self.cfg)
        self.config_changed.emit()
        QMessageBox.information(self, "已保存", "人设已保存喵～")

    # ---------- 历史记录页 ----------
    def _page_history(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        card, lay = self._card("聊天历史", "所有对话都记录在这里，可查看或清理")
        outer.addWidget(card)

        split = QSplitter(Qt.Horizontal)
        self.history_list = QListWidget()
        self.history_list.setObjectName("history")
        self.history_list.currentRowChanged.connect(self._show_history_item)
        split.addWidget(self.history_list)

        self.history_view = QTextEdit()
        self.history_view.setReadOnly(True)
        self.history_view.setPlaceholderText("选中左侧记录查看内容…")
        split.addWidget(self.history_view)
        split.setSizes([260, 380])
        lay.addWidget(split, 1)

        btn_row = QHBoxLayout()
        self.btn_del = QPushButton("删除选中")
        self.btn_del.setObjectName("danger")
        self.btn_del.clicked.connect(self._delete_history_item)
        self.btn_clear = QPushButton("清空全部")
        self.btn_clear.setObjectName("danger")
        self.btn_clear.clicked.connect(self._clear_history)
        self.history_count = QLabel()
        self.history_count.setObjectName("hint")
        btn_row.addWidget(self.history_count)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_del)
        btn_row.addWidget(self.btn_clear)
        lay.addLayout(btn_row)
        return page

    def _refresh_history(self):
        import history_manager as hm
        items = hm.all_items()
        self._history_data = items
        self.history_list.clear()
        role_name = {"user": "我", "assistant": "桌宠", "system": "系统"}
        for rec in reversed(items):
            role = role_name.get(rec.get("role", ""), rec.get("role", ""))
            content = rec.get("content", "").replace("\n", " ")
            if len(content) > 30:
                content = content[:30] + "…"
            self.history_list.addItem(QListWidgetItem(f"[{rec.get('time','')}] {role}：{content}"))
        self.history_count.setText(f"共 {len(items)} 条记录")

    def _show_history_item(self, row):
        if row is None or row < 0 or row >= len(self._history_data):
            return
        rec = self._history_data[-(row + 1)]
        role_name = {"user": "我", "assistant": "桌宠", "system": "系统"}
        self.history_view.setPlainText(
            f"时间：{rec.get('time','')}\n角色：{role_name.get(rec.get('role',''), rec.get('role',''))}\n"
            f"内容：\n{rec.get('content','')}")

    def _delete_history_item(self):
        row = self.history_list.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "先选中一条记录喵")
            return
        import history_manager as hm
        hm.delete(row)
        self._refresh_history()
        self.history_view.clear()

    def _clear_history(self):
        if QMessageBox.question(self, "确认", "确定清空全部聊天历史吗？此操作不可恢复。") == QMessageBox.Yes:
            import history_manager as hm
            hm.clear()
            self._refresh_history()
            self.history_view.clear()

    # ---------- 通用页 ----------
    def _page_general(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        card, lay = self._card("通用设置", "连接、对话参数与窗口行为")
        outer.addWidget(card)

        # 模型
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("模型"))
        self.model_box = QComboBox()
        model_row.addWidget(self.model_box, 1)
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self._load_models)
        model_row.addWidget(self.btn_refresh)
        self.conn_label = QLabel()
        self.conn_label.setObjectName("hint")
        model_row.addWidget(self.conn_label)
        lay.addLayout(model_row)

        # 温度
        temp_row = QHBoxLayout()
        temp_row.addWidget(QLabel("创意度"))
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(0, 20)
        self.temp_slider.setValue(int(self.cfg.get("temperature", 0.7) * 20))
        self.temp_slider.valueChanged.connect(self._on_temp)
        self.temp_val = QLabel(f"{self.temp_slider.value() / 20:.1f}")
        self.temp_val.setObjectName("hint")
        temp_row.addWidget(self.temp_slider, 1)
        temp_row.addWidget(self.temp_val)
        lay.addLayout(temp_row)

        # 打字速度
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("打字速度"))
        self.type_slider = QSlider(Qt.Horizontal)
        self.type_slider.setRange(1, 60)
        self.type_slider.setValue(self.cfg.get("typewriter_speed", 28))
        self.type_slider.valueChanged.connect(self._on_type_speed)
        self.type_val = QLabel(f"{self.type_slider.value()}ms")
        self.type_val.setObjectName("hint")
        type_row.addWidget(self.type_slider, 1)
        type_row.addWidget(self.type_val)
        lay.addLayout(type_row)

        # 透明度
        opa_row = QHBoxLayout()
        opa_row.addWidget(QLabel("透明度"))
        self.opa_slider = QSlider(Qt.Horizontal)
        self.opa_slider.setRange(30, 100)
        self.opa_slider.setValue(int(self.cfg.get("opacity", 1.0) * 100))
        self.opa_slider.valueChanged.connect(self._on_opacity)
        self.opa_val = QLabel(f"{self.opa_slider.value()}%")
        self.opa_val.setObjectName("hint")
        opa_row.addWidget(self.opa_slider, 1)
        opa_row.addWidget(self.opa_val)
        lay.addLayout(opa_row)

        # 开关
        self.chk_top = QCheckBox("窗口置顶（始终显示在其他窗口上方）")
        self.chk_top.setChecked(self.cfg.get("always_on_top", True))
        self.chk_top.toggled.connect(self._on_top)
        lay.addWidget(self.chk_top)

        self.chk_through = QCheckBox("鼠标穿透（点击不挡桌面，关闭后需右键菜单重新打开）")
        self.chk_through.setChecked(self.cfg.get("click_through", False))
        self.chk_through.toggled.connect(self._on_through)
        lay.addWidget(self.chk_through)

        hint = QLabel("提示：穿透开启后桌宠无法被点击，需通过本面板或系统托盘关闭。")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addStretch()
        return page

    def _load_models(self):
        models = self.client.list_models()
        if models:
            self.conn_label.setText("● 已连接")
            self.conn_label.setStyleSheet("color:#2e9e5b;")
            current = self.cfg.get("model")
            self.model_box.clear()
            self.model_box.addItems(models)
            if current in models:
                self.model_box.setCurrentText(current)
            self.model_box.currentTextChanged.connect(self._on_model)
        else:
            self.conn_label.setText("○ 未连接 Ollama")
            self.conn_label.setStyleSheet("color:#c0392b;")

    def _on_model(self, name):
        self.cfg["model"] = name
        cm.save_config(self.cfg)
        self.config_changed.emit()

    def _on_temp(self, v):
        self.temp_val.setText(f"{v / 20:.1f}")
        self.cfg["temperature"] = v / 20.0
        cm.save_config(self.cfg)
        self.config_changed.emit()

    def _on_type_speed(self, v):
        self.type_val.setText(f"{v}ms")
        self.cfg["typewriter_speed"] = v
        cm.save_config(self.cfg)
        self.config_changed.emit()

    def _on_opacity(self, v):
        self.opa_val.setText(f"{v}%")
        self.cfg["opacity"] = v / 100.0
        cm.save_config(self.cfg)
        self.config_changed.emit()

    def _on_top(self, on):
        self.cfg["always_on_top"] = on
        cm.save_config(self.cfg)
        self.config_changed.emit()

    def _on_through(self, on):
        self.cfg["click_through"] = on
        cm.save_config(self.cfg)
        self.config_changed.emit()
