import os
import shutil

# Use a temporary testing path
os.environ["MEMORY_MCP_STORAGE"] = "./test_memory_data"

from memory_mcp.db import VectorDB

def run_tests():
    print("Initializing VectorDB...")
    db = VectorDB()
    
    print("Testing add_memory...")
    mem1 = db.add_memory("The secret password is 'tangerine'.", tags=["secrets", "passwords"], context="project-x")
    assert mem1["id"] is not None
    assert "tangerine" in mem1["content"]
    
    mem2 = db.add_memory("The server IP address is 192.168.1.100.", tags=["server", "ip"], context="infrastructure")
    
    print("Testing search_memory (Semantic Search)...")
    results = db.search_memory("What is the password?", limit=1)
    assert len(results) > 0
    assert "tangerine" in results[0]["content"], f"Semantic search failed, got: {results[0]['content']}"
    
    print("Testing search_memory (Tag Filter)...")
    tag_results = db.search_memory("server", tags=["ip"], limit=5)
    assert len(tag_results) == 1
    assert "192.168.1.100" in tag_results[0]["content"]

    print("Testing update_memory...")
    updated = db.update_memory(mem1["id"], content="The updated password is 'orange'.")
    assert "orange" in updated["content"]
    
    print("Testing get_memory_stats...")
    stats = db.get_memory_stats()
    assert stats["total_memories"] == 2
    
    print("Testing remove_memory...")
    db.remove_memory(mem2["id"])
    stats2 = db.get_memory_stats()
    assert stats2["total_memories"] == 1
    
    print("Testing clear_all_memory...")
    db.clear_all_memory(confirmation=True)
    stats3 = db.get_memory_stats()
    assert stats3["total_memories"] == 0
    
    print("All tests passed successfully!")

if __name__ == "__main__":
    try:
        run_tests()
    finally:
        # Cleanup
        if os.path.exists("./test_memory_data"):
            import stat
            def remove_readonly(func, path, _):
                os.chmod(path, stat.S_IWRITE)
                func(path)
            shutil.rmtree("./test_memory_data", onerror=remove_readonly)
