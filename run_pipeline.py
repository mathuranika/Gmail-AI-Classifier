import os
import boto3
from app.processing.classify import classify_unread_threads
from app.gmail.labels import ensure_labels_exist, apply_label_to_thread
from app.gmail.drafts import draft_replies_for_threads


def run_full_pipeline(max_threads=20):
    print("\n🚀 Starting Gmail AI Organizer Pipeline\n")

    # Step 1: Fetch + classify unread threads
    print("🔍 Fetching and classifying unread threads...")
    results = classify_unread_threads(max_threads=max_threads)

    if not results:
        print("✅ No unread threads found. Inbox is clean.")
        return

    # Step 2: Ensure labels exist
    print("🏷️  Ensuring Gmail labels exist...")
    label_ids = ensure_labels_exist()

    # Step 3: Apply labels
    print("📌 Applying labels...")
    for r in results:
        category = r["classification"]["category"]
        thread_id = r["thread_id"]

        label_id = label_ids.get(category)
        if label_id:
            apply_label_to_thread(thread_id, label_id)

    # Step 4: Create drafts where needed
    print("✍️  Creating drafts where required...")
    draft_replies_for_threads(results)

    # Step 5: Print summary
    print("\n📊 Summary")
    print("=" * 50)

    for r in results:
        c = r["classification"]
        print(f"""
Thread ID       : {r['thread_id']}
Category        : {c['category']}
Needs Reply     : {c['needs_reply']}
Reason          : {c['urgency_reason']}
Suggested Action: {c['suggested_action']}
""")

    print("✅ Pipeline completed successfully.\n")


def shutdown_ec2():
    """
    Stops the current EC2 instance to avoid idle costs.
    Works only when running inside EC2.
    """
    try:
        instance_id = open("/var/lib/cloud/data/instance-id").read().strip()
        region = os.getenv("AWS_REGION", "us-east-1")

        ec2 = boto3.client("ec2", region_name=region)
        ec2.stop_instances(InstanceIds=[instance_id])

        print("🛑 EC2 shutdown initiated")

    except Exception as e:
        print(f"⚠️ Failed to shut down EC2: {e}")


if __name__ == "__main__":
    run_full_pipeline(max_threads=20)
    shutdown_ec2()
