# DouyinLiveRecorder

> 可循环值守和多人录制的直播录制软件，支持 40+ 平台直播录制，内置 AI 场控助手

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/ihmily/DouyinLiveRecorder)

## 📋 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [开发指南](#开发指南)
- [打包部署](#打包部署)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)

## ✨ 功能特性

### 核心功能

- 🎥 **多平台支持**：支持 40+ 直播平台（抖音、TikTok、快手、虎牙、斗鱼、B站、小红书等）
- 🔄 **循环值守**：自动检测直播状态，开播自动录制
- 👥 **多人录制**：支持同时录制多个直播间
- 📹 **多格式支持**：TS、MKV、FLV、MP4、MP3、M4A
- 🎬 **质量选择**：原画、蓝光、超清、高清、标清、流畅
- ⏱️ **分段录制**：支持按时间自动分段
- 🔔 **消息推送**：支持钉钉、微信、TG、邮件等多种推送方式

### AI 场控助手（GUI 版本）

- 🧠 **智能分析**：基于 DeepSeek API 的实时内容分析
- 🎙️ **语音识别**：集成讯飞语音识别，实时转写主播语音
- 📊 **合规审查**：自动检测违规词、逼单动作等
- ⚡ **热更新**：支持运行时修改 AI 指令，无需重启
- 📈 **实时监控**：双面板显示，实时字幕 + AI 分析报告

## 🛠 技术栈

### 核心依赖

- **Python 3.10+**
- **FFmpeg**：音视频处理
- **Flet**：跨平台 GUI 框架
- **httpx**：异步 HTTP 客户端
- **websocket-client**：WebSocket 连接
- **PyExecJS**：JavaScript 执行引擎

### 主要库

```
flet>=0.80.1          # GUI 框架
httpx[http2]>=0.28.1  # HTTP 客户端
websocket-client==1.7.0  # WebSocket
openai                 # DeepSeek API 客户端
loguru>=0.7.3         # 日志系统
pycryptodome>=3.20.0  # 加密库
PyExecJS>=1.5.1       # JS 执行
```

## 📦 环境要求

### 系统要求

- **macOS**: 10.15 (Catalina) 或更高
- **Windows**: Windows 10 或更高
- **Linux**: Ubuntu 18.04+ / CentOS 7+

### 必需软件
Python
1. **Python 3.11.9**
   ```bash
   python --version  # 检查版本
   ```

2. **FFmpeg**
   - macOS: `brew install ffmpeg`
   - Linux: `apt install ffmpeg` 或 `yum install ffmpeg`
   - Windows: 下载并解压到 `bin/ffmpeg`

3. **Node.js** (可选，用于某些平台的 JS 签名)
   ```bash
   node --version
   ```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/ihmily/DouyinLiveRecorder.git
cd DouyinLiveRecorder
```

### 2. 创建虚拟环境

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

**macOS/Linux:**
```bash
# 如果系统已安装 FFmpeg，跳过此步
# 否则将 FFmpeg 二进制文件放到 bin/ 目录
cp /usr/local/bin/ffmpeg bin/ffmpeg
chmod +x bin/ffmpeg
```

**Windows:**
- 下载 FFmpeg 并解压
- 将 `ffmpeg.exe` 放到 `bin/` 目录

### 5. 运行程序

**命令行模式：**
```bash
python main.py
```

**GUI 模式（AI 场控助手）：**
```bash
python gui.py
# 或
python run_gui.py
```

### 6. 配置直播间

编辑 `config/URL_config.ini`，添加直播间 URL：

```
https://live.douyin.com/123456789
```

或通过 GUI 界面直接输入。

## 📁 项目结构

```
DouyinLiveRecorder/
├── bin/                    # FFmpeg 二进制文件
│   └── ffmpeg
├── config/                 # 配置文件
│   ├── config.ini         # 主配置文件
│   └── URL_config.ini     # 直播间 URL 配置
├── src/                    # 核心源码
│   ├── spider.py          # 爬虫模块（获取直播流）
│   ├── stream.py          # 流处理模块
│   ├── room.py            # 房间信息处理
│   ├── proxy.py           # 代理检测
│   ├── utils.py           # 工具函数
│   ├── logger.py          # 日志系统
│   ├── http_clients/      # HTTP 客户端
│   └── javascript/        # JS 签名脚本
├── i18n/                   # 国际化文件
├── downloads/              # 下载目录（运行时生成）
├── logs/                   # 日志目录（运行时生成）
├── main.py                # 命令行入口
├── gui.py                 # GUI 入口（AI 场控助手）
├── run_gui.py            # GUI 打包入口
├── ffmpeg_install.py      # FFmpeg 安装工具
├── msg_push.py           # 消息推送模块
├── gui.spec              # PyInstaller 打包配置
├── build.sh              # macOS/Linux 打包脚本
├── build.bat             # Windows 打包脚本
└── requirements.txt      # Python 依赖
```

## 💻 开发指南

### 开发环境设置

1. **安装开发依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置 IDE**
   - 推荐使用 VS Code 或 PyCharm
   - 设置 Python 解释器为虚拟环境
   - 安装 Python 扩展

3. **代码风格**
   - 遵循 PEP 8
   - 使用类型提示（Type Hints）
   - 函数和类添加文档字符串

### 核心模块说明

#### 1. `main.py` - 命令行录制核心

- `start_record()`: 启动录制流程
- `check_subprocess()`: 监控 FFmpeg 进程
- `direct_download_stream()`: 直接下载 FLV 流

#### 2. `gui.py` - GUI 界面和 AI 场控

- `LiveMonitor`: 监控逻辑封装类
- `deepseek_analysis_task()`: AI 分析任务
- `on_message()`: 讯飞语音识别回调
- `find_latest_file()`: 查找最新录制的音频文件

#### 3. `src/spider.py` - 平台爬虫

- `get_douyin_web_stream_data()`: 获取抖音直播流
- `get_tiktok_stream_data()`: 获取 TikTok 直播流
- 各平台的流获取函数

#### 4. `src/stream.py` - 流处理

- `get_douyin_stream_url()`: 解析抖音流 URL
- `get_stream_url()`: 通用流 URL 解析

### 添加新平台支持

1. 在 `src/spider.py` 中添加获取流数据的函数
2. 在 `src/stream.py` 中添加解析流 URL 的函数
3. 在 `main.py` 的 `start_record()` 中添加平台判断逻辑
4. 更新 `platforms` 字符串

示例：

```python
# src/spider.py
async def get_new_platform_stream_data(url, proxy_addr=None, cookies=""):
    # 实现获取流数据的逻辑
    pass

# src/stream.py
async def get_new_platform_stream_url(json_data, record_quality):
    # 实现解析流 URL 的逻辑
    pass

# main.py
elif record_url.find("newplatform.com/") > -1:
    platform = "新平台"
    with semaphore:
        json_data = asyncio.run(
            spider.get_new_platform_stream_data(
                url=record_url,
                proxy_addr=proxy_address,
                cookies=new_platform_cookie,
            )
        )
        port_info = asyncio.run(
            stream.get_new_platform_stream_url(json_data, record_quality)
        )
```

### 调试技巧

1. **启用详细日志**
   ```python
   # 在 main.py 中
   logger.setLevel(logging.DEBUG)
   ```

2. **测试单个平台**
   ```bash
   python main.py "https://live.douyin.com/123456789"
   ```

3. **GUI 调试模式**
   ```bash
   # 在终端运行，查看控制台输出
   python gui.py
   ```

4. **检查 FFmpeg 路径**
   ```python
   from ffmpeg_install import get_ffmpeg_path
   print(get_ffmpeg_path())
   ```

## 📦 打包部署

### macOS 打包

```bash
# 使用打包脚本
./build.sh

# 或手动打包
pyinstaller gui.spec --noconfirm
```

**输出：** `dist/DouyinLiveRecorder.app`

**注意事项：**
- 确保 `bin/ffmpeg` 存在
- 未签名的 App 需要用户右键"打开"绕过 Gatekeeper
- 可以添加代码签名（需要 Apple Developer 账号）

### Windows 打包

```bash
# 使用打包脚本
build.bat

# 或手动打包
pyinstaller gui.spec --noconfirm
```

**输出：** `dist/DouyinLiveRecorder/` 目录

### Linux 打包

```bash
./build.sh
```

**输出：** `dist/DouyinLiveRecorder/` 目录

### 打包配置说明

`gui.spec` 文件包含打包配置：

- **binaries**: FFmpeg 等二进制文件
- **datas**: 配置文件、资源文件
- **hiddenimports**: 隐式导入的模块

### 分发注意事项

1. **路径问题**：打包后使用 `get_resource_path()` 和 `get_user_data_dir()` 处理路径
2. **FFmpeg 依赖**：确保 FFmpeg 及其依赖库都包含
3. **架构兼容**：Intel/Apple Silicon 可能需要分别打包
4. **系统权限**：首次运行需要网络和文件系统权限

## ⚙️ 配置说明

### 主配置文件 (`config/config.ini`)

```ini
[录制设置]
直播保存路径(不填则默认) =                    # 留空使用默认路径
保存文件夹是否以作者区分 = 是
保存文件夹是否以时间区分 = 否
视频保存格式ts|mkv|flv|mp4|mp3音频|m4a音频 = mp3音频
原画|超清|高清|标清|流畅 = 流畅
是否使用代理ip(是/否) = 是
代理地址 = http://proxy.example.com:8080
同一时间访问网络的线程数 = 3
循环时间(秒) = 120

[推送配置]
直播状态推送渠道 = 钉钉,微信
钉钉推送接口链接 = https://oapi.dingtalk.com/robot/send?access_token=xxx
微信推送接口链接 = https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
```

### URL 配置文件 (`config/URL_config.ini`)

```
https://live.douyin.com/123456789
https://live.douyin.com/987654321,主播: 主播名称
原画,https://live.douyin.com/111222333
```

格式：`[画质],URL,主播: 名称`（画质和主播名可选）

### GUI 配置

GUI 版本支持运行时配置：

- **分析间隔**：AI 分析频率（秒）
- **回顾窗口**：分析最近 N 分钟的内容
- **场控指令**：DeepSeek 系统提示词（支持热更新）

## 🔧 常见问题

### 1. FFmpeg 找不到

**问题：** `ffmpeg: command not found`

**解决：**
```bash
# 检查 FFmpeg 路径
python -c "from ffmpeg_install import get_ffmpeg_path; print(get_ffmpeg_path())"

# 确保 bin/ffmpeg 存在且可执行
chmod +x bin/ffmpeg
```

### 2. 打包后找不到文件

**问题：** 打包后路径错误

**解决：**
- 使用 `get_resource_path()` 获取资源文件路径
- 使用 `get_user_data_dir()` 获取用户数据目录
- 检查 `gui.spec` 中的 `datas` 配置

### 3. GUI 无法启动

**问题：** Flet 相关错误

**解决：**
```bash
# 重新安装 Flet
pip uninstall flet
pip install flet>=0.80.1

# 检查 Python 版本
python --version  # 需要 3.10+
```

### 4. 录制文件找不到

**问题：** GUI 在 `~/Documents/LiveMonitor` 查找，但文件在 `~/Documents/DouyinLiveRecorder`

**解决：**
- 确保 `gui.py` 和 `main.py` 使用相同的用户数据目录
- 检查 `get_user_data_dir()` 函数返回的路径

### 5. 网络连接失败

**问题：** 无法获取直播流

**解决：**
- 检查网络连接
- 配置代理（如需要）
- 检查 Cookie 是否有效
- 查看日志文件 `logs/streamget.log`

### 6. macOS 安全限制

**问题：** "无法打开，因为来自身份不明的开发者"

**解决：**
```bash
# 方法1：移除隔离属性
xattr -cr dist/DouyinLiveRecorder.app

# 方法2：右键打开
右键点击 App → 选择"打开"
```

## 🤝 贡献指南

### 提交 Issue

- 使用中文或英文描述问题
- 提供复现步骤
- 附上错误日志和系统信息

### 提交 Pull Request

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 遵循 PEP 8
- 添加类型提示
- 编写文档字符串
- 添加必要的注释

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- 原作者：[Hmily](https://github.com/ihmily)
- 项目地址：https://github.com/ihmily/DouyinLiveRecorder

## 📞 联系方式

- GitHub Issues: https://github.com/ihmily/DouyinLiveRecorder/issues
- 项目主页: https://github.com/ihmily/DouyinLiveRecorder

---

**注意：** 本项目仅供学习交流使用，请遵守各平台的使用条款和相关法律法规。
