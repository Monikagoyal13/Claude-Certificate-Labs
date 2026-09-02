# Lab 4.3 — Scaling Output: Batch Processing & Multi-Pass Review

Scenario: a Helix Robotics media-monitoring pipeline with three jobs that pull in different
directions — overnight bulk sentiment (cost/scale matter, latency doesn't), a breaking-news
burst (latency is everything), and a morning briefing (quality matters most). Each job gets the
Claude pattern that actually fits it.

```
overnight (bulk sentiment)  -> Message Batches API   (async, cheap, large scale)
breaking news (burst)       -> ThreadPoolExecutor     (concurrent, fast, rate-limited)
morning briefing (quality)  -> Multi-pass review      (draft -> critique -> refine)
```

## Setup

```
pip install -r requirements.txt
cp .env.example .env        # paste a real ANTHROPIC_API_KEY into .env
export $(grep -v '^#' .env | xargs)
```

`ANTHROPIC_MODEL` defaults to `claude-sonnet-4-5` (the PDF's stated default,
`claude-sonnet-4-6`, is not a real model id — substituted and noted here rather than silently
changed, same as Labs 4.1 and 4.2).

## Exercise 1 — `exercise_1_message_batches.py` (Message Batches API)

`build_requests(headlines)` returns one `{custom_id, params}` dict per headline — `params`
mirrors a normal `messages.create()` call (model, `max_tokens`, `messages`). `custom_id` is
`f"headline-{i}"`: stable, unique, and the *only* correct way to join a result back to its
input, because **batch results return in completion order, not submission order.** Matching by
result index instead of `custom_id` would silently mislabel every result whose completion order
differs from submission order.

`main()`:
1. `client.messages.batches.create(requests=...)` — submit once.
2. Poll `client.messages.batches.retrieve(batch.id)` every 10s, printing
   `status: ... | counts: ...`, until `processing_status == "ended"`.
3. A deadline (300s in this build — shorter than the PDF's 600s default, a practical concession
   for this session; production code should use a longer or configurable deadline) stops the
   poll loop and prints `Fetch later with --fetch <batch_id>` instead of hanging forever. No work
   is lost — the batch keeps processing server-side regardless of whether this script is
   watching it.
4. `client.messages.batches.results(batch.id)` streams results; each is printed as
   `custom_id: sentiment`, or `custom_id: ERROR (type)` if that particular request failed —
   failures are visible per-item, not swallowed.

Resume later without re-submitting: `python exercise_1_message_batches.py --fetch <batch_id>`.

**Why the Message Batches API here and not real-time calls:** the overnight sentiment job has no
user waiting on it — cost and scale matter, latency doesn't. Batches are billed lower than
real-time calls at the cost of an unpredictable (usually minutes, sometimes longer) completion
time, which is a good trade for a job that can wait until morning and a bad one for anything
synchronous.

## Exercise 2 — `exercise_2_parallel.py` (ThreadPoolExecutor for throughput)

`classify(client, headline)` — one sentiment call, reused both sequentially and in the pool, so
the comparison is apples-to-apples.

`run_sequential()` times a plain loop. `run_parallel(client, headlines, workers=5)` wraps the
same `classify()` calls in `ThreadPoolExecutor(max_workers=5).map(...)` — `.map()` preserves
input order, so results line up with `headlines` without any manual id-tagging (unlike the batch
API, this is a live, ordered call, not an async job that can complete out of order).

**Why threads, not processes or asyncio:** this workload is I/O-bound — nearly all the wall
clock is spent waiting on the network round trip to the API, not doing CPU work. Python's GIL
only blocks *CPU-bound* parallelism; I/O-bound waits release the GIL, so threads overlap them
with far less overhead than a process pool (no per-process memory/startup cost) and less
restructuring than `asyncio` (no need for an async client or `await` throughout).

**What caps the speedup:** the slowest single request in the batch (with `.map()`, the pool
waits for all of them), the size of the thread pool itself, and — beyond a certain pool size —
the API's own rate limits (429s). `workers=5` is the PDF's stated safe starting point.

## Exercise 3 — `exercise_3_multipass.py` (draft → critique → refine)

`STANDARDS` is the exact string from the PDF: lead with the biggest development, balance
positive/negative coverage, be specific, stay neutral, no speculation, ≤120 words.

- `draft()` — deliberately **not** given the standards, so it can realistically violate some of
  them (this mirrors the PDF's framing: "a single-shot draft often misses one of those — too
  long, leans positive, buries the lede").
- `critique()` — given the standards, the headlines, and the draft; explicitly told **"Do NOT
  rewrite - only list issues"**. This instruction is load-bearing: without it, the critique step
  would collapse into a second draft, and the separation between generating and judging — the
  entire point of multi-pass review — disappears.
- `refine()` — given everything critique had, plus the critique itself; told to fix every point
  and **output only the final briefing text**, so no parsing-around-an-explanation is needed
  downstream.

**Why two separate calls instead of one "review and rewrite" prompt:** a single call asked to
both judge and fix its own draft tends to be lenient with itself — it wrote the thing, so it's
biased to defend it. Splitting the passes gives the critique step fresh, undivided attention on
"what's wrong" before any pressure to also produce a fix, and gives the refine step a concrete,
already-decided checklist instead of re-deciding what's wrong from scratch.

## Actual results (this run)

All three scripts ran against the live API (`claude-sonnet-4-5`), no fabricated output.

### Exercise 1 — Message Batches

Submitted batch `msgbatch_012jDj5nArzVPdKQDgfNSy5J` for all 8 headlines. It did **not** reach
`"ended"` within the script's 300s deadline — the script correctly printed
`Still processing. Fetch later with --fetch msgbatch_012jDj5nArzVPdKQDgfNSy5J` and exited
cleanly rather than hanging. Continued polling separately (an extended ~1-2 minute wait) until
the batch reached `ended` with `succeeded=8, errored=0`, then ran
`--fetch msgbatch_012jDj5nArzVPdKQDgfNSy5J` to collect:

```
headline-1: negative   headline-7: neutral    headline-2: negative   headline-0: positive
headline-6: positive   headline-5: positive   headline-4: negative   headline-3: positive
```

**Concrete proof of the lab's core point:** results came back in *completion* order
(`headline-1, headline-7, headline-2, headline-0, ...`), not submission order
(`headline-0, headline-1, headline-2, ...`). Matching by result index instead of `custom_id`
would have silently mislabeled every one of these. All 8 sentiment labels are correct given the
headlines (recall/probe/stock-drop → negative, revenue/partnership/award/throughput → positive,
analysts-split → neutral).

### Exercise 2 — Parallel processing

```
sequential: 10.83s
parallel:    2.84s
order preserved (parallel == sequential): True
speedup: 3.81x
```

Real, measured 3.81× speedup at `workers=5` — squarely inside the PDF's expected 3–5× range for
8 headlines. All 8 parallel results matched the sequential results exactly, confirming `.map()`
preserved input order.

### Exercise 3 — Multi-pass review

- **DRAFT** (164 words): led with a "mixed signals" framing rather than the single biggest story,
  included editorial language ("dominates today's coverage," "markets are clearly weighing"),
  and ran well over the 120-word limit.
- **CRITIQUE** (11 concrete bullets, no rewrite): correctly flagged the buried lede, the word
  count, two instances of speculation beyond the headlines, an unnecessary "Bottom Line"
  analysis section, editorial framing, and unbalanced emphasis between positive/negative items.
- **REFINED** (94 words): leads with the stock drop/earnings miss (the single biggest
  development), states the record-revenue figure and the 30%/12% numbers, names the regulatory
  probe and safety recall specifically, stays neutral (no "clearly weighing" language), and
  comes in under the 120-word cap. This is a real, verifiable improvement over the draft, not
  just a superficial trim.

One cosmetic artifact: the live critique output contained a single stray `�` character (a
console encoding glitch rendering an em dash), left as-is rather than silently cleaned, since
it's real model/terminal output, not a bug in the script's logic.

## Design notes / deviations from the PDF

- `ANTHROPIC_MODEL` defaults to `claude-sonnet-4-5`, not the PDF's `claude-sonnet-4-6` (not a
  real model id).
- Exercise 1's poll deadline is 300s rather than the PDF's 600s, to keep this session's live run
  bounded; the `--fetch <batch_id>` resume path is unaffected and works identically either way.
- Each script stays self-contained (duplicates the headline list, prompt, etc.) per the lab's
  own spec that each exercise is "one self-contained Python script."
