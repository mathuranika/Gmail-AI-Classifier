from app.processing.classify import classify_unread_threads
from app.gmail.labels import ensure_labels_exist, apply_label_to_thread


def label_unread_threads(max_threads=10):
    label_ids = ensure_labels_exist()
    results = classify_unread_threads(max_threads=max_threads)

    for r in results:
        category = r["classification"]["category"]
        thread_id = r["thread_id"]

        label_id = label_ids.get(category)
        if label_id:
            apply_label_to_thread(thread_id, label_id)

    return results
