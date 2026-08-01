"""Authority continuity is a separate question from policy admission."""
from .models import RuntimeState


def is_active(state: RuntimeState) -> bool:
    """Return whether delegated authority remains in force now."""
    return state.authority_active
