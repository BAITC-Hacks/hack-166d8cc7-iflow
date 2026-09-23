# Session and Halyk Market API

All routes require the existing development Bearer identity and return `Cache-Control: no-store`.
The market is a demo catalog; a redemption records a demo receipt and does not place a real order.

## Contracts

- `GET /api/session`: `{role: "employee" | "hr", employee_id: string | null}`. The backend resolves the identity; the browser does not choose an employee ID to gain access.
- `GET /api/market`: catalog plus the authenticated employee's authoritative balance. Fields: `rewards`, `employee_id`, `balance`, `earned`, `spent`, `coins_per_completion`, `redemptions`, `revision`, `as_of_date`.
- `POST /api/market/redeem`: `{command_id: UUID, reward_id: string}`. Returns `{command_id, employee_id, reward_id, price, balance, redeemed_on}`. Generate a UUID once per intended redemption and keep it for retries after a network failure.

Reward fields are `id`, `title`, `description`, `price`, `category`, `art`, `color`. Current rewards: `cup` (160), `book` (80), `bag` (240), `ticket` (400). Categories are `Мерч`, `Обучение`, `События`; art identifiers are the reward IDs; colors are `mint`, `lilac`, `yellow`, `peach` respectively.

HR may read the catalog but receives `employee_id`, `balance`, `earned`, and `spent` as `null`, and an empty `redemptions` array. HR cannot redeem. Employee identities see only their own receipts.

## Coins and completion

Every employee starts with zero coins. Each persisted **runtime** completion of a voluntary event earns 80 coins. Existing completed rows in raw history or jury imports earn nothing. Mandatory events never earn coins. Completing an imported or historical `in_progress` / `overdue` participation through the normal completion API counts as a new runtime completion if its event is voluntary. Repeating the same completion command does not mint additional coins.

The frontend refreshes `GET /api/market` after a successful activity completion or redemption. Browser local storage has no authority over coins, completion, or receipts. A reward is redeemable once per employee in this demo. HR metrics remain independent of reward balances.

Coins become available on a runtime completion's server-owned `completed_on`, not the original participation date. A receipt stores the earned total at the moment of redemption: later completions on that same application date do not invalidate its original balance. An exact retry returns the original receipt without recomputing its date or minting/spending coins again. Rewinding `APPLICATION_DATE` before a saved redemption blocks fresh market reads/redemptions with 409; it does not erase the saved receipt.

## Persistence and consistency

`MutableState` gains a default-empty `market_receipts` map. Existing schema-version-1 overlays load without a manual migration. Receipts, imported records, and runtime completions share the existing `STATE_PATH` file and raw-data fingerprint. No second state file is created.

The dataset's single process mutation lock covers reading earned coins, checking duplicates/funds, and persisting a receipt. Atomic temporary-file replacement publishes a new snapshot only after the write succeeds. The full prospective state validates receipt keys, fingerprints, employee/reward references, fixed prices, unique employee/reward pairs, dates, earned totals and receipt balances. Restarting preserves successful receipts and their idempotency. A changed catalog price requires a deliberate migration; inconsistent state fails validation rather than resetting itself.

Use exactly **one backend process / Uvicorn worker**, as for the existing dataset overlay. Do not run multiple backend processes against the same state file. An intentional disposable-demo state reset affects both progress and market receipts; ordinary restarts preserve both. This feature adds no reset endpoint and never changes `data/raw`.

## Error handling

The existing `{error: {code, message, details}}` envelope is retained. Missing/unknown identity is 401; HR redemption is 403; unknown reward is 404; duplicate reward, insufficient funds, reused command ID with different content, or a demo date earlier than saved market activity is 409; malformed input is 422; a persistence failure is 503. Retrying the same successful market command returns the original receipt even if the current balance has since changed; refresh the market for current totals.

No test suite or build was run for this integration task.
