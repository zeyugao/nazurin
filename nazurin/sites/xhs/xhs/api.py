from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from nazurin.utils import Request
from nazurin.utils.exceptions import NazurinError
from nazurin.utils.logging import logger

from ..config import API_COOKIE, API_ENDPOINT, API_PROXY


class XhsApi:
    def __init__(self) -> None:
        self.endpoint = API_ENDPOINT
        self.cookie = API_COOKIE or None
        self.proxy = API_PROXY or None

    async def get_dynamic(self, note_url: str) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"url": note_url, "download": False}
        if self.cookie:
            payload["cookie"] = self.cookie
        if self.proxy:
            payload["proxy"] = self.proxy

        async with Request() as session:
            async with session.post(self.endpoint, json=payload) as response:
                response.raise_for_status()
                result = await response.json()

        data = result.get("data") if isinstance(result, dict) else None
        if not data:
            message = (
                result.get("message")
                if isinstance(result, dict)
                else "Unknown server response"
            )
            raise NazurinError(f"Failed to fetch XiaoHongShu note: {message}")

        normalized = self._normalize(note_url, data)
        logger.debug("XiaoHongShu normalized data: {}", normalized)
        return normalized

    def get_video_info(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return data.get("video")

    def _normalize(
        self,
        original_url: str,
        raw: Dict[str, Any],
    ) -> Dict[str, Any]:
        note_type = self._map_type(raw.get("作品类型"))
        download_urls = self._ensure_str_list(raw.get("下载地址"))
        gif_urls = [
            url for url in self._ensure_str_list(raw.get("动图地址")) if url is not None
        ]

        images = [
            {
                "urlDefault": url,
                "width": 0,
                "height": 0,
                "index": index,
            }
            for index, url in enumerate(download_urls)
            if url is not None
        ]

        video_info = None
        if note_type == "video":
            video_url = next((url for url in download_urls if url), None)
            if not video_url:
                video_url = next((url for url in gif_urls if url), None)
            if video_url:
                video_info = {
                    "masterUrl": video_url,
                    "format": self._guess_video_format(video_url),
                }

        note_id = str(raw.get("作品ID") or raw.get("作品链接") or "").strip()
        if not note_id and original_url:
            fallback = original_url.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
            note_id = fallback.strip()
        normalized = {
            "noteId": note_id,
            "title": raw.get("作品标题") or "",
            "desc": raw.get("作品描述") or "",
            "type": note_type,
            "time": self._extract_timestamp(raw),
            "url": raw.get("作品链接") or original_url,
            "user": {
                "userId": raw.get("作者ID") or "",
                "nickname": raw.get("作者昵称") or "",
                "link": raw.get("作者链接") or "",
            },
            "tagList": self._parse_tags(raw.get("作品标签")),
            "stats": {
                "collects": raw.get("收藏数量"),
                "comments": raw.get("评论数量"),
                "shares": raw.get("分享数量"),
                "likes": raw.get("点赞数量"),
            },
            "imageList": images,
            "video": video_info,
            "download_urls": download_urls,
            "gif_urls": gif_urls,
            "raw": raw,
        }
        return normalized

    @staticmethod
    def _map_type(value: Optional[str]) -> str:
        if not value:
            return "normal"
        value = str(value)
        if "视频" in value:
            return "video"
        return "normal"

    @staticmethod
    def _ensure_str_list(value: Any) -> List[Optional[str]]:
        if not value:
            return []
        if isinstance(value, list):
            return [str(item) if item is not None else None for item in value]
        return [str(value)]

    def _extract_timestamp(self, raw: Dict[str, Any]) -> int:
        timestamp = raw.get("时间戳")
        if timestamp is not None:
            try:
                return int(float(timestamp) * 1000)
            except (TypeError, ValueError):
                logger.debug("Failed to parse 时间戳 value: {}", timestamp)

        published_at = raw.get("发布时间")
        if isinstance(published_at, str):
            try:
                dt = datetime.strptime(published_at, "%Y-%m-%d_%H:%M:%S")
                return int(dt.timestamp() * 1000)
            except ValueError:
                logger.debug("Failed to parse 发布时间 value: {}", published_at)
        return 0

    @staticmethod
    def _parse_tags(tags: Any) -> List[Dict[str, str]]:
        if not tags:
            return []
        if isinstance(tags, list):
            parsed = []
            for tag in tags:
                if isinstance(tag, dict) and "name" in tag:
                    parsed.append({"name": str(tag["name"])})
                else:
                    parsed.append({"name": str(tag)})
            return parsed
        if isinstance(tags, str):
            cleaned = tags.replace("，", " ").replace(",", " ").replace("#", " #")
            parts = [part.strip() for part in cleaned.split() if part.strip()]
            normalized_parts = []
            for part in parts:
                stripped = part.lstrip("#").replace("[话题]", "").strip()
                if stripped:
                    normalized_parts.append(stripped)
            return [{"name": value} for value in normalized_parts]
        return [{"name": str(tags)}]

    @staticmethod
    def _guess_video_format(url: str) -> str:
        if not url:
            return "mp4"
        path = url.split("?", 1)[0]
        filename = path.rsplit("/", 1)[-1]
        if "." in filename:
            ext = filename.rsplit(".", 1)[-1].lower()
            if 0 < len(ext) <= 5:
                return ext
        return "mp4"
