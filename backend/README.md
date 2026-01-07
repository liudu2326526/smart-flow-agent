# SmartFlow Agent Hub - Backend

SmartFlow Agent Hub 的后端服务，基于 FastAPI 和 LangChain 构建，支持多种 Agent 模式、工具调用（包括 MCP）以及 RAG（基于 Elasticsearch）。

## 🚀 核心功能

- **双模式 Agent**: 支持普通模式和“深度思考”模式（基于豆包大模型推理能力）。
- **RAG 知识库**: 集成 Elasticsearch 实现高性能的向量搜索和知识检索。
- **工具集成**: 内置天气查询、神奇计算器等演示工具，并支持 **MCP (Model Context Protocol)**。
- **对话管理**: 完整的会话持久化方案，基于 SQLite 和 SQLModel。
- **全链路监控**: 集成 Langfuse 进行 Agent 的追踪、性能监控和调试。
- **Monkey Patch 增强**: 特别针对豆包大模型优化，支持 `reasoning_content` 的流式输出和展示。

## 🛠️ 技术栈

- **Web 框架**: FastAPI
- **LLM 框架**: LangChain, LangGraph, LangSmith
- **大模型**: 豆包 (Doubao) 系列模型 (via Volcengine Ark)
- **数据库**: SQLite (本地存储), Elasticsearch (向量数据库)
- **监控**: Langfuse
- **工具协议**: MCP (Model Context Protocol)
- **异步处理**: asyncio, httpx

## 📂 项目结构

```text
backend/
├── app/
│   ├── api/            # API 路由 (v1)
│   │   ├── chat.py     # 聊天接口 (流式输出)
│   │   └── conversations.py # 会话管理
│   ├── core/           # 核心配置 (config.py)
│   ├── db/             # 数据库模型与会话 (SQLModel)
│   ├── schemas/        # Pydantic 数据模型
│   ├── services/       # 业务逻辑 (Agent 核心实现)
│   │   ├── agent_service.py # Agent 初始化与执行逻辑
│   │   └── tools.py    # 工具定义 (RAG, Weather 等)
│   └── utils/          # 工具类 (Logger 等)
├── main.py             # 入口文件
└── requirements.txt    # 依赖项
```

## 🧪 开发备注

- **Monkey Patch**: 为了支持豆包模型的 `reasoning_content`，我们在 `app/services/agent_service.py` 中对 `langchain-openai` 进行了猴子补丁。
- **数据库**: 首次运行会自动在 `./data` 目录下生成 `sql_app.db`。
- **MCP**: 未来可以通过扩展 `AgentService` 动态加载更多的 MCP 服务。
