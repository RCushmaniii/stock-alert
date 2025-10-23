---
trigger: always_on
---

Separation of Concerns means to keep thins in distinct parts of the app isolated (UI, state, data).

- Keep distinct parts of the app isolated: UI, state, and data.
- Example: Place UI logic in components, state in a store (e.g., Zustand/Redux), and API calls in a client module.
- Example: A form component that renders inputs but retrieves options from a separate data service.
- Avoid: A component that both renders UI and calls fetch() directly.
- Avoid: Mixing state management logic inside UI components.
