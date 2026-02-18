from src.core.hooks import hookimpl
from src.core.config import settings
from .local import LocalDataSource
from .s3 import S3DataSource
import os
@hookimpl
def register_data_sources(afs):
    """
    Registers the default local storage source and S3 source.
    """
    # Use a 'data' directory in the project root by default
    storage_root = os.path.join(os.getcwd(), "data", "storage")
    
    local_source = LocalDataSource(storage_root)
    afs.register_source("local", local_source)
    print(f"Registered data source: local -> {storage_root}")

    # Register S3 Source
    s3_source = S3DataSource(
        endpoint_url=settings.S3_ENDPOINT,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        bucket_name=settings.S3_BUCKET,
        region=settings.S3_REGION
    )
    afs.register_source("s3", s3_source)
    print(f"Registered data source: s3 -> {settings.S3_ENDPOINT}/{settings.S3_BUCKET}")
