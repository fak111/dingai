import flet as ft
import websocket
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime, timedelta
from time import mktime
import _thread as thread
import subprocess
import os
import threading
import sys
from openai import OpenAI


# ================= 路径处理函数 =================
def get_resource_path(relative_path):
    """
    获取资源的绝对路径。
    - 开发环境：返回当前脚本所在目录 + relative_path
    - 打包环境：返回 sys._MEIPASS (临时解压目录) + relative_path

    Args:
        relative_path: 相对于项目根目录的路径，如 "bin/ffmpeg" 或 "config/config.ini"

    Returns:
        str: 资源的绝对路径
    """
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller 打包后的临时目录
        base_path = sys._MEIPASS
    else:
        # 开发环境：使用脚本所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


def get_user_data_dir():
    """
    获取用户数据目录（用于存储下载文件、日志等可写数据）。
    打包后的 App 内部可能是只读的，所以数据存到用户文档目录。
    注意：必须与 main.py 中的路径保持一致！

    Returns:
        str: 用户数据目录路径，如 ~/Documents/DouyinLiveRecorder
    """
    user_docs = os.path.expanduser("~/Documents")
    app_data_dir = os.path.join(user_docs, "DouyinLiveRecorder")

    # 确保目录存在
    if not os.path.exists(app_data_dir):
        try:
            os.makedirs(app_data_dir, exist_ok=True)
        except Exception as e:
            print(f"⚠️  无法创建用户数据目录 {app_data_dir}: {e}")
            # 回退到当前目录
            app_data_dir = os.path.dirname(os.path.abspath(__file__))

    return app_data_dir


# --- 延迟导入 main 模块，避免重复初始化 ---
_main_module_cache = None
_get_ffmpeg_path_cache = None


def get_main_module():
    """延迟导入 main 模块，只在需要时导入，避免重复初始化"""
    global _main_module_cache, _get_ffmpeg_path_cache
    if _main_module_cache is None:
        try:
            import main as main_module
            from ffmpeg_install import get_ffmpeg_path

            _main_module_cache = main_module
            _get_ffmpeg_path_cache = get_ffmpeg_path
            print("✅ main 模块加载成功")
        except ImportError as e:
            print(f"❌ 严重错误: 无法导入 main 模块。原因: {e}")
            print("请检查 main.py 是否在同一目录，或其依赖是否缺失。")
            _main_module_cache = False  # 使用 False 表示加载失败
            _get_ffmpeg_path_cache = lambda: "ffmpeg"  # 默认回退
        except Exception as e:
            print(f"❌ main 模块加载时发生未知错误: {e}")
            _main_module_cache = False
            _get_ffmpeg_path_cache = lambda: "ffmpeg"  # 默认回退
    return _main_module_cache if _main_module_cache else None


def get_ffmpeg_path():
    """获取 ffmpeg 路径"""
    global _get_ffmpeg_path_cache
    if _get_ffmpeg_path_cache is None:
        get_main_module()  # 触发导入
    return _get_ffmpeg_path_cache() if _get_ffmpeg_path_cache else "ffmpeg"


# ================= 原有配置常量 =================
APPID = "x"
API_KEY = "xx"
API_SECRET = "xx"

DEEPSEEK_API_KEY = "sk-x"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 使用用户文档目录存储下载文件（打包后 App 内部可能是只读的）
USER_DATA_DIR = get_user_data_dir()
DOWNLOAD_DIR = os.path.join(USER_DATA_DIR, "downloads", "抖音直播")
# 确保下载目录存在
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
PYTHON_ENV_PATH = sys.executable

# ================= 业务逻辑封装类 =================


