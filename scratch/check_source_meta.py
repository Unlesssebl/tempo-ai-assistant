
import asyncio
from src.core.config import Config
from src.core.clients import ClientManager
from qdrant_client import models

async def check_specific_source():
    config = Config.from_env()
    client = ClientManager.get_instance(config).get_qdrant_client()
    
    target = "technotron/graphics/canteen_schedule_technotron.md"
    
    res, _ = client.scroll(
        collection_name=config.collection_name,
        scroll_filter=models.Filter(
            must=[models.FieldCondition(key="source", match=models.MatchValue(value=target))]
        ),
        limit=1,
        with_payload=True
    )
    
    if res:
        print(f"FOUND SOURCE: {target}")
        payload = res[0].payload
        print("METADATA:")
        for k, v in payload.items():
            if k != "text": # Пропускаем текст чтобы не забивать экран
                print(f"  {k}: {v}")
    else:
        print(f"NOT FOUND: {target}")

if __name__ == "__main__":
    asyncio.run(check_specific_source())
