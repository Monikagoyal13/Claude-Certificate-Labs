"""Lab 5.2 - Resilient Systems: Error Propagation & Large Codebase Exploration.

Scenario: a healthcare claims processing pipeline (intake -> validation ->
adjudication) over three sample claims. CLM-001 and CLM-003 are well-formed;
CLM-002 is for an inactive member and is deliberately malformed.

Safe to Ctrl+C and restart at any time - the scratchpad (scratchpad.json)
is the coordinator's audit trail and checkpoint in one file. Delete it by
hand to reset; the script never deletes it itself.
"""

from dotenv import load_dotenv

from agents import run_adjudication, run_intake, run_validation
from sample_claims import CLAIMS
from scratchpad import Scratchpad

load_dotenv()

STAGES = [
    ("intake", run_intake),
    ("validation", run_validation),
    ("adjudication", run_adjudication),
]


def process_claim(claim: dict, pad: Scratchpad) -> str:
    """Walk one claim through all three stages, logging and checkpointing
    as it goes. Stops (and marks the claim failed) at the first stage that
    returns ok=False; marks the claim done only once every stage succeeds.
    """
    claim_id = claim["claim_id"]
    for stage_name, fn in STAGES:
        result = fn(claim)
        pad.log(claim_id, stage_name, result.to_dict())
        status_word = "ok" if result.ok else f"FAIL ({result.error})"
        print(f"  [{claim_id}] {stage_name}...{status_word}")
        if not result.ok:
            pad.mark_failed(claim_id, f"{stage_name}: {result.error}")
            return "failed"
    pad.mark_done(claim_id)
    return "done"


def main() -> None:
    pad = Scratchpad("scratchpad.json")
    done_count = failed_count = skipped_count = 0

    for claim in CLAIMS:
        claim_id = claim["claim_id"]
        status = pad.status(claim_id)

        # ----- Crash recovery: skip claims already finished. -----
        if status in ("done", "failed"):
            print(f"[CLAIM {claim_id}] (already {status}, skipping)")
            skipped_count += 1
            continue

        print(f"[CLAIM {claim_id}]")
        final = process_claim(claim, pad)
        if final == "done":
            done_count += 1
        else:
            failed_count += 1

    print(f"\ndone: {done_count}  failed: {failed_count}  skipped: {skipped_count}")


if __name__ == "__main__":
    main()
