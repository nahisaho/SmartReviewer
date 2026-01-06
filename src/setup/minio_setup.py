"""
SmartReviewer - MinIO Setup Script
Object Storage initialization and bucket management

Usage:
    python -m src.setup.minio_setup
"""

import os
from typing import Any

from minio import Minio
from minio.error import S3Error


# Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"


# Bucket configurations
BUCKETS = {
    "documents": {
        "description": "Uploaded documents for review",
        "versioning": True,
    },
    "embeddings": {
        "description": "Cached embeddings and chunks",
        "versioning": False,
    },
    "ontologies": {
        "description": "OWL/RDF ontology files",
        "versioning": True,
    },
    "results": {
        "description": "Review results and reports",
        "versioning": True,
    },
    "guidelines": {
        "description": "Guideline documents",
        "versioning": True,
    },
}


def get_client() -> Minio:
    """Create MinIO client instance."""
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )


def check_health(client: Minio) -> bool:
    """Check MinIO server health."""
    try:
        buckets = client.list_buckets()
        print(f"✅ MinIO is healthy. Buckets: {len(buckets)}")
        return True
    except Exception as e:
        print(f"❌ MinIO health check failed: {e}")
        return False


def create_bucket(
    client: Minio,
    name: str,
    config: dict[str, Any],
) -> bool:
    """Create a bucket if it doesn't exist."""
    try:
        if client.bucket_exists(name):
            print(f"  ⏭️  Bucket '{name}' already exists, skipping")
            return True
        
        client.make_bucket(name)
        print(f"  ✅ Created bucket: {name}")
        
        # Note: MinIO versioning requires enterprise edition
        # For community edition, we skip versioning setup
        
        return True
        
    except S3Error as e:
        print(f"  ❌ Failed to create bucket '{name}': {e}")
        return False


def setup_buckets() -> bool:
    """Setup all required buckets."""
    print("\n🔧 Setting up MinIO buckets...")
    
    client = get_client()
    
    if not check_health(client):
        return False
    
    success = True
    for name, config in BUCKETS.items():
        if not create_bucket(client, name, config):
            success = False
    
    return success


def show_status() -> None:
    """Show status of all buckets."""
    print("\n📊 MinIO Bucket Status:")
    print("-" * 60)
    
    client = get_client()
    
    if not check_health(client):
        return
    
    for name in BUCKETS:
        try:
            if client.bucket_exists(name):
                # Count objects
                objects = list(client.list_objects(name, recursive=True))
                total_size = sum(obj.size for obj in objects if obj.size)
                
                print(f"  {name}:")
                print(f"    - Objects: {len(objects)}")
                print(f"    - Total Size: {format_size(total_size)}")
            else:
                print(f"  {name}: Not found")
        except Exception as e:
            print(f"  {name}: Error - {e}")
    
    print("-" * 60)


def format_size(size: int) -> str:
    """Format size in human readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def upload_sample_data(client: Minio) -> None:
    """Upload sample/test data for development."""
    import io
    import json
    
    print("\n  Uploading sample data...")
    
    # Sample check items metadata
    check_items_meta = {
        "version": "1.0.0",
        "document_types": ["basic_design", "test_plan"],
        "items_per_type": 10,
    }
    
    data = json.dumps(check_items_meta, ensure_ascii=False, indent=2).encode("utf-8")
    client.put_object(
        "results",
        "metadata/check_items_meta.json",
        io.BytesIO(data),
        len(data),
        content_type="application/json",
    )
    print("    ✅ Uploaded: results/metadata/check_items_meta.json")


def main() -> None:
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MinIO Setup for SmartReviewer")
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show bucket status only",
    )
    parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Upload sample data for development",
    )
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
    else:
        success = setup_buckets()
        if success:
            print("\n✅ MinIO setup completed successfully!")
            
            if args.sample_data:
                client = get_client()
                upload_sample_data(client)
            
            show_status()
        else:
            print("\n❌ MinIO setup failed!")
            exit(1)


if __name__ == "__main__":
    main()
