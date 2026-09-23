# -------------------------
# 이모지
# -------------------------
EMOJI_PATTERN = (
    r"[\U0001F300-\U0001FAFF"  # 대부분의 이모지
    r"\U00002600-\U000026FF"  # ☀ ☁ ☂ ☎ 등
    r"\U00002700-\U000027BF"  # ✂ ✈ ✔ ✨ 등
    r"]+"
)

EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

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
    r"Key\s*Points\s*-?\s*",
    EMOJI_PATTERN,
    EMAIL_PATTERN
]

COMMON_PATTERNS = [
    r"\[.*?\]",
    r"\(.*?\)",
]

ALL_CONTENT_PATTERNS = COMMON_PATTERNS + NOISE_PATTERNS