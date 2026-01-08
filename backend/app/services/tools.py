from langchain_core.tools import tool
from langchain_elasticsearch import ElasticsearchStore
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
import logging
import os
import base64
import mimetypes
from pathlib import Path
from app.utils.logger import get_logger

# 配置日志
logger = get_logger(__name__)

# 全局变量缓存 VectorStore 实例，避免每次调用工具都重新连接
_vectorstore = None

def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        try:
            logger.info("Initializing Elasticsearch connection...")
            # 1. 初始化 Embedding 模型
            embeddings = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                base_url=settings.OPENAI_BASE_URL,
                api_key=settings.OPENAI_API_KEY,
                check_embedding_ctx_length=False,
            )

            # 2. 连接到现有索引
            _vectorstore = ElasticsearchStore(
                es_url=settings.ES_URL,
                index_name=settings.ES_INDEX_NAME,
                embedding=embeddings,
                es_user=settings.ES_USER if settings.ES_USER else None,
                es_password=settings.ES_PASSWORD if settings.ES_PASSWORD else None,
            )
            logger.info(f"✅ Successfully connected to Elasticsearch index '{settings.ES_INDEX_NAME}'")
            print(f"✅ Successfully connected to Elasticsearch index '{settings.ES_INDEX_NAME}'")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Elasticsearch: {e}", exc_info=True)
            print(f"❌ Failed to connect to Elasticsearch: {e}")
            return None
    return _vectorstore

@tool
def magic_calculator(a: int, b: int) -> int:
    """
    一个神奇的计算器，它会将两个数字相加，然后乘以 2。
    用于演示工具调用。
    """
    logger.info(f"Tool called: magic_calculator with a={a}, b={b}")
    return (a + b) * 2

@tool
def get_weather(city: str) -> str:
    """
    获取指定城市的天气。
    """
    logger.info(f"Tool called: get_weather with city={city}")
    return f"{city} 的天气是晴朗，气温 25 度。"

@tool
def search_knowledge_base(query: str) -> str:
    """
    查阅知识库（Elasticsearch），获取关于 LangChain、Elasticsearch 或 RAG 相关的专业知识。
    当用户询问技术概念、框架介绍或具体实现细节时，请优先使用此工具。
    """
    logger.info(f"Tool called: search_knowledge_base with query={query}")
    vectorstore = get_vectorstore()
    if not vectorstore:
        return "知识库连接失败，暂时无法查询。"
    
    try:
        # 执行相似度搜索，获取前 3 个相关片段
        docs = vectorstore.similarity_search(query, k=3)
        if not docs:
            logger.info("No documents found in knowledge base.")
            return "知识库中没有找到相关内容。"
            
        # 格式化返回结果
        result = "\n\n".join([f"--- 片段 {i+1} ---\n{doc.page_content}" for i, doc in enumerate(docs)])
        logger.info(f"Found {len(docs)} documents.")
        return result
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}", exc_info=True)
        return f"查询知识库时发生错误: {str(e)}"

@tool
def ark_analyze_image(image_path: str) -> str:
    """
    分析图片内容并生成文生图提示词。支持本地路径或 HTTP 链接。
    输出包含详细版和精简版两种格式的提示词，包含主体、场景、风格、构图、光线等要素。
    """
    logger.info(f"Tool called: ark_analyze_image with image_path={image_path}")
    try:
        try:
            from volcenginesdkarkruntime import Ark
        except Exception:
            return "[ERROR] Ark SDK 未安装，请执行: pip install volcenginesdkarkruntime"

        api_key = settings.OPENAI_API_KEY
        if not api_key:
            return "[ERROR] 未设置 OPENAI_API_KEY 环境变量"
        
        s = (image_path or "").strip()
        if not s:
            return "[ERROR] 未提供图片路径"

        data_url = ""
        try:
            if s.lower().startswith("http://") or s.lower().startswith("https://"):
                import requests
                resp = requests.get(s, timeout=60)
                resp.raise_for_status()
                content = resp.content
                ct = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
                if not ct or not ct.startswith("image/"):
                    ct_guess, _ = mimetypes.guess_type(s)
                    ct = ct_guess if ct_guess and ct_guess.startswith("image/") else "image/jpeg"
                b64 = base64.b64encode(content).decode("utf-8")
                data_url = f"data:{ct};base64,{b64}"
            else:
                with open(s, "rb") as f:
                    content = f.read()
                ct, _ = mimetypes.guess_type(s)
                if not ct:
                    ct = "image/jpeg"
                b64 = base64.b64encode(content).decode("utf-8")
                data_url = f"data:{ct};base64,{b64}"
        except Exception as e:
            return f"[ERROR] 读取或下载图片失败: {e}"

        client = Ark(api_key=api_key, base_url=settings.OPENAI_BASE_URL)
        resp = client.chat.completions.create(
            model=settings.ARK_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {"type": "text", "text": "请用中文解读这张图片，并按以下固定格式输出两版文生图提示词。不得出现英文和符号*。输出格式：详细版：主体：…；场景：…；风格：…；构图：…；光线：…；色彩：…；材质：…；镜头：…；文字内容：…；尺寸比例：…；其他要点：…。精简版：主体：…；场景：…；风格：…；构图：…；光线：…；色彩：…；材质：…；镜头：…；文字内容：…；尺寸比例：…；其他要点：…。不可识别的项目填写“无”。"},
                    ],
                }
            ],
            stream=False,
        )

        content = resp.choices[0].message.content
        if isinstance(content, list):
            parts = []
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    parts.append(c.get("text", ""))
            return "\n".join([p for p in parts if p]).strip() or ""
        return str(content)
    except Exception as e:
        logger.error(f"Error in ark_analyze_image: {e}", exc_info=True)
        return f"[ERROR] {e}"

# 基础工具列表
base_tools = [
    magic_calculator,
    get_weather,
    search_knowledge_base,
    ark_analyze_image,
]
