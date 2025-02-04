from nazurin.config import env

PRIORITY = 4
COLLECTION = "douyin"

with env.prefixed("DOUYIN_"), env.prefixed("FILE_"):
    DESTINATION: str = env.str("PATH", default="douyin")
    FILENAME: str = env.str(
        "NAME",
        default="{id_str}_{index} - {user}",
    )
