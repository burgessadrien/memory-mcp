# Use official Python full image for better library support
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Configure paths for permanent storage. 
# Map a volume to /data when running this container.
ENV MEMORY_MCP_STORAGE=/data/vector_db
ENV HF_HOME=/models

# Create the data mount directories
RUN mkdir -p /data/vector_db /models

# Set work directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/

# Upgrade build tools and install the project
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# Pre-download the embedding model to be ready on first start
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# MCP servers communicate via stdio by default. 
ENTRYPOINT ["memory-mcp"]
