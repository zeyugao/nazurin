"""Nazurin storage drivers and storage manager."""

import asyncio
import importlib
import os
from typing import ClassVar, Callable, TypeVar, Any, Coroutine

from nazurin.config import STORAGE, DANBOORU_SITE_URL, DANBOORU_USERNAME, DANBOORU_API_KEY
from nazurin.models import Illust
from nazurin.utils import logger
from .danbooru import MyDanbooru
from pybooru.exceptions import PybooruHTTPError


R = TypeVar("R")


def async_wrapper(function: Callable[..., R]) -> Callable[..., Coroutine[Any, Any, R]]:
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, function, *args, **kwargs)
        return result

    return wrapper


class Storage:
    """Storage manager."""

    disks: ClassVar[list[object]] = []
    danbooru_client: MyDanbooru = MyDanbooru(
        site_url=DANBOORU_SITE_URL,
        username=DANBOORU_USERNAME,
        api_key=DANBOORU_API_KEY,
    )

    def load(self):
        """Dynamically load all storage drivers."""
        for driver_name in STORAGE:
            driver = importlib.import_module("nazurin.storage." + driver_name.lower())
            self.disks.append(getattr(driver, driver_name)())
        logger.info("Loaded {} storage(s), using: {}", len(self.disks), STORAGE)

    @async_wrapper
    def danbooru_upload(self, illust: Illust):
        danbooru_metadata = illust.danbooru_metadata
        if not danbooru_metadata:
            return

        try:
            artist_detail = danbooru_metadata['artist']
            self.danbooru_client.artist_create(**artist_detail)
        except Exception as e:
            logger.info(f"Unable to create artists: {e}")

        files = [file.path for file in illust.all_files]
        tags = [
            danbooru_metadata['artist']['name'],
            danbooru_metadata['tag_str'],
        ]
        if 'tags' in danbooru_metadata:
            tags.extend(danbooru_metadata['tags'])

        exception = None

        for _ in range(3):
            try:
                self.danbooru_client.bulk_upload_then_post(
                    files=files,
                    tags=tags,
                    **danbooru_metadata['posts'],
                )
                return
            except PybooruHTTPError as e:
                if 'Duplicate post' in str(e):
                    logger.info("Duplicate post")
                    return
                logger.exception(e)
                exception = e
            except Exception as e:
                logger.exception(e)
                exception = e

        if exception:
            raise exception

    async def store(self, illust: Illust):
        await self.danbooru_upload(illust)

        try:
            for file in illust.all_files:
                os.unlink(file.path)
        except Exception as e:
            logger.exception(f"Error while deleting files: {e}")
        # tasks = [disk.store(illust.all_files) for disk in self.disks]
        # await asyncio.gather(*tasks)
        logger.info("Storage completed")
