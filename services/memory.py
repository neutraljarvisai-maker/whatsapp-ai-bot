import chromadb
from chromadb.utils import embedding_functions
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self, persist_directory: str = "data/memory"):
        self.persist_directory = persist_directory
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)

        self.client = chromadb.PersistentClient(path=persist_directory)
        # Use a lightweight embedding model
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        self.collection = self.client.get_or_create_collection(
            name="vecta_memory",
            embedding_function=self.embedding_fn
        )

    def store(self, uid: str, text: str, metadata: Dict[str, Any] = None):
        """Stores a memory for a specific user."""
        try:
            # Generate a unique ID for the memory entry
            import uuid
            memory_id = str(uuid.uuid4())

            meta = metadata or {}
            meta["user_id"] = uid

            self.collection.add(
                documents=[text],
                metadatas=[meta],
                ids=[memory_id]
            )
            logger.info(f"Stored memory for user {uid}: {text[:50]}...")
        except Exception as e:
            logger.error(f"Error storing memory: {e}")

    def search(self, uid: str, query: str, n_results: int = 5) -> List[str]:
        """Searches for relevant memories for a specific user."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"user_id": uid}
            )

            if results and results["documents"]:
                return results["documents"][0]
            return []
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return []

    def clear_user_memory(self, uid: str):
        """Clears all memories for a specific user."""
        try:
            self.collection.delete(where={"user_id": uid})
            logger.info(f"Cleared memory for user {uid}")
        except Exception as e:
            logger.error(f"Error clearing user memory: {e}")

# Singleton instance
memory_service = MemoryService()
