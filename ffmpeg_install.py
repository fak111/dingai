# -*- coding: utf-8 -*-

"""
Author: Hmily
GitHub: https://github.com/ihmily
Copyright (c) 2024 by Hmily, All Rights Reserved.
"""

import os
import re
import shutil
import subprocess
import sys
import platform
import zipfile
from pathlib import Path
import requests
from tqdm import tqdm
from src.logger import logger

current_platform = platform.system()


def get_resource_path(relative_path):
    """
    获取资源的绝对路径。
    - 开发环境：返回当前脚本所在目录 + relative_path
    - 打包环境：返回 sys._MEIPASS (临时解压目录) + relative_path

    Args:
        relative_path: 相对于项目根目录的路径，如 "bin/ffmpeg"

    Returns:
        str: 资源的绝对路径
    """
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller 打包后的临时目录
        base_path = sys._MEIPASS
    else:
        # 开发环境：使用脚本所在目录
        base_path = os.path.split(os.path.realpath(sys.argv[0]))[0]

    return os.path.join(base_path, relative_path)


# 打包后 sys.argv[0] 指向临时目录，需要获取实际可执行文件所在目录
if getattr(sys, "frozen", False):
    # PyInstaller 打包后的路径
    execute_dir = os.path.dirname(sys.executable)
else:
    # 开发环境路径
    execute_dir = os.path.split(os.path.realpath(sys.argv[0]))[0]
current_env_path = os.environ.get("PATH")


def get_ffmpeg_path() -> str:
    """
    智能解析 ffmpeg 路径，按以下优先级查找：
    1. 资源路径中的 bin/ffmpeg (使用 get_resource_path，支持打包环境)
    2. execute_dir/bin/ffmpeg (打包后的标准位置)
    3. 脚本同级目录的 ffmpeg
    4. 系统 PATH 中的 ffmpeg (通过 shutil.which)
    5. 返回 ffmpeg 让系统查找

    Returns:
        str: ffmpeg 可执行文件的完整路径
    """
    # 方案1: 使用 get_resource_path 查找 bin/ffmpeg (支持打包环境)
    resource_ffmpeg = get_resource_path("bin/ffmpeg")
    if os.path.isfile(resource_ffmpeg) and os.access(resource_ffmpeg, os.X_OK):
        logger.debug(f"Found ffmpeg at resource path: {resource_ffmpeg}")
        return resource_ffmpeg

    # 方案2: execute_dir/bin/ffmpeg (打包后的标准位置)
    bin_ffmpeg = os.path.join(execute_dir, "bin", "ffmpeg")
    if os.path.isfile(bin_ffmpeg) and os.access(bin_ffmpeg, os.X_OK):
        logger.debug(f"Found ffmpeg at: {bin_ffmpeg}")
        return bin_ffmpeg

    # 方案3: 脚本同级目录的 ffmpeg (Windows/Linux)
    root_ffmpeg = os.path.join(execute_dir, "ffmpeg")
    if os.path.isfile(root_ffmpeg) and os.access(root_ffmpeg, os.X_OK):
        logger.debug(f"Found ffmpeg at: {root_ffmpeg}")
        return root_ffmpeg

    # 方案4: 脚本同级目录的 ffmpeg (macOS 可执行文件可能是包 bundle)
    root_ffmpeg_macos = os.path.join(execute_dir, "ffmpeg.exe")
    if os.path.isfile(root_ffmpeg_macos) and os.access(root_ffmpeg_macos, os.X_OK):
        logger.debug(f"Found ffmpeg at: {root_ffmpeg_macos}")
        return root_ffmpeg_macos

    # 方案5: 通过 shutil.which 在系统 PATH 中查找
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        logger.debug(f"Found ffmpeg in system PATH: {system_ffmpeg}")
        return system_ffmpeg

    # 方案6: 返回默认路径，让后续检查逻辑处理
    logger.debug(f"ffmpeg not found in local paths, using default: ffmpeg")
    return "ffmpeg"


