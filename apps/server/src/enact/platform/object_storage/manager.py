"""Application-level ownership of object-storage infrastructure."""

from contextlib import AsyncExitStack

from aiobotocore.config import AioConfig
from aiobotocore.session import AioSession, get_session
from types_aiobotocore_s3.client import S3Client

from .interfaces import ObjectStorage
from .minio import MinioObjectStorage


class ObjectStorageManager:
    """Own the asynchronous S3 client and object-storage adapter lifecycle."""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str,
    ) -> None:
        """Initialize an unstarted object-storage manager.

        Args:
            endpoint_url: S3-compatible service endpoint.
            access_key: Access key used to authenticate to the object store.
            secret_key: Secret key used to authenticate to the object store.
            bucket: Pre-provisioned bucket owned by Enact.
            region: S3 signing region.
        """
        self._endpoint_url = endpoint_url
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket
        self._region = region
        self._session: AioSession = get_session()
        self._exit_stack: AsyncExitStack | None = None
        self._storage: MinioObjectStorage | None = None

    async def initialize(self) -> None:
        """Create the asynchronous S3 client once."""
        if self._storage is not None:
            return

        exit_stack = AsyncExitStack()
        client: S3Client = await exit_stack.enter_async_context(
            self._session.create_client(
                's3',
                endpoint_url=self._endpoint_url,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                region_name=self._region,
                config=AioConfig(signature_version='s3v4', s3={'addressing_style': 'path'}),
            )
        )
        self._exit_stack = exit_stack
        self._storage = MinioObjectStorage(client, self._bucket)

    def get_storage(self) -> ObjectStorage:
        """Return the initialized object-storage adapter.

        Returns:
            The process-wide object-storage adapter.

        Raises:
            RuntimeError: If object storage has not been initialized.
        """
        if self._storage is None:
            raise RuntimeError('Object-storage manager has not been initialized.')
        return self._storage

    async def ping(self) -> None:
        """Verify that the configured object-storage bucket is available.

        Raises:
            RuntimeError: If object storage has not been initialized.
            ObjectStorageUnavailableError: If the bucket cannot be accessed.
        """
        await self.get_storage().ping()

    async def dispose(self) -> None:
        """Close object-storage resources when initialized."""
        if self._exit_stack is None:
            return

        exit_stack = self._exit_stack
        self._storage = None
        self._exit_stack = None
        await exit_stack.aclose()
