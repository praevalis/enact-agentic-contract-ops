"""Encode and decode opaque case-list cursors at the HTTP boundary."""

import base64
import binascii
import json
from datetime import datetime
from uuid import UUID

from enact.cases import CaseCursor


def encode_case_cursor(cursor: CaseCursor) -> str:
    """Encode a stable newest-first case position for a client.

    Args:
        cursor: Last case position in a page.

    Returns:
        URL-safe opaque cursor value.
    """
    payload = json.dumps(
        {'id': str(cursor.id), 'created_at': cursor.created_at.isoformat()},
        separators=(',', ':'),
    )
    return base64.urlsafe_b64encode(payload.encode('utf-8')).decode('ascii')


def decode_case_cursor(value: str) -> CaseCursor:
    """Decode a client-supplied case position.

    Args:
        value: URL-safe cursor value.

    Returns:
        Parsed case position.

    Raises:
        ValueError: If the cursor is malformed or lacks a time zone.
    """
    try:
        raw = base64.b64decode(value.encode('ascii'), altchars=b'-_', validate=True)
        payload = json.loads(raw.decode('utf-8'))
        created_at = datetime.fromisoformat(payload['created_at'])
        case_id = UUID(payload['id'])

        if created_at.tzinfo is None:
            raise ValueError('Cursor timestamp must include a time zone.')

    except (ValueError, TypeError, KeyError, UnicodeError, binascii.Error) as error:
        raise ValueError('Invalid case cursor.') from error

    return CaseCursor(created_at=created_at, id=case_id)
