#!/usr/bin/env python3
"""
MCP Server for Scientific Research Assistant
Exposes academic research tools via Model Context Protocol
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import tools
from tools.arxiv_tool import ArxivTool
from tools.pubmed_tool import PubmedTool
from tools.semantic_scholar_tool import SemanticScholarTool
from tools.crossref_tool import CrossrefTool
from tools.ieee_tool import IEEETool
from tools.google_scholar_tool import GoogleScholarTool

# Import prompts
from prompts.research_prompts import RESEARCH_PROMPTS

# Constants
DEFAULT_MAX_RESULTS = 10
MAX_ALLOWED_RESULTS = 100
DEFAULT_TIMEOUT = 30.0

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
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": DEFAULT_MAX_RESULTS},
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
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": DEFAULT_MAX_RESULTS}
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
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": DEFAULT_MAX_RESULTS},
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
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": DEFAULT_MAX_RESULTS}
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
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": DEFAULT_MAX_RESULTS}
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
                    "max_results": {"type": "integer", "description": "Maximum number of results", "default": DEFAULT_MAX_RESULTS}
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


def validate_and_sanitize_inputs(arguments: dict) -> tuple[str, int]:
    """Validate and sanitize common input parameters"""
    query = arguments.get("query", "").strip()
    if not query:
        raise ValueError("Query cannot be empty")
    
    if len(query) > 500:
        logger.warning("Query too long, truncating to 500 characters")
        query = query[:500]
    
    max_results = arguments.get("max_results", DEFAULT_MAX_RESULTS)
    if not isinstance(max_results, int) or max_results <= 0 or max_results > MAX_ALLOWED_RESULTS:
        logger.warning(f"Invalid max_results {max_results}, setting to {DEFAULT_MAX_RESULTS}")
        max_results = DEFAULT_MAX_RESULTS
    
    return query, max_results


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution"""    
    if not arguments:
        return [types.TextContent(type="text", text="Error: Missing arguments")]
    
    logger.info(f"Executing tool: {name} with arguments: {arguments}")    
    try:
        # Validate common inputs
        query, max_results = validate_and_sanitize_inputs(arguments)
        
        if name == "search_arxiv":
            results = await arxiv.search(
                query=query,
                max_results=max_results,
                sort_by=arguments.get("sort_by", "relevance")
            )
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
        elif name == "search_pubmed":
            results = await pubmed.search(
                query=query,
                max_results=max_results
            )
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
        elif name == "search_semantic_scholar":
            results = await semantic_scholar.search(
                query=query,
                max_results=max_results,
                fields=arguments.get("fields")
            )
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
        elif name == "search_crossref":
            results = await crossref.search(
                query=query,
                max_results=max_results
            )
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
        elif name == "search_ieee":
            results = await ieee.search(
                query=query,
                max_results=max_results
            )
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
        elif name == "search_google_scholar":
            results = await google_scholar.search(
                query=query,
                max_results=max_results
            )
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
        elif name == "multi_source_search":
            if "sources" not in arguments or not arguments["sources"]:
                return [types.TextContent(type="text", text="Error: Sources list cannot be empty")]
            
            results = await perform_multi_source_search(
                query=query,
                sources=arguments["sources"],
                max_results=arguments.get("max_results_per_source", 5)
            )
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]
        
        else:
            raise ValueError(f"Unknown tool: {name}")    
    except ValueError as e:
        logger.error(f"Validation error in {name}: {str(e)}")
        return [types.TextContent(type="text", text=f"Invalid input: {str(e)}")]
    except asyncio.TimeoutError:
        logger.error(f"Timeout error in {name}")
        return [types.TextContent(type="text", text=f"Timeout error: Operation took too long")]
    except Exception as e:
        logger.error(f"Unexpected error in {name}: {str(e)}", exc_info=True)
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
    source_map = {
        "arxiv": arxiv.search,
        "pubmed": pubmed.search,
        "semantic_scholar": semantic_scholar.search,
        "crossref": crossref.search,
        "ieee": ieee.search,
        "google_scholar": google_scholar.search
    }
    
    # Filter valid sources
    valid_sources = [s for s in sources if s in source_map]
    invalid_sources = [s for s in sources if s not in source_map]
    
    if not valid_sources:
        return {"error": "No valid sources specified", "invalid_sources": invalid_sources}
    
    # Create tasks only for valid sources
    tasks = [source_map[source](query=query, max_results=max_results) for source in valid_sources]
    
    # Execute with timeout
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=DEFAULT_TIMEOUT
        )
    except asyncio.TimeoutError:
        logger.error(f"Multi-source search timeout after {DEFAULT_TIMEOUT} seconds")
        return {"error": f"Search timeout after {DEFAULT_TIMEOUT} seconds"}
    
    # Build output
    output = {}
    for i, source in enumerate(valid_sources):
        if isinstance(results[i], Exception):
            logger.error(f"Source {source} failed: {str(results[i])}")
            output[source] = {"error": str(results[i])}
        else:
            output[source] = results[i]
    
    # Add warning about invalid sources
    if invalid_sources:
        output["_warnings"] = f"Invalid sources skipped: {', '.join(invalid_sources)}"
        logger.warning(f"Invalid sources skipped: {invalid_sources}")
    
    return output


async def main():
    """Run the MCP server"""
    logger.info("Starting MCP Scientific Research Assistant Server...")
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
