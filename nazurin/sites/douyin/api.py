import os

from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import List, Tuple

from nazurin.models import Caption, Illust, Image, File, Ugoira
from nazurin.utils import Request
from nazurin.utils.decorators import network_retry
from nazurin.utils.exceptions import NazurinError
from nazurin.utils.logging import logger

from .config import DESTINATION, FILENAME
from .models import DouyinIllust, DouyinImage

ERROR_NOT_FOUND = 4101147


class Douyin:
    url_type_code_dict = {
            # common
            0: 'video',
            # Douyin
            2: 'image',
            4: 'video',
            68: 'image',
            # TikTok
            51: 'video',
            55: 'video',
            58: 'video',
            61: 'video',
            150: 'image'
    }

    @network_retry
    async def get_dynamic(self, dynamic_id: str):
        """
            Get dynamic data from API.
            Use API : https://github.com/Evil0ctal/Douyin_TikTok_Download_API
        """
        api = (
            f"http://127.0.0.1:8080/api/hybrid/video_data?url={dynamic_id}&minimal=false"
        )

        async with Request() as request, request.get(api) as response:
            response.raise_for_status()
            data = await response.json()
            # For some IDs, the API returns code 0 but empty content
            # logger.info(data)
            code = data.get("code")
            if code != 200 or not data.get('data',False):
                raise NazurinError(
                    f"Failed to get dynamic: code = {code}, "
                    f"message = {data['message']}",
                )
        return data["data"]
        # return self.cleanup_item(item)

    async def fetch(self, dynamic_id: str) -> Illust:
        """Fetch images and detail."""
        self.dynamic_id = dynamic_id
        data = await self.get_dynamic(dynamic_id)


        # 判断链接类型/Judge link type
        url_type = Douyin.url_type_code_dict.get(data.get('aweme_type'), 'video')
        caption = self.build_caption(dynamic_id, data)
        if url_type == 'video':
            return await self.get_video(data)
        elif url_type == 'image':
            return await self.get_images(data)
        return caption

    async def get_video(self, data: dict) -> Ugoira:
        # 将信息储存在字典中/Store information in a dictionary
        name = data.get('item_title')
        aweme_id = data.get('aweme_id')
        try:
            all_video_data = data['video']['bit_rate']
            logger.info(all_video_data)
            max_bit_rate_video = max(all_video_data, key=lambda x: x["bit_rate"])
            logger.info(max_bit_rate_video)
            video_format =  '.{}'.format(max_bit_rate_video['format'])
            url = max_bit_rate_video['play_addr']['url_list'][0]
            logger.info("download max_bit_rate_video!!!")
        except Exception:
            logger.info("not has max_bit_rate_video...")
            wm_video_url_HQ = data['video']['play_addr']['url_list'][0]
            nwm_video_url_HQ = wm_video_url_HQ.replace('playwm', 'play')
            video_format = '.mp4'
            url = nwm_video_url_HQ

        destination, filename = self.get_storage_dest(aweme_id, data,video_format)
        file = File(filename, url, destination)
        async with Request() as session:
            await file.download(session)
        return Ugoira(aweme_id, file, self.build_caption(self.dynamic_id, data), data)
    


    async def get_images(self, data: dict) -> List[Image]:
        """Get all images in a dynamic card."""
        name = data.get('item_title')
        aweme_id = data.get('aweme_id')

        images = data.get('images',None)
        if not images or len(images) == 0:
            raise NazurinError("No image found")
    
        imgs = []
        for index, pic in enumerate(images):
            url = pic["url_list"][0]
            
            basename = urlparse(url).path
            filename, extension = os.path.splitext(basename)
            destination, filename = self.get_storage_dest(aweme_id, data, extension, index)
 
            size = None
            imgs.append(
                DouyinImage(
                    filename,
                    url,
                    destination,
                    aweme_id,
                    size,
                    pic["width"],
                    pic["height"],
                ),
            )
        return DouyinIllust(int(aweme_id), imgs, self.build_caption(self.dynamic_id, data), data)

    @staticmethod
    def get_storage_dest(filename:str, data: dict, file_format, index: int = 0) -> Tuple[str, str]:
        """
        Format destination and filename.
        """

        timestamp = datetime.fromtimestamp(
            data["create_time"],
            tz=timezone.utc,
        )
        # filename, extension = os.path.splitext(filename)
        user = data["author_user_id"]
        context = {
            **data,
            "user": user,
            # Original filename, without extension
            "index": index,
            "filename": filename,
            "timestamp": timestamp,
            "extension": file_format,
            "id_str": data["aweme_id"],
        }
        return (
            DESTINATION.format_map(context),
            FILENAME.format_map(context) + file_format,
        )

    @staticmethod
    def build_caption(dynamic_id: str, data: dict) -> Caption:
        return Caption(
            {
                "author": "#" + data["author"]["nickname"],
                "content": data["desc"],
                "url": dynamic_id
            },
        )
