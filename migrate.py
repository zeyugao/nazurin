import asyncio
from pathlib import Path
from tinydb import TinyDB
from motor.motor_asyncio import AsyncIOMotorClient
from nazurin.config import DATA_DIR, env
from tqdm import tqdm


async def migrate_collection(collection_name):
    # Initialize TinyDB
    local_db_path = Path(DATA_DIR) / f"{collection_name}.json"
    local_db = TinyDB(local_db_path)

    # Initialize MongoDB
    mongo_uri = env.str(
        "MONGO_URI", default="mongodb://localhost:27017/nazurin")
    client = AsyncIOMotorClient(mongo_uri)
    mongo_db = client.get_default_database()
    mongo_collection = mongo_db[collection_name]

    # Fetch all documents from TinyDB
    all_documents = local_db.all()

    # Insert documents into MongoDB
    for document in tqdm(all_documents):
        try:
            key = document['key']
            document["_id"] = key
            await mongo_collection.insert_one(document)
        except Exception as e:
            print(f"Error inserting document with key {key}: {e}")

    # Close TinyDB
    local_db.close()


async def main():
    db_files = Path(DATA_DIR).glob("*.json")
    tasks = [migrate_collection(file.stem) for file in db_files]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
