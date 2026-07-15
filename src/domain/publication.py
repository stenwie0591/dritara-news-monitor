"""State machine pura per la consegna editoriale anti-duplicato."""

from enum import StrEnum


class PublicationState(StrEnum):
    SCHEDULED = "scheduled"
    CLAIMED = "claimed"
    DISPATCHING = "dispatching"
    DELIVERED = "delivered"
    FAILED_RETRYABLE = "failed_retryable"
    DELIVERY_UNKNOWN = "delivery_unknown"
    CANCELLED = "cancelled"


class InvalidPublicationTransition(ValueError):
    pass


_AUTOMATIC_TRANSITIONS: dict[PublicationState, frozenset[PublicationState]] = {
    PublicationState.SCHEDULED: frozenset(
        {PublicationState.CLAIMED, PublicationState.CANCELLED}
    ),
    PublicationState.CLAIMED: frozenset(
        {
            PublicationState.SCHEDULED,  # lease scaduta prima di qualunque rete
            PublicationState.DISPATCHING,
            PublicationState.CANCELLED,
        }
    ),
    PublicationState.DISPATCHING: frozenset(
        {
            PublicationState.DELIVERED,
            PublicationState.FAILED_RETRYABLE,
            PublicationState.DELIVERY_UNKNOWN,
        }
    ),
    PublicationState.FAILED_RETRYABLE: frozenset(
        {PublicationState.SCHEDULED, PublicationState.CANCELLED}
    ),
    PublicationState.DELIVERY_UNKNOWN: frozenset(),
    PublicationState.DELIVERED: frozenset(),
    PublicationState.CANCELLED: frozenset(),
}

_MANUAL_UNKNOWN_TRANSITIONS = frozenset(
    {
        PublicationState.DELIVERED,
        PublicationState.SCHEDULED,
        PublicationState.CANCELLED,
    }
)


def transition_publication(
    current: PublicationState,
    target: PublicationState,
    *,
    manual_reconciliation: bool = False,
) -> PublicationState:
    """Valida una transizione senza produrre side effect.

    `delivery_unknown` è intenzionalmente bloccato per worker automatici. Solo
    una riconciliazione umana può confermare, ritentare o annullare.
    """
    allowed = _AUTOMATIC_TRANSITIONS[current]
    if current is PublicationState.DELIVERY_UNKNOWN and manual_reconciliation:
        allowed = _MANUAL_UNKNOWN_TRANSITIONS
    if target not in allowed:
        raise InvalidPublicationTransition(f"{current.value} -> {target.value}")
    return target


def is_terminal(state: PublicationState) -> bool:
    return state in {PublicationState.DELIVERED, PublicationState.CANCELLED}
