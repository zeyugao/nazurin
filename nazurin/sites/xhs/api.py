import os

from urllib.parse import urlparse, urlunparse
from datetime import datetime, timezone
from typing import List, Tuple

from nazurin.models import Caption, Illust, Image, File, Ugoira
from nazurin.utils import Request
from nazurin.utils.decorators import network_retry
from nazurin.utils.exceptions import NazurinError
from nazurin.utils.logging import logger

from .config import DESTINATION, FILENAME

ERROR_NOT_FOUND = 4101147


class Xhs:
    CONTENT_TYPE_MAP = {
        "image/png": "png",
        "image/jpeg": "jpeg",
        "image/webp": "webp",
        "video/mp4": "mp4",
        "video/quicktime": "mov",
        "audio/mp4": "m4a",
        "audio/mpeg": "mp3",
    }

    async def get_dynamic(self, dynamic_id: str):
        """
            Get dynamic data from API.
            Use API : https://github.com/Evil0ctal/Douyin_TikTok_Download_API
        """
        api = (
            f"http://127.0.0.1:8000/xhs/"
        )

        async with Request() as request, request.get(api) as response:
            response.raise_for_status()
            data = await response.json()
            # For some IDs, the API returns code 0 but empty content
            logger.info(data)
            msg = data.get("message")
            if msg != '获取小红书作品数据成功' or not data.get('data',False):
                raise NazurinError(
                    f"Failed to get dynamic: msg = {msg}, "
                    f"message = {data}",
                )
        return data["data"]
        # return self.cleanup_item(item)

    async def fetch(self, dynamic_id: str) -> Illust:
        """Fetch images and detail."""
        
        data = await self.get_dynamic(dynamic_id)
        self.dynamic_id = data['作品ID']

        # 判断链接类型/Judge link type
        url_type = data["作品类型"]
        caption = self.build_caption(data)
        if url_type == '视频':
            return await self.get_video(data)
        elif url_type == '图文':
            return await self.get_images(data)
        return caption

    async def get_video_format(self, url) -> str:
        async with Request() as request, request.get(url) as response:
            response.raise_for_status()
            content_type = await response.headers.get("Content-Type")
            format = Xhs.CONTENT_TYPE_MAP.get(content_type,'mp4')
            return format
        
    async def get_video(self, data: dict) -> Ugoira:
        # 将信息储存在字典中/Store information in a dictionary
        url = data.get('下载地址',None)[0]
        if not url:
            raise NazurinError("No video found")
        
        video_format = await self.get_video_format(url)

        destination, filename = self.get_storage_dest(self.dynamic_id, data, video_format)
        file = File(filename, url, destination)
        async with Request() as session:
            await file.download(session)
        return Ugoira(self.dynamic_id, file, self.build_caption(data), data)
    
    async def get_image_info(self, url) -> dict:
        async with Request() as request, request.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            # {"format":"png","width":"1240","height":"1664","size":"2243009","frame_count":"1","bit_depth":"8","md5":"56024e58bff75198e03ed11bc938c3f4","crc32":"4165107902","mime_type":"image/png","colorspace":"srgb"}
        return data

    async def get_images(self, data: dict) -> List[Image]:
        """Get all images in a dynamic card."""
        

        images = data.get('下载地址',None)
        if not images or len(images) == 0:
            raise NazurinError("No image found")
    
        imgs = []
        for index, pic in enumerate(images):
            url = pic
            
            parsed_url = urlparse(url)
            # 修改查询字符串
            media_info_url = urlunparse(parsed_url._replace(query="imageInfo"))
            media_info = self.get_image_info(media_info_url)

            extension = media_info['format']
            # filename = os.basename(parsed_url.path)

            destination, filename = self.get_storage_dest(self.dynamic_id, data, extension, index)
 
            size = None
            imgs.append(
                Image(
                    filename,
                    url,
                    destination,
                    self.dynamic_id,
                    size,
                    media_info["width"],
                    media_info["height"],
                ),
            )
        return Illust(int(self.dynamic_id), imgs, self.build_caption(data), data)

    @staticmethod
    def get_storage_dest(filename:str, data: dict, file_format, index: int = 0) -> Tuple[str, str]:
        """
        Format destination and filename.
        """

        timestamp = datetime.fromtimestamp(
            data["发布时间"],
            tz=timezone.utc,
        )
        # filename, extension = os.path.splitext(filename)
        user = data["作者ID"]
        context = {
            **data,
            "user": user,
            # Original filename, without extension
            "index": index,
            "filename": filename,
            "timestamp": timestamp,
            "extension": file_format,
            "id_str": data["作品ID"],
        }
        return (
            DESTINATION.format_map(context),
            FILENAME.format_map(context) + file_format,
        )

    @staticmethod
    def build_caption(data: dict) -> Caption:
        return Caption(
            {
                "author": "#" + data['作者昵称'],
                "title": data["作品标题"],
                "url": data["作品链接"]
            },
        )
