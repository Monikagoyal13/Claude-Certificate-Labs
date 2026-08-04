import { track } from "./analytics";

export function markDelivered(orderId: string): void {
  track({ name: "order_delivered", props: { orderId } });
}

export function cancelOrder(orderId: string, reason: string): void {
  track({ name: "order_canceled", props: { orderId, reason } });
}
