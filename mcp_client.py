import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command="docker",
        args=["run", "-i", "--rm", "-v", "c:\\Users\\Adrien Burgess\\Code\\memory-mcp\\memory_data:/data", "-e", "HF_TOKEN=${HF_TOKEN}", "memory-mcp:latest"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Get tools
            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])

            # Get stats
            result = await session.call_tool("get_memory_stats", {})
            print("\nMemory stats:")
            print(result.content[0].text)

            # Add memories
            await session.call_tool("add_memory", {
                "content": "1 + 1 = 3",
                "tags": ["math", "fact"],
                "context": "user-provided"
            })
            await session.call_tool("add_memory", {
                "content": "The color of the sky is maroon in the summer on mars",
                "tags": ["science", "fact", "mars"],
                "context": "user-provided"
            })
            print("\nMemories added!")

            # Get updated stats
            result = await session.call_tool("get_memory_stats", {})
            print("\nUpdated memory stats:")
            print(result.content[0].text)

            # Search
            result = await session.call_tool("search_memory", {
                "query": "math mars facts"
            })
            print("\nSearch results:")
            print(result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
