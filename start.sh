#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting SmartFlow Agent ===${NC}"

# 获取脚本所在目录的绝对路径
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 1. 启动后端
echo -e "${GREEN}Starting Backend...${NC}"
cd "$PROJECT_ROOT/backend"

# 检查 Python 环境
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 检查端口 8000 是否被占用
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "Port 8000 is already in use. Skipping backend start."
else
    # 后台启动后端，日志重定向到 logs/backend.log
    mkdir -p ../logs
    nohup python main.py > ../logs/backend.log 2>&1 &
    echo "Backend running in background. Logs: logs/backend.log"
fi

# 2. 启动前端
echo -e "${GREEN}Starting Frontend...${NC}"
cd "$PROJECT_ROOT/frontend"

# 检查端口 5173 是否被占用
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
    echo "Port 5173 is already in use. Skipping frontend start."
else
    # 后台启动前端，日志重定向到 logs/frontend.log
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    echo "Frontend running in background. Logs: logs/frontend.log"
fi

echo -e "${BLUE}=== SmartFlow Agent Started ===${NC}"
echo -e "Frontend: ${GREEN}http://localhost:5173${NC}"
echo -e "Backend:  ${GREEN}http://localhost:8000/docs${NC}"
echo -e "Logs are available in the 'logs' directory."
