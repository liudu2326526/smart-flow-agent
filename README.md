# SmartFlow Agent

SmartFlow Agent 是一个全栈 AI 智能助手平台，基于 FastAPI 和 Vue 3 构建。它集成了 LangChain 和 LangGraph，支持流式对话、工具调用、会话管理以及 MCP (Model Context Protocol) 扩展能力。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Vue](https://img.shields.io/badge/vue-3.x-green.svg)

## ✨ 特性

- **智能对话**: 基于 LangChain + LangGraph 的 Agent 架构，支持流式响应 (SSE)。
- **工具调用**: 支持 Agent 自动调用工具（如计算器、天气查询等）。
- **会话管理**: 完整的会话历史记录、新建、删除及持久化存储 (SQLite)。
- **自动标题**: 后台异步任务根据对话内容自动生成会话标题。
- **现代化 UI**: 使用 Vue 3 + Arco Design 构建的响应式界面，支持 Markdown 渲染。
- **MCP 支持**: 预留 Model Context Protocol 架构，方便接入外部工具服务。

## 🛠 技术栈

### Backend
- **Framework**: FastAPI
- **AI/LLM**: LangChain, LangGraph, OpenAI SDK
- **Database**: SQLite, SQLModel (SQLAlchemy)
- **Runtime**: Python 3.10+

### Frontend
- **Framework**: Vue 3, Vite
- **Language**: TypeScript
- **UI Library**: Arco Design Vue
- **State Management**: Pinia
- **Router**: Vue Router

## 🚀 快速开始

### 前置要求
- Python 3.10+
- Node.js 16+
- Git

### 1. 克隆项目
```bash
git clone <repository-url>
cd smart-flow-agent
```

### 2. 环境配置
在项目根目录下创建 `.env` 文件（已提供 `.env.example` 参考）：
```ini
# Server
PROJECT_NAME="SmartFlow Agent Hub"
HOST="0.0.0.0"
PORT=8000

# Database
DATABASE_URL="sqlite:///./data/sql_app.db"

# LLM Configuration (支持 OpenAI 兼容接口)
OPENAI_API_KEY="your-api-key"
OPENAI_BASE_URL="https://api.example.com/v1"
OPENAI_MODEL="deepseek-chat"
```

### 3. 一键启动
我们提供了便捷的启停脚本：

```bash
# 添加执行权限 (首次运行)
chmod +x start.sh stop.sh

# 启动服务 (同时启动前端和后端)
./start.sh
```

启动后访问：
- **前端页面**: http://localhost:5173
- **后端文档**: http://localhost:8000/docs

### 4. 停止服务
```bash
./stop.sh
```

---

## 📂 目录结构

```text
smart-flow-agent/
├── backend/                 # Python 后端
│   ├── app/
│   │   ├── api/            # API 路由 (Chat, Conversations)
│   │   ├── core/           # 核心配置
│   │   ├── db/             # 数据库模型与初始化
│   │   ├── services/       # 业务逻辑 (Agent Service)
│   │   └── schemas/        # Pydantic 模型
│   ├── data/               # SQLite 数据文件
│   ├── main.py             # 入口文件
│   └── requirements.txt    # 依赖列表
│
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── api/            # API 接口定义
│   │   ├── hooks/          # Vue Hooks (useChat)
│   │   ├── layout/         # 布局组件 (MainLayout)
│   │   ├── store/          # Pinia 状态管理
│   │   └── views/          # 页面视图
│   └── package.json
│
├── start.sh                 # 一键启动脚本
├── stop.sh                  # 一键停止脚本
└── .env                     # 环境变量配置
```

## 🔧 手动安装 (开发模式)

如果你需要分别调试前后端：

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.db.init_db  # 初始化数据库
python main.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📝 开发计划

- [ ] 集成真实 MCP Server 连接
- [ ] 支持更多模态（文件上传分析）
- [ ] 知识库 (RAG) 功能实现
- [ ] 用户鉴权系统

## 📄 License

MIT
