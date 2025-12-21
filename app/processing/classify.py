from app.llm.bedrock import BedrockClassifier
from app.gmail.fetch import fetch_unread_threads
from app.processing.preprocess import clean_email_text


def classify_unread_threads(max_threads=10):
    classifier = BedrockClassifier()
    threads = fetch_unread_threads(max_threads=max_threads)

    results = []

    for thread in threads:
        # 🔑 CLEAN + TRUNCATE INPUT BEFORE LLM
        cleaned_text = clean_email_text(thread.get("text", ""))

        # If cleaning wipes everything, skip safely
        if not cleaned_text:
            classification = {
                "category": "skip",
                "urgency_reason": "empty or unparseable content",
                "needs_reply": False,
                "suggested_action": "ignore"
            }
        else:
            classification = classifier.classify_email(cleaned_text)

        results.append({
            "thread_id": thread["thread_id"],
            "email_text": cleaned_text,
            "classification": classification
        })

    return results
