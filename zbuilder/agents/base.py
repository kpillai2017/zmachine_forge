"""Shared plumbing: every agent has a provider, the run log, and a call
budget (proforma Section 8: bound every loop)."""
from __future__ import annotations

from zbuilder.llm.provider import Provider, ProviderError
from zbuilder.persona import system_prompt
from zbuilder.state import RunLog


class BudgetExceeded(Exception):
    pass


class Budget:
    def __init__(self, max_calls: int):
        self.max_calls = max_calls
        self.calls = 0

    def spend(self) -> None:
        if self.calls >= self.max_calls:
            raise BudgetExceeded(f"LLM call budget of {self.max_calls} used up")
        self.calls += 1


class Agent:
    role = "base"

    def __init__(self, provider: Provider, log: RunLog, budget: Budget):
        self.provider = provider
        self.log = log
        self.budget = budget

    @property
    def offline(self) -> bool:
        return self.provider.offline

    def ask(self, task_id: str, user: str) -> str:
        """One bounded LLM call; retried once on a provider error."""
        for attempt in (1, 2):
            self.budget.spend()
            try:
                reply = self.provider.complete(system_prompt(self.role), user)
                self.log.event(self.role, task_id, "llm_call", provider=self.provider.name,
                               prompt_chars=len(user), reply_chars=len(reply))
                return reply
            except ProviderError as exc:
                self.log.event(self.role, task_id, "llm_error", error=str(exc), attempt=attempt)
                if attempt == 2:
                    raise
        raise AssertionError("unreachable")
