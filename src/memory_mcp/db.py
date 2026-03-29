import os
import uuid
import datetime
import chromadb
from chromadb.utils import embedding_functions

import datetime
import chromadb
from chromadb.utils import embedding_functions

# Get the storage path from environment variable, default to local directory
STORAGE_PATH = os.environ.get("MEMORY_MCP_STORAGE", "./memory_data")
COLLECTION_NAME = "agent_memories"

class VectorDB:
    def __init__(self):
        self._initialize_db()

    def _initialize_db(self):
        """Attempts to initialize the database, providing one automated repair attempt if it fails."""
        try:
            print(f"--- DATABASE INITIALIZATION START ---")
            self._connection_logic()
            print(f"--- DATABASE INITIALIZATION SUCCESS ---")
        except Exception as e:
            error_msg = str(e).lower()
            print(f"--- DATABASE INITIALIZATION FAILED: {e} ---")
            
            # Check for common corruption or initialization errors
            is_corrupted = any(phrase in error_msg for phrase in [
                "no such table: collections", 
                "unable to open database file",
                "table collections already exists"
            ])
            
            if is_corrupted:
                print("Repair condition met. Attempting automated recovery...")
                if self._force_repair():
                    print("Repair executed. Retrying connection logic (Last Attempt).")
                    try:
                        self._connection_logic()
                        return
                    except Exception as retry_e:
                        print(f"FATAL: Connection failed after repair: {retry_e}")
            raise

    def _connection_logic(self):
        """Core initialization logic for ChromaDB using absolute paths and explicit steps."""
        abs_storage_path = os.path.abspath(STORAGE_PATH)
        print(f"[Step 1/3] Target Path: {abs_storage_path}")
        
        # Ensure the directory exists before client initialization
        if not os.path.exists(abs_storage_path):
            print(f"[Step 1.1] Creating missing directory: {abs_storage_path}")
            os.makedirs(abs_storage_path, exist_ok=True)
            
        print(f"[Step 2/3] Initializing PersistentClient...")
        self.client = chromadb.PersistentClient(path=abs_storage_path)
        
        print(f"[Step 3/3] Loading Embeddings & Collection...")
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"description": "Long-term memories for AI agents"}
        )
        print(f"Initialization complete. Collection '{COLLECTION_NAME}' is ready.")

    def _force_repair(self) -> bool:
        """Backs up the current storage folder and clears it for re-initialization."""
        import shutil
        import time
        
        if not os.path.exists(STORAGE_PATH):
            return False
            
        backup_path = f"{STORAGE_PATH}_backup_{int(time.time())}"
        print(f"Backing up data to: {backup_path}")
        try:
            shutil.copytree(STORAGE_PATH, backup_path)
            # Clear existing directory contents
            for filename in os.listdir(STORAGE_PATH):
                file_path = os.path.join(STORAGE_PATH, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Warning: Failed to delete {file_path}: {e}")
            print("Database directory cleared.")
            return True
        except Exception as repair_e:
            print(f"Repair process failed: {repair_e}")
            return False

    def _get_isotime(self) -> str:
        """Returns the current UTC time in ISO 8601 format."""
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def add_memory(self, content: str, tags: list[str] = None, context: str = "global") -> dict:
        memory_id = str(uuid.uuid4())
        timestamp = self._get_isotime()
        tags = tags or []
        
        # We store tags as a comma-separated string for simpler Chroma metadata
        tags_str = ",".join(tags)
        
        metadata = {
            "tags": tags_str,
            "context": context,
            "timestamp": timestamp
        }
        
        self.collection.add(
            documents=[content],
            ids=[memory_id],
            metadatas=[metadata]
        )
        
        return {"id": memory_id, "content": content, "metadata": metadata}

    def search_memory(self, query: str, tags: list[str] = None, context: str = None, limit: int = 5) -> list[dict]:
        where_clause = {}
        filters = []
        
        if context:
            filters.append({"context": context})
        if tags:
            for tag in tags:
                # Use $contains to match substring within the tags comma-separated string
                filters.append({"tags": {"$contains": tag}})

        if len(filters) > 1:
            where_clause = {"$and": filters}
        elif len(filters) == 1:
            where_clause = filters[0]
            
        if not where_clause:
            where_clause = None

        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_clause
        )
        
        memories = []
        if results and results.get("ids") and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                memories.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
        return memories

    def update_memory(self, memory_id: str, content: str = None, tags: list[str] = None, context: str = None) -> dict:
        existing = self.collection.get(ids=[memory_id])
        if not existing or not existing.get("ids"):
            raise ValueError(f"Memory with ID {memory_id} not found.")
            
        old_content = existing["documents"][0]
        old_metadata = existing["metadatas"][0]
        
        new_content = content if content is not None else old_content
        
        new_tags = old_metadata.get("tags", "")
        if tags is not None:
            new_tags = ",".join(tags)
            
        new_context = context if context is not None else old_metadata.get("context", "global")
        
        new_metadata = {
            "tags": new_tags,
            "context": new_context,
            "timestamp": self._get_isotime()
        }
        
        self.collection.update(
            ids=[memory_id],
            documents=[new_content],
            metadatas=[new_metadata]
        )
        
        return {"id": memory_id, "content": new_content, "metadata": new_metadata}

    def remove_memory(self, memory_id: str) -> bool:
        existing = self.collection.get(ids=[memory_id])
        if not existing or not existing.get("ids"):
            return False
            
        self.collection.delete(ids=[memory_id])
        return True

    def clear_all_memory(self, confirmation: bool) -> str:
        if not confirmation:
            return "Clear operation aborted. Confirmation flag must be True."
        
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"description": "Long-term memories for AI agents"}
        )
        return "All memories have been permanently deleted."

    def get_memory_stats(self) -> dict:
        count = self.collection.count()
        return {
            "total_memories": count,
            "collection_name": COLLECTION_NAME,
            "storage_path": STORAGE_PATH
        }

    def export_memories(self) -> str:
        all_data = self.collection.get()
        if not all_data or not all_data.get("ids"):
            return "# Memory Export\n\nNo memories found."
            
        lines = ["# Memory Export\n"]
        for i in range(len(all_data["ids"])):
            m_id = all_data["ids"][i]
            m_doc = all_data["documents"][i]
            m_meta = all_data["metadatas"][i]
            
            lines.append(f"## Memory ID: {m_id}")
            lines.append(f"**Context**: {m_meta.get('context')}")
            lines.append(f"**Tags**: {m_meta.get('tags')}")
            lines.append(f"**Timestamp**: {m_meta.get('timestamp')}")
            lines.append(f"**Content**:\n{m_doc}")
            lines.append("\n---\n")
            
        return "\n".join(lines)