def get_app_base_path() -> str:
    """
    获取应用程序的基准路径。
    打包后返回 Resources 目录，开发环境返回脚本目录。

    Returns:
        str: 应用程序基准路径
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # 打包后：Resources 目录
        # sys._MEIPASS 是临时解压目录，需要找到 Resources
        # macOS: executable -> MacOS -> ../Resources
        exe_dir = os.path.dirname(sys.executable)
        resources_dir = os.path.join(exe_dir, "..", "Resources")
        return os.path.normpath(resources_dir)
    else:
        # 开发环境：脚本目录
        return os.path.split(os.path.realpath(sys.argv[0]))[0]


# 获取实际可用的 ffmpeg 路径
ffmpeg_path = get_ffmpeg_path()


def unzip_file(
    zip_path: str | Path, extract_to: str | Path, delete: bool = True
) -> None:
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

    if delete and os.path.exists(zip_path):
        os.remove(zip_path)


def get_lanzou_download_link(url: str, password: str | None = None) -> str | None:
    try:
        headers = {
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Origin": "https://wweb.lanzouv.com",
            "Referer": "https://wweb.lanzouv.com/iXncv0dly6mh",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        }
        response = requests.get(url, headers=headers)
        sign = re.search("var skdklds = '(.*?)';", response.text).group(1)
        data = {
            "action": "downprocess",
            "sign": sign,
            "p": password,
            "kd": "1",
        }
        response = requests.post(
            "https://wweb.lanzouv.com/ajaxm.php", headers=headers, data=data
        )
        json_data = response.json()
        download_url = json_data["dom"] + "/file/" + json_data["url"]
        response = requests.get(download_url, headers=headers)
        return response.url
    except Exception as e:
        logger.error(f"Failed to obtain ffmpeg download address. {e}")


def install_ffmpeg_windows():
    try:
        logger.warning("ffmpeg is not installed.")
        logger.debug("Installing the latest version of ffmpeg for Windows...")
        ffmpeg_url = get_lanzou_download_link(
            "https://wweb.lanzouv.com/iHAc22ly3r3g", "eots"
        )
        if ffmpeg_url:
            full_file_name = "ffmpeg_latest_build_20250124.zip"
            version = "v20250124"
            zip_file_path = Path(execute_dir) / full_file_name
            if Path(zip_file_path).exists():
                logger.debug(
                    "ffmpeg installation file already exists, start install..."
                )
            else:
                response = requests.get(ffmpeg_url, stream=True)
                total_size = int(response.headers.get("Content-Length", 0))
                block_size = 1024

                with tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    ncols=100,
                    desc=f"Downloading ffmpeg ({version})",
                ) as t:
                    with open(zip_file_path, "wb") as f:
                        for data in response.iter_content(block_size):
                            t.update(len(data))
                            f.write(data)

            unzip_file(zip_file_path, execute_dir)
            os.environ["PATH"] = ffmpeg_path + os.pathsep + current_env_path
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
            if result.returncode == 0:
                logger.debug("ffmpeg installation was successful")
            else:
                logger.error(
                    "ffmpeg installation failed. Please manually install ffmpeg by yourself"
                )
            return True
        else:
            logger.error("Please manually install ffmpeg by yourself")
    except Exception as e:
        logger.error(f"type: {type(e).__name__}, ffmpeg installation failed {e}")


def install_ffmpeg_mac():
    logger.warning("ffmpeg is not installed.")
    logger.debug("Installing the stable version of ffmpeg for macOS...")
    try:
        result = subprocess.run(["brew", "install", "ffmpeg"], capture_output=True)
        if result.returncode == 0:
            logger.debug(
                "ffmpeg installation was successful. Restart for changes to take effect."
            )
            return True
        else:
            logger.error("ffmpeg installation failed")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install ffmpeg using Homebrew. {e}")
        logger.error(
            "Please install ffmpeg manually or check your Homebrew installation."
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


def install_ffmpeg_linux():
    is_RHS = True

    try:
        logger.warning("ffmpeg is not installed.")
        logger.debug("Trying to install the stable version of ffmpeg")
        result = subprocess.run(["yum", "-y", "update"], capture_output=True)
        if result.returncode != 0:
            logger.error("Failed to update package lists using yum.")
            return False

        result = subprocess.run(["yum", "install", "-y", "ffmpeg"], capture_output=True)
        if result.returncode == 0:
            logger.debug(
                "ffmpeg installation was successful using yum. Restart for changes to take effect."
            )
            return True
        logger.error(result.stderr.decode("utf-8").strip())
    except FileNotFoundError:
        logger.debug("yum command not found, trying to install using apt...")
        is_RHS = False
    except Exception as e:
        logger.error(f"An error occurred while trying to install ffmpeg using yum: {e}")

    if not is_RHS:
        try:
            logger.debug(
                "Trying to install the stable version of ffmpeg for Linux using apt..."
            )
            result = subprocess.run(["apt", "update"], capture_output=True)
            if result.returncode != 0:
                logger.error("Failed to update package lists using apt")
                return False

            result = subprocess.run(
                ["apt", "install", "-y", "ffmpeg"], capture_output=True
            )
            if result.returncode == 0:
                logger.debug(
                    "ffmpeg installation was successful using apt. Restart for changes to take effect."
                )
                return True
            else:
                logger.error(result.stderr.decode("utf-8").strip())
        except FileNotFoundError:
            logger.error(
                "apt command not found, unable to install ffmpeg. Please manually install ffmpeg by yourself"
            )
        except Exception as e:
            logger.error(
                f"An error occurred while trying to install ffmpeg using apt: {e}"
            )
    logger.error(
        "Manual installation of ffmpeg is required. Please manually install ffmpeg by yourself."
    )
    return False


def install_ffmpeg() -> bool:
    if current_platform == "Windows":
        return install_ffmpeg_windows()
    elif current_platform == "Linux":
        return install_ffmpeg_linux()
    elif current_platform == "Darwin":
        return install_ffmpeg_mac()
    else:
        logger.debug(
            f"ffmpeg auto installation is not supported on this platform: {current_platform}. "
            f"Please install ffmpeg manually."
        )
    return False


def ensure_ffmpeg_installed(func):
    def wrapper(*args, **kwargs):
        try:
            result = subprocess.run(
                [get_ffmpeg_path(), "-version"], capture_output=True
            )
            version = result.stdout.strip()
            if result.returncode == 0 and version:
                return func(*args, **kwargs)
        except FileNotFoundError:
            pass
        return False

    def wrapped_func(*args, **kwargs):
        if sys.version_info >= (3, 7):
            res = wrapper(*args, **kwargs)
        else:
            res = wrapper(*args, **kwargs)
        if not res:
            install_ffmpeg()
            res = wrapper(*args, **kwargs)

        if not res:
            raise RuntimeError("ffmpeg is not installed.")

        return func(*args, **kwargs)

    return wrapped_func


def check_ffmpeg_installed() -> bool:
    try:
        result = subprocess.run([get_ffmpeg_path(), "-version"], capture_output=True)
        version = result.stdout.strip()
        if result.returncode == 0 and version:
            return True
    except FileNotFoundError:
        pass
    except OSError as e:
        print(
            f"OSError occurred: {e}. ffmpeg may not be installed correctly or is not available in the system PATH."
        )
        print("Please delete the ffmpeg and try to download and install again.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return False


def check_ffmpeg() -> bool:
    if not check_ffmpeg_installed():
        return install_ffmpeg()
    return True
