import os
from datetime import datetime, timezone

from nazurin.models import Caption, Illust, Image
from nazurin.utils import Request
from nazurin.utils.decorators import network_retry
from nazurin.utils.exceptions import NazurinError

from .config import DESTINATION, FILENAME

ERROR_NOT_FOUND = 4101147


class Bilibili:
    @network_retry
    async def get_dynamic(self, dynamic_id: str):
        """Get dynamic data from API."""
        api = (
            f"https://api.bilibili.com/x/polymer/web-dynamic/v1/detail?id={dynamic_id}"
        )
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) "
            "Gecko/20100101 Firefox/135.0"
        )
        async with (
            Request(headers={"User-Agent": ua}) as request,
            request.get(api) as response,
        ):
            response.raise_for_status()
            data = await response.json()
            # For some IDs, the API returns code 0 but empty content
            code = data.get("code")
            if code == ERROR_NOT_FOUND or "data" not in data:
                raise NazurinError("Dynamic not found")
            if code != 0:
                raise NazurinError(
                    f"Failed to get dynamic: code = {code}, "
                    f"message = {data['message']}",
                )
        item = data["data"]["item"]
        return self.cleanup_item(item)

    def parse_danbooru_metadata(self, dynamic_id: int, item: dict) -> dict:
        """Parse Danbooru metadata from dynamic."""
        bili_uid = item['modules']['module_author']['mid']
        name = f'bili_{bili_uid}'
        other_name = item['modules']['module_author']['name']

        desc = item['modules']['module_dynamic']['desc']['text']

        return {
            'artist': {
                'name': name,
                'other_names': other_name,
                'url_string': f'https://space.bilibili.com/{bili_uid}'
            },
            'posts': {
                'source': f'https://t.bilibili.com/{dynamic_id}',
                'artist_commentary_title': '',
                'artist_commentary_desc': desc,
            },
            'tag_str': 'bili_dyn',
        }

    async def fetch(self, dynamic_id: str) -> Illust:
        """Fetch images and detail."""
        item = await self.get_dynamic(dynamic_id)
        imgs = self.get_images(item)
        caption = self.build_caption(item)
        caption["url"] = f"https://www.bilibili.com/opus/{dynamic_id}"
        danbooru_metadata = self.parse_danbooru_metadata(int(dynamic_id), item)
        return Illust(int(dynamic_id), imgs, caption, item, danbooru_metadata=danbooru_metadata)

    @staticmethod
    def get_images(item: dict) -> list[Image]:
        """Get all images in a dynamic card."""
        major_items = item["modules"]["module_dynamic"]["major"]
        if not major_items:
            raise NazurinError("No image found")
        draw_items = major_items["draw"]["items"]
        if len(draw_items) == 0:
            raise NazurinError("No image found")
        imgs = []
        for index, pic in enumerate(draw_items):
            url = pic["src"]
            destination, filename = Bilibili.get_storage_dest(item, pic, index)
            size = pic["size"] * 1024  # size returned by API is in KB
            # Sometimes it returns a wrong size that is not in whole bytes,
            # in this case we just ignore it.
            if size % 1 != 0:
                size = None
            imgs.append(
                Image(
                    filename,
                    url,
                    destination,
                    url + "@518w.jpg",
                    size,
                    pic["width"],
                    pic["height"],
                ),
            )
        return imgs

    @staticmethod
    def get_storage_dest(item: dict, pic: dict, index: int = 0) -> tuple[str, str]:
        """
        Format destination and filename.
        """

        url = pic["src"]
        timestamp = datetime.fromtimestamp(
            item["modules"]["module_author"]["pub_ts"],
            tz=timezone.utc,
        )
        basename = os.path.basename(url)
        filename, extension = os.path.splitext(basename)
        user = item["modules"]["module_author"]
        context = {
            "user": user,
            # Original filename, without extension
            "filename": filename,
            # Image index
            "index": index,
            "timestamp": timestamp,
            "extension": extension,
            "id_str": item["id_str"],
            "pic": pic,
        }
        return (
            DESTINATION.format_map(context),
            FILENAME.format_map(context) + extension,
        )

    @staticmethod
    def build_caption(item: dict) -> Caption:
        modules = item["modules"]
        return Caption(
            {
                "author": "#" + modules["module_author"]["name"],
                "content": modules["module_dynamic"]["desc"]["text"],
            },
        )

    @staticmethod
    def cleanup_item(item: dict) -> dict:
        try:
            del item["basic"]
            del item["modules"]["module_author"]["avatar"]
            del item["modules"]["module_more"]
        except KeyError:
            pass
        return item
