import asyncio
import time
from mcp.server.fastmcp import FastMCP
from memory_mcp.db import VectorDB

# Initialize FastMCP Server
mcp = FastMCP("Memory-MCP")

# Initialize VectorDB
db = VectorDB()

# --- Short Term Memory (Scratchpad) Management ---
scratchpads: dict[str, dict] = {}
SCRATCHPAD_TTL_SECONDS = 2 * 60 * 60 # 2 hours

def _cleanup_scratchpads():
    """Lazily cleans up stale scratchpads."""
    current_time = time.time()
    stale_keys = [
        k for k, v in scratchpads.items()
        if current_time - v.get("last_accessed", current_time) > SCRATCHPAD_TTL_SECONDS
    ]
    for k in stale_keys:
        del scratchpads[k]

def _get_scratchpad(session_id: str) -> list[str]:
    """Retrieves or creates a scratchpad for the given session ID."""
    _cleanup_scratchpads()
    if session_id not in scratchpads:
        scratchpads[session_id] = {"notes": [], "last_accessed": time.time()}
    else:
        scratchpads[session_id]["last_accessed"] = time.time()
    return scratchpads[session_id]["notes"]

@mcp.tool()
def add_to_scratchpad(note: str, session_id: str = "default") -> str:
    """
    Add a temporary note to the short-term scratchpad.
    
    Use this for ephemeral information that only matters for the current session/task.
    Scratchpad data is stored in memory and expires after 2 hours of inactivity.
    
    When to use:
    - Tracking context during a multi-step conversation
    - Holding temporary information that doesn't need permanent storage
    - Storing intermediate results before deciding what to keep long-term
    
    Args:
        note: The content to temporarily store.
        session_id: A unique ID for this conversation/task (defaults to "default").
    """
    notes = _get_scratchpad(session_id)
    notes.append(note)
    return f"Added to scratchpad for session '{session_id}'."

@mcp.tool()
def read_scratchpad(session_id: str = "default") -> str:
    """
    Read all temporary notes from the scratchpad for a session.
    
    Use this to retrieve information stored with add_to_scratchpad.
    Note: Scratchpad data expires after 2 hours of inactivity.
    
    Args:
        session_id: The session to read from (defaults to "default").
    """
    notes = _get_scratchpad(session_id)
    if not notes:
        return f"Scratchpad for session '{session_id}' is empty."
    
    output = [f"Scratchpad for '{session_id}':"]
    for idx, note in enumerate(notes, 1):
        output.append(f"[{idx}] {note}")
    return "\n".join(output)

@mcp.tool()
def clear_scratchpad(session_id: str = "default") -> str:
    """
    Clear all temporary notes from the scratchpad for a session.
    
    Use this when finishing a task to free up memory.
    This is safe to call even if the scratchpad is already empty.
    
    Args:
        session_id: The session to clear (defaults to "default").
    """
    _cleanup_scratchpads()
    if session_id in scratchpads:
        del scratchpads[session_id]
        return f"Cleared scratchpad for session '{session_id}'."
    return f"Scratchpad for session '{session_id}' is already empty."


@mcp.tool()
def add_memory(content: str, tags: list[str] | None = None, context: str = "global") -> str:
    """
    Store completely NEW information in the vector database.
    
    Use this when adding facts, preferences, or context that has NEVER been stored before.
    If you're correcting existing information or unsure if it already exists, use 
    add_or_update_memory instead to avoid duplicates.
    
    Args:
        content: The actual information, fact, or memory to store.
        tags: Optional list of topic tags for organization (e.g., ["facts", "work"]).
        context: Optional project or domain context (defaults to "global", e.g., "gaming", "work").
    
    Returns:
        The ID of the newly created memory.
    """
    result = db.add_memory(content, tags=tags, context=context)
    return f"Memory stored successfully. ID: {result['id']}"

