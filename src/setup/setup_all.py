"""
SmartReviewer - Full Infrastructure Setup Script
Run all setup scripts in sequence

Usage:
    python -m src.setup.setup_all
"""

import sys
import time


def main() -> None:
    """Run all infrastructure setup."""
    print("=" * 60)
    print("🚀 SmartReviewer Infrastructure Setup")
    print("=" * 60)
    
    start_time = time.time()
    
    # Import setup modules
    from . import qdrant_setup, neo4j_setup, minio_setup
    
    results = {}
    
    # 1. Qdrant Setup
    print("\n" + "=" * 60)
    print("1️⃣  Qdrant (Vector Database)")
    print("=" * 60)
    try:
        results["qdrant"] = qdrant_setup.setup_collections()
    except Exception as e:
        print(f"❌ Qdrant setup failed: {e}")
        results["qdrant"] = False
    
    # 2. Neo4j Setup
    print("\n" + "=" * 60)
    print("2️⃣  Neo4j (Graph Database)")
    print("=" * 60)
    try:
        results["neo4j"] = neo4j_setup.setup_database()
    except Exception as e:
        print(f"❌ Neo4j setup failed: {e}")
        results["neo4j"] = False
    
    # 3. MinIO Setup
    print("\n" + "=" * 60)
    print("3️⃣  MinIO (Object Storage)")
    print("=" * 60)
    try:
        results["minio"] = minio_setup.setup_buckets()
    except Exception as e:
        print(f"❌ MinIO setup failed: {e}")
        results["minio"] = False
    
    # Summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("📋 Setup Summary")
    print("=" * 60)
    
    all_success = True
    for service, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {service}")
        if not success:
            all_success = False
    
    print(f"\n  ⏱️  Total time: {elapsed:.1f}s")
    print("=" * 60)
    
    if all_success:
        print("\n✅ All infrastructure setup completed successfully!")
        print("\nNext steps:")
        print("  1. Verify services: docker-compose ps")
        print("  2. Access UIs:")
        print("     - Qdrant: http://localhost:6333/dashboard")
        print("     - Neo4j:  http://localhost:7474")
        print("     - MinIO:  http://localhost:9001")
    else:
        print("\n⚠️  Some services failed to setup. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
