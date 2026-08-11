# Style Rules

- Follow the project's existing Python style (PEP 8, standard library, no new dependencies).
- Functions should be pure where appropriate — avoid hidden state or side effects for pricing/calculation logic.
- Validate inputs; raise `ValueError` for invalid arguments (e.g. negative prices) rather than failing silently.
- Public functions must have type hints on parameters and the return value.
- Public functions must have a concise, useful docstring describing what they do.
- Avoid unnecessary changes — touch only what the task requires.
- Keep implementations simple and maintainable; prefer clarity over cleverness.
