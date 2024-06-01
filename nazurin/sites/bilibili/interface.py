import re

from nazurin.models import Document
from nazurin.sites import HandlerResult
from nazurin.utils import Request
from nazurin.utils.exceptions import NazurinError

from .api import Bilibili
from .config import COLLECTION

patterns = [
    # https://t.bilibili.com/123456789012345678
    r"t\.bilibili\.com/(\d+)",
    # https://t.bilibili.com/h5/dynamic/detail/123456789012345678
    r"t\.bilibili\.com/h5/dynamic/detail/(\d+)",
    # https://www.bilibili.com/opus/123456789012345678
    r"bilibili\.com/opus/(\d+)",
    r"m\.bilibili\.com/dynamic/(\d+)",
    # b23.tv/O8xWAlB
    r"b23.tv/(\w+)",
]


async def resolve_b23(b23_url: str) -> str:
    b23_url = f"https://b23.tv/{b23_url}"
    async with Request() as request, request.get(b23_url) as response:
        new_url = str(response.url)
        for pattern in patterns:
            match = re.search(pattern, new_url)
            if match:
                return match.group(1)
    raise NazurinError("Dynamic not found for b23.tv link")


async def handle(match: re.Match) -> HandlerResult:
    dynamic_id = match.group(1)
    try:
        int(dynamic_id)
    except ValueError:
        dynamic_id = await resolve_b23(dynamic_id)
    illust = await Bilibili().fetch(dynamic_id)
    documnet = Document(id=illust.id, collection=COLLECTION, data=illust.metadata)
    return illust, documnet
