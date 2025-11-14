#!/usr/bin/env python3
"""
Simple debugging script to test Notion API connection.

Two independent flows:
1. Using notion-client SDK
2. Using direct HTTP requests

For debugging purposes only!
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)
        print(f"📄 Loaded environment from {env_file}\n")
except ImportError:
    print("ℹ️  python-dotenv not installed\n")

# Imports
import httpx
from notion_client import AsyncClient as NotionAsyncClient
from notion_client.errors import APIResponseError


# ============================================================================
# FLOW 1: Using notion-client SDK
# ============================================================================

async def flow_sdk(api_key: str, database_id: str):
    """Test using notion-client SDK."""
    print("=" * 70)
    print("FLOW 1: Using notion-client SDK")
    print("=" * 70)

    client = NotionAsyncClient(auth=api_key)

    try:
        # Step 1: Retrieve database
        print("\n[1] client.databases.retrieve()")
        database = await client.databases.retrieve(database_id=database_id)
        print(f"    Response keys: {list(database.keys())}")
        print(f"    Has 'properties': {('properties' in database)}")
        print(f"    Has 'data_sources': {('data_sources' in database)}")

        if 'data_sources' in database:
            print(f"\n    Data sources found: {len(database['data_sources'])}")
            for ds in database['data_sources']:
                print(f"      - ID: {ds['id']}, Name: {ds.get('name', 'N/A')}")

        # Step 2: Try to get data source if SDK supports it
        print("\n[2] Checking if SDK has data_sources endpoint...")
        if hasattr(client, 'data_sources'):
            print("    ✅ SDK has data_sources!")
            if 'data_sources' in database and database['data_sources']:
                data_source_id = database['data_sources'][0]['id']
                print(f"    Trying to retrieve: {data_source_id}")
                try:
                    data_source = await client.data_sources.retrieve(data_source_id=data_source_id)
                    print(f"    Response keys: {list(data_source.keys())}")
                    print(f"    Has 'properties': {('properties' in data_source)}")
                    if 'properties' in data_source:
                        print(f"    Properties: {list(data_source['properties'].keys())}")
                except Exception as e:
                    print(f"    ❌ Error: {e}")
        else:
            print("    ❌ SDK does NOT have data_sources endpoint")

    except Exception as e:
        print(f"\n❌ SDK Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await client.aclose()

    print("\n" + "=" * 70 + "\n")


# ============================================================================
# FLOW 2: Using direct HTTP requests
# ============================================================================

async def flow_http(api_key: str, database_id: str):
    """Test using direct HTTP requests."""
    print("=" * 70)
    print("FLOW 2: Using Direct HTTP Requests")
    print("=" * 70)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            # Step 1: GET /databases/{id}
            print("\n[1] GET /v1/databases/{id}")
            url = f"https://api.notion.com/v1/databases/{database_id}"
            response = await client.get(url, headers=headers)

            print(f"    Status: {response.status_code}")

            if response.status_code == 200:
                database = response.json()
                print(f"    Response keys: {list(database.keys())}")
                print(f"    Has 'properties': {('properties' in database)}")
                print(f"    Has 'data_sources': {('data_sources' in database)}")

                if 'data_sources' in database:
                    print(f"\n    Data sources found: {len(database['data_sources'])}")
                    for ds in database['data_sources']:
                        print(f"      - ID: {ds['id']}, Name: {ds.get('name', 'N/A')}")

                # Step 2: GET /data_sources/{id}
                if 'data_sources' in database and database['data_sources']:
                    data_source_id = database['data_sources'][0]['id']
                    print(f"\n[2] GET /v1/data_sources/{data_source_id}")

                    url = f"https://api.notion.com/v1/data_sources/{data_source_id}"
                    response = await client.get(url, headers=headers)

                    print(f"    Status: {response.status_code}")

                    if response.status_code == 200:
                        data_source = response.json()
                        print(f"    Response keys: {list(data_source.keys())}")
                        print(f"    Has 'properties': {('properties' in data_source)}")

                        if 'properties' in data_source:
                            print(f"\n    Properties found:")
                            for prop_name, prop_info in data_source['properties'].items():
                                prop_type = prop_info.get('type', 'unknown')
                                print(f"      - '{prop_name}': {prop_type}")
                    else:
                        error = response.json()
                        print(f"    ❌ Error: {error}")
            else:
                error = response.json()
                print(f"    ❌ Error: {error}")

        except Exception as e:
            print(f"\n❌ HTTP Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70 + "\n")


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run both flows for comparison."""

    # Get credentials
    api_key = os.getenv("NOTION_TEST_API_KEY")
    database_id = os.getenv("NOTION_TEST_DATABASE_ID")

    if not api_key or not database_id:
        print("❌ ERROR: Missing environment variables")
        print("\nRequired:")
        print("  NOTION_TEST_API_KEY=secret_xxxxx")
        print("  NOTION_TEST_DATABASE_ID=xxxxx")
        return

    print("🔍 NOTION API DEBUGGING SCRIPT")
    print("=" * 70)
    print(f"API Key: {api_key[:15]}...{api_key[-4:]}")
    print(f"Database ID: {database_id}")
    print("=" * 70)
    print()

    # Run both flows
    await flow_sdk(api_key, database_id)
    await flow_http(api_key, database_id)

    print("✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
