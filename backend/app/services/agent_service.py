import asyncio
from typing import List, AsyncGenerator
from contextlib import AsyncExitStack

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool, Tool
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

from app.core.config import settings

# ==========================================
# 1. 定义工具 (Tools)
# ==========================================
@tool
def magic_calculator(a: int, b: int) -> int:
    """
    一个神奇的计算器，它会将两个数字相加，然后乘以 2。
    用于演示工具调用。
    """
    return (a + b) * 2

@tool
def get_weather(city: str) -> str:
    """
    获取指定城市的天气。
    """
    return f"{city} 的天气是晴朗，气温 25 度。"

# 基础工具列表
base_tools = [magic_calculator, get_weather]
# base_tools = []
# ==========================================
# 2. Memory 管理
# ==========================================
def get_chat_history(session_id: str) -> SQLChatMessageHistory:
    """
    获取基于 SQLite 的聊天记录管理器。
    """
    # 使用配置中的数据库 URL
    return SQLChatMessageHistory(session_id=session_id, connection=settings.DATABASE_URL)

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ... (Existing imports)

# ==========================================
# 3. Agent Service 类
# ==========================================
class AgentService:
    def __init__(self):
        self.llm = None
        self.stack = AsyncExitStack()
        self.mcp_tools: List[Tool] = []
        self.agent = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return

        # 1. 初始化 LLM
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0,
                base_url=settings.OPENAI_BASE_URL if settings.OPENAI_BASE_URL else None,
                api_key=settings.OPENAI_API_KEY,
                streaming=True
            )
        else:
            raise ValueError("OPENAI_API_KEY is not set")

        # 2. 加载 MCP 工具 (模拟连接，未来可从配置读取)
        # 这里可以根据需求加入 MCP Server 的配置参数
        
        # 3. 合并所有工具
        all_tools = base_tools + self.mcp_tools
        
        # 4. 创建 Agent (使用 create_agent，返回 CompiledGraph)
        from langchain.agents import create_agent
        
        # 创建 Agent (create_agent 返回的是一个 CompiledGraph，可以直接调用 astream)
        self.agent = create_agent(self.llm, all_tools)
        
        self._initialized = True
        print(f"✅ Agent Service Initialized with {len(all_tools)} tools.")

    async def generate_summary_title(self, session_id: str):
        """
        根据会话历史生成标题
        """
        if not self._initialized:
            await self.initialize()

        history = get_chat_history(session_id)
        messages = history.messages
        
        # 至少要有 2 条消息（一问一答）才生成标题，且如果消息太少可能不准确
        if not messages:
            return

        # 使用 LLM 生成标题
        prompt = ChatPromptTemplate.from_template(
            "请根据以下对话内容，生成一个简短的标题（不超过 10 个字）。不要使用引号。如果无法生成，返回 '新的对话'。\n\n对话内容：\n{conversation}"
        )
        chain = prompt | self.llm | StrOutputParser()
        
        # 取前几条消息作为上下文
        conversation_text = "\n".join([f"{m.type}: {m.content}" for m in messages[:4]])
        
        try:
            title = await chain.ainvoke({"conversation": conversation_text})
            title = title.strip().replace('"', '').replace("'", "")
            
            # 更新数据库
            from sqlmodel import Session, select
            from app.db.session import engine
            from app.db.models import Conversation
            
            with Session(engine) as session:
                conv = session.exec(select(Conversation).where(Conversation.id == session_id)).first()
                if conv:
                    conv.title = title
                    session.add(conv)
                    session.commit()
                    print(f"✅ Title updated for session {session_id}: {title}")
        except Exception as e:
            print(f"❌ Failed to generate title: {e}")

    async def chat(self, session_id: str, user_input: str) -> AsyncGenerator[str, None]:
        # ... (Existing chat implementation)

        if not self._initialized:
            await self.initialize()

        # 1. 获取历史记录
        history = get_chat_history(session_id)
        
        # 2. 构造临时上下文（不立即保存用户消息）
        # 我们希望在 AI 回复生成完毕后，一起保存 HumanMessage 和 AIMessage
        # 这样可以保证事务性（虽然 SQLite 不是严格事务，但逻辑上是一次 turn）
        # 但 LangGraph 需要完整的 history。
        
        # 方案：先不 add_user_message 到 history，而是构造一个新的 list
        # current_messages = history.messages + [HumanMessage(content=user_input)]
        
        # 但 history.messages 是从 DB 读出来的。
        # 如果我们不 save，下次请求就没了。
        # 所以必须 save。
        
        # 用户的意思是：防止只存入用户问题（即 AI 生成失败时，只有用户问题被存了）
        # 可以在 try-except 中处理，或者在最后一起保存。
        
        # 采用 "最后一起保存" 策略
        # 1. 获取当前 DB 中的历史
        db_messages = history.messages
        
        # 2. 构造本次对话的输入
        current_messages = db_messages + [HumanMessage(content=user_input)]
        
        accumulated_content = ""
        
        # 3. 流式调用
        try:
            async for chunk, metadata in self.agent.astream(
                {"messages": current_messages}, 
                stream_mode="messages"
            ):
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    content = chunk.content
                    accumulated_content += content
                    yield content
            
            # 4. 成功生成后，同时保存用户消息和 AI 消息
            # 注意：这里有轻微的竞态风险，但在单用户 session 场景下可忽略
            if accumulated_content:
                history.add_user_message(user_input)
                history.add_ai_message(accumulated_content)
                        
        except Exception as e:
            print(f"Agent Execution Error: {e}")
            yield f"[Error: {str(e)}]"
            # 出错时不保存任何消息，或者只保存用户消息？
            # 根据需求 "防止只存入用户问题"，出错时应该都不存，或者回滚。
            # 这里如果不调用 add_user_message，就都不存。

    async def get_history_messages(self, session_id: str) -> List[dict]:
        """
        获取历史消息，并转换为 API 格式。
        """
        history = get_chat_history(session_id)
        messages = []
        for msg in history.messages:
            role = "user"
            if isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, HumanMessage):
                role = "user"
            
            # 暂时简化处理，只返回 type 和 content
            # 实际场景可能需要处理 tool calls
            messages.append({
                "role": role,
                "content": msg.content,
                "type": "human" if role == "user" else "ai" # 兼容 API 文档中的 type
            })
        return messages

# 单例模式
agent_service = AgentService()
