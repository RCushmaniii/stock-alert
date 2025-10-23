---
trigger: always_on
---

Single Responsibility Principle means each module or function should do one thing and have one reason to change.

- Each module, class, or function should do one thing only.
- Example: `formatDate()` only handles date formatting.
- Example: `userService` only manages fetching user data.
- Avoid: A `userService` that both fetches users and formats display names.
- Avoid: A component that manages UI rendering and business logic at the same time.