class LiveMonitor:
    def __init__(self, update_log_callback, update_ai_callback):
        self.stop_flag = True
        self.transcript_buffer = []
        self.buffer_lock = threading.Lock()
        self.log_callback = update_log_callback
        self.ai_callback = update_ai_callback
        self.rec_thread = None
        self.g_file_offset = 0

        # 用户配置参数
        self.video_url = ""
        self.analysis_interval = 60
        self.lookback_window = 5
        self.system_prompt = ""

    def log(self, text, level="INFO"):
        """统一的日志输出，支持不同级别"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {text}"
        print(log_msg)
        self.log_callback(f"[系统] {log_msg}")

    def transcript_log(self, text):
        self.log_callback(text)

    # --- 动态更新参数的方法 ---
    def update_config(self, prompt, interval, window):
        """允许在运行时更新部分配置"""
        self.system_prompt = prompt
        # interval 和 window 涉及到计时器逻辑，暂时只更新 prompt 比较安全
        # 如果需要更新 interval，需要更复杂的线程同步，这里主要满足 prompt 调优
        print(f"🔄 配置已热更新: Prompt长度={len(prompt)}")

    # --- 讯飞鉴权 ---
    def create_url(self):
        url = "wss://ws-api.xfyun.cn/v2/iat"
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        signature_sha = hmac.new(
            API_SECRET.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding="utf-8")
        authorization_origin = (
            'api_key="%s", algorithm="%s", headers="%s", signature="%s"'
            % (API_KEY, "hmac-sha256", "host date request-line", signature_sha)
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(
            encoding="utf-8"
        )
        v = {"authorization": authorization, "date": date, "host": "ws-api.xfyun.cn"}
        return url + "?" + urlencode(v)

    # --- DeepSeek 分析线程 ---
    def deepseek_analysis_task(self):
        self.log(f"🧠 AI场控启动：每 {self.analysis_interval} 秒分析一次。", "INFO")
        self.log(f"🔑 DeepSeek API: {DEEPSEEK_BASE_URL}", "DEBUG")
        try:
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
            self.log("✅ DeepSeek 客户端初始化成功", "DEBUG")
        except Exception as e:
            self.log(f"❌ DeepSeek 客户端初始化失败: {e}", "ERROR")
            return

        cycle_count = 0
        while not self.stop_flag:
            # 倒计时循环，提高响应速度
            for _ in range(self.analysis_interval):
                if self.stop_flag:
                    break
                time.sleep(1)

            if self.stop_flag:
                break

            cycle_count += 1
            try:
                now = datetime.now()
                start_time = now - timedelta(minutes=self.lookback_window)
                self.log(
                    f"🔄 第 {cycle_count} 次分析周期开始 (回顾窗口: {self.lookback_window} 分钟)",
                    "DEBUG",
                )

                lines_to_analyze = []
                with self.buffer_lock:
                    valid_data = [
                        item
                        for item in self.transcript_buffer
                        if item["time"] > start_time
                    ]
                    lines_to_analyze = [item["text"] for item in valid_data]
                    self.log(
                        f"📊 缓冲区状态: 总记录={len(self.transcript_buffer)}, 有效记录={len(valid_data)}",
                        "DEBUG",
                    )

                if not lines_to_analyze:
                    self.log("⚠️  没有可分析的内容，跳过本次分析", "WARNING")
                    continue

                full_text = "".join(lines_to_analyze)
                if len(full_text) < 10:
                    self.log(f"⚠️  文本太短 ({len(full_text)} 字)，跳过分析", "WARNING")
                    continue

                self.log(f"🤔 AI正在分析... ({len(full_text)} 字)", "INFO")
                self.log(f"📝 分析文本预览: {full_text[:50]}...", "DEBUG")

                # ⚠️ 关键点：每次循环都读取最新的 self.system_prompt
                # 这样就实现了运行时修改 Prompt
                try:
                    self.log("📤 发送请求到 DeepSeek API...", "DEBUG")
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": self.system_prompt},
                            {
                                "role": "user",
                                "content": f"【当前时间】{now.strftime('%H:%M:%S')}\n【主播语音】{full_text}",
                            },
                        ],
                        stream=False,
                    )
                    content = response.choices[0].message.content
                    timestamp_str = now.strftime("%H:%M:%S")

                    self.log(f"✅ AI分析完成，响应长度: {len(content)} 字", "DEBUG")
                    report = f"🕒 {timestamp_str}\n{content}\n{'-' * 30}\n"
                    self.ai_callback(report)
                except Exception as api_error:
                    self.log(f"❌ DeepSeek API 调用失败: {api_error}", "ERROR")
                    import traceback

                    self.log(f"❌ API错误详情: {traceback.format_exc()}", "ERROR")

            except Exception as e:
                self.log(f"❌ AI分析失败: {e}", "ERROR")
                import traceback

                self.log(f"❌ 错误详情: {traceback.format_exc()}", "ERROR")

    # --- 讯飞回调 ---
    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            code = data.get("code", -1)
            if code != 0:
                error_msg = data.get("message", "未知错误")
                self.log(
                    f"⚠️  讯飞返回错误: code={code}, message={error_msg}", "WARNING"
                )
                return
            if "data" in data and data["data"].get("result") is not None:
                result_data = data["data"]["result"]["ws"]
                text_parts = []
                for i in result_data:
                    for w in i.get("cw", []):
                        text_parts.append(w.get("w", ""))
                if text_parts:
                    text = "".join(text_parts)
                    now = datetime.now()
                    timestamp_str = now.strftime("%H:%M:%S")

                    display_text = f"[{timestamp_str}] 🎙️ {text}"
                    self.transcript_log(display_text)
                    self.log(f"🎙️ 识别到文本: {text}", "DEBUG")

                    with self.buffer_lock:
                        self.transcript_buffer.append({"time": now, "text": text})
                        if len(self.transcript_buffer) > 5000:
                            self.transcript_buffer.pop(0)
                            self.log("⚠️  字幕缓冲区已满，删除最旧记录", "DEBUG")
        except Exception as e:
            self.log(f"❌ 处理讯飞消息错误: {e}", "ERROR")
            import traceback

            self.log(f"❌ 错误详情: {traceback.format_exc()}", "ERROR")

    # --- 文件流处理 ---
    def file_feeder(self, file_path, process):
        self.log(f"📂 文件流处理启动: {file_path}", "DEBUG")
        wait_count = 0
        while not os.path.exists(file_path):
            if self.stop_flag:
                self.log("🛑 文件流处理被停止", "WARNING")
                return
            wait_count += 1
            if wait_count % 5 == 0:
                self.log(
                    f"⏳ 等待文件出现: {file_path} (已等待 {wait_count} 秒)", "DEBUG"
                )
            time.sleep(1)

        try:
            self.log(f"📖 打开文件: {file_path}, 偏移量: {self.g_file_offset}", "DEBUG")
            f = open(file_path, "rb")
            f.seek(self.g_file_offset)
            read_count = 0
            while not self.stop_flag:
                data = f.read(4096)
                if not data:
                    if process.poll() is not None:
                        self.log("⚠️  FFmpeg 进程已结束", "WARNING")
                        break
                    time.sleep(0.1)
                    f.seek(f.tell())
                    continue
                try:
                    process.stdin.write(data)
                    process.stdin.flush()
                    self.g_file_offset += len(data)
                    read_count += 1
                    if read_count % 100 == 0:  # 每读取约400KB打印一次
                        self.log(
                            f"📊 已读取: {self.g_file_offset / 1024 / 1024:.2f} MB",
                            "DEBUG",
                        )
                except Exception as e:
                    self.log(f"❌ 写入管道失败: {e}", "ERROR")
                    break
            f.close()
            self.log(
                f"✅ 文件流处理完成，总读取: {self.g_file_offset / 1024 / 1024:.2f} MB",
                "INFO",
            )
        except Exception as e:
            self.log(f"❌ 文件流处理错误: {e}", "ERROR")
            import traceback

            self.log(f"❌ 错误详情: {traceback.format_exc()}", "ERROR")

    def on_open(self, ws, video_file_path):
        def run():
            self.log(
                f"🔌 WebSocket 连接已建立，准备处理音频: {video_file_path}", "INFO"
            )
            ffmpeg_path = get_ffmpeg_path()
            self.log(f"🎬 使用 FFmpeg: {ffmpeg_path}", "DEBUG")
            cmd = [
                ffmpeg_path,
                "-err_detect",
                "ignore_err",
                "-i",
                "pipe:0",
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-f",
                "s16le",
                "-loglevel",
                "error",
                "pipe:1",
            ]
            self.log(f"📝 FFmpeg 命令: {' '.join(cmd)}", "DEBUG")
            try:
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=80000,
                )
                self.log(f"✅ FFmpeg 进程已启动，PID: {process.pid}", "DEBUG")
            except Exception as e:
                self.log(f"❌ FFmpeg 启动失败: {e}", "ERROR")
                return

            feeder = threading.Thread(
                target=self.file_feeder, args=(video_file_path, process)
            )
            feeder.daemon = True
            feeder.start()
            self.log("✅ 文件流处理线程已启动", "DEBUG")

            frameSize = 8000
            send_count = 0
            try:
                while not self.stop_flag:
                    buf = process.stdout.read(frameSize)
                    if not buf:
                        if process.poll() is not None:
                            self.log("⚠️  FFmpeg 进程已退出，关闭 WebSocket", "WARNING")
                            ws.close()
                            break
                        time.sleep(0.01)
                        continue

                    try:
                        ws.send(
                            json.dumps(
                                {
                                    "common": {"app_id": APPID},
                                    "business": {
                                        "domain": "iat",
                                        "language": "zh_cn",
                                        "accent": "mandarin",
                                        "vinfo": 1,
                                        "vad_eos": 60000,
                                    },
                                    "data": {
                                        "status": 1,
                                        "format": "audio/L16;rate=16000",
                                        "audio": str(base64.b64encode(buf), "utf-8"),
                                        "encoding": "raw",
                                    },
                                }
                            )
                        )
                        send_count += 1
                        if send_count % 100 == 0:  # 每发送100帧打印一次
                            self.log(
                                f"📤 已发送 {send_count} 帧音频数据到讯飞", "DEBUG"
                            )
                    except Exception as e:
                        self.log(f"❌ WebSocket 发送失败: {e}", "ERROR")
                        break
                    time.sleep(0.04)
            except Exception as e:
                self.log(f"❌ 音频处理循环错误: {e}", "ERROR")
                import traceback

                self.log(f"❌ 错误详情: {traceback.format_exc()}", "ERROR")
            finally:
                try:
                    self.log("🛑 正在终止 FFmpeg 进程...", "DEBUG")
                    process.terminate()
                    process.wait(timeout=2)
                except Exception as e:
                    self.log(f"⚠️  终止 FFmpeg 时出错: {e}", "WARNING")
                try:
                    ws.close()
                    self.log("🔌 WebSocket 已关闭", "DEBUG")
                except:
                    pass

        thread.start_new_thread(run, ())

    # --- 启动录制 ---
    def start_recording_process(self):
        main_module = get_main_module()  # 延迟导入
        if main_module is None:
            self.log("❌ 无法录制: main 模块未加载，请检查后台日志。", "ERROR")
            return

        self.log(f"🎬 启动录制: {self.video_url}", "INFO")
        try:
            # 构造 url_data 元组: (record_quality_zh, record_url, anchor_name)
            # 使用默认质量 "原画"，anchor_name 为空字符串
            url_data = ("原画", self.video_url, "")
            self.log(f"📋 录制参数: url_data={url_data}, count=-1", "DEBUG")
            # 在独立线程中启动录制
            self.rec_thread = threading.Thread(
                target=main_module.start_record, args=(url_data, -1), daemon=True
            )
            self.rec_thread.start()
            self.log(f"✅ 录制线程已启动，线程ID: {self.rec_thread.ident}", "DEBUG")
        except Exception as e:
            import traceback

            self.log(f"❌ 录制启动失败: {e}", "ERROR")
            self.log(f"❌ 错误详情: {traceback.format_exc()}", "ERROR")

    def find_latest_file(self, start_ts):
        self.log(f"⏳ 等待音频文件生成... (搜索目录: {DOWNLOAD_DIR})", "INFO")
        self.log(
            f"📂 启动时间戳: {start_ts} ({datetime.fromtimestamp(start_ts)})", "DEBUG"
        )

        if not os.path.exists(DOWNLOAD_DIR):
            self.log(f"📁 创建下载目录: {DOWNLOAD_DIR}", "DEBUG")
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        else:
            # 列出目录中的所有文件，方便调试
            try:
                all_files = []
                for root, dirs, files in os.walk(DOWNLOAD_DIR):
                    for f in files:
                        full = os.path.join(root, f)
                        all_files.append(full)
                if all_files:
                    self.log(f"📋 目录中现有文件数: {len(all_files)}", "DEBUG")
                    for f in all_files[:5]:  # 只显示前5个
                        self.log(f"   - {os.path.basename(f)}", "DEBUG")
                else:
                    self.log(f"📋 目录为空，等待文件生成...", "DEBUG")
            except Exception as e:
                self.log(f"⚠️  列出目录文件时出错: {e}", "WARNING")

        check_count = 0
        while not self.stop_flag:
            try:
                check_count += 1
                if check_count % 10 == 0:  # 每20秒打印一次
                    self.log(
                        f"🔍 正在搜索音频文件... (已检查 {check_count * 2} 秒)", "DEBUG"
                    )

                for dp, dn, filenames in os.walk(DOWNLOAD_DIR):
                    for f in filenames:
                        if f.endswith(".mp3"):
                            full = os.path.join(dp, f)
                            file_mtime = os.path.getmtime(full)
                            if file_mtime > start_ts:
                                self.log(
                                    f"✅ 找到新文件: {f} (修改时间: {datetime.fromtimestamp(file_mtime)})",
                                    "INFO",
                                )
                                return full
                            else:
                                if check_count <= 3:  # 前几次检查时打印详细信息
                                    self.log(
                                        f"⏭️  跳过旧文件: {f} (修改时间: {datetime.fromtimestamp(file_mtime)}, 启动时间: {datetime.fromtimestamp(start_ts)})",
                                        "DEBUG",
                                    )
            except Exception as e:
                self.log(f"⚠️  搜索文件时出错: {e}", "WARNING")
                import traceback

                self.log(f"❌ 错误详情: {traceback.format_exc()}", "ERROR")
            time.sleep(2)

        self.log("❌ 停止标志已设置，退出文件搜索", "WARNING")
        return None

    # --- 主运行入口 ---
    def run(self):
        self.log("🚀 开始运行监控流程", "INFO")
        self.stop_flag = False
        self.transcript_buffer = []
        self.g_file_offset = 0
        start_ts = time.time()
        self.log(
            f"⏰ 启动时间戳: {start_ts} ({datetime.fromtimestamp(start_ts)})", "DEBUG"
        )

        # 1. 启动AI线程
        self.log("🧠 启动 AI 分析线程...", "DEBUG")
        ai_thread = threading.Thread(target=self.deepseek_analysis_task)
        ai_thread.daemon = True
        ai_thread.start()
        self.log(f"✅ AI 线程已启动，线程ID: {ai_thread.ident}", "DEBUG")

        # 2. 启动录制进程
        self.log("🎬 启动录制进程...", "DEBUG")
        self.start_recording_process()
        if not self.rec_thread:
            self.log("❌ 录制线程未创建，退出", "ERROR")
            return
        self.log("⏳ 等待录制线程启动...", "DEBUG")
        time.sleep(2)  # 给录制线程一些启动时间

        # 3. 找文件
        self.log("🔍 开始查找音频文件...", "DEBUG")
        video_path = self.find_latest_file(start_ts)
        if not video_path:
            self.log("❌ 未找到音频文件，退出", "ERROR")
            return
        self.log(f"✅ 捕获文件: {os.path.basename(video_path)}", "INFO")
        file_size = os.path.getsize(video_path) / 1024 / 1024
        self.log(f"📊 文件大小: {file_size:.2f} MB", "DEBUG")

        # 4. 循环连接
        reconnect_count = 0
        while not self.stop_flag:
            reconnect_count += 1
            self.log(f"🔌 建立 WebSocket 连接 (第 {reconnect_count} 次)...", "DEBUG")
            try:
                wsUrl = self.create_url()
                self.log(f"🌐 WebSocket URL: {wsUrl[:50]}...", "DEBUG")
                ws = websocket.WebSocketApp(
                    wsUrl,
                    on_message=self.on_message,
                    on_error=lambda ws, err: self.log(
                        f"❌ WebSocket 错误: {err}", "ERROR"
                    ),
                    on_close=lambda ws, a, b: self.log(
                        f"🔌 WebSocket 已关闭: code={a}, reason={b}", "WARNING"
                    ),
                )
                ws.on_open = lambda ws: self.on_open(ws, video_path)
                self.log("🔄 开始运行 WebSocket...", "DEBUG")
                ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
                if not self.stop_flag:
                    self.log("⚠️  WebSocket 连接断开，1秒后重连...", "WARNING")
                time.sleep(1)
            except Exception as e:
                self.log(f"❌ WebSocket 连接异常: {e}", "ERROR")
                import traceback

                self.log(f"❌ 错误详情: {traceback.format_exc()}", "ERROR")
                if not self.stop_flag:
                    time.sleep(2)  # 出错后等待更长时间再重连

    def stop(self):
        self.log("🛑 正在停止系统...", "INFO")
        self.stop_flag = True
        # 设置全局标志来停止录制
        main_module = get_main_module()  # 延迟导入
        if main_module:
            main_module.exit_recording = True
            self.log("✅ 已设置录制退出标志", "DEBUG")
        # 等待录制线程结束（可选，给一个短暂的超时）
        if self.rec_thread and self.rec_thread.is_alive():
            self.log("⏳ 等待录制线程结束...", "DEBUG")
            self.rec_thread.join(timeout=2.0)
            if self.rec_thread.is_alive():
                self.log("⚠️  录制线程未在2秒内结束", "WARNING")
            else:
                self.log("✅ 录制线程已结束", "DEBUG")
        self.rec_thread = None
        self.log("🛑 系统已停止", "INFO")


# ================= Flet UI 主程序 =================


def main(page: ft.Page):
    page.title = "全能场控助手 (DeepSeek + 讯飞)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1300
    page.window_height = 850
    page.padding = 0  # 移除默认内边距，以便自定义布局

    monitor_thread = None
    monitor_logic = None

    # --- UI 状态回调 ---
    def update_log_ui(text):
        lv_transcript.controls.append(ft.Text(text, size=13, font_family="Consolas"))
        page.update()

    def update_ai_ui(text):
        container = ft.Container(
            content=ft.Markdown(text, selectable=True),  # 使用Markdown支持更好看的排版
            bgcolor=ft.Colors.BLUE_GREY_50,
            padding=15,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
        )
        lv_ai_report.controls.append(container)
        page.update()

    # --- 事件处理 ---
    def on_config_change(e):
        """当用户修改输入框时，实时更新后台逻辑（如果正在运行）"""
        if monitor_logic:
            monitor_logic.update_config(
                prompt=txt_prompt.value,
                interval=int(txt_interval.value),
                window=int(txt_window.value),
            )
            # 给个小提示（可选）
            page.snack_bar = ft.SnackBar(
                ft.Text("配置已热更新，下个周期生效"), duration=1000
            )
            page.snack_bar.open = True
            page.update()

    def start_click(e):
        nonlocal monitor_thread, monitor_logic
        if monitor_thread and monitor_thread.is_alive():
            return

        btn_start.disabled = True
        btn_stop.disabled = False
        status_text.value = "🟢 运行中 - 正在监听..."
        status_text.color = ft.Colors.GREEN

        # 禁用不需要热更新的基础配置
        txt_url.disabled = True
        page.update()

        monitor_logic = LiveMonitor(update_log_ui, update_ai_ui)
        monitor_logic.video_url = txt_url.value
        monitor_logic.analysis_interval = int(txt_interval.value)
        monitor_logic.lookback_window = int(txt_window.value)
        monitor_logic.system_prompt = txt_prompt.value

        monitor_thread = threading.Thread(target=monitor_logic.run)
        monitor_thread.daemon = True
        monitor_thread.start()

    def stop_click(e):
        nonlocal monitor_logic
        if monitor_logic:
            monitor_logic.stop()

        btn_start.disabled = False
        btn_stop.disabled = True
        status_text.value = "⚫ 已停止"
        status_text.color = ft.Colors.GREY

        # 恢复基础配置编辑
        txt_url.disabled = False
        page.update()

    # --- 组件定义 ---

    # 1. 侧边栏（配置区）
    txt_url = ft.TextField(
        label="直播间 URL",
        value="https://live.douyin.com/295178185857",
        text_size=12,
        border_color=ft.Colors.BLUE_400,
    )

    txt_interval = ft.TextField(
        label="分析间隔(秒)",
        value="60",
        width=100,
        text_size=12,
        on_change=on_config_change,
    )
    txt_window = ft.TextField(label="回顾窗口(分)", value="5", width=100, text_size=12)

    txt_prompt = ft.TextField(
        label="DeepSeek 场控指令 (支持热修改)",
        multiline=True,
        min_lines=10,
        max_lines=15,
        text_size=13,
        value="""你是一个专业的直播间场控总监。
