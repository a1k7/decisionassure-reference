"""Policy currency is evaluated independently of the original authorization."""
from .models import GovernanceReceipt, RuntimeState


def is_current(receipt: GovernanceReceipt, state: RuntimeState) -> bool:
    return receipt.policy_version == state.policy_version
