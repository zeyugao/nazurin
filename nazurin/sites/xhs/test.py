import requests
def api_demo(url):
    server = "http://127.0.0.1:8000/xhs/"
    data = {
        "url": url,
        "download": False
    }
    response = requests.post(server, json=data)
    print(response.text)

if __name__ == '__main__':
    image = '"79 【哇哦！混搭jk来啦！ - 不吃榴莲 | 小红书 - 你的生活指南】 😆 3FPIPkS2wu9BGRh 😆 https://www.xiaohongshu.com/discovery/item/67a1a17f0000000018010bc6?source=webshare&xhsshare=pc_web&xsec_token=AB7h0XKTH3d3haMJo8Pea3ls3eb1GZ6HVVOAxapmeYztw=&xsec_source=pc_share",'
    video = '33 【ootd仙女氛围感新中式穿搭💗 - 3mer | 小红书 - 你的生活指南】 😆 ZZbtmJ4qiAA8avb 😆 https://www.xiaohongshu.com/discovery/item/6462167f0000000027011ea7?source=webshare&xhsshare=pc_web&xsec_token=ABEZHlPZ5CNKcqv0fwT_LvmAgcZWumyepR4ELYfSX4fsI=&xsec_source=pc_share'
    api_demo(video)