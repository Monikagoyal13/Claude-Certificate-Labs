# Migration Notes

- Replaced deprecated logEvent(name, payload) with track({ name, props })
  across src/notifications.ts and src/orders.ts; imports updated.
- Done (Exercise 3): renamed analytics event order_cancelled -> order_canceled (one L)
  in src/orders.ts.
