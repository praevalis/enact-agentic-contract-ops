"""Functional tests for the S3-compatible object-storage boundary."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from aiobotocore.config import AioConfig
from aiobotocore.session import get_session
from enact.platform.object_storage import (
    ObjectNotFoundError,
    ObjectStorage,
    ObjectStorageManager,
)
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

MINIO_IMAGE = 'quay.io/minio/minio:RELEASE.2025-09-07T16-13-09Z'
MINIO_ACCESS_KEY = 'test-access-key'
MINIO_SECRET_KEY = 'test-secret-key'
MINIO_BUCKET = 'enact-test-documents'
MINIO_PORT = 9000


# Move this fixture to conftest.py if other test modules need it instead of duplicating it.
@pytest_asyncio.fixture
async def object_storage() -> AsyncGenerator[ObjectStorage]:
    """Provide object storage backed by a disposable MinIO server."""
    container = (
        DockerContainer(MINIO_IMAGE)
        .with_env('MINIO_ROOT_USER', MINIO_ACCESS_KEY)
        .with_env('MINIO_ROOT_PASSWORD', MINIO_SECRET_KEY)
        .with_exposed_ports(MINIO_PORT)
        .with_command('server /data')
        .waiting_for(LogMessageWaitStrategy('API:').with_startup_timeout(60))
    )
    container.start()
    endpoint_url = (
        f'http://{container.get_container_host_ip()}:{container.get_exposed_port(MINIO_PORT)}'
    )

    session = get_session()
    async with session.create_client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name='us-east-1',
        config=AioConfig(signature_version='s3v4', s3={'addressing_style': 'path'}),
    ) as client:
        await client.create_bucket(Bucket=MINIO_BUCKET)

    manager = ObjectStorageManager(
        endpoint_url=endpoint_url,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        bucket=MINIO_BUCKET,
        region='us-east-1',
    )
    await manager.initialize()

    try:
        yield manager.get_storage()
    finally:
        await manager.dispose()
        container.stop()


@pytest.mark.integration
@pytest.mark.asyncio
class TestMinioObjectStorage:
    """Exercise observable object-storage behavior against real MinIO."""

    async def test_object_lifecycle(self, object_storage: ObjectStorage) -> None:
        """Store, inspect, retrieve, and delete an object through the boundary."""
        key = 'documents/contract.pdf'
        content = b'%PDF-1.7\n\x00binary-contract-content'
        application_metadata = {'sha256': 'contract-content-hash'}

        stored = await object_storage.put_object(
            key=key,
            content=content,
            content_type='application/pdf',
            metadata=application_metadata,
        )
        inspected = await object_storage.stat_object(key)
        retrieved = await object_storage.get_object(key)

        assert stored.key == key
        assert stored.content_length == len(content)
        assert stored.etag is not None
        assert inspected == stored
        assert retrieved.content == content
        assert retrieved.details == stored

        await object_storage.delete_object(key)

        with pytest.raises(ObjectNotFoundError) as missing:
            await object_storage.get_object(key)
        assert missing.value.code == 'object_not_found'
