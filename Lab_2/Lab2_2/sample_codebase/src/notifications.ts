import { track } from "./analytics";

export function sendOrderShipped(orderId: string, email: string): void {
  // ... send the "your order shipped" email ...
  track({ name: "order_shipped_email", props: { orderId, email } });
}

export function sendReturnApproved(orderId: string): void {
  // ... send the "return approved" email ...
  track({ name: "return_approved_email", props: { orderId } });
}
