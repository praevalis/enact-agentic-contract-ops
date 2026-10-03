"""S3-compatible object-storage adapter used with MinIO locally."""

from collections.abc import Mapping
from typing import Never

from botocore.exceptions import BotoCoreError, ClientError
from types_aiobotocore_s3.client import S3Client

from .errors import ObjectNotFoundError, ObjectStorageUnavailableError
from .interfaces import ObjectMetadata, StoredObject

NOT_FOUND_CODES = frozenset({'404', 'NoSuchKey', 'NotFound'})


def raise_client_error(error: ClientError, key: str) -> Never:
    """Translate a botocore client error into the application contract."""
    error_code = error.response.get('Error', {}).get('Code')
    status_code = error.response.get('ResponseMetadata', {}).get('HTTPStatusCode')

    if error_code in NOT_FOUND_CODES or status_code == 404:
        raise ObjectNotFoundError(key) from error

    raise ObjectStorageUnavailableError from error


class MinioObjectStorage:
    """Implement object storage through MinIO's S3-compatible API."""

    def __init__(self, client: S3Client, bucket: str) -> None:
        """Initialize the adapter.

        Args:
            client: Initialized asynchronous S3 client.
            bucket: Pre-provisioned bucket owned by Enact.
        """
        self._client = client
        self._bucket = bucket

    async def put_object(
        self,
        key: str,
        content: bytes,
        content_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> ObjectMetadata:
        """Store bytes at an application-owned key.

        Args:
            key: Opaque storage key selected by the calling application service.
            content: Complete object content.
            content_type: Media type recorded with the object.
            metadata: Optional application metadata recorded with the object.

        Returns:
            Metadata describing the stored object.

        Raises:
            ObjectStorageUnavailableError: If MinIO cannot store the object.
        """
        try:
            response = await self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=content,
                ContentLength=len(content),
                ContentType=content_type,
                Metadata=dict(metadata or {}),
            )
        except (BotoCoreError, ClientError) as error:
            raise ObjectStorageUnavailableError from error

        return ObjectMetadata(
            key=key,
            content_length=len(content),
            content_type=content_type,
            etag=response['ETag'].strip('"'),
            metadata=dict(metadata or {}),
        )

    async def get_object(self, key: str) -> StoredObject:
        """Retrieve an object's bytes and metadata.

        Args:
            key: Opaque storage key.

        Returns:
            The stored bytes and their metadata.

        Raises:
            ObjectNotFoundError: If the key does not exist.
            ObjectStorageUnavailableError: If MinIO cannot retrieve the object.
        """
        try:
            response = await self._client.get_object(Bucket=self._bucket, Key=key)
            async with response['Body'] as stream:
                content = await stream.read()
        except ClientError as error:
            raise_client_error(error, key)
        except BotoCoreError as error:
            raise ObjectStorageUnavailableError from error

        return StoredObject(
            content=content,
            details=ObjectMetadata(
                key=key,
                content_length=response.get('ContentLength', 0),
                content_type=response.get('ContentType'),
                etag=response['ETag'].strip('"'),
                metadata=dict(response.get('Metadata', {})),
            ),
        )

    async def stat_object(self, key: str) -> ObjectMetadata:
        """Retrieve metadata without downloading object content.

        Args:
            key: Opaque storage key.

        Returns:
            Metadata describing the stored object.

        Raises:
            ObjectNotFoundError: If the key does not exist.
            ObjectStorageUnavailableError: If MinIO cannot retrieve metadata.
        """
        try:
            response = await self._client.head_object(Bucket=self._bucket, Key=key)
        except ClientError as error:
            raise_client_error(error, key)
        except BotoCoreError as error:
            raise ObjectStorageUnavailableError from error

        return ObjectMetadata(
            key=key,
            content_length=response.get('ContentLength', 0),
            content_type=response.get('ContentType'),
            etag=response['ETag'].strip('"'),
            metadata=dict(response.get('Metadata', {})),
        )

    async def delete_object(self, key: str) -> None:
        """Delete an object if it exists.

        Args:
            key: Opaque storage key.

        Raises:
            ObjectStorageUnavailableError: If MinIO cannot complete the delete.
        """
        try:
            await self._client.delete_object(Bucket=self._bucket, Key=key)
        except (BotoCoreError, ClientError) as error:
            raise ObjectStorageUnavailableError from error

    async def ping(self) -> None:
        """Verify that the configured bucket is accessible.

        Raises:
            ObjectStorageUnavailableError: If MinIO cannot access the bucket.
        """
        try:
            await self._client.head_bucket(Bucket=self._bucket)
        except (BotoCoreError, ClientError) as error:
            raise ObjectStorageUnavailableError from error
