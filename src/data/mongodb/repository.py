from datetime import datetime
import pymongo
from typing import Dict, Any, Optional

class MongoRepository:
    def __init__(self, uri: str, database: str, collection: str):
        self.client = pymongo.MongoClient(uri)
        self.db = self.client[database]
        self.collection = self.db[collection]

    def insert_one(self, document: Dict[str, Any]) -> bool:
        try:
            self.collection.insert_one(document)
            return True
        except Exception as e:
            print(f"Error inserting document: {e}")
            return False

    def insert_many(self, documents: list[Dict[str, Any]]) -> int:
        try:
            result = self.collection.insert_many(documents)
            return len(result.inserted_ids)
        except Exception as e:
            print(f"Error inserting documents: {e}")
            return 0

    def find_duplicates(self, email: str, password: str, url: Optional[str] = None) -> bool:
        query = {"email": email, "password": password}
        if url:
            query["url"] = url
        return self.collection.find_one(query) is not None

    def close(self):
        self.client.close()