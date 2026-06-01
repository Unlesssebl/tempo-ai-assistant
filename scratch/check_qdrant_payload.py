import asyncio
import logging
import os
import sys

# Добавляем корень проекта в путь
sys.path.append(os.getcwd())

from src.core.clients import ClientManager
from src.core.config import Config

async def check_payload():
    cfg = Config.from_env()
    cm = ClientManager.get_instance(cfg)
    client = cm.get_qdrant_client()
    
    collection_name = cfg.collection_name # documents_v2
    
    # Ищем чанки технотрона
    results = client.scroll(
        collection_name=collection_name,
        limit=5,
        with_payload=True,
        with_vectors=False
    )
    
    points = results[0]
    print(f"Total points fetched: {len(points)}")
    
    for p in points:
        payload = p.payload
        print(f"\n--- Point ID: {p.id} ---")
        print(f"Source: {payload.get('source')}")
        print(f"Text present: {bool(payload.get('text'))}")
        print(f"Parent Text present: {bool(payload.get('parent_text'))}")
        if not payload.get('parent_text'):
            print("WARNING: parent_text is MISSING!")
        else:
            print(f"Parent Text len: {len(payload.get('parent_text'))}")

if __name__ == "__main__":
    asyncio.run(check_payload())
