import asyncio
import json
import logging
from typing import List, AsyncGenerator
from contextlib import AsyncExitStack
from pathlib import Path

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool, Tool
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, BaseMessage
import langchain_openai.chat_models.base as base_module
from app.utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)

# ==========================================
# Monkey Patch: 支持 reasoning_content
# ==========================================
# 保存原始函数
_original_convert_dict_to_message = base_module._convert_dict_to_message


def _patched_convert_dict_to_message(_dict):
    # 调用原始转换逻辑
    message = _original_convert_dict_to_message(_dict)

    # 如果是 AIMessage 且原始字典中有 reasoning_content，则注入到 additional_kwargs
    if isinstance(message, AIMessage) and "reasoning_content" in _dict:
        message.additional_kwargs["reasoning_content"] = _dict["reasoning_content"]

    return message


# 应用 Patch
base_module._convert_dict_to_message = _patched_convert_dict_to_message
# ==========================================

# ==========================================
# Monkey Patch 2: 支持流式 reasoning_content
# ==========================================
_original_convert_delta_to_message_chunk = base_module._convert_delta_to_message_chunk


def _patched_convert_delta_to_message_chunk(_dict, default_class):
    # 调用原始函数
    chunk = _original_convert_delta_to_message_chunk(_dict, default_class)

    # 注入 reasoning_content
    if isinstance(chunk, AIMessageChunk) and "reasoning_content" in _dict:
        chunk.additional_kwargs["reasoning_content"] = _dict["reasoning_content"]

    return chunk


base_module._convert_delta_to_message_chunk = _patched_convert_delta_to_message_chunk
# End Monkey Patch


from sqlmodel import Session, select
from app.db.session import engine
from app.db.models import Conversation, Message as DBMessage
from app.core.config import settings
from app.services.tools import base_tools

