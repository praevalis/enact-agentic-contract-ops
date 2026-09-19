"""ASGI middleware and context for server-generated request correlation IDs."""

import logging
from contextvars import ContextVar
from time import perf_counter
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

request_id_context: ContextVar[str] = ContextVar('request_id', default='-')
logger = logging.getLogger(__name__)


class RequestContextMiddleware:
    """Attach a generated request ID to each HTTP request and its log context."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application wrapped by this middleware.
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process an ASGI request while its correlation context is active.

        Args:
            scope: ASGI connection scope.
            receive: ASGI message receiver.
            send: ASGI message sender.
        """
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())
        context_token = request_id_context.set(request_id)
        started_at = perf_counter()
        status_code: int | None = None

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message['type'] == 'http.response.start':
                status_code = message['status']
                headers = [
                    (name, value)
                    for name, value in message.get('headers', [])
                    if name.lower() != b'x-request-id'
                ]
                headers.append((b'x-request-id', request_id.encode('ascii')))
                message = {**message, 'headers': headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            duration_ms = (perf_counter() - started_at) * 1000
            logger.info(
                'HTTP request completed method=%s path=%s status_code=%s duration_ms=%.2f',
                scope['method'],
                scope['path'],
                status_code if status_code is not None else 'not_started',
                duration_ms,
            )
            request_id_context.reset(context_token)
