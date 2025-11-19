#!/usr/bin/env python3
"""
MCP Server for Scientific Research Assistant
Exposes academic research tools via Model Context Protocol
"""
import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Import tools
from tools.arxiv_tool import ArxivTool
from tools.pubmed_tool import PubmedTool
from tools.semantic_scholar_tool import SemanticScholarTool
from tools.crossref_tool import CrossrefTool
from tools.ieee_tool import IEEETool
from tools.google_scholar_tool import GoogleScholarTool

# Import prompts
from prompts.research_prompts import RESEARCH_PROMPTS

# Initialize server
server = Server("scientific-research-assistant")

# Initialize tools
arxiv = ArxivTool()
pubmed = PubmedTool()
semantic_scholar = SemanticScholarTool()
crossref = CrossrefTool()
ieee = IEEETool()
google_scholar = GoogleScholarTool()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List all available research tools"""
    return [
        types.Tool(
            name="search_arxiv",
            description="Search arXiv for academic papers in physics, mathematics, computer science, and related fields",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": 10},
                    "sort_by": {"type": "string", "description": "Sort by: relevance, lastUpdatedDate, submittedDate", "default": "relevance"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="search_pubmed",
            description="Search PubMed for biomedical and life sciences literature",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": 10}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="search_semantic_scholar",
            description="Search Semantic Scholar for academic papers across all fields with citation data",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": 10},
                    "fields": {"type": "string", "description": "Comma-separated fields to include"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="search_crossref",
            description="Search CrossRef for scholarly works with DOI information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": 10}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="search_ieee",
            description="Search IEEE Xplore for technical literature in engineering and technology",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": 10}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="search_google_scholar",
            description="Search Google Scholar for academic papers across all disciplines",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": 10}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="multi_source_search",
            description="Search across multiple academic sources simultaneously",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "sources": {"type": "array", "items": {"type": "string"}, "description": "List of sources to search"},
                    "max_results_per_source": {"type": "integer", "description": "Max results per source", "default": 5}
                },
                "required": ["query", "sources"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution"""
    
    if not arguments:
        raise ValueError("Missing arguments")
    
    try:
        if name == "search_arxiv":
            results = await arxiv.search(
                query=arguments["query"],
                max_results=arguments.get("max_results", 10),
                sort_by=arguments.get("sort_by", "relevance")
            )
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
        elif name == "search_pubmed":
            results = await pubmed.search(
                query=arguments["query"],
                max_results=arguments.get("max_results", 10)
            )
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
        elif name == "search_semantic_scholar":
            results = await semantic_scholar.search(
                query=arguments["query"],
                max_results=arguments.get("max_results", 10),
                fields=arguments.get("fields")
            )
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
        elif name == "search_crossref":
            results = await crossref.search(
                query=arguments["query"],
                max_results=arguments.get("max_results", 10)
            )
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
        elif name == "search_ieee":
            results = await ieee.search(
                query=arguments["query"],
                max_results=arguments.get("max_results", 10)
            )
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
        elif name == "search_google_scholar":
            results = await google_scholar.search(
                query=arguments["query"],
                max_results=arguments.get("max_results", 10)
            )
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
        elif name == "multi_source_search":
            results = await perform_multi_source_search(
                query=arguments["query"],
                sources=arguments["sources"],
                max_results=arguments.get("max_results_per_source", 5)
            )
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """List available research prompts"""
    return [
        types.Prompt(
            name=prompt_name,
            description=prompt_data["description"],
            arguments=[
                types.PromptArgument(
                    name=arg["name"],
                    description=arg["description"],
                    required=arg.get("required", False)
                )
                for arg in prompt_data.get("arguments", [])
            ]
        )
        for prompt_name, prompt_data in RESEARCH_PROMPTS.items()
    ]


@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """Get a specific research prompt"""
    
    if name not in RESEARCH_PROMPTS:
        raise ValueError(f"Unknown prompt: {name}")
    
    prompt_data = RESEARCH_PROMPTS[name]
    template = prompt_data["template"]
    
    # Fill in arguments
    if arguments:
        for key, value in arguments.items():
            template = template.replace(f"{{{key}}}", value)
    
    return types.GetPromptResult(
        description=prompt_data["description"],
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(type="text", text=template)
            )
        ]
    )


async def perform_multi_source_search(query: str, sources: List[str], max_results: int) -> Dict[str, Any]:
    """Perform parallel search across multiple sources"""
    tasks = []
    
    source_map = {
        "arxiv": arxiv.search,
        "pubmed": pubmed.search,
        "semantic_scholar": semantic_scholar.search,
        "crossref": crossref.search,
        "ieee": ieee.search,
        "google_scholar": google_scholar.search
    }
    
    for source in sources:
        if source in source_map:
            tasks.append(source_map[source](query=query, max_results=max_results))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    output = {}
    for i, source in enumerate(sources):
        if source in source_map:
            if isinstance(results[i], Exception):
                output[source] = {"error": str(results[i])}
            else:
                output[source] = results[i]
    
    return output


async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="scientific-research-assistant",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
