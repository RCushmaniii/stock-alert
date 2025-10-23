---
trigger: always_on
---

- Always assume operations can fail; handle errors explicitly.
- Wrap all server actions, API calls, and async logic with `try/catch` or equivalent error boundaries.
- Return structured error responses (e.g., `{ success: false, error: 'Message' }`) instead of letting errors bubble unhandled.
- Ensure the UI provides meaningful feedback on failure (error messages, fallback states).
- Never allow silent failures — log errors to console in dev, and report to monitoring (e.g., Sentry) in production.
- Default loading states must always transition to either a **success** or an **error** state.
