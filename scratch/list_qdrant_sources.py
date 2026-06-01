
import asyncio
from src.core.config import Config
from src.core.clients import ClientManager
from qdrant_client import models

async def list_qdrant_sources():
    config = Config.from_env()
    client = ClientManager.get_instance(config).get_qdrant_client()
    
    print(f"Collection: {config.collection_name}")
    
    # Скроллим все точки
    offset = None
    all_sources = set()
    all_companies = set()
    
    while True:
        res, next_offset = client.scroll(
            collection_name=config.collection_name,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        for point in res:
            p = point.payload
            all_sources.add(p.get("source", "UNKNOWN"))
            all_companies.add(p.get("company", "UNKNOWN"))
            
        offset = next_offset
        if offset is None:
            break
            
    print("\nUNIQUE SOURCES IN QDRANT:")
    for s in sorted(list(all_sources)):
        print(f" - {s}")
        
    print("\nUNIQUE COMPANIES IN QDRANT:")
    for c in sorted(list(all_companies)):
        print(f" - '{c}'")

if __name__ == "__main__":
    asyncio.run(list_qdrant_sources())
