"""Unit tests for server-generated request correlation context."""

import pytest
from enact.platform.middleware.request_context import RequestContextMiddleware, request_id_context
from starlette.types import Message, Receive, Scope, Send


@pytest.mark.unit
@pytest.mark.asyncio
class TestRequestContextMiddleware:
    """Verify request ID response propagation and context lifecycle."""

    async def test_adds_server_generated_request_id(self) -> None:
        observed_request_id = ''
        sent_messages: list[Message] = []

        async def application(scope: Scope, receive: Receive, send: Send) -> None:
            nonlocal observed_request_id
            observed_request_id = request_id_context.get()
            await send(
                {
                    'type': 'http.response.start',
                    'status': 200,
                    'headers': [(b'x-request-id', b'client-supplied-id')],
                }
            )
            await send({'type': 'http.response.body', 'body': b'ok'})

        async def receive() -> Message:
            return {'type': 'http.request', 'body': b'', 'more_body': False}

        async def send(message: Message) -> None:
            sent_messages.append(message)

        await RequestContextMiddleware(application)(self._http_scope(), receive, send)

        response_start = sent_messages[0]
        assert response_start['type'] == 'http.response.start'
        response_headers = dict(response_start['headers'])
        response_request_id = response_headers[b'x-request-id'].decode('ascii')
        assert response_request_id == observed_request_id
        assert response_request_id != 'client-supplied-id'

    async def test_resets_request_context_after_request(self) -> None:
        async def application(scope: Scope, receive: Receive, send: Send) -> None:
            assert request_id_context.get() != '-'
            await send(
                {
                    'type': 'http.response.start',
                    'status': 204,
                    'headers': [],
                }
            )
            await send({'type': 'http.response.body', 'body': b''})

        async def receive() -> Message:
            return {'type': 'http.request', 'body': b'', 'more_body': False}

        async def send(message: Message) -> None:
            pass

        assert request_id_context.get() == '-'
        await RequestContextMiddleware(application)(self._http_scope(), receive, send)
        assert request_id_context.get() == '-'

    @staticmethod
    def _http_scope() -> Scope:
        """Build a minimal HTTP ASGI scope for middleware tests."""
        return {
            'type': 'http',
            'asgi': {'version': '3.0'},
            'http_version': '1.1',
            'method': 'GET',
            'scheme': 'http',
            'path': '/test',
            'raw_path': b'/test',
            'query_string': b'',
            'root_path': '',
            'headers': [(b'x-request-id', b'client-supplied-id')],
            'client': ('testclient', 123),
            'server': ('testserver', 80),
        }
