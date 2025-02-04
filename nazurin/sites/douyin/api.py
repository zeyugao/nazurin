import os
from datetime import datetime, timezone
from typing import List, Tuple

from nazurin.models import Caption, Illust, Image, File, Ugoira
from nazurin.utils import Request
from nazurin.utils.decorators import network_retry
from nazurin.utils.exceptions import NazurinError

from .config import DESTINATION, FILENAME

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
            # print(data)
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
        return caption
        # imgs = self.get_images(item)
        # caption = self.build_caption(item)
        # caption["url"] = f"https://www.bilibili.com/opus/{dynamic_id}"
        # return Illust(int(dynamic_id), imgs, caption, item)

    async def get_video(self, data: dict) -> Ugoira:
        # 将信息储存在字典中/Store information in a dictionary
        name = data.get('item_title')
        aweme_id = data.get('aweme_id')
        try:
            all_video_data = data['video']['bit_rate']
            print(all_video_data)
            max_bit_rate_video = max(all_video_data, key=lambda x: x["bit_rate"])
            print(max_bit_rate_video)
            video_format =  '.{}'.format(max_bit_rate_video['format'])
            url = max_bit_rate_video['play_addr']['url_list'][0]
            print("download max_bit_rate_video!!!")
        except Exception:
            print("not has max_bit_rate_video...")
            wm_video_url_HQ = data['video']['play_addr']['url_list'][0]
            nwm_video_url_HQ = wm_video_url_HQ.replace('playwm', 'play')
            video_format = '.mp4'
            url = nwm_video_url_HQ

        destination, filename = self.get_storage_dest(aweme_id, data, video_format)
        file = File(filename, url, destination)
        async with Request() as session:
            await file.download(session)
        return Ugoira(aweme_id, file, self.build_caption(self.dynamic_id, data), data)
    # @staticmethod
    # def get_images(item: dict) -> List[Image]:
    #     """Get all images in a dynamic card."""
    #     major_items = item["modules"]["module_dynamic"]["major"]
    #     if not major_items:
    #         raise NazurinError("No image found")
    #     draw_items = major_items["draw"]["items"]
    #     if len(draw_items) == 0:
    #         raise NazurinError("No image found")
    #     imgs = []
    #     for index, pic in enumerate(draw_items):
    #         url = pic["src"]
    #         destination, filename = Bilibili.get_storage_dest(item, pic, index)
    #         size = pic["size"] * 1024  # size returned by API is in KB
    #         # Sometimes it returns a wrong size that is not in whole bytes,
    #         # in this case we just ignore it.
    #         if size % 1 != 0:
    #             size = None
    #         imgs.append(
    #             Image(
    #                 filename,
    #                 url,
    #                 destination,
    #                 url + "@518w.jpg",
    #                 size,
    #                 pic["width"],
    #                 pic["height"],
    #             ),
    #         )
    #     return imgs

    @staticmethod
    def get_storage_dest(filename:str, data: dict, video_format: str = 'mp4', index: int = 0) -> Tuple[str, str]:
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
            "extension": video_format,
            "id_str": data["aweme_id"],
        }
        return (
            DESTINATION.format_map(context),
            FILENAME.format_map(context) + video_format,
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

    # @staticmethod
    # def cleanup_item(item: dict) -> dict:
    #     try:
    #         del item["basic"]
    #         del item["modules"]["module_author"]["avatar"]
    #         del item["modules"]["module_more"]
    #     except KeyError:
    #         pass
    #     return item
