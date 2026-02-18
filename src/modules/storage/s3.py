import aioboto3
from typing import List, BinaryIO
from io import BytesIO
from src.core.storage import DataSource, FileMetadata

class S3DataSource(DataSource):
    """
    Storage backend using S3-compatible service (MinIO/AWS S3).
    """
    def __init__(self, endpoint_url: str, access_key: str, secret_key: str, bucket_name: str, region: str = "us-east-1"):
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.region = region
        self.session = aioboto3.Session()

    async def connect(self) -> None:
        # Check if bucket exists
        async with self.session.client("s3", endpoint_url=self.endpoint_url,
                                     aws_access_key_id=self.access_key,
                                     aws_secret_access_key=self.secret_key,
                                     region_name=self.region) as s3:
            try:
                await s3.head_bucket(Bucket=self.bucket_name)
            except:
                await s3.create_bucket(Bucket=self.bucket_name)

    async def list_dir(self, path: str) -> List[FileMetadata]:
        path = path.lstrip("/")
        if path and not path.endswith("/"):
            path += "/"
            
        async with self.session.client("s3", endpoint_url=self.endpoint_url,
                                     aws_access_key_id=self.access_key,
                                     aws_secret_access_key=self.secret_key,
                                     region_name=self.region) as s3:
            paginator = s3.get_paginator("list_objects_v2")
            results = []
            async for page in paginator.paginate(Bucket=self.bucket_name, Prefix=path, Delimiter="/"):
                # Folders (CommonPrefixes)
                for prefix in page.get("CommonPrefixes", []):
                    name = prefix["Prefix"][len(path):].rstrip("/")
                    results.append(FileMetadata(
                        name=name,
                        path=prefix["Prefix"].rstrip("/"),
                        size=0,
                        is_dir=True
                    ))
                
                # Files (Contents)
                for obj in page.get("Contents", []):
                    if obj["Key"] == path:
                        continue # Skip the directory object itself
                    name = obj["Key"][len(path):]
                    results.append(FileMetadata(
                        name=name,
                        path=obj["Key"],
                        size=obj["Size"],
                        is_dir=False,
                        modified_at=obj["LastModified"].timestamp()
                    ))
            return results

    async def open_file(self, path: str, mode: str = "rb") -> BinaryIO:
        # S3 objects are usually read into memory or streamed.
        # For simplicity, we'll download the whole thing into a BytesIO.
        async with self.session.client("s3", endpoint_url=self.endpoint_url,
                                     aws_access_key_id=self.access_key,
                                     aws_secret_access_key=self.secret_key,
                                     region_name=self.region) as s3:
            resp = await s3.get_object(Bucket=self.bucket_name, Key=path.lstrip("/"))
            content = await resp["Body"].read()
            return BytesIO(content)

    async def save_file(self, path: str, content: bytes) -> None:
        async with self.session.client("s3", endpoint_url=self.endpoint_url,
                                     aws_access_key_id=self.access_key,
                                     aws_secret_access_key=self.secret_key,
                                     region_name=self.region) as s3:
            await s3.put_object(Bucket=self.bucket_name, Key=path.lstrip("/"), Body=content)
