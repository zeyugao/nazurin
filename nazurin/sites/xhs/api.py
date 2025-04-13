from typing import List, Tuple

from nazurin.models import Caption, Illust, Image, File, Ugoira
from nazurin.utils import Request
from nazurin.utils.decorators import network_retry
from nazurin.utils.exceptions import NazurinError
from nazurin.utils.logging import logger

from .config import DESTINATION, FILENAME
from .xhs import XhsApi


class Xhs:

    def __init__(self):
        self.api = XhsApi()

    def parse_danbooru_metadata(self, note_id: str, data: dict) -> dict:
        """Parse Danbooru metadata from XHS note."""
        user = data["user"]
        user_id = user.get("userId", "")
        nickname = user.get("nickname", "")
        
        # Extract tags from tagList if available
        tags = []
        if "tagList" in data and data["tagList"]:
            tags = [tag["name"] for tag in data["tagList"]]
            
        return {
            'artist': {
                'name': f'xhs_{user_id}',
                'other_names': nickname,
                'url_string': f'https://www.xiaohongshu.com/user/profile/{user_id}'
            },
            'posts': {
                'source': f'https://www.xiaohongshu.com/discovery/item/{note_id}',
                'artist_commentary_title': data.get('title', ''),
                'artist_commentary_desc': data.get('desc', ''),
            },
            'tag_str': 'xhs',
            'tags': tags
        }

    async def fetch(self, dynamic_id: str) -> Illust:
        """Fetch images and detail."""
        self.url = dynamic_id
        data = await self.api.get_dynamic(dynamic_id)
        logger.info(data)

        # 判断链接类型/Judge link type
        url_type = data["type"]
        caption = self.build_caption(self.url, data)
        if url_type == 'video':
            illust = await self.get_video(data)
        elif url_type == 'normal':
            illust = await self.get_images(data)
        else:
            illust = caption
            
        # Add danbooru metadata to the illust
        if isinstance(illust, Illust) or isinstance(illust, Ugoira):
            illust.danbooru_metadata = self.parse_danbooru_metadata(data['noteId'], data)
            
        return illust

    async def get_video(self, data: dict) -> Ugoira:
        # 将信息储存在字典中/Store information in a dictionary
        video_data = self.api.get_video_info(data)
        if not video_data:
            raise NazurinError("No video found")
        
        url = video_data['masterUrl']
        video_format = video_data['format']
        format = '.{}'.format(video_format)
        destination, filename = self.get_storage_dest(data, format)
        file = File(filename, url, destination)
        async with Request() as session:
            await file.download(session)
        return Ugoira(data['noteId'], file, self.build_caption(self.url, data), data)
    
    async def get_images(self, data: dict) -> List[Image]:
        """Get all images in a dynamic card."""
        

        images = data.get('imageList',None)
        if not images or len(images) == 0:
            raise NazurinError("No image found")
    
        imgs = []
        for index, pic in enumerate(images):
            url = pic['urlDefault']
            extension = '.jpg'
            destination, filename = self.get_storage_dest( data, extension, index)
 
            size = None
            imgs.append(
                Image(
                    filename,
                    url,
                    destination,
                    data['noteId'],
                    size,
                    pic['width'],
                    pic['height'],
                ),
            )
        return Illust(data['noteId'], imgs, self.build_caption(self.url, data), data)

    @staticmethod
    def get_storage_dest(data: dict, file_format, index: int = 0) -> Tuple[str, str]:
        """
        Format destination and filename.
        """
        timestamp = int(data['time'] / 1000)

        user = data["user"]["nickname"]
        context = {
            **data,
            "user": user,
            # Original filename, without extension
            "index": index,
            "filename": data['noteId'],
            "timestamp": timestamp,
            "extension": file_format,
            "id_str": data['noteId'],
        }
        return (
            DESTINATION.format_map(context),
            FILENAME.format_map(context) + file_format,
        )

    @staticmethod
    def build_caption(url, data: dict) -> Caption:
        return Caption(
            {
                "author": "#" + data["user"]["nickname"],
                "title": data["title"],
                "url": url.split('?')[0]
            },
        )