@mcp.tool()
def add_or_update_memory(content: str, tags: list[str] | None = None, context: str = "global", similarity_threshold: float = 0.7) -> str:
    """
    Add new information OR update existing similar memories.
    
    This is the RECOMMENDED tool for storing information when you're unsure whether it already exists.
    It searches for similar content and either updates an existing memory or creates a new one.
    
    When to use:
    - Storing corrected information (e.g., "sky is purple" when "sky is blue" exists)
    - Adding info that might already be stored under different wording
    - When you want to avoid duplicate memories on the same topic
    
    Args:
        content: The information to store (will update existing similar content if found).
        tags: Optional list of topic tags for organization.
        context: Optional project or domain context (defaults to "global").
        similarity_threshold: How similar existing memories must be to update (0.0-1.0, default 0.7).
            Higher = stricter matching, Lower = more likely to update existing.
    
    Returns:
        Whether memory was created new or updated existing (with the ID).
    """
    results = db.search_memory(content, tags=tags, context=context, limit=3)
    
    if results and results[0].get("distance") is not None:
        distance = results[0]["distance"]
        similarity = 1 - distance
        
        if similarity >= similarity_threshold:
            existing_id = results[0]["id"]
            db.update_memory(existing_id, content=content, tags=tags, context=context)
            return f"Updated existing memory (similarity: {similarity:.2f}). ID: {existing_id}"
    
    result = db.add_memory(content, tags=tags, context=context)
    return f"Created new memory. ID: {result['id']}"

@mcp.tool()
def search_memory(query: str, session_id: str = "default", tags: list[str] | None = None, context: str | None = None, limit: int = 5) -> str:
    """
    Search for relevant memories across both short-term and long-term storage.
    
    This is the PRIMARY tool for retrieving stored information. It searches:
    1. Short-term scratchpad (recent notes for current session)
    2. Long-term vector database (semantic search)
    
    When to use:
    - When you need to recall previously stored facts, preferences, or context
    - Before updating or deleting memories (to find their IDs)
    - To verify what information already exists before adding new data
    
    Args:
        query: The question, topic, or keywords to search for.
        session_id: The scratchpad session to search (defaults to "default").
        tags: Optional tags to filter long-term results (e.g., ["gaming"]).
        context: Optional context to filter long-term results (e.g., "gaming", "work").
        limit: Maximum number of long-term results to return (default 5).
    """
    output = []
    
    # 1. Search short-term memory (scratchpad)
    notes = _get_scratchpad(session_id)
    if notes:
        query_lower = query.lower()
        matching_notes = [n for n in notes if query_lower in n.lower()]
        
        output.append("=== SHORT-TERM MEMORY (SCRATCHPAD) MATCHES ===")
        if matching_notes:
            for idx, note in enumerate(matching_notes, 1):
                output.append(f"[*] {note}")
        else:
            output.append("(No direct keyword matches in scratchpad. Recent notes below:)")
            for idx, note in enumerate(notes[-3:], 1):
                output.append(f"[Recent] {note}")
        output.append("")

    # 2. Search long-term memory (vector DB)
    results = db.search_memory(query, tags=tags, context=context, limit=limit)
    if not results and not notes:
        return "No relevant memories found in short-term or long-term storage."
        
    output.append("=== LONG-TERM MEMORY MATCHES ===")
    if not results:
        output.append("No matches found in long-term DB.")
    else:
        for idx, mem in enumerate(results, 1):
            output.append(f"[{idx}] ID: {mem['id']}")
            output.append(f"    Tags: {mem['metadata']['tags']} | Context: {mem['metadata']['context']}")
            output.append(f"    Content: {mem['content']}")
            output.append("")
            
    return "\n".join(output)

@mcp.tool()
def update_memory(memory_id: str, content: str | None = None, tags: list[str] | None = None, context: str | None = None) -> str:
    """
    Update a specific existing memory.
    
    Use this when you need to CORRECT, REVISE, or SUPPLEMENT existing information.
    You MUST know the memory's UUID (run search_memory or export_memories first to get it).
    
    When to use:
    - Correcting factual errors (e.g., "sky is purple" instead of "sky is blue")
    - Updating outdated information
    - Changing tags or context
    - Adding more detail to existing content
    
    Args:
        memory_id: The UUID of the memory to update (get from search_memory).
        content: New content to replace the old (leave empty/null to keep existing).
        tags: New tags to replace old (leave empty/null to keep existing).
        context: New context to replace old (leave empty/null to keep existing).
    """
    try:
        db.update_memory(memory_id, content=content, tags=tags, context=context)
        return f"Memory {memory_id} updated successfully."
    except Exception as e:
        return f"Error updating memory: {str(e)}"

