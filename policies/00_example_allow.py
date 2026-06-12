"""Baseline no-op policy — template for drop-in policies (one Policy subclass
per file; the loader hot-reloads on save)."""
from antigreedy.governance.policy import Policy


class AllowAllPolicy(Policy):
    name = "allow_all"
    priority = 1000

    def evaluate(self, action, state, history):
        return self.allow(reason="baseline allow-all")
