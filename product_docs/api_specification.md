# SmartFlow Agent Hub - API 接口文档 (v1.0)

本文档定义了 SmartFlow Agent Hub 前后端交互的 RESTful API 规范。

## 1. 基础说明

- **Base URL**: `/api/v1`
- **协议**: HTTP/1.1 (推荐 HTTP/2)
- **数据格式**: JSON (Content-Type: application/json)
- **认证方式**: Bearer Token (Authorization: Bearer <token>)
- **时间格式**: ISO 8601 (YYYY-MM-DDTHH:mm:ssZ)

## 2. 通用响应结构

除流式响应外，所有接口默认返回以下标准结构：

```json
{
  "code": 200,          // 业务状态码：200 成功，非 200 失败
  "message": "success", // 提示信息
  "data": { ... }       // 业务数据
}
```

错误响应示例：
```json
{
  "code": 400101,
  "message": "Invalid parameter: file_type not supported",
  "data": null
}
```

---

## 3. 认证模块 (Auth)

### 3.1 用户登录
获取访问令牌 (Access Token)。

- **URL**: `/auth/login`
- **Method**: `POST`
- **Content-Type**: `application/x-www-form-urlencoded` (兼容 OAuth2 标准) 或 `application/json`

**Request Body (JSON):**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Response (Success):**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "user_123",
      "username": "admin",
      "role": "admin"
    }
  }
}
```

### 3.2 获取当前用户信息
- **URL**: `/auth/me`
- **Method**: `GET`
- **Auth**: Required

**Response (Success):**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "user_123",
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

---

## 4. 会话管理 (Conversations)

### 4.1 获取会话列表
按更新时间倒序分页返回会话列表。

- **URL**: `/conversations`
- **Method**: `GET`
- **Query Params**:
  - `user_id`: string (必填，用户标识)
  - `page`: int (default: 1)
  - `size`: int (default: 20)

**Response (Success):**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "conv_123456789",
        "title": "分析 Q3 财报",
        "created_at": "2024-05-20T10:00:00Z",
        "updated_at": "2024-05-20T10:05:00Z"
      }
    ],
    "total": 15,
    "page": 1,
    "size": 20
  }
}
```

### 4.2 创建新会话
- **URL**: `/conversations`
- **Method**: `POST`

**Request Body:**
```json
{
  "user_id": "user_789", // 必填，用户标识
  "title": "新的对话" // 可选，若不传则后端生成默认标题
}
```

**Response (Success):**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "conv_new_uuid",
    "title": "新的对话",
    "created_at": "..."
  }
}
```

### 4.3 删除会话
- **URL**: `/conversations/{session_id}`
- **Method**: `DELETE`
- **Query Params**:
  - `user_id`: string (必填)

**Response:**
```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

## 5. 对话核心 (Chat)

### 5.1 获取会话历史消息
- **URL**: `/conversations/{session_id}/messages`
- **Method**: `GET`
- **Query Params**:
  - `user_id`: string (必填)
  - `limit`: int (default: 50) - 获取最近 N 条
  - `before_id`: int (optional) - 用于游标分页

