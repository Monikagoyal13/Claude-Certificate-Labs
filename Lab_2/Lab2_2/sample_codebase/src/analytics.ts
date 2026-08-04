// Analytics helpers.
//
// logEvent(name, payload) is DEPRECATED. Do not use it in new code.
// New code should call track({ name, props }) instead.

/** @deprecated Use track({ name, props }) instead. */
export function logEvent(name: string, payload: Record<string, unknown>): void {
  console.log(`[deprecated logEvent] ${name}`, payload);
}

export function track(event: { name: string; props: Record<string, unknown> }): void {
  console.log(`[track] ${event.name}`, event.props);
}
