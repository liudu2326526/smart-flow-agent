#!/bin/bash

# 颜色定义
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}=== Stopping SmartFlow Agent ===${NC}"

# 停止后端 (端口 8000)
BACKEND_PID=$(lsof -t -i:8000)
if [ -n "$BACKEND_PID" ]; then
    echo "Stopping Backend (PID: $BACKEND_PID)..."
    kill -9 $BACKEND_PID
    echo "Backend stopped."
else
    echo "Backend (Port 8000) is not running."
fi

# 停止前端 (端口 5173)
FRONTEND_PID=$(lsof -t -i:5173)
if [ -n "$FRONTEND_PID" ]; then
    echo "Stopping Frontend (PID: $FRONTEND_PID)..."
    kill -9 $FRONTEND_PID
    echo "Frontend stopped."
else
    echo "Frontend (Port 5173) is not running."
fi

echo -e "${RED}=== All services stopped ===${NC}"
