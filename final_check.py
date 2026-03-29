import os
import sys

# Add src to python path
sys.path.append(os.path.join(os.getcwd(), "src"))

from memory_mcp.db import VectorDB

def main():
    db = VectorDB()
    stats = db.get_memory_stats()
    print(f"Total memories found: {stats['total_memories']}")
    
    if stats['total_memories'] == 0:
        print("No memories found.")
        return

    export_markdown = db.export_memories()
    print("\n--- Current Memories ---\n")
    print(export_markdown)

if __name__ == "__main__":
    main()
