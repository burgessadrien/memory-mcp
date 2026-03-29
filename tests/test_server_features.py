import os
import shutil

# Override storage for testing
os.environ["MEMORY_MCP_STORAGE"] = "./test_server_data"

from memory_mcp.server import (
    add_memory, search_memory, update_memory, remove_memory,
    get_memory_stats, export_memories, clear_all_memory, import_memories,
    add_to_scratchpad, read_scratchpad, clear_scratchpad
)

def run_feature_test():
    print("=== Testing Memory MCP Features ===\n")
    
    # 1. Add Memory
    print("1. Adding memories...")
    res1 = add_memory("The sky is blue on Earth.", tags=["nature", "facts"], context="global")
    res2 = add_memory("My favorite color is green.", tags=["preferences"])
    print(res1)
    print(res2)
    print("---")
    
    # Extract ID from res1 output: "Memory stored successfully. ID: <uuid>"
    id1 = res1.split("ID: ")[1].strip()
    id2 = res2.split("ID: ")[1].strip()
    
    # 2. Search Memory
    print("2. Searching memories...")
    search_res = search_memory("What color is the sky?", tags=["nature"])
    print(search_res)
    assert "blue" in search_res
    print("---")
    
    # 3. Update Memory
    print("3. Updating a memory...")
    update_res = update_memory(id2, content="My favorite color is emerald green.", tags=["preferences", "updated"])
    print(update_res)
    assert "updated successfully" in update_res
    print("---")
    
    # 4. Get Stats
    print("4. Getting memory stats...")
    stats = get_memory_stats()
    print(stats)
    assert "Total Memories: 2" in stats
    print("---")
    
    # 5. Export Memories
    print("5. Exporting memories...")
    export_content = export_memories()
    print("Exported Format:")
    print(export_content[:150] + "...\n(truncated)")
    assert "## Memory ID:" in export_content
    print("---")
    
    # 6. Remove Memory
    print("6. Removing a memory...")
    remove_res = remove_memory(id1)
    print(remove_res)
    assert "successfully deleted" in remove_res
    print("---")
    
    # 7. Import Memories
    print("7. Importing memories from Markdown...")
    import_text = """
---
## Memory ID: anything
**Context**: newly-imported
**Tags**: test, import
**Content**:
This is a bulk imported memory test.
---
"""
    import_res = import_memories(import_text)
    print(import_res)
    assert "Successfully imported 1" in import_res
    print("---")
    
    # 8. Clear All Memory
    print("8. Clearing all memories...")
    clear_res = clear_all_memory(confirmation=True)
    print(clear_res)
    assert "deleted" in clear_res
    
    final_stats = get_memory_stats()
    print("Final Stats:", final_stats.split("\n")[0])
    print("---")
    
    # 9. Short Term Memory Scratchpad
    print("9. Testing Short Term Memory (Scratchpad)...")
    add_to_scratchpad("Agent working on task to refactor login.", session_id="test_agent_1")
    add_to_scratchpad("Login refactor completed.", session_id="test_agent_1")
    
    scratchpad_content = read_scratchpad("test_agent_1")
    print(scratchpad_content)
    assert "refactor completed" in scratchpad_content
    
    # Search should show scratchpad first
    search_scratch_res = search_memory("login refactor", session_id="test_agent_1")
    print(search_scratch_res)
    assert "SHORT-TERM" in search_scratch_res
    assert "refactor completed" in search_scratch_res
    
    clear_scratchpad("test_agent_1")
    assert "is empty" in read_scratchpad("test_agent_1")
    
    print("\n=== ALL FEATURES TESTED SUCCESSFULLY ===")

if __name__ == "__main__":
    try:
        run_feature_test()
    finally:
        import stat
        def remove_readonly(func, path, _):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        if os.path.exists("./test_server_data"):
            shutil.rmtree("./test_server_data", onerror=remove_readonly)
