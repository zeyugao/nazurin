from nazurin.config import env

PRIORITY = 4
COLLECTION = "Xhs"

with env.prefixed("XHS_"):
    API_ENDPOINT: str = env.str(
        "API_ENDPOINT", default="https://xhs.s.elsanna.me/xhs/detail"
    )
    _COOKIE_FALLBACK: str = env.str("COOKIE", default=None)
    API_COOKIE: str = env.str("API_COOKIE", default=_COOKIE_FALLBACK)
    API_PROXY: str = env.str("API_PROXY", default=None)

    with env.prefixed("FILE_"):
        DESTINATION: str = env.str("PATH", default="XHS")
        FILENAME: str = env.str(
            "NAME",
            default="{id_str}_{index} - {user}",
        )
