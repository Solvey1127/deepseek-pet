# -*- coding: utf-8 -*-
"""DeepSeek 桌宠 · 入口"""
import sys, os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from pet_window import PetWindow
from main_ui import MainUI


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DeepSeek 桌宠")
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base, "assets", "app_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    pet = PetWindow()
    ui = MainUI()

    # 桌宠双击 / 右键 -> 打开设置面板
    pet.open_settings.connect(lambda: (ui.show(), ui.raise_(), ui.activateWindow()))
    # 面板改配置 -> 桌宠热重载
    ui.config_changed.connect(pet.reload_config)

    pet.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
