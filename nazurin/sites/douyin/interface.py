import re

from nazurin.models import Document
from nazurin.sites import HandlerResult

from .api import Douyin
from .config import COLLECTION

patterns = [
    # 3.30 09/23 J@v.fo PKJ:/ 宝宝你是一个白巧小蛋糕 # cos # 碧蓝航线 # 可畏  https://v.douyin.com/ifwEwmBg/ 复制此链接，打开Dou音搜索，直接观看视频！
    # https://www.douyin.com/video/7465981563767901498
    r"(.*\.douyin\.com/.*)",
]


async def handle(match: re.Match) -> HandlerResult:
    dynamic_id = match.group(1)
    illust = await Douyin().fetch(dynamic_id)
    # print(illust)
    documnet = Document(id=illust.id, collection=COLLECTION, data=illust.metadata)
    return illust, documnet
