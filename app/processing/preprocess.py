import re
from html import unescape


MAX_CHARS = 3000  # safe for Bedrock + LLaMA


def clean_email_text(raw_text: str) -> str:
    if not raw_text:
        return ""

    text = unescape(raw_text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove common newsletter / footer noise
    noise_patterns = [
        r"unsubscribe.*",
        r"view this email.*",
        r"manage preferences.*",
        r"privacy policy.*",
        r"terms of service.*",
        r"sent from my .*",
        r"this message was sent to .*",
    ]

    for p in noise_patterns:
        text = re.sub(p, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Remove excessive whitespace
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"\s{2,}", " ", text).strip()

    # Keep ONLY the most recent content
    # (Gmail threads often repeat history)
    split_markers = [
        "On ", "From:", "Sent:", "-----Original Message-----"
    ]

    for marker in split_markers:
        if marker in text:
            text = text.split(marker)[0]

    # Hard truncate to protect model
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]

    return text.strip()
