import os
from nazurin.utils import Request
from urllib.parse import urlparse, urlunparse
from datetime import datetime, timezone
from typing import List, Tuple
from .converter import Converter

class XhsApi:

    def __init__(self):
        self.converter = Converter()

    async def get_dynamic(self, dynamic_id: str):
        async with Request() as session:
            async with session.get(dynamic_id) as response:
                response.raise_for_status()
                data = await response.text()
                
            return self.converter.run(data)
        
    def __get_image_token(self, url: str) -> str:
        return "/".join(url.split("/")[5:]).split("!")[0]

    def get_jpg_url(self,url: str) -> str:
        token = self.__get_image_token(url)
        return f"https://sns-img-bd.xhscdn.com/{token}"

    def get_video_info(self, data) -> str:
        try:
            return data['video']['media']['stream']['h264'][0]
        except:
            return None
        
    def get_raw_video_url(self, data) -> str:
        try:
            token = data['video']['consumer']['originVideoKey']
            return f"https://sns-video-bd.xhscdn.com/{token}"
        except:
            return None


if __name__ == '__main__':
    import asyncio
    import json

    loop = asyncio.get_event_loop()
    aa = XhsApi()
    bb = Converter()

    # 图片
    # data = loop.run_until_complete(aa.get_dynamic('https://www.xiaohongshu.com/explore/67a1a17f0000000018010bc6?xsec_token=AB7h0XKTH3d3haMJo8Pea3ls3eb1GZ6HVVOAxapmeYztw=&xsec_source=pc_feed'))
    # cc = bb.run(data)
    # print(json.dumps(cc))
    # if cc['type'] == 'normal':
    # title = cc['title']
    # desc = cc['desc']
    # time = cc['time'] / 1000
    # for pic in cc['imageList']:
    #     url = aa.get_jpg_url(pic['urlDefault'])
    #     print(url)
    
    # 视频
    video = loop.run_until_complete(aa.get_dynamic('http://xhslink.com/a/3agqAg4qWBz7'))
    dd = bb.run(video)
    print(json.dumps(dd))

    aa = 'https://sns-video-bd.xhscdn.com/1040g2so31erog6ig6o705ndut3o099ioi1kgfdg'