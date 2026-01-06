import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from app.services.agent_service import agent_service
from app.db.session import get_session
from app.db.models import Conversation, User
from app.schemas.conversation import ConversationCreate, ConversationResponse

router = APIRouter()

from sqlmodel import Session, select, func


@router.get("/conversations", response_model=dict)
async def get_conversations(
    page: int = 1, size: int = 20, session: Session = Depends(get_session)
):
    """
    获取会话列表
    """
    user_id = 1  # 模拟用户 ID

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
    # 暂时模拟用户 ID (MVP 阶段未集成完整 Auth)
    # 实际应从 current_user 获取
    user_id = 1

    # 确保存在一个默认用户，否则外键报错
    # 仅用于开发环境
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        user = User(
            id=user_id,
            username="admin",
            email="admin@example.com",
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

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": db_conversation.id,
            "title": db_conversation.title,
            "created_at": db_conversation.created_at.isoformat(),
        },
    }


@router.delete("/conversations/{session_id}", response_model=dict)
async def delete_conversation(session_id: str, session: Session = Depends(get_session)):
    """
    删除会话
    """
    user_id = 1  # 模拟用户 ID

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
async def get_conversation_messages(session_id: str, limit: int = 50):
    """
    获取会话历史消息
    """
    try:
        messages = await agent_service.get_history_messages(session_id)
        # 转换格式以匹配 API 文档
        # API 文档: id, type, content, created_at, tool_calls...
        # 这里简化返回，主要适配前端展示

        formatted_messages = []
        for idx, msg in enumerate(messages):
            formatted_messages.append(
                {
                    "id": idx + 1,  # 临时生成 ID
                    "type": msg["type"],
                    "content": msg["content"],
                    "created_at": "2024-01-01T00:00:00Z",  # 暂无时间戳
                }
            )

        return {
            "code": 200,
            "message": "success",
            "data": formatted_messages[-limit:],  # 简单的切片分页
        }
    except Exception as e:
        return {"code": 500, "message": str(e), "data": None}
