## 📦 Order State Flow

```mermaid
stateDiagram-v2
    [*] --> unpaid: Create unpaid order

    unpaid --> pending_pay: Balance payment success
    unpaid --> cancelled: User deletes order / timeout

    state pending_pay {
        [*] --> normal
        normal --> refund_applying: Apply refund
        refund_applying --> normal: Revoke refund
        refund_applying --> refund_approved: Admin approves refund
    }

    pending_pay --> paid_pending: Confirm order(refund_status = none and status = pending_pay)
    pending_pay --> cancelled: Refund approved

    paid_pending --> [*]
    cancelled --> [*]

```markdown
### Order Status Design

The order system uses a controlled state transition model:

- `unpaid` → created but not paid
- `pending_pay` → paid / frozen, waiting for confirmation
- `paid_pending` → completed order
- `cancelled` → closed or refunded

Refund flow is handled as a sub-state under `pending_pay`:
- `none`
- `applying`
- `approved`
- `rejected`

This design prevents invalid transitions and improves payment/order safety
```
