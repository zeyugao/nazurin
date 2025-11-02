from typing import List, Tuple

from nazurin.models import Caption, Illust, Image, File, Ugoira
from nazurin.utils import Request
from nazurin.utils.exceptions import NazurinError
from nazurin.utils.logging import logger

from .config import DESTINATION, FILENAME
from .xhs import XhsApi


class Xhs:
    def __init__(self):
        self.api = XhsApi()

    def parse_danbooru_metadata(self, note_id: str, data: dict) -> dict:
        """Parse Danbooru metadata from XHS note."""
        user = data.get("user", {})
        user_id = (user.get("userId") or "").strip()
        nickname = (user.get("nickname") or "").strip()
        artist_name = f"xhs_{user_id}" if user_id else f"xhs_{nickname or 'unknown'}"

        profile_url = user.get("link")
        if not profile_url and user_id:
            profile_url = f"https://www.xiaohongshu.com/user/profile/{user_id}"

        tags: List[str] = []
        for tag in data.get("tagList", []):
            if isinstance(tag, dict):
                name = tag.get("name")
            else:
                name = str(tag)
            if name:
                tags.append(name.strip())

        return {
            "artist": {
                "name": artist_name,
                "other_names": nickname,
                "url_string": profile_url or "",
            },
            "posts": {
                "source": data.get("url")
                or f"https://www.xiaohongshu.com/discovery/item/{note_id}",
                "artist_commentary_title": data.get("title", ""),
                "artist_commentary_desc": data.get("desc", ""),
            },
            "tag_str": "xhs",
            "tags": tags,
        }

    async def fetch(self, dynamic_id: str) -> Illust:
        """Fetch images and detail."""
        data = await self.api.get_dynamic(dynamic_id)
        self.url = (data.get("url") or dynamic_id).split("?", 1)[0]
        logger.debug("XiaoHongShu final data: {}", data)

        # 判断链接类型/Judge link type
        url_type = data["type"]
        caption = self.build_caption(self.url, data)
        if url_type == "video":
            illust = await self.get_video(data)
        elif url_type == "normal":
            illust = await self.get_images(data)
        else:
            illust = caption

        # Add danbooru metadata to the illust
        if isinstance(illust, Illust) or isinstance(illust, Ugoira):
            illust.danbooru_metadata = self.parse_danbooru_metadata(
                data["noteId"], data
            )

        return illust

    async def get_video(self, data: dict) -> Ugoira:
        # 将信息储存在字典中/Store information in a dictionary
        video_data = self.api.get_video_info(data)
        if not video_data:
            raise NazurinError("No video found")

        url = video_data.get("masterUrl")
        if not url:
            raise NazurinError("No video URL found")
        video_format = (video_data.get("format") or "mp4").lstrip(".")
        format_suffix = f".{video_format}"
        destination, filename = self.get_storage_dest(data, format_suffix)
        file = File(filename, url, destination)
        async with Request() as session:
            await file.download(session)
        return Ugoira(data["noteId"], file, self.build_caption(self.url, data), data)

    async def get_images(self, data: dict) -> List[Image]:
        """Get all images in a dynamic card."""

        images = data.get("imageList", None)
        if not images:
            raise NazurinError("No image found")

        imgs = []
        for index, pic in enumerate(images):
            url = pic.get("urlDefault")
            if not url:
                continue
            extension = self._guess_extension(url, ".jpg")
            destination, filename = self.get_storage_dest(data, extension, index)

            size = None
            imgs.append(
                Image(
                    filename,
                    url,
                    destination,
                    data["noteId"],
                    size,
                    pic.get("width", 0),
                    pic.get("height", 0),
                ),
            )
        if not imgs:
            raise NazurinError("No valid image found")
        return Illust(data["noteId"], imgs, self.build_caption(self.url, data), data)

    @staticmethod
    def get_storage_dest(
        data: dict, file_format: str, index: int = 0
    ) -> Tuple[str, str]:
        """
        Format destination and filename.
        """
        raw_time = data.get("time") or 0
        try:
            timestamp = int(float(raw_time) / 1000)
        except (TypeError, ValueError):
            timestamp = 0

        user = data.get("user", {}).get("nickname") or "unknown"
        context = {
            **data,
            "user": user,
            # Original filename, without extension
            "index": index,
            "filename": str(data["noteId"]),
            "timestamp": timestamp,
            "extension": file_format,
            "id_str": str(data["noteId"]),
        }
        return (
            DESTINATION.format_map(context),
            FILENAME.format_map(context) + file_format,
        )

    @staticmethod
    def build_caption(url: str, data: dict) -> Caption:
        author = data.get("user", {}).get("nickname") or "XiaoHongShu"
        return Caption(
            {
                "author": f"#{author}",
                "title": data.get("title", ""),
                "url": (url or "").split("?", 1)[0],
            },
        )

    @staticmethod
    def _guess_extension(url: str, default: str = ".jpg") -> str:
        if not url:
            return default
        path = url.split("?", 1)[0]
        filename = path.rsplit("/", 1)[-1]
        if "." in filename:
            ext = filename.rsplit(".", 1)[-1].lower()
            if ext:
                return f".{ext}"
        if "/format/" in url:
            candidate = url.rsplit("/format/", 1)[-1]
            for delimiter in ("/", "&", "?"):
                candidate = candidate.split(delimiter, 1)[0]
            candidate = candidate.strip().lower()
            if candidate:
                return f".{candidate}"
        return default
