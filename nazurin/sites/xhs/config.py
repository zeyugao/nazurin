from nazurin.config import env

PRIORITY = 4
COLLECTION = "Xhs"



with env.prefixed("XHS_"), env.prefixed("FILE_"):
    DESTINATION: str = env.str("PATH", default="XHS")
    FILENAME: str = env.str(
        "NAME",
        default="{id_str}_{index} - {user}",
    )
