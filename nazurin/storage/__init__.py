"""Nazurin storage drivers and storage manager."""

import asyncio
import importlib
from typing import ClassVar, List

from nazurin.config import STORAGE, DANBOORU_SITE_URL, DANBOORU_USERNAME, DANBOORU_API_KEY
from nazurin.models import Illust
from nazurin.utils import logger
from .danbooru import MyDanbooru


class Storage:
    """Storage manager."""

    disks: ClassVar[List[object]] = []
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

    def danbooru_upload(self, illust: Illust):
        danbooru_metadata = illust.danbooru_metadata
        if danbooru_metadata is None:
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

        try:
            self.danbooru_client.bulk_upload_then_post(
                files=files,
                tags=tags,
                **danbooru_metadata['posts'],
            )
        except Exception as e:
            logger.exception(e)

    async def store(self, illust: Illust):
        self.danbooru_upload(illust)
        tasks = [disk.store(illust.all_files) for disk in self.disks]
        await asyncio.gather(*tasks)
        logger.info("Storage completed")
