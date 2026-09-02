"""Exercise 2 — Parallel processing for throughput (Lab 4.3, S6).

Classifies the same headlines sequentially and through a ThreadPoolExecutor,
comparing wall-clock time. The work is I/O-bound (waiting on the API), so
threads overlap the waits without GIL contention. .map() preserves input
order so results line up with headlines without manual id-tagging.

Run:
    python exercise_2_parallel.py
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor

from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

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


def classify(client, headline: str) -> str:
    """Classify one headline's sentiment as a single word."""
    msg = client.messages.create(
        model=MODEL,
        max_tokens=20,
        messages=[{"role": "user", "content": PROMPT.format(h=headline)}],
    )
    return "".join(b.text for b in msg.content if b.type == "text").strip()


def run_sequential(client, headlines):
    t0 = time.time()
    out = [classify(client, h) for h in headlines]
    return out, time.time() - t0


def run_parallel(client, headlines, workers=5):
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        # .map preserves input order, so results line up with headlines.
        out = list(pool.map(lambda h: classify(client, h), headlines))
    return out, time.time() - t0


if __name__ == "__main__":
    client = Anthropic()

    seq_results, seq_time = run_sequential(client, HEADLINES)
    print(f"sequential: {seq_time:.2f}s")
    for h, r in zip(HEADLINES, seq_results):
        print(f"  {r:<10} | {h}")

    par_results, par_time = run_parallel(client, HEADLINES, workers=5)
    print(f"\nparallel:   {par_time:.2f}s")
    for h, r in zip(HEADLINES, par_results):
        print(f"  {r:<10} | {h}")

    order_preserved = seq_results == par_results
    speedup = seq_time / par_time if par_time > 0 else float("inf")
    print(f"\norder preserved (parallel == sequential): {order_preserved}")
    print(f"speedup: {speedup:.2f}x")
