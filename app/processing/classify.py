from app.llm.bedrock import BedrockClassifier
from app.gmail.fetch import fetch_unread_threads


def classify_unread_threads(max_threads=10):
    classifier = BedrockClassifier()
    threads = fetch_unread_threads(max_threads=max_threads)

    results = []

    for thread in threads:
        classification = classifier.classify_email(thread["text"])

        results.append({
            "thread_id": thread["thread_id"],
            "email_text": thread["text"],
            "classification": classification
        })

    return results