@mcp.tool()
def remove_memory(memory_id: str) -> str:
    """
    Permanently delete a single memory by its ID.
    
    Use this to REMOVE specific information that is incorrect, outdated, or unwanted.
    You MUST know the memory's UUID (run search_memory or export_memories first to get it).
    
    When to use:
    - Removing factually incorrect information
    - Deleting outdated or obsolete memories
    - Cleaning up test or unwanted data
    
    Args:
        memory_id: The UUID of the memory to delete (get from search_memory).
    """
    success = db.remove_memory(memory_id)
    if success:
        return f"Memory {memory_id} successfully deleted."
    return f"Memory {memory_id} not found."

@mcp.tool()
def clear_all_memory(confirmation: bool) -> str:
    """
    DANGER: Completely wipe the entire memory database.
    
    This action is IRREVERSIBLE. All memories (both short-term and long-term) will be permanently deleted.
    
    When to use:
    - Starting completely fresh with a clean database
    - After exporting and backing up important data
    - When you need to reset everything
    
    Args:
        confirmation: MUST be exactly True to execute. Any other value will be rejected.
    """
    return db.clear_all_memory(confirmation)

@mcp.tool()
def get_memory_stats() -> str:
    """
    Get a quick overview of the memory database.
    
    Use this to check how much data is stored without retrieving the full content.
    
    Returns:
        Total memory count, collection name, and storage path.
    """
    stats = db.get_memory_stats()
    return f"Total Memories: {stats['total_memories']}\nCollection: {stats['collection_name']}\nStorage Path: {stats['storage_path']}"

@mcp.tool()
def export_memories() -> str:
    """
    Export all memories to a Markdown-formatted string.
    
    Use this to:
    - Back up all stored data
    - Review everything in one place
    - Share memories with other systems
    
    Returns:
        All memories in Markdown format with ID, context, tags, and content.
    """
    return db.export_memories()

@mcp.tool()
def import_memories(markdown_content: str) -> str:
    """
    Import multiple memories from a Markdown-formatted string.
    
    Use this to:
    - Restore memories from a previous export
    - Bulk-import data from external sources
    - Migrate memories from another system
    
    The format should match the export format:
    ---
    ## Memory ID: <any-id>
    **Context**: <context>
    **Tags**: <tag1, tag2>
    **Content**:
    <the actual content>
    ---
    
    Args:
        markdown_content: The Markdown-formatted memory data to import.
    """
    imported_count = 0
    blocks = markdown_content.split("---")
    for block in blocks:
        if "**Content**:" not in block:
            continue
            
        context = "global"
        tags = []
        
        lines = block.strip().split("\n")
        content_lines = []
        is_content = False
        
        for line in lines:
            if line.startswith("**Context**:"):
                context = line.replace("**Context**:", "").strip()
                if context == "None":
                    context = "global"
            elif line.startswith("**Tags**:"):
                raw_tags = line.replace("**Tags**:", "").strip()
                if raw_tags and raw_tags != "None":
                    tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
            elif line.startswith("**Content**:"):
                is_content = True
            elif is_content:
                content_lines.append(line)
        
        content = "\n".join(content_lines).strip()
        if content:
            db.add_memory(content, tags=tags, context=context)
            imported_count += 1

    return f"Successfully imported {imported_count} memories."

def print_stats():
    """CLI entrypoint to print current memory stats."""
    db = VectorDB()
    stats = db.get_memory_stats()
    print(f"Total Memories: {stats['total_memories']}")
    print(f"Collection: {stats['collection_name']}")
    print(f"Storage Path: {stats['storage_path']}")

def main():
    """Main entrypoint for the memory-mcp server."""
    mcp.run()

if __name__ == "__main__":
    main()
