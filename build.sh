#!/bin/bash
# DouyinLiveRecorder 打包脚本
# 用法: ./build.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}🚀 开始打包 DouyinLiveRecorder...${NC}"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 未找到虚拟环境，请先创建虚拟环境: python -m venv venv${NC}"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
echo -e "${YELLOW}📦 检查依赖...${NC}"
pip install -q -r requirements.txt

# 检查 ffmpeg
if [ ! -f "bin/ffmpeg" ]; then
    echo -e "${YELLOW}⚠️  未找到 bin/ffmpeg，请确保 ffmpeg 已放置在 bin/ 目录${NC}"
fi

# 清理之前的构建
echo -e "${YELLOW}🧹 清理之前的构建...${NC}"
rm -rf build dist

# 开始打包
echo -e "${YELLOW}📦 开始打包 (这可能需要几分钟)...${NC}"

# macOS 签名 (可选)
if [ -n "$APPLE_ID" ] && [ -n "$APPLE_ID_PASS" ]; then
    echo -e "${GREEN}🍎 检测到 Apple ID，将进行签名...${NC}"
    export CSC_LINK="$SCRIPT_DIR/certificate.p12"
    export CSC_KEY_PASSWORD="$APPLE_ID_PASS"
fi

# 执行打包
pyinstaller gui.spec --noconfirm

# 验证打包结果
if [ -d "dist/DouyinLiveRecorder.app" ]; then
    echo -e "${GREEN}✅ 打包成功！${NC}"
    echo -e "${GREEN}📁 输出目录: dist/DouyinLiveRecorder.app${NC}"
    echo ""
    echo -e "${YELLOW}使用方法:${NC}"
    echo "  1. 打开 dist/DouyinLiveRecorder.app"
    echo "  2. 如果遇到安全提示，请在系统偏好设置 > 安全性与隐私中允许运行"
    echo ""
    echo -e "${YELLOW}注意:${NC}"
    echo "  - 确保 bin/ffmpeg 存在，否则录制功能可能无法正常工作"
    echo "  - 首次运行可能需要较长时间启动"
elif [ -d "dist/DouyinLiveRecorder" ]; then
    echo -e "${GREEN}✅ 打包成功！${NC}"
    echo -e "${GREEN}📁 输出目录: dist/DouyinLiveRecorder${NC}"
    echo ""
    echo -e "${YELLOW}使用方法:${NC}"
    echo "  1. 进入 dist/DouyinLiveRecorder 目录"
    echo "  2. 运行 ./DouyinLiveRecorder"
    echo ""
    echo -e "${YELLOW}注意:${NC}"
    echo "  - 确保 bin/ffmpeg 存在，否则录制功能可能无法正常工作"
else
    echo -e "${RED}❌ 打包失败，请检查错误信息${NC}"
    exit 1
fi

echo -e "${GREEN}✨ 打包完成！${NC}"
