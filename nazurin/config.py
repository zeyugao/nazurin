import enum
import hashlib
from os import path
from typing import Optional

from environs import Env

env = Env()
# read config from .env file if exists
env.read_env()

ENV: str = env.str("ENV", default="production")
TOKEN: str = env.str("TOKEN")

# Webhook url, eg: https://xxx.fly.dev/, should end with '/'
WEBHOOK_URL: str = env.str("WEBHOOK_URL", default=None)
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = hashlib.sha256(TOKEN.encode()).hexdigest()
HOST: str = env.str("HOST", default="0.0.0.0")
# Port is automatically set if on Heroku or fly.io
PORT: int = env.int("PORT", default=80)

STORAGE: list[str] = env.list("STORAGE", subcast=str, default=["Local"])
STORAGE_DIR: str = env.str("STORAGE_DIR", default="Pictures")

DANBOORU_SITE_URL: str = env.str("DANBOORU_SITE_URL", default="https://danbooru.donmai.us")
DANBOORU_USERNAME: str = env.str("DANBOORU_USERNAME", default=None)
DANBOORU_API_KEY: str = env.str("DANBOORU_API_KEY", default=None)

DATABASE: str = env.str("DATABASE", default="Local")
# Nazurin data collection in database
NAZURIN_DATA: str = "nazurin"
# Ignored items in image caption
CAPTION_IGNORE: list[str] = env.list("CAPTION_IGNORE", subcast=str, default=[])

GALLERY_ID: Optional[int] = env.int("GALLERY_ID", default=None)

ADMIN_ID: int = env.int("ADMIN_ID")
IS_PUBLIC: bool = env.bool("IS_PUBLIC", default=False)
# If IS_PUBLIC is True, the following items will be ignored
ALLOW_ID: list[int] = env.list("ALLOW_ID", subcast=int, default=[])
ALLOW_USERNAME: list[str] = env.list("ALLOW_USERNAME", default=[])
ALLOW_GROUP: list[int] = env.list("ALLOW_GROUP", subcast=int, default=[])

RETRIES: int = env.int("RETRIES", default=5)
TIMEOUT: int = env.int("TIMEOUT", default=20)
DOWNLOAD_CHUNK_SIZE: int = env.int("DOWNLOAD_CHUNK_SIZE", default=4096)
MAX_PARALLEL_DOWNLOAD: int = env.int("MAX_PARALLEL_DOWNLOAD", default=5)
MAX_PARALLEL_UPLOAD: int = env.int("MAX_PARALLEL_UPLOAD", default=5)
PROXY: str = env.str("HTTP_PROXY", default=None)
UA: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Local directory to store database and temporary files
DATA_DIR: str = "data"
TEMP_DIR: str = '/tmp/nazurin'
CLEANUP_INTERVAL: int = env.int("CLEANUP_INTERVAL", default=7)
ACCESS_LOG_FORMAT: str = '%a "%r" %s %b "%{Referer}i" "%{User-Agent}i"'
LOG_LEVEL: int = env.log_level("LOG_LEVEL", default="INFO")


class FeedbackType(str, enum.Enum):
    REPLY = "reply"
    REACTION = "reaction"
    BOTH = "both"
    NONE = "none"


FEEDBACK_TYPE: FeedbackType = env.enum(
    "FEEDBACK_TYPE",
    default=FeedbackType.REPLY,
    enum=FeedbackType,
    by_value=True,
)
