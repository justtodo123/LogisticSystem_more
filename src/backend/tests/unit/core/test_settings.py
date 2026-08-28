"""Configuration invariants for request ownership leases."""

import pytest
from pydantic import ValidationError

from config.settings import Settings


def test_idempotency_lease_must_outlive_request_timeout():
    settings = Settings(
        REQUEST_TIMEOUT_SECONDS=30,
        IDEMPOTENCY_PROCESSING_LEASE_SECONDS=31,
        _env_file=None,
    )

    assert settings.IDEMPOTENCY_PROCESSING_LEASE_SECONDS == 31


@pytest.mark.parametrize("lease_seconds", [29, 30])
def test_idempotency_lease_rejects_timeout_or_shorter(lease_seconds):
    with pytest.raises(
        ValidationError,
        match=(
            "IDEMPOTENCY_PROCESSING_LEASE_SECONDS must be greater than "
            "REQUEST_TIMEOUT_SECONDS"
        ),
    ):
        Settings(
            REQUEST_TIMEOUT_SECONDS=30,
            IDEMPOTENCY_PROCESSING_LEASE_SECONDS=lease_seconds,
            _env_file=None,
        )
