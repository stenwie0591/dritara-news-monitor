import pytest

from src.domain.publication import (
    InvalidPublicationTransition,
    PublicationState,
    is_terminal,
    transition_publication,
)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (PublicationState.SCHEDULED, PublicationState.CLAIMED),
        (PublicationState.CLAIMED, PublicationState.DISPATCHING),
        (PublicationState.DISPATCHING, PublicationState.DELIVERED),
        (PublicationState.DISPATCHING, PublicationState.FAILED_RETRYABLE),
        (PublicationState.DISPATCHING, PublicationState.DELIVERY_UNKNOWN),
        (PublicationState.FAILED_RETRYABLE, PublicationState.SCHEDULED),
    ],
)
def test_valid_automatic_transitions(current, target) -> None:
    assert transition_publication(current, target) is target


@pytest.mark.parametrize(
    "target",
    [
        PublicationState.DELIVERED,
        PublicationState.SCHEDULED,
        PublicationState.CANCELLED,
    ],
)
def test_unknown_requires_manual_reconciliation(target) -> None:
    with pytest.raises(InvalidPublicationTransition):
        transition_publication(PublicationState.DELIVERY_UNKNOWN, target)

    assert (
        transition_publication(
            PublicationState.DELIVERY_UNKNOWN,
            target,
            manual_reconciliation=True,
        )
        is target
    )


@pytest.mark.parametrize("state", [PublicationState.DELIVERED, PublicationState.CANCELLED])
def test_terminal_states_cannot_transition(state) -> None:
    assert is_terminal(state)
    with pytest.raises(InvalidPublicationTransition):
        transition_publication(state, PublicationState.SCHEDULED)


def test_dispatching_cannot_return_to_scheduled() -> None:
    with pytest.raises(InvalidPublicationTransition):
        transition_publication(
            PublicationState.DISPATCHING,
            PublicationState.SCHEDULED,
        )
