# DeepSeek 桌宠

一个运行在 Windows 桌面上的 DeepSeek-R1 桌宠聊天助手，基于本地 Ollama 部署的 `deepseek-r1:8b` 模型。

无边框透明悬浮窗 + Q 版猫娘形象 + 情绪差分表情，随聊天内容自动切换心情；不占用浏览器，开机即陪伴。

## 功能特性

- 🐾 **桌宠形态**：无边框透明悬浮窗，支持鼠标穿透、置顶、透明度调节、大小缩放
- 🎭 **差分表情系统**：待机 / 思考 / 开心 / 伤心 / 惊讶 / 害羞 / 害怕 / 无语 八种状态，根据聊天内容与对话阶段自动切换（思考时气泡显示「少女思考中…」）
- 🖼️ **形象自定义**：内置多套形象，也可导入自己的图片（PNG 透明底 / GIF 动图），每个情绪状态可单独换图
- 💬 **流式对话**：基于 Ollama `/api/chat` 流式输出，打字机效果，自动剥离思考链
- 📜 **历史记录**：会话历史自动保存，支持查看与一键清理
- 🎨 **人设可调**：性格、语气、温度、top_p 等参数全部可配置
- 📌 **淡蓝白 UI**：简约清爽的设置面板

## 运行要求

- Windows 10 / 11
- [Ollama](https://ollama.com/download) 已安装并拉取模型：
  ```
  ollama pull deepseek-r1:8b
  ```
- 无需安装 Python（使用打包版 exe 时）

## 快速开始

### 方式一：直接运行 exe（推荐）

1. 从 [Releases](../../releases) 下载 `DeepSeekPet.exe`
2. 双击运行（首次启动稍慢，正在解压资源）
3. 确保 Ollama 已启动（`ollama serve` 或打开 Ollama 桌面端）

### 方式二：源码运行

```bash
pip install PySide6 pillow requests
python main.py
```

## 使用说明

- **单击**桌宠：对话
- **双击 / 右键**桌宠：打开设置面板
- 设置面板可调整：形象与差分图片、人设提示词、模型参数、窗口行为（置顶 / 穿透 / 透明 / 大小）、历史记录

## 配置与数据

- 配置文件：`data/config.json`（exe 同目录下自动生成）
- 聊天历史：`data/history.json`
- 删除 `data` 目录即可完全重置

## 技术栈

- Python 3.13 + PySide6（Qt6）
- Ollama REST API（流式聊天）
- Pillow（图片处理）

## 目录结构

```
deepseek-pet/
├── main.py            # 入口
├── pet_window.py      # 桌宠悬浮窗
├── main_ui.py         # 设置面板
├── chat_client.py     # Ollama 流式对话客户端
├── config_manager.py  # 配置管理
├── history_manager.py # 历史记录
└── assets/            # 形象与差分图片
```

## License

MIT
