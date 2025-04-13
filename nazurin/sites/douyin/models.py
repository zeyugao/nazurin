from dataclasses import dataclass

from nazurin.models import Illust, Image
from nazurin.utils import Request
from nazurin.utils.network import NazurinRequestSession
from .config import HEADER

@dataclass
class DouyinImage(Image):

    async def size(self, **kwargs):
        return await super().size(headers=HEADER, **kwargs)
    

@dataclass
class DouyinIllust(Illust):

    async def download(self, *, request_class: NazurinRequestSession = Request, **kwargs):
        # logger.info("ignore douyin images download!")
        await super().download(headers=HEADER, **kwargs)
