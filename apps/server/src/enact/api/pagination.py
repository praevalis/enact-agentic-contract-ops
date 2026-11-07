"""Encode and decode opaque newest-first collection cursors."""

import base64
import binascii
import json
from datetime import datetime
from uuid import UUID


def encode_cursor(created_at: datetime, identifier: UUID) -> str:
    """Encode a collection position for a client.

    Args:
        created_at: Creation timestamp of the last item in a page.
        identifier: Stable tie-breaker of the last item in a page.

    Returns:
        URL-safe opaque cursor value.
    """
    payload = json.dumps(
        {'id': str(identifier), 'created_at': created_at.isoformat()},
        separators=(',', ':'),
    )
    return base64.urlsafe_b64encode(payload.encode('utf-8')).decode('ascii')


def decode_cursor(value: str) -> tuple[datetime, UUID]:
    """Decode a client-supplied collection position.

    Args:
        value: URL-safe cursor value.

    Returns:
        Creation timestamp and stable tie-breaker.

    Raises:
        ValueError: If the cursor is malformed or lacks a time zone.
    """
    try:
        raw = base64.b64decode(value.encode('ascii'), altchars=b'-_', validate=True)
        payload = json.loads(raw.decode('utf-8'))
        created_at = datetime.fromisoformat(payload['created_at'])
        identifier = UUID(payload['id'])

        if created_at.tzinfo is None:
            raise ValueError('Cursor timestamp must include a time zone.')

    except (ValueError, TypeError, KeyError, UnicodeError, binascii.Error) as error:
        raise ValueError('Invalid cursor.') from error

    return created_at, identifier
