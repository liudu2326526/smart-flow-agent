import json
import asyncio
import time
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.schemas.chat import ChatCompletionRequest
from app.core.config import settings
from app.services.agent_service import agent_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

async def generate_stream_response(request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
    """
    Generator function to stream SSE events compatible with OpenAI format.
    """
    model_name = request.model
    session_id = request.session_id
    
    # Create the ID for this completion
    completion_id = f"chatcmpl-{int(time.time())}"
    
    logger.info(f"Starting stream response for session_id={session_id}")
    
    # 1. Send "thinking" event (Optional now since real thinking comes from LLM)
    # thinking_data = {
    #     "id": completion_id,
    #     "object": "chat.completion.chunk",
    #     "created": int(time.time()),
    #     "model": model_name,
    #     "choices": [
    #         {
    #             "index": 0,
    #             "delta": {"role": "assistant", "reasoning_content": "正在思考并规划任务..."},
    #             "finish_reason": None
    #         }
    #     ]
    # }
    # yield f"data: {json.dumps(thinking_data)}\n\n"

    # try:
        # Check if we have a valid API key to use real LLM
    if settings.OPENAI_API_KEY:
        # Use Agent Service
        
        # Get the last user message
        user_input = request.messages[-1].content if request.messages else ""
        deep_thinking = request.deep_thinking
        urls = request.urls
        
        if not user_input:
            return

        async for chunk_str in agent_service.chat(session_id, user_input, deep_thinking=deep_thinking, urls=urls):
            try:
                chunk_data = json.loads(chunk_str)
            except json.JSONDecodeError:
                continue

            delta = {}
            if "reasoning_content" in chunk_data:
                delta["reasoning_content"] = chunk_data["reasoning_content"]
            if "content" in chunk_data:
                delta["content"] = chunk_data["content"]
            
            if not delta:
                continue

            response_data = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_name,
                "choices": [
                    {
                        "index": 0,
                        "delta": delta,
                        "finish_reason": None
                    }
                ]
            }
            yield f"data: {json.dumps(response_data)}\n\n"
    else:
        # MOCK LOGIC
        response_text = f"收到您的消息：'{request.messages[-1].content}'。\n\n目前后端未配置 OPENAI_API_KEY..."
        # ... (Existing Mock Logic) ...
        for char in response_text:
            await asyncio.sleep(0.02)
            response_data = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "delta": {"content": char},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(response_data)}\n\n"
                
    # except Exception as e:
    #     error_data = {
    #         "id": completion_id,
    #         "object": "error",
    #         "created": int(time.time()),
    #         "model": model_name,
    #         "error": str(e)
    #     }
    #     yield f"data: {json.dumps(error_data)}\n\n"
    #     return

    # Send [DONE] signal
    yield "data: [DONE]\n\n"
    logger.info(f"Stream response completed for session_id={session_id}")

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import Conversation
# ...

@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    logger.info(f"Received chat completion request: session_id={request.session_id}, user_id={request.user_id}, model={request.model}")
    # Check if we need to generate a title
    conv = session.exec(
        select(Conversation)
        .where(Conversation.id == request.session_id)
        .where(Conversation.user_id == request.user_id)
    ).first()
    
    if not conv:
        # 如果会话不存在，自动创建一个
        from datetime import datetime
        conv = Conversation(
            id=request.session_id,
            user_id=request.user_id,
            title="新的对话",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(conv)
        session.commit()
        session.refresh(conv)
    
    if conv and (not conv.title or conv.title == "新的对话"):
        # Add background task to generate title
        background_tasks.add_task(agent_service.generate_summary_title, request.session_id)

    return StreamingResponse(
        generate_stream_response(request),
        media_type="text/event-stream"
    )
