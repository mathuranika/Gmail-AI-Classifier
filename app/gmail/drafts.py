from app.gmail.auth import get_gmail_service
from app.llm.bedrock import BedrockClassifier
import base64
import email
import email.message
import json

def _thread_has_draft(service, thread_id: str) -> bool:
    """Check if a thread already has a draft."""
    drafts = service.users().drafts().list(userId="me").execute().get("drafts", [])
    for d in drafts:
        msg = service.users().drafts().get(
            userId="me", id=d["id"], format="metadata"
        ).execute()
        if msg.get("message", {}).get("threadId") == thread_id:
            return True
    return False


def generate_reply_text(email_text: str) -> str:
    """
    Ask Bedrock to draft a context-aware reply.
    Tone and length should match urgency and complexity.
    """
    classifier = BedrockClassifier()

    prompt = f"""
You are a professional email assistant.

Rules:
- Draft a reply only (no explanations)
- Match tone and length to urgency and complexity
- Be concise for urgent/simple requests
- Be polite and professional for non-urgent requests

Email to reply to:
\"\"\"{email_text}\"\"\"

Write the email reply body only.
"""

    body = {
        "prompt": prompt,
        "max_gen_len": 200,
        "temperature": 0.2,
        "top_p": 0.9
    }

    # Reuse the same Bedrock client pattern
    response = classifier.client.invoke_model(
        modelId=classifier.model_id,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    raw = json.loads(response["body"].read())["generation"]
    return raw.strip()


def create_draft_reply(thread_id: str, reply_text: str):
    service = get_gmail_service()

    msg = email.message.EmailMessage()
    msg.set_content(reply_text)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    service.users().drafts().create(
        userId="me",
        body={
            "message": {
                "raw": raw,
                "threadId": thread_id
            }
        }
    ).execute()


def draft_replies_for_threads(classified_results):
    service = get_gmail_service()

    for r in classified_results:
        if not r["classification"]["needs_reply"]:
            continue

        thread_id = r["thread_id"]

        if _thread_has_draft(service, thread_id):
            continue

        reply_text = generate_reply_text(r["email_text"])
        create_draft_reply(thread_id, reply_text)
