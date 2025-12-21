from app.gmail.auth import get_gmail_service

LABEL_CONFIG = {
    "urgent": {"name": "AI/Urgent"},
    "important": {"name": "AI/Important"},
    "promotional": {"name": "AI/Promotional"},
    "skip": {"name": "AI/LowPriority"}
}


def ensure_labels_exist():
    service = get_gmail_service()
    existing = service.users().labels().list(userId="me").execute()
    existing_labels = {l["name"]: l["id"] for l in existing["labels"]}

    label_ids = {}

    for key, config in LABEL_CONFIG.items():
        name = config["name"]

        if name in existing_labels:
            label_ids[key] = existing_labels[name]
            continue

        label = service.users().labels().create(
            userId="me",
            body={
                "name": name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show"
            }
        ).execute()

        label_ids[key] = label["id"]

    return label_ids

def apply_label_to_thread(thread_id: str, label_id: str):
    service = get_gmail_service()

    service.users().threads().modify(
        userId="me",
        id=thread_id,
        body={"addLabelIds": [label_id]}
    ).execute()
