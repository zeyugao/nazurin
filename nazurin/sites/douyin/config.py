from nazurin.config import env

PRIORITY = 4
COLLECTION = "douyin"

HEADER = {
      "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
      "Referer": "https://www.douyin.com/",
      "Cookie": "__ac_nonce=06688805800feabd0488; __ac_signature=_02B4Z6wo00f01uD9yLQAAIDDPIRXALVKsdrg3cwAAN7Fb0; ttwid=1%7CY3tr3NnjDAbW8n6XjSF31tTHDzCCcFEz5Bq12tRDG3o%7C1720221784%7Ca7d14bd093d22c7cb9238cceaf7f4d4e0966eeaa566fc7dea03a1018c76c35bf; UIFID_TEMP=3c3e9d4a635845249e00419877a3730e2149197a63ddb1d8525033ea2b3354c2e4e209d591bdd0dd678a41489f74bacd5643d8ac82c61f801e7d08895f95074527d26a84ac51fd07414c893b452b25a6; douyin.com; device_web_cpu_core=32; device_web_memory_size=8; architecture=amd64; IsDouyinActive=true; home_can_add_dy_2_desktop=%220%22; dy_swidth=1463; dy_sheight=915; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1463%2C%5C%22screen_height%5C%22%3A915%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A32%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A50%7D%22; strategyABtestKey=%221720221787.528%22; fpk1=U2FsdGVkX1/PHJWrr34dlQOtMNbk1POhDsZytNmw7q3nzP6RO1++Ta+Gl7eZ+ZFizEL6AlisgxzYy90lV16jDw==; fpk2=f1f6b29a6cc1f79a0fea05b885aa33d0; stream_player_status_params=%22%7B%5C%22is_auto_play%5C%22%3A0%2C%5C%22is_full_screen%5C%22%3A0%2C%5C%22is_full_webscreen%5C%22%3A0%2C%5C%22is_mute%5C%22%3A1%2C%5C%22is_speed%5C%22%3A1%2C%5C%22is_visible%5C%22%3A1%7D%22; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Atrue%2C%22volume%22%3A0.5%7D; csrf_session_id=6f34e666e71445c9d39d8d06a347a13f; passport_csrf_token=c0ace937a38083a0abf5e537a4d21094; passport_csrf_token_default=c0ace937a38083a0abf5e537a4d21094; FORCE_LOGIN=%7B%22videoConsumedRemainSeconds%22%3A180%7D; odin_tt=e7c9f6ae63907dbd47a55d0d7ab8c1f63e4a39bba773e7aa74002644b636d0c3ec88b980caceb1c125a4191f01228ecb440d627c627680b5d2f7ad4868289321df8da3e73abc0b27a8ef47ecad5d2913; biz_trace_id=21e3deea; xgplayer_user_id=236721600851; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCQWdPWlV1QSs5VmViK3B3M09xSFhJR0tBWmMzQS85emVjeUFnd2FkZHRuYUtWdjJLZUhZVjEzZHc0ZlhndXdBdGtjRDVUYW9QZHBqcnAvcjAwemNLVjg9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoxfQ%3D%3D; bd_ticket_guard_client_web_domain=2; s_v_web_id=verify_ly9bn3e2_K5nh68iF_eJRa_48Fq_80mp_dUR4VkUIOrFr"
}

with env.prefixed("DOUYIN_"), env.prefixed("FILE_"):
    DESTINATION: str = env.str("PATH", default="douyin")
    FILENAME: str = env.str(
        "NAME",
        default="{id_str}_{index} - {user}",
    )
