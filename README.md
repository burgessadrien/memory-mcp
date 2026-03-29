# MEMORY MCP

Memory MCP is a small, self-contained Model Context Protocol (MCP) server for persistent AI agent memory. It uses a local vector database (ChromaDB) + offline/supervised embeddings (SentenceTransformers), enabling low-latency memory operations without external cloud dependencies.

## 🚀 What it supports

- Long-term semantic memory (`add_memory`, `search_memory`, `update_memory`, `remove_memory`)
- Short-term scratchpad memory per session (`add_to_scratchpad`, `read_scratchpad`, `clear_scratchpad`)
- Bulk + lifecycle tools (`export_memories`, `import_memories`, `clear_all_memory`, `get_memory_stats`)
- Local persistence via directory/mounted volume (works with Docker or native Python)

## 📦 Components

- `src/memory_mcp/server.py` - MCP tool gateway exposing REST-style calls to clients
- `src/memory_mcp/db.py` - vector storage logic (Chroma, SQLite gateway)
- `mcp_client.py` - example client for quickly testing call patterns
- `check_db.py`/`final_check.py` - sanity checks for DB state
- `tests/` - existing and future test coverage tasks

## 🛠️ Endpoint methods (MCP tools)

### Short-Term Scratchpad
- `add_to_scratchpad(note, session_id)
- `read_scratchpad(session_id)
- `clear_scratchpad(session_id)`

### Long-Term Memory
- `add_memory(content, tags, context)`
- `search_memory(query, session_id, tags, context, limit)`
- `update_memory(memory_id, content, tags, context)`
- `remove_memory(memory_id)`

### Administration
- `get_memory_stats()`
- `export_memories()`
- `import_memories(markdown_content)`
- `clear_all_memory(confirmation)`

## 🧩 Install

### Option 1: Docker (Recommended)

1. Build:
   ```bash
   docker build -t memory-mcp .
   ```

2. Run (persist data on host):
   ```bash
   docker run -it --rm -v memory_data:/data -p 8000:8000 memory-mcp
   ```

3. Configure your MCP client to call the server command as appropriate.

### Option 2: Native Python

1. Create and activate a virtual env:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -e .
   ```

2. Start server directly:
   ```bash
   python -m memory_mcp.server
   ```

> Tip: `MEMORY_MCP_STORAGE` can override the default data path from `./memory_data`.

## 🧪 Test

Run tests with:
```bash
python -m pytest -q
```

Validate basic memory API quickly:
```bash
python mcp_client.py # (if implemented as interactive example)
```

## 🗂️ Data layout

- `memory_data/` - persistent SQLite/Chroma state for native mode
- `memory_data/vector_db/` - vector DB data
- `memory_data/chroma.sqlite3` - metadata database

## 🧰 Usage samples

### Add memory
```python
client.add_memory('Your fact', tags=['fact'], context='user')
```

### Search memory
```python
client.search_memory('fact about sky', limit=5)
```

### Export & restore
```python
md = client.export_memories()
client.import_memories(md)
```

## ✅ Keeping this README up to date

- Always reflect actual available methods in `src/memory_mcp/server.py`
- Add new methods in Features + Usage sections
- Ensure install section includes the latest dependency/runtime directives from `pyproject.toml`