请根据主播语音内容，进行严格的合规与逻辑审查。
检查重点：
1. 是否包含违规词（如：第一、最、国家级、绝对）。
2. 是否有逼单动作（如：库存不多、马上截单）。
3. 逻辑是否通顺。
请输出简短的诊断报告，指出问题和亮点。""",
        on_change=on_config_change,  # 绑定修改事件
    )

    btn_start = ft.FilledButton(
        "启动监控",
        icon=ft.Icons.PLAY_ARROW,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE, padding=20
        ),
        on_click=start_click,
        height=42,
    )

    btn_stop = ft.FilledButton(
        "停止运行",
        icon=ft.Icons.STOP,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE, padding=20
        ),
        on_click=stop_click,
        disabled=True,
        height=42,
    )

    status_text = ft.Text("等待启动", size=12)

    sidebar = ft.Container(
        width=280,
        bgcolor=ft.Colors.GREY_50,
        padding=15,
        border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.GREY_200)),
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text("⚙️ 场控配置", size=18, weight=ft.FontWeight.BOLD),
                txt_url,
                ft.Row(
                    [txt_interval, txt_window],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text("场控指令", size=11, color=ft.Colors.GREY_600),
                txt_prompt,
                ft.Column([btn_start, btn_stop], spacing=8),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.CIRCLE,
                                size=8,
                                color=ft.Colors.GREEN_400
                                if btn_start.disabled
                                else ft.Colors.GREY_400,
                            ),
                            status_text,
                        ],
                        spacing=5,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    margin=ft.margin.only(top=10),
                ),
            ],
        ),
    )

    # 2. 内容区（监控面板）
    lv_transcript = ft.ListView(expand=True, spacing=4, auto_scroll=True)
    lv_ai_report = ft.ListView(expand=True, spacing=8, auto_scroll=True)

    def create_panel_header(
        icon: str, title: str, color: str, bg_color: str
    ) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(icon, size=14),
                    ft.Text(title, size=13, weight=ft.FontWeight.W_500, color=color),
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=bg_color,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=6,
        )

    content_area = ft.Container(
        expand=True,
        padding=15,
        content=ft.Row(
            [
                ft.Container(
                    expand=1,
                    content=ft.Column(
                        [
                            create_panel_header(
                                "🎙️", "实时字幕", ft.Colors.BLUE_700, ft.Colors.BLUE_50
                            ),
                            ft.Container(
                                content=lv_transcript,
                                border=ft.border.all(1, ft.Colors.GREY_200),
                                border_radius=8,
                                padding=10,
                                expand=True,
                                bgcolor=ft.Colors.WHITE,
                            ),
                        ],
                        spacing=8,
                        expand=True,
                    ),
                ),
                ft.Container(width=12),
                ft.Container(
                    expand=1,
                    content=ft.Column(
                        [
                            create_panel_header(
                                "🧠",
                                "AI 分析",
                                ft.Colors.PURPLE_700,
                                ft.Colors.PURPLE_50,
                            ),
                            ft.Container(
                                content=lv_ai_report,
                                border=ft.border.all(1, ft.Colors.GREY_200),
                                border_radius=8,
                                padding=10,
                                expand=True,
                                bgcolor=ft.Colors.WHITE,
                            ),
                        ],
                        spacing=8,
                        expand=True,
                    ),
                ),
            ],
            expand=True,
        ),
    )

    # 主布局
    page.add(ft.Row([sidebar, content_area], expand=True, spacing=0))

    # 窗口关闭清理
    def window_event(e):
        if e.data == "close":
            if monitor_logic:
                monitor_logic.stop()
            page.window_destroy()

    page.window_prevent_close = True
    page.on_window_event = window_event


def start_gui():
    """GUI 入口函数 - 用于打包后的启动"""
    ft.run(main)


# 只在直接运行时才执行，避免导入时自动启动
if __name__ == "__main__":
    start_gui()
