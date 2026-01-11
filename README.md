
# Ding AI

> 智能直播录制与场控助手，支持 40+ 平台自动录制，内置 DeepSeek 驱动的 AI 实时分析。

[📺 查看演示视频](https://www.bilibili.com/video/BV1h96fBQEGd/?share_source=copy_web&vd_source=fed0463c5e2f2a5d15192f02da148180)

## ✨ 功能特性

### 核心录制

* **多平台支持**：覆盖 40+ 主流直播平台（抖音、TikTok、快手、虎牙、斗鱼、B站、小红书等）。
* **无人值守**：支持循环监控，检测到开播即自动录制。

### AI 场控助手 (GUI)

* **智能分析**：集成 **DeepSeek API**，对直播内容进行实时逻辑与风控分析。
* **语音转写**：内置 **讯飞语音识别**，实时将主播语音转为文字字幕。
* **合规审查**：自动检测违规词汇及高压逼单话术，输出诊断报告。
* **实时监控**：提供“实时字幕 + AI 分析报告”双面板可视界面。
* **热更新**：支持运行时动态调整 AI 指令（Prompt），无需重启程序。

## 🛠 技术栈

**核心依赖**

* **Python 3.11.9**
* **Flet**: 跨平台 GUI 框架
* **FFmpeg**: 音视频流处理
* **OpenAI SDK**: 对接 DeepSeek 大模型
* **WebSocket-Client**: 实时数据传输

## 📦 环境要求

* **操作系统**: macOS 26.1
* **Python**: 3.11.9 (推荐)
* **FFmpeg**: 必须安装并配置环境变量


## 🚀 快速开始

### 1. 获取项目

```bash
git clone https://github.com/fak111/dingai.git
cd dingai

```

### 2. 环境配置

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate

```

### 3. 安装依赖

```bash
pip install -r requirements.txt

```

### 4. 配置 FFmpeg

确保 `ffmpeg` 可执行文件位于系统路径中，或手动放置于项目目录：

* **macOS**: `cp /usr/local/bin/ffmpeg bin/ffmpeg` 并赋予执行权限 `chmod +x bin/ffmpeg`

### 5. 配置文件

请在代码或配置文件中填入必要的 API 密钥（DeepSeek API Key、讯飞 AppID 等），否则 AI 功能无法使用。

### 6. 运行程序

**GUI 模式 (AI 场控):**

```bash
python gui.py

```

**命令行录制模式:**

```bash
python main.py

```

## 📁 项目结构

```text
dingai/
├── bin/                 # 存放 FFmpeg 二进制文件
├── config/              # 配置目录
│   ├── config.ini       # 全局配置
│   └── URL_config.ini   # 直播间监控列表
├── src/                 # 核心源码 (爬虫、流处理、工具类)
├── downloads/           # 录制文件存储路径 (自动生成)
├── logs/                # 运行日志
├── gui.py               # AI 场控助手入口
├── main.py              # 录制程序入口
├── gui.spec             # PyInstaller 打包配置
└── requirements.txt     # Python 依赖清单

```

## 📦 打包与部署

### macOS 打包

```bash
# 使用脚本自动打包
./build.sh

# 或手动执行 PyInstaller
pyinstaller gui.spec --noconfirm

```

生成产物位于 `dist/` 目录。

**注意事项：**

1. **路径兼容**：代码已通过 `get_resource_path()` 处理打包后的资源路径问题。
2. **权限**：macOS 首次运行可能需要右键点击应用选择“打开”以绕过安全检查。
3. **架构**：Apple Silicon (M系列) 与 Intel 芯片需分别打包。

## ❓ 常见问题

**Q: 无法获取直播流？**

* 检查网络连接及代理设置。
* 确认 `config/URL_config.ini` 中的链接有效。
* 查看 `logs/streamget.log` 获取详细错误信息。

**Q: 录制启动失败？**

* 确保 FFmpeg 已正确安装且路径配置无误。

## 🤝 贡献指南

欢迎提交 Pull Request 或 Issue。提交代码前请确保：

1. 代码风格保持一致。
2. 新增功能经过测试。
3. 描述清晰简洁。

## 📝 许可证与致谢

本项目基于 MIT 许可证开源。

**致谢：**
核心录制功能基于 [DouyinLiveRecorder](https://github.com/ihmily/DouyinLiveRecorder) 开发，感谢原作者 [Hmily](https://github.com/ihmily) 的贡献。

---

*免责声明：本项目仅供技术学习与交流，请勿用于非法用途。使用本软件时请严格遵守各直播平台的服务条款。*
