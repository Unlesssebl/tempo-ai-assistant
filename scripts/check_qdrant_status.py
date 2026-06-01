
import asyncio
from qdrant_client import QdrantClient
from pathlib import Path

async def check():
    path = Path("qdrant_storage_v2")
    if not path.exists():
        print(f"❌ Папка {path} не найдена")
        return
    
    client = QdrantClient(path=str(path))
    collections = client.get_collections()
    print(f"Коллекции: {[c.name for c in collections.collections]}")
    
    for coll in collections.collections:
        info = client.get_collection(coll.name)
        print(f"Коллекция '{coll.name}': {info.points_count} точек")
        
        # Проверка первой точки
        res = client.scroll(collection_name=coll.name, limit=1, with_payload=True)
        if res[0]:
            print(f"Пример payload (ID {res[0][0].id}): {list(res[0][0].payload.keys())}")
            text_preview = str(res[0][0].payload.get('text', 'НЕТ ТЕКСТА'))[:100]
            print(f"Превью текста: {text_preview}")
        else:
            print("❌ Точки не найдены через scroll")

if __name__ == "__main__":
    asyncio.run(check())
