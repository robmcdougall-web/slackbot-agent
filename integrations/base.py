"""
Abstract base class for third-party integrations.

New integrations (e.g. Navan, Expensify) should inherit from Integration
and implement the required methods so the bot can dynamically discover
and use them.
"""

from abc import ABC, abstractmethod


class Integration(ABC):
    """Base class that all future integrations should inherit from."""

    @abstractmethod
    def is_enabled(self) -> bool:
        """Return True if this integration is configured and ready to use."""
        ...

    @abstractmethod
    def enrich_context(self, question: str, user_email: str) -> str | None:
        """
        Given a user's question and email, return additional context that
        should be injected into the Claude prompt.  Return None if no
        enrichment is available.
        """
        ...