**Response (Success):**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "type": "human",
      "content": "帮我查一下天气",
      "file_urls": ["https://..."],
      "created_at": "2024-05-20T10:01:00Z"
    },
    {
      "id": 2,
      "type": "ai",
      "reasoning_content": "用户想了解天气...",
      "content": "深圳今天多云，气温 28 度。",
      "file_urls": null,
      "created_at": "2024-05-20T10:01:05Z"
    }
  ]
}
```

### 5.2 发送消息 (Completions)
核心对话接口，**完全兼容 OpenAI Chat Completions API 规范**。

- **URL**: `/chat/completions`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Response-Type**: `text/event-stream` (推荐) 或 `application/json`

**Request Body (OpenAI Compatible):**
```json
{
  "user_id": "user_123", // 必需：用户标识
  "model": "smart-flow-agent-v1", // 必需，虽然是 Agent，但保持字段兼容
  "messages": [
    {
      "role": "user",
      "content": "帮我生成一张春节海报"
    }
    // 支持传递历史消息，或仅传最新一条（由后端 Session 拼接）
  ],
  "stream": true, // 强烈推荐 true
  
  // --- 以下为 SmartFlow 扩展参数 (OpenAI SDK 允许传入 extra_body) ---
  "session_id": "conv_123456789", // 必需：用于关联会话上下文
  "urls": ["https://..."],       // 可选：本轮对话引用的文件链接列表
  "deep_thinking": true           // 可选：是否开启深度思考 (默认 false)
}
```

**Response (Stream - OpenAI Compatible):**
遵循 Server-Sent Events (SSE) 标准，每行以 `data: ` 开头，结束发送 `data: [DONE]`。

**1. 文本生成 (Standard)**
```json
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1700000000,"model":"smart-flow-agent-v1","choices":[{"index":0,"delta":{"content":"好"},"finish_reason":null}]}
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1700000000,"model":"smart-flow-agent-v1","choices":[{"index":0,"delta":{"content":"的"},"finish_reason":null}]}
```

**2. 思考过程 (Reasoning - DeepSeek/R1 Style)**
使用 `reasoning_content` 字段透传 Agent 的规划与思考。
```json
data: {"id":"...","choices":[{"index":0,"delta":{"reasoning_content":"正在检索知识库..."},"finish_reason":null}]}
```

**3. 工具调用 (Tool Calls)**
标准 OpenAI 工具调用格式。
```json
data: {"id":"...","choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"id":"call_abc","type":"function","function":{"name":"image_gen","arguments":""}}]},"finish_reason":null}]}
data: {"id":"...","choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\"prompt\""}}]},"finish_reason":null}]}
```

**4. 扩展事件 (Extension Events)**
为了支持 Agent 的特殊状态（如执行结果回显、审批请求），我们在 `choices[0]` 中添加 `extension` 字段。
*注：标准 OpenAI SDK 会自动忽略此字段，不会报错；定制前端可解析此字段以增强体验。*

*   **工具执行结果 (Tool Output)**:
    ```json
    {
      "choices": [{
        "delta": {},
        "extension": {
          "type": "tool_result",
          "tool_call_id": "call_abc",
          "content": "https://image.url/gen.png" // 图片或工具结果
        }
      }]
    }
    ```

*   **请求审批 (Request Approval)**:
    ```json
    {
      "choices": [{
        "finish_reason": "manual_approval_required", // 自定义结束原因
        "extension": {
          "type": "approval_request",
          "approval_id": "appr_789",
          "tool_call_id": "call_def",
          "tool_name": "send_email",
          "tool_args": {"to": "boss@company.com"}
        }
      }]
    }
    ```

**5. 结束 (Completion)**
```json
data: [DONE]
```

> **契约说明 (Contract)**:
> 当客户端收到 `data: [DONE]` 信号时，意味着：
> 1.  **生成结束**：AI 已完成所有内容的输出（包括文本、思考过程和工具调用）。
> 2.  **持久化完成**：后端已将本轮 Human/AI/Tool 消息全部写入数据库。
> 3.  **状态安全**：前端可以安全地刷新会话列表 (Conversations List) 以获取最新摘要，或重新拉取消息历史。

### 5.3 提交工具审批结果
当收到 `request_approval` 事件后，用户点击批准或拒绝，调用此接口。

- **URL**: `/chat/approval/{approval_id}`
- **Method**: `POST`

**Request Body:**
```json
{
  "action": "approve", // 或 "reject"
  "feedback": "同意发送" // 可选备注
}
```

**Response:**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "resumed" // 或者返回新的 stream URL
  }
}
```

---

## 6. 知识库与文档 (Documents)

### 6.1 上传文档
- **URL**: `/documents/upload`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`

**Form Data:**
- `user_id`: (String) 必需，用户标识
- `file`: (Binary) 文件内容
- `session_id`: (String) 可选，若关联特定会话

**Response (Success):**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 555,
    "filename": "2024规范.pdf",
    "size": 102400,
    "status": "pending", // pending -> indexing -> indexed
    "url": "https://obs.example.com/documents/..."
  }
}
```

### 6.2 获取文档列表
- **URL**: `/documents`
- **Method**: `GET`
- **Query Params**:
  - `user_id`: string (必填)
  - `status`: string (optional) 筛选状态

**Response (Success):**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "filename": "2024规范.pdf",
      "file_path": "https://obs.example.com/documents/...",
      "status": "indexed",
      "uploaded_at": "2024-01-01T10:00:00Z",
      "size": 102400
    }
  ]
}
```

### 6.3 删除文档
- **URL**: `/documents/{doc_id}`
- **Query Params**:
  - `user_id`: string (必填)
- **Method**: `DELETE`

**Response:**
```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

---

## 7. 工具管理 (Tools - MCP)

### 7.1 获取可用工具列表
- **URL**: `/tools`
- **Method**: `GET`

**Response (Success):**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "name": "google_search",
      "description": "Search the web for current information",
      "source": "mcp_server_google",
      "is_active": true
    },
    {
      "name": "read_file",
      "description": "Read file content",
      "source": "builtin",
      "is_active": true
    }
  ]
}
```

### 7.2 配置 MCP Server
- **URL**: `/tools/mcp/configure`
- **Method**: `POST`

**Request Body:**
```json
{
  "server_name": "google_search_server",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-google-search"],
  "env": {"GOOGLE_API_KEY": "..."}
}
```

**Response (Success):**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "connected",
    "tools_discovered": 2
  }
}
```
