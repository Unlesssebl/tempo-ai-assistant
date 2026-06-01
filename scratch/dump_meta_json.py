
import asyncio
import json
from src.core.config import Config
from src.core.clients import ClientManager
from qdrant_client import models

async def dump_meta_to_json():
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
        payload = res[0].payload
        # Удаляем текст для компактности
        if "text" in payload: del payload["text"]
        if "original_text" in payload: del payload["original_text"]
        if "document_text" in payload: del payload["document_text"]
        if "parent_text" in payload: del payload["parent_text"]
        
        with open("scratch/technotron_meta.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print("DONE: scratch/technotron_meta.json")
    else:
        print("NOT FOUND")

if __name__ == "__main__":
    asyncio.run(dump_meta_to_json())
