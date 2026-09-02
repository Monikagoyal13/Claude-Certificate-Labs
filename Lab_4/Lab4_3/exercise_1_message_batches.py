"""Exercise 1 — Classify a workload with the Message Batches API (Lab 4.3, S5).

Submits a batch of sentiment-classification requests (one per news headline),
polls until processing_status == "ended", then collects results joined back
to their inputs by custom_id (never by result order — batches complete out
of order).

Run:
    python exercise_1_message_batches.py
Resume a batch from a prior run that hadn't finished yet:
    python exercise_1_message_batches.py --fetch <batch_id>
"""
import os
import sys
import time

from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
POLL_DEADLINE_SECONDS = 300
POLL_INTERVAL_SECONDS = 10

PROMPT = (
    "Classify the sentiment of this headline about Helix Robotics as exactly "
    "one word - positive, negative, or neutral.\n\nHeadline: {h}"
)

HEADLINES = [
    "Helix Robotics unveils new warehouse-automation arm, beating throughput benchmarks by 30%.",
    "Helix Robotics stock drops 8% after quarterly earnings miss analyst expectations.",
    "Regulators open a probe into Helix Robotics' overseas manufacturing practices.",
    "Helix Robotics announces a new partnership with a major logistics provider.",
    "Helix Robotics recalls a batch of assembly-line robots over a safety defect.",
    "Helix Robotics CEO named to industry's top-40-under-40 list.",
    "Helix Robotics reports record quarterly revenue, up 12% year over year.",
    "Analysts split on Helix Robotics' long-term outlook amid rising competition.",
]


def build_requests(headlines):
    """One batch request per headline, each with a unique, stable custom_id."""
    return [
        {
            "custom_id": f"headline-{i}",
            "params": {
                "model": MODEL,
                "max_tokens": 20,
                "messages": [{"role": "user", "content": PROMPT.format(h=h)}],
            },
        }
        for i, h in enumerate(headlines)
    ]


def collect_results(client, batch_id):
    """Print each succeeded result labeled by its custom_id; flag failures by type."""
    for entry in client.messages.batches.results(batch_id):
        if entry.result.type == "succeeded":
            text = "".join(
                b.text for b in entry.result.message.content if b.type == "text"
            ).strip()
            print(f"{entry.custom_id}: {text}")
        else:
            print(f"{entry.custom_id}: ERROR ({entry.result.type})")


def poll_until_ended(client, batch_id):
    """Poll until processing_status == 'ended' or the deadline passes."""
    deadline = time.time() + POLL_DEADLINE_SECONDS
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        print("status:", batch.processing_status, "| counts:", batch.request_counts)
        if batch.processing_status == "ended":
            return True
        if time.time() > deadline:
            print(f"Still processing. Fetch later with --fetch {batch_id}")
            return False
        time.sleep(POLL_INTERVAL_SECONDS)


def main():
    client = Anthropic()

    if "--fetch" in sys.argv:
        batch_id = sys.argv[sys.argv.index("--fetch") + 1]
        batch = client.messages.batches.retrieve(batch_id)
        print("status:", batch.processing_status, "| counts:", batch.request_counts)
        if batch.processing_status == "ended":
            collect_results(client, batch_id)
        else:
            print(f"Still processing. Fetch later with --fetch {batch_id}")
        return

    requests = build_requests(HEADLINES)
    batch = client.messages.batches.create(requests=requests)
    print(f"submitted batch: {batch.id}")

    if poll_until_ended(client, batch.id):
        collect_results(client, batch.id)


if __name__ == "__main__":
    main()
