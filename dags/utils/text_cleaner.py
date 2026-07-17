import re

from core.text_patterns import ALL_CONTENT_PATTERNS, COMMON_PATTERNS

# -------------------------
# 텍스트 정제
# -------------------------
def clean_text(text: str, patterns=ALL_CONTENT_PATTERNS) -> str:
    if not text:
        return ""

    text = text.strip()

    for pattern in patterns:
        text = re.sub(pattern, "", text)

    # 공백 정리
    text = re.sub(r"\s+", " ", text).strip()

    return text

# -------------------------
# 제목 정규화
# -------------------------
def normalize_title(title: str) -> str:
    if not title:
        return ""

    return clean_text(title, COMMON_PATTERNS)

# -------------------------
# 본문 정제
# -------------------------
def clean_content(content: str) -> str:
    if not content:
        return ""

    return clean_text(content)