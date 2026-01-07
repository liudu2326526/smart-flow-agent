from langchain_core.tools import tool
from langchain_elasticsearch import ElasticsearchStore
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
import logging
from pathlib import Path
from app.utils.logger import get_logger

# 配置日志
logger = get_logger(__name__, "tools.log")

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

# 基础工具列表
base_tools = []
