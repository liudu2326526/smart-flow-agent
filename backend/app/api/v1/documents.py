import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
from sqlmodel import Session, select
from app.core.config import settings
from app.utils.obs import upload_content_to_obs
from app.utils.logger import get_logger
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.db.session import get_session
from app.db.models import Document, User

logger = get_logger(__name__, "documents.log")

router = APIRouter()

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg"}

@router.get("/documents", response_model=DocumentListResponse, summary="获取文档列表")
async def get_documents(
    user_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_session)
):
    """
    获取用户的文档列表，支持按状态筛选。
    """
    try:
        # 构建查询
        statement = select(Document).where(
            Document.user_id == user_id,
            Document.is_deleted == False
        )
        
        if status:
            statement = statement.where(Document.status == status)
            
        # 按上传时间倒序排列
        statement = statement.order_by(Document.uploaded_at.desc())
        
        documents = db.exec(statement).all()
        
        # 组装响应数据
        doc_list = [
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_path": doc.file_path,
                "status": doc.status,
                "uploaded_at": doc.uploaded_at,
                "size": doc.size
            }
            for doc in documents
        ]
        
        return {
            "code": 200,
            "message": "success",
            "data": doc_list
        }
        
    except Exception as e:
        logger.error(f"获取文档列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取文档列表过程中发生意外错误: {str(e)}")

@router.post("/documents/upload", response_model=DocumentResponse, summary="上传文档到知识库")
async def upload_document(
    user_id: str = Form(..., description="用户标识"),
    file: UploadFile = File(..., description="要上传的文档文件"),
    session_id: Optional[str] = Form(None, description="可选，关联特定会话ID"),
    db: Session = Depends(get_session)
):
    """
    上传文档到知识库，并保存到 OBS 和数据库。
    """
    logger.info(f"收到上传请求: user_id={user_id}, filename={file.filename}, content_type={file.content_type}, session_id={session_id}")
    try:
        user = db.exec(select(User).where(User.id == user_id)).first()
        if not user:
            user = User(
                id=user_id,
                username=f"user_{user_id}",
                email=f"{user_id}@example.com",
                password_hash="hash",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # 1. 校验文件大小
        file_content = await file.read()
        file_size = len(file_content)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件大小超过限制({MAX_FILE_SIZE // (1024*1024)}MB)",
            )

        # 2. 校验文件扩展名
        original_filename = file.filename
        file_ext = os.path.splitext(original_filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式: {file_ext}。支持的格式: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # 2.5 检查同名文件，如果存在则重命名（加日期后缀）
        existing_doc = db.exec(
            select(Document).where(
                Document.filename == original_filename,
                Document.user_id == user_id,
                Document.is_deleted == False
            )
        ).first()
        if existing_doc:
            name_base, name_ext = os.path.splitext(original_filename)
            date_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_filename = f"{name_base}_{date_suffix}{name_ext}"
            logger.info(f"发现同名文件，重命名为: {original_filename}")

        # 3. 构建 OBS 保存路径
        # 路径格式: documents/YYYY-MM-DD/uuid_filename
        date_folder = datetime.now().strftime("%Y-%m-%d")
        unique_id = str(uuid.uuid4())[:8]
        object_key = f"documents/{date_folder}/{unique_id}_{original_filename}".replace("\\", "/")

        # 4. 上传到 OBS
        logger.info(f"正在上传文件到 OBS: {object_key} (大小: {file_size} bytes)")
        upload_result = upload_content_to_obs(file_content, object_key)
        
        if not upload_result.get("success"):
            error_msg = upload_result.get("error")
            logger.error(f"OBS 上传失败: {error_msg}")
            raise HTTPException(status_code=500, detail=f"文件存储服务上传失败: {error_msg}")

        # 5. 保存到数据库
        final_url = f"{settings.OBS_PUBLIC_BASE_URL.rstrip('/')}/{object_key}" if settings.OBS_PUBLIC_BASE_URL else object_key
        db_document = Document(
            user_id=user_id,
            session_id=session_id,
            filename=original_filename,
            file_path=final_url,
            file_type=file_ext,
            size=file_size,
            status="pending",
            is_deleted=False
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        logger.info(f"✅ 文档记录已保存到数据库, ID: {db_document.id}")

        # 6. 返回响应
        return {
            "code": 200,
            "message": "success",
            "data": {
                "id": str(db_document.id),
                "filename": db_document.filename,
                "size": db_document.size,
                "status": db_document.status,
                "url": db_document.file_path
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文档失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传文档过程中发生意外错误: {str(e)}")

@router.delete("/documents/{doc_id}", summary="删除文档 (伪删除)")
async def delete_document(
    doc_id: int,
    user_id: str,
    db: Session = Depends(get_session)
):
    """
    逻辑删除文档记录。
    """
    try:
        # 查找文档
        db_document = db.exec(
            select(Document).where(
                Document.id == doc_id, 
                Document.user_id == user_id,
                Document.is_deleted == False
            )
        ).first()
        
        if not db_document:
            raise HTTPException(status_code=404, detail="文档不存在或已被删除")
        
        # 执行伪删除
        db_document.is_deleted = True
        db.add(db_document)
        db.commit()
        
        logger.info(f"✅ 文档已逻辑删除, ID: {doc_id}")
        
        return {
            "code": 200,
            "message": "success",
            "data": None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除文档过程中发生意外错误: {str(e)}")
