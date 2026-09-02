# Helix Robotics Media-Monitoring Pipeline

Three jobs, three different cost/latency/quality trade-offs:

```
overnight (bulk sentiment)  -> Message Batches API   (async, cheap, large scale)
breaking news (burst)       -> ThreadPoolExecutor     (concurrent, fast, rate-limited)
morning briefing (quality)  -> Multi-pass review      (draft -> critique -> refine)
```

Mixing them up costs time, money, or quality: batching a breaking-news burst makes it late;
threading an overnight bulk job burns rate-limit budget for no reason; shipping the morning
briefing single-shot skips the review pass that catches what generation alone misses.

## Notes

- Batch requests are matched back to inputs by `custom_id`, never by result order — batch
  results return in completion order, not submission order.
- The parallel pool uses threads, not processes: this workload is I/O-bound (waiting on the
  API), so the GIL doesn't matter and threads have far lower overhead.
- The critique pass must only list problems, never rewrite — that separation is what makes the
  refine pass have a concrete checklist instead of re-deciding what's wrong from scratch.