# ==========================================
# 2. Memory 管理
# ==========================================
def get_chat_history(session_id: str) -> List[BaseMessage]:
    """
    从数据库 Message 表中获取历史记录，并转换为 LangChain 消息对象。
    """
    messages = []
    with Session(engine) as db_session:
        statement = select(DBMessage).where(DBMessage.session_id == session_id).order_by(DBMessage.created_at.asc())
        db_messages = db_session.exec(statement).all()
        for msg in db_messages:
            additional_kwargs = {}
            if msg.file_urls:
                additional_kwargs["file_urls"] = msg.file_urls
            
            if msg.type == "human":
                messages.append(HumanMessage(content=msg.content, additional_kwargs=additional_kwargs))
            elif msg.type == "ai":
                # 处理 reasoning_content
                if msg.response_metadata and "reasoning_content" in msg.response_metadata:
                    additional_kwargs["reasoning_content"] = msg.response_metadata["reasoning_content"]
                messages.append(AIMessage(content=msg.content, additional_kwargs=additional_kwargs))
    return messages

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ==========================================
# 3. Agent Service 类
# ==========================================
class AgentService:
    def __init__(self):
        self.stack = AsyncExitStack()
        self.mcp_tools: List[Tool] = []
        self.agents = {}  # 使用字典存储不同配置的 Agent: {deep_thinking: bool -> agent}
        self._initialized = False
        self.langfuse_handler = None
        self.llms = {}  # 存储不同配置的 LLM: {deep_thinking: bool -> llm}

    async def initialize(self):
        if self._initialized:
            return

        logger.info("Initializing AgentService...")

        # 0. 初始化 Langfuse (Monitoring)
        try:
            import os

            os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
            os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
            os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST

            from langfuse.langchain import CallbackHandler

            self.langfuse_handler = CallbackHandler()
            logger.info("✅ Langfuse Monitoring Initialized")
        except ImportError as e:
            logger.warning(
                f"Langfuse package or CallbackHandler not found: {e}. Please run `pip install langfuse`."
            )
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse: {e}")

        # 1. 初始化 LLM
        if not settings.OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY is not set")
            raise ValueError("OPENAI_API_KEY is not set")
        else:
            self.llms[False] = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0,
                base_url=settings.OPENAI_BASE_URL if settings.OPENAI_BASE_URL else None,
                api_key=settings.OPENAI_API_KEY,
                streaming=True,
                extra_body={"thinking": {"type": "disabled"}},
            )
            self.llms[True] = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0,
                base_url=settings.OPENAI_BASE_URL if settings.OPENAI_BASE_URL else None,
                api_key=settings.OPENAI_API_KEY,
                streaming=True,
                extra_body={"thinking": {"type": "enabled"}},
            )

        # 2. 加载 MCP 工具 (模拟连接，未来可从配置读取)
        # 这里可以根据需求加入 MCP Server 的配置参数

        # 3. 合并所有工具
        self.all_tools = base_tools + self.mcp_tools

        # 4. 创建不同模式的 Agent (使用 create_agent，返回 CompiledGraph)
        from langchain.agents import create_agent

        # 根据 deep_thinking 参数控制 disabled 和 enabled
        for deep_thinking in [False, True]:
            thinking_type = "enabled" if deep_thinking else "disabled"
            mode_llm = self.llms[deep_thinking]
            self.agents[deep_thinking] = create_agent(mode_llm, self.all_tools)
            logger.info(
                f"Initialized agent with deep_thinking={deep_thinking} (mode={thinking_type})"
            )

        self._initialized = True
        logger.info(f"✅ Agent Service Initialized with {len(self.all_tools)} tools.")
        print(f"✅ Agent Service Initialized with {len(self.all_tools)} tools.")

    async def generate_summary_title(self, session_id: str):
        """
        根据会话历史生成标题
        """
        if not self._initialized:
            await self.initialize()

        messages = get_chat_history(session_id)

        # 至少要有 2 条消息（一问一答）才生成标题，且如果消息太少可能不准确
        if not messages:
            return

        # 使用 LLM 生成标题
        prompt = ChatPromptTemplate.from_template(
            "请根据以下对话内容，生成一个简短的标题（不超过 10 个字）。不要使用引号。如果无法生成，返回 '新的对话'。\n\n对话内容：\n{conversation}"
        )
        chain = prompt | self.llms[False] | StrOutputParser()

        # 取前几条消息作为上下文
        conversation_text = "\n".join([f"{m.type}: {m.content}" for m in messages[:4]])

        try:
            logger.info(f"Generating title for session {session_id}")
            title = await chain.ainvoke({"conversation": conversation_text})
            title = title.strip().replace('"', "").replace("'", "")

            # 更新数据库
            from sqlmodel import Session, select
            from app.db.session import engine
            from app.db.models import Conversation

            with Session(engine) as session:
                conv = session.exec(
                    select(Conversation).where(Conversation.id == session_id)
                ).first()
                if conv:
                    conv.title = title
                    session.add(conv)
                    session.commit()
                    logger.info(f"✅ Title updated for session {session_id}: {title}")
                    print(f"✅ Title updated for session {session_id}: {title}")
        except Exception as e:
            logger.error(f"❌ Failed to generate title: {e}")
            print(f"❌ Failed to generate title: {e}")

    async def chat(
        self, session_id: str, user_input: str, deep_thinking: bool = False, urls: List[str] = None
    ) -> AsyncGenerator[str, None]:
        if not self._initialized:
            await self.initialize()

        logger.info(
            f"Starting chat for session {session_id} (deep_thinking={deep_thinking}) with input: {user_input[:50]}..."
        )

        # 1. 获取历史记录
        db_messages = get_chat_history(session_id)

        # 2. 构造本次对话的输入
        user_msg_kwargs = {}
        full_content = user_input
        if urls:
            user_msg_kwargs["file_urls"] = urls
            # 将文件链接追加到内容中，方便 LLM 识别和调用工具
            full_content += "\n\n[文件列表]:\n" + "\n".join(urls)
        
        current_messages = db_messages + [HumanMessage(content=full_content, additional_kwargs=user_msg_kwargs)]

        accumulated_content = ""
        accumulated_reasoning = ""

        # 3. 选择 Agent
        agent = self.agents.get(deep_thinking, self.agents[False])

        # 4. 流式调用
        try:
            is_thinking = False
            # Log tool calls
            async for event in agent.astream_events(
                {"messages": current_messages},
                version="v1",
                config={
                    "callbacks": (
                        [self.langfuse_handler] if self.langfuse_handler else []
                    )
                },
            ):
                kind = event["event"]

                # Log Tool Start
                if kind == "on_tool_start":
                    logger.info(
                        f"🛠️  Tool Call Start: {event['name']} Input: {event['data'].get('input')}"
                    )

                # Log Tool End
                elif kind == "on_tool_end":
                    logger.info(
                        f"✅ Tool Call End: {event['name']} Output: {str(event['data'].get('output'))[:100]}..."
                    )

                # Handle Streaming Content (AIMessageChunk)
                elif kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if isinstance(chunk, AIMessageChunk):
                        # 检查是否有思考内容
                        reasoning_content = None
                        if (
                            chunk.additional_kwargs
                            and "reasoning_content" in chunk.additional_kwargs
                        ):
                            reasoning_content = chunk.additional_kwargs[
                                "reasoning_content"
                            ]

                        content = chunk.content

                        if reasoning_content:
                            if not is_thinking:
                                logger.info("🤖 AI Start Thinking...")
                                is_thinking = True
                            accumulated_reasoning += reasoning_content
                            yield json.dumps({"reasoning_content": reasoning_content})

                        if content:
                            if is_thinking:
                                logger.info("💡 AI End Thinking, Start Responding...")
                                is_thinking = False
                            accumulated_content += content
                            yield json.dumps({"content": content})

            if is_thinking:
                logger.info("💡 AI End Thinking (Stream Ended)")

            # 4. 成功生成后，同时保存用户消息和 AI 消息
            if accumulated_content or accumulated_reasoning:
                logger.info(f"Chat completed for session {session_id}. Saving history.")
                
                with Session(engine) as db_session:
                    # 保存用户消息
                    user_db_msg = DBMessage(
                        session_id=session_id,
                        type="human",
                        content=user_input,
                        file_urls=urls if urls else None
                    )
                    db_session.add(user_db_msg)
                    
                    # 保存 AI 消息
                    ai_db_msg = DBMessage(
                        session_id=session_id,
                        type="ai",
                        content=accumulated_content,
                        response_metadata={"reasoning_content": accumulated_reasoning} if accumulated_reasoning else None
                    )
                    db_session.add(ai_db_msg)
                    
                    # 更新会话更新时间
                    conv = db_session.exec(select(Conversation).where(Conversation.id == session_id)).first()
                    if conv:
                        from datetime import datetime
                        conv.updated_at = datetime.utcnow()
                        db_session.add(conv)
                        
                    db_session.commit()
                    logger.info(f"✅ History saved for session {session_id}")
            else:
                logger.warning(f"No content generated for session {session_id}")

        except Exception as e:
            logger.error(f"Agent Execution Error: {e}", exc_info=True)
            print(f"Agent Execution Error: {e}")
            yield f"[Error: {str(e)}]"
            # 出错时不保存任何消息，或者只保存用户消息？
            # 根据需求 "防止只存入用户问题"，出错时应该都不存，或者回滚。
            # 这里如果不调用 add_user_message，就都不存。

    async def get_history_messages(self, session_id: str) -> List[dict]:
        """
        获取历史消息，并转换为 API 格式。
        """
        messages = []
        with Session(engine) as db_session:
            statement = select(DBMessage).where(DBMessage.session_id == session_id).order_by(DBMessage.created_at.asc())
            db_messages = db_session.exec(statement).all()
            
            for msg in db_messages:
                role = "user" if msg.type == "human" else "assistant"
                reasoning_content = None
                
                if msg.type == "ai" and msg.response_metadata:
                    reasoning_content = msg.response_metadata.get("reasoning_content")

                message_data = {
                    "role": role,
                    "content": msg.content,
                    "type": msg.type,
                    "file_urls": msg.file_urls,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
                if reasoning_content:
                    message_data["reasoning_content"] = reasoning_content

                messages.append(message_data)
        return messages


# 单例模式
agent_service = AgentService()
