"""Shared API cursor codec checks."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from enact.api.pagination import decode_cursor, encode_cursor


@pytest.mark.unit
class TestCursorCodec:
    """Verify opaque collection cursor round trips and malformed input handling."""

    def test_cursor_round_trip(self) -> None:
        """Preserve the timestamp and stable tie-breaker in a cursor."""
        created_at = datetime(2026, 11, 7, tzinfo=UTC)
        identifier = uuid4()

        assert decode_cursor(encode_cursor(created_at, identifier)) == (created_at, identifier)

    @pytest.mark.parametrize('value', ['not-a-cursor', 'eyJpZCI6IjEyMyJ9'])
    def test_malformed_cursor(self, value: str) -> None:
        """Reject malformed and incomplete cursor payloads."""
        with pytest.raises(ValueError, match='Invalid cursor'):
            decode_cursor(value)

    def test_cursor_requires_timezone(self) -> None:
        """Reject a timestamp whose ordering is ambiguous across time zones."""
        value = encode_cursor(datetime(2026, 11, 7), uuid4())

        with pytest.raises(ValueError, match='Invalid cursor'):
            decode_cursor(value)
