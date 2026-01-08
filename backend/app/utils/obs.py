import os
from obs import ObsClient
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

def get_obs_client():
    return ObsClient(
        access_key_id=settings.OBS_AK,
        secret_access_key=settings.OBS_SK,
        server=settings.OBS_ENDPOINT
    )

def upload_content_to_obs(content, object_key):
    """
    上传内容到华为云 OBS
    """
    try:
        obs_client = get_obs_client()
        bucket_name = settings.OBS_BUCKET
        
        # 上传二进制内容
        resp = obs_client.putContent(bucket_name, object_key, content=content)
        
        if resp.status < 300:
            logger.info(f"Successfully uploaded to OBS: {object_key}")
            return {"success": True, "object_key": object_key}
        else:
            logger.error(f"Failed to upload to OBS: {resp.errorCode}, {resp.errorMessage}")
            return {"success": False, "error": f"{resp.errorCode}: {resp.errorMessage}"}
    except Exception as e:
        logger.error(f"Error uploading to OBS: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        if 'obs_client' in locals():
            obs_client.close()
