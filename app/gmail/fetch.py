from app.gmail.auth import get_gmail_service
from base64 import urlsafe_b64decode
import re


def _decode_body(payload):
    """Extract plain text from Gmail message payload."""
    body = ""

    if "parts" in payload:
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            if mime_type == "text/plain":
                data = part["body"].get("data")
                if data:
                    body += urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    else:
        data = payload["body"].get("data")
        if data:
            body += urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return body


def _clean_text(text: str) -> str:
    """Remove excessive whitespace and signatures."""
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"--\s.*", "", text, flags=re.DOTALL)  # crude signature removal
    return text.strip()


def fetch_unread_threads(max_threads=10):
    service = get_gmail_service()

    response = service.users().threads().list(
        userId="me",
        q="is:unread in:inbox -category:promotions",
        maxResults=max_threads
    ).execute()

    threads = response.get("threads", [])
    results = []

    for thread in threads:
        thread_id = thread["id"]

        thread_data = service.users().threads().get(
            userId="me",
            id=thread_id,
            format="full"
        ).execute()

        messages_text = []

        for msg in thread_data["messages"]:
            payload = msg["payload"]
            body = _decode_body(payload)
            cleaned = _clean_text(body)

            if cleaned:
                messages_text.append(cleaned)

        if messages_text:
            results.append({
                "thread_id": thread_id,
                "text": "\n\n---\n\n".join(messages_text)
            })

    return results
