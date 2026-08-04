import { sendOrderShipped, sendReturnApproved } from "../src/notifications";

describe("notifications", () => {
  it("sends an order-shipped email without throwing", () => {
    expect(() => sendOrderShipped("NP-100245", "dana.lee@example.com")).not.toThrow();
  });

  it("sends a return-approved email without throwing", () => {
    expect(() => sendReturnApproved("NP-100190")).not.toThrow();
  });
});
