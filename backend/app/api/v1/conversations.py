import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from app.services.agent_service import agent_service
from app.db.session import get_session
from app.db.models import Conversation, User
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

from sqlmodel import Session, select, func


@router.get("/conversations", response_model=dict)
async def get_conversations(
    user_id: str,
    page: int = 1,
    size: int = 20,
    session: Session = Depends(get_session)
):
    """
    获取会话列表
    """
    logger.info(f"Fetching conversations for user_id={user_id}, page={page}, size={size}")
    # 计算总数
    total_statement = (
        select(func.count())
        .select_from(Conversation)
        .where(Conversation.user_id == user_id, Conversation.is_deleted == False)
    )
    total = session.exec(total_statement).one()

    # 分页查询
    statement = ( 
        select(Conversation)
        .where(Conversation.user_id == user_id, Conversation.is_deleted == False)
        .order_by(Conversation.updated_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )

    conversations = session.exec(statement).all()

    items = []
    for conv in conversations:
        items.append(
            {
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
            }
        )

    return {
        "code": 200,
        "message": "success",
        "data": {"items": items, "total": total, "page": page, "size": size},
    }


@router.post("/conversations", response_model=dict)
async def create_conversation(
    conversation_in: ConversationCreate, session: Session = Depends(get_session)
):
    """
    创建新会话
    """
    logger.info(f"Creating new conversation for user_id={conversation_in.user_id}, title={conversation_in.title}")
    try:
        user_id = conversation_in.user_id

        # 确保存在一个用户，否则外键报错
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            user = User(
                id=user_id,
                username=f"user_{user_id}",
                email=f"{user_id}@example.com",
                password_hash="hash",
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        session_id = f"conv_{uuid.uuid4().hex}"
        title = conversation_in.title if conversation_in.title else "新的对话"

        db_conversation = Conversation(
            id=session_id,
            user_id=user_id,
            title=title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        session.add(db_conversation)
        session.commit()
        session.refresh(db_conversation)

        logger.info(f"Conversation created successfully: session_id={db_conversation.id}")
        return {
            "code": 200,
            "message": "success",
            "data": {
                "id": db_conversation.id,
                "title": db_conversation.title,
                "created_at": db_conversation.created_at.isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
        return {
            "code": 500,
            "message": f"Internal Server Error: {str(e)}",
            "data": None
        }


@router.delete("/conversations/{session_id}", response_model=dict)
async def delete_conversation(
    session_id: str,
    user_id: str,
    session: Session = Depends(get_session)
):
    """
    删除会话
    """
    logger.info(f"Deleting conversation: session_id={session_id}, user_id={user_id}")
    # 查询会话
    conversation = session.exec(
        select(Conversation)
        .where(Conversation.id == session_id)
        .where(Conversation.user_id == user_id)
    ).first()

    if not conversation:
        return {"code": 404, "message": "Conversation not found", "data": None}

    conversation.is_deleted = True
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    return {"code": 200, "message": "success", "data": None}


@router.get("/conversations/{session_id}/messages")
async def get_conversation_messages(
    session_id: str, 
    user_id: str,
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """
    获取会话历史消息
    """
    logger.info(f"Fetching messages for session_id={session_id}, user_id={user_id}, limit={limit}")
    try:
        # 验证会话是否属于该用户
        conversation = session.exec(
            select(Conversation)
            .where(Conversation.id == session_id)
            .where(Conversation.user_id == user_id)
        ).first()

        if not conversation:
            return {"code": 404, "message": "Conversation not found or access denied", "data": []}

        messages = await agent_service.get_history_messages(session_id)
        # 转换格式以匹配 API 文档
        # API 文档: id, type, content, created_at, tool_calls...
        # 这里简化返回，主要适配前端展示

        formatted_messages = []
        for idx, msg in enumerate(messages):
            message_item = {
                "id": idx + 1,  # 临时生成 ID 或使用 DB ID
                "type": msg["type"],
                "content": msg["content"],
                "created_at": msg.get("created_at") or datetime.utcnow().isoformat(),
                "file_urls": msg.get("file_urls")
            }
            if "reasoning_content" in msg:
                message_item["reasoning_content"] = msg["reasoning_content"]
            
            formatted_messages.append(message_item)

        return {
            "code": 200,
            "message": "success",
            "data": formatted_messages[-limit:],  # 简单的切片分页
        }
    except Exception as e:
        logger.error(f"Error fetching messages for session_id={session_id}: {str(e)}", exc_info=True)
        return {"code": 500, "message": str(e), "data": None}
