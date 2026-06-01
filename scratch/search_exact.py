
import asyncio
from src.core.config import Config
from src.core.clients import ClientManager
from qdrant_client import models

async def search_exact_phrase():
    config = Config.from_env()
    client = ClientManager.get_instance(config).get_qdrant_client()
    embedder = ClientManager.get_instance(config).get_embedder()
    
    query = "11:00 – 12:00 Бухгалтерия"
    vector = embedder.encode(query)[0]
    
    res = client.search(
        collection_name=config.collection_name,
        query_vector=vector,
        limit=5,
        with_payload=True
    )
    
    print(f"SEARCH FOR: {query}")
    for i, point in enumerate(res):
        p = point.payload
        print(f"[{i+1}] Score: {point.score:.4f} | Source: {p.get('source')} | Company: {p.get('company')}")
        # print(f"    Text snippet: {p.get('text', '')[:100]}...")

if __name__ == "__main__":
    asyncio.run(search_exact_phrase())
