# -------------------------
# 노이즈 키워드
# -------------------------
NOISE_PATTERNS = [
    r"\s*-\s*기사\s*스크랩.*",
    r"\s*-\s*댓글.*",
    r"\s*-\s*공유.*",
    r"\s*-\s*글자\s*크기.*",
    r"\s*-\s*프린트.*",
    r"\S+\s*기자\s*=",
    r".*Google 검색.*",
    r".*저작권.*",
    r".*무단\s*전재.*",
    r".*서비스\s*이용\s*제한.*",
    r".*AI\s*학습\s*활용.*",
    r"[■▲◆●▪︎▶►※]",
]

COMMON_PATTERNS = [
    r"\[.*?\]",
    r"\(.*?\)",
]

ALL_CONTENT_PATTERNS = COMMON_PATTERNS + NOISE_PATTERNS