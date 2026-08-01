"""Evidence freshness is a live admissibility condition."""
from .models import RuntimeState


def is_fresh(state: RuntimeState) -> bool:
    return state.evidence_fresh
