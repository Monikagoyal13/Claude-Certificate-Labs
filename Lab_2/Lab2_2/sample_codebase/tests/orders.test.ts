import { markDelivered, cancelOrder } from "../src/orders";

describe("orders", () => {
  it("marks an order delivered without throwing", () => {
    expect(() => markDelivered("NP-100190")).not.toThrow();
  });

  it("cancels an order without throwing", () => {
    expect(() => cancelOrder("NP-100201", "customer request")).not.toThrow();
  });
});
