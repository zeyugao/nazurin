import re

from nazurin.models import Document
from nazurin.sites import HandlerResult

from .api import Xhs
from .config import COLLECTION

patterns = [
    # https://www.xiaohongshu.com/explore/作品ID?xsec_token=XXX
    # https://www.xiaohongshu.com/discovery/item/作品ID?xsec_token=XXX
    # https://xhslink.com/分享码
    r"(https?://www\.xiaohongshu\.com/explore/[a-zA-Z0-9_\-]+(?:\?[^?\s]*)?)",
    r"(https?://www\.xiaohongshu\.com/discovery/item/[a-zA-Z0-9_\-]+(?:\?[^?\s]*)?)",
    r"(https?://xhslink\.com/[a-zA-Z0-9_\-/]+)"
]


async def handle(match: re.Match) -> HandlerResult:
    dynamic_id = match.group(1)
    illust = await Xhs().fetch(dynamic_id)
    # print(illust)
    documnet = Document(id=illust.id, collection=COLLECTION, data=illust.metadata)
    return illust, documnet
