# SmartFlow Agent Hub - Frontend

SmartFlow Agent Hub 的前端界面，基于 Vue 3、TypeScript 和 Arco Design 构建。提供流畅的 AI 对话体验，支持流式响应、深度思考展示及 RAG 知识库管理。

## ✨ 核心功能

- **流畅对话体验**: 支持 SSE (Server-Sent Events) 流式输出，实时响应 AI 生成内容。
- **深度思考 (Deep Thinking)**: 专门适配豆包大模型的推理过程，支持展示中间思考链（`reasoning_content`）。
- **Markdown 渲染**: 完整支持 Markdown 语法，包括代码高亮（Highlight.js）、数学公式、表格等。
- **会话管理**: 支持创建、删除、切换多个对话，对话状态通过 Pinia 进行持久化管理。
- **知识库展示**: 提供文档列表视图，展示已上传或索引的知识库内容。
- **响应式布局**: 适配不同尺寸屏幕，基于 Arco Design 提供的现代 UI 规范。

## 🛠️ 技术栈

- **框架**: [Vue 3](https://vuejs.org/) (Composition API + `<script setup>`)
- **构建工具**: [Vite 7](https://vitejs.dev/)
- **语言**: [TypeScript](https://www.typescriptlang.org/)
- **状态管理**: [Pinia](https://pinia.vuejs.org/)
- **路由**: [Vue Router 4](https://router.vuejs.org/)
- **UI 组件库**: [Arco Design Vue](https://arco.design/vue/)
- **Markdown 处理**: `markdown-it` + `highlight.js`
- **样式**: Less

## 📂 项目结构

```text
frontend/
├── src/
│   ├── api/            # 接口请求封装
│   ├── assets/         # 静态资源
│   ├── components/     # 公用组件
│   ├── hooks/          # 组合式函数 (如 useChat.ts)
│   ├── layout/         # 页面布局 (MainLayout.vue)
│   ├── router/         # 路由配置
│   ├── store/          # Pinia 状态管理
│   ├── views/          # 页面视图
│   │   ├── chat/       # 聊天界面
│   │   └── knowledge/  # 知识库管理
│   ├── App.vue         # 根组件
│   └── main.ts         # 入口文件
├── index.html          # HTML 入口
└── vite.config.ts      # Vite 配置
```

## 🧪 开发指南

- **对话逻辑**: 核心逻辑封装在 `src/hooks/useChat.ts` 中，处理了流式解析和状态切换。
- **主题定制**: 可以在 `src/style.css` 中修改 Arco Design 的全局变量，或通过 Arco 官方配置进行深度定制。
