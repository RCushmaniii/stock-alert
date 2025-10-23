---
trigger: model_decision
description: Apply when implementing or maintaining code to avoid duplication by reusing shared functions, hooks, or utilities instead of copy-pasting logic.
---

- Abstract repeated logic into reusable functions, hooks, or utilities.
- Example: Create a shared `validateEmail()` function and reuse it across forms.
- Example: Extract common API fetch logic into a custom hook.
- Example: Centralize constants (e.g., error messages, regex patterns) in a config file.
- Avoid: Copy-pasting regex or validation logic into multiple components.
- Avoid: Duplicating API calls or state management logic across different parts of the app.
- Regularly refactor duplicated code when discovered to improve maintainability.
