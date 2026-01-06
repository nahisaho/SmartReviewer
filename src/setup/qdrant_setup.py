"""
SmartReviewer - Qdrant Setup Script
Vector Database initialization and collection management

Usage:
    python -m src.setup.qdrant_setup
"""

import asyncio
import os
from typing import Any

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse


# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# Collection configurations
COLLECTIONS = {
    "documents": {
        "description": "Document chunks and their embeddings",
        "vector_size": 1024,  # multilingual-e5-large
        "distance": models.Distance.COSINE,
    },
    "guidelines": {
        "description": "Guideline document embeddings",
        "vector_size": 1024,
        "distance": models.Distance.COSINE,
    },
    "check_items": {
        "description": "Check item embeddings for semantic matching",
        "vector_size": 1024,
        "distance": models.Distance.COSINE,
    },
}


def get_client() -> QdrantClient:
    """Create Qdrant client instance."""
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def check_health(client: QdrantClient) -> bool:
    """Check Qdrant server health."""
    try:
        info = client.get_collections()
        print(f"✅ Qdrant is healthy. Collections: {len(info.collections)}")
        return True
    except Exception as e:
        print(f"❌ Qdrant health check failed: {e}")
        return False


def create_collection(
    client: QdrantClient,
    name: str,
    config: dict[str, Any],
    recreate: bool = False,
) -> bool:
    """Create a collection if it doesn't exist."""
    try:
        # Check if collection exists
        collections = client.get_collections()
        exists = any(c.name == name for c in collections.collections)
        
        if exists:
            if recreate:
                print(f"  Recreating collection: {name}")
                client.delete_collection(name)
            else:
                print(f"  ⏭️  Collection '{name}' already exists, skipping")
                return True
        
        # Create collection
        client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(
                size=config["vector_size"],
                distance=config["distance"],
            ),
        )
        
        # Create payload indexes for filtering
        client.create_payload_index(
            collection_name=name,
            field_name="document_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        client.create_payload_index(
            collection_name=name,
            field_name="document_type",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        client.create_payload_index(
            collection_name=name,
            field_name="chunk_index",
            field_schema=models.PayloadSchemaType.INTEGER,
        )
        
        print(f"  ✅ Created collection: {name}")
        return True
        
    except UnexpectedResponse as e:
        print(f"  ❌ Failed to create collection '{name}': {e}")
        return False


def setup_collections(recreate: bool = False) -> bool:
    """Setup all required collections."""
    print("\n🔧 Setting up Qdrant collections...")
    
    client = get_client()
    
    if not check_health(client):
        return False
    
    success = True
    for name, config in COLLECTIONS.items():
        if not create_collection(client, name, config, recreate):
            success = False
    
    return success


def get_collection_info(client: QdrantClient, name: str) -> dict[str, Any] | None:
    """Get collection information."""
    try:
        info = client.get_collection(name)
        return {
            "name": name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": info.status.name,
            "vector_size": info.config.params.vectors.size,
        }
    except Exception:
        return None


def show_status() -> None:
    """Show status of all collections."""
    print("\n📊 Qdrant Collection Status:")
    print("-" * 60)
    
    client = get_client()
    
    if not check_health(client):
        return
    
    for name in COLLECTIONS:
        info = get_collection_info(client, name)
        if info:
            print(f"  {name}:")
            print(f"    - Status: {info['status']}")
            print(f"    - Vectors: {info['vectors_count']}")
            print(f"    - Vector Size: {info['vector_size']}")
        else:
            print(f"  {name}: Not found")
    
    print("-" * 60)


def main() -> None:
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Qdrant Setup for SmartReviewer")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate collections if they exist",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show collection status only",
    )
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
    else:
        success = setup_collections(recreate=args.recreate)
        if success:
            print("\n✅ Qdrant setup completed successfully!")
            show_status()
        else:
            print("\n❌ Qdrant setup failed!")
            exit(1)


if __name__ == "__main__":
    main()
