import chromadb
import os

STORAGE_PATH = "c:\\Users\\Adrien Burgess\\Code\\memory-mcp\\memory_data\\vector_db"

def check_db():
    print(f"Checking ChromaDB at {STORAGE_PATH}")
    if not os.path.exists(STORAGE_PATH):
        print(f"Directory {STORAGE_PATH} does not exist.")
        return
    
    try:
        client = chromadb.PersistentClient(path=STORAGE_PATH)
        collections = client.list_collections()
        print(f"Successfully connected! Collections: {[c.name for c in collections]}")
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}")

if __name__ == "__main__":
    check_db()
