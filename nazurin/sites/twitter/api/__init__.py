import re
from nazurin.models import Illust
from nazurin.utils.exceptions import NazurinError

from ..config import API, TwitterAPI
from .syndication import SyndicationAPI
from .web import WebAPI

hashtag_pattern = re.compile(r'[#|＃](\S+)')


class Twitter:
    syndication = SyndicationAPI()
    web = WebAPI()

    def parse_danbooru_metadata(self, tweet_id: int, metadata: dict) -> dict:
        user_detail = metadata['user']
        screen_name = user_detail['screen_name']
        user_id = user_detail['id_str']
        name = user_detail['name']

        hash_tag = hashtag_pattern.findall(metadata['text'])

        return {
            'artist': {
                'name': screen_name.strip('_').replace('__', '_'),
                'other_names': f'{name} {user_id}',
                'url_string': f'https://twitter.com/{screen_name}'
            },
            'tags': hash_tag,
            'posts': {
                'source': f'https://twitter.com/{screen_name}/status/{tweet_id}',
                'artist_commentary_title': '',
                'artist_commentary_desc': metadata['text'],
            },
            'tag_str': 'tweet',
        }

    async def fetch(self, status_id: int) -> Illust:
        """Fetch & return tweet images and information."""
        if API == TwitterAPI.SYNDICATION:
            illust = await Twitter.syndication.fetch(status_id)
        elif API == TwitterAPI.WEB:
            illust = await Twitter.web.fetch(status_id)
        else:
            raise NazurinError(f"Unsupported Twitter API type: {API}")

        danbooru_metadata = self.parse_danbooru_metadata(status_id, illust.metadata)

        illust.danbooru_metadata = danbooru_metadata
        return illust


__all__ = ["Twitter"]
