from app.processing.classify import classify_unread_threads
from app.gmail.drafts import draft_replies_for_threads


def draft_replies(max_threads=10):
    results = classify_unread_threads(max_threads=max_threads)
    draft_replies_for_threads(results)
    return results
