"""Demo 1 (Preservation) - a tiny store for facts that must survive every turn.

Long sessions evict early messages from the model's effective context. If the
customer's id or tier only appeared in turn 2, by turn 18 it may be out of the
window entirely, or its attention weak. Re-injecting a small, always-visible
[CASE FACTS] block into the system prompt on every turn means the model never
has to dig through history to remember who it is talking to.
"""


class CaseFacts:
    """A tiny key-value store of facts that must survive every turn."""

    def __init__(self):
        self._facts: dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        self._facts[key] = value

    def as_system_block(self) -> str:
        """Render the pinned facts as a system-prompt block.

        Every token here is paid for on every API call, so keep it short -
        identity-class facts only (customer id, tier, active order), not
        long lists.
        """
        if not self._facts:
            return ""
        lines = ["[CASE FACTS - these are confirmed and must be preserved]"]
        for k, v in self._facts.items():
            lines.append(f"- {k}: {v}")
        return "\n".join(lines)
