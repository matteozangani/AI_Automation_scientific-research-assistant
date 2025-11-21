#!/usr/bin/env python3
"""
Research Agent Orchestrator
Coordinates research tasks using MCP tools
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


dataclass
class ResearchQuery:
    """Represents a research query"""
    query: str
    sources: List[str]
    max_results: int = 10
    filters: Optional[Dict[str, Any]] = field(default_factory=lambda: None)


class ResearchOrchestrator:
    """
    Orchestrates research tasks across multiple academic sources
    Uses MCP server tools to perform searches
    """
    
    AVAILABLE_SOURCES = [
        "arxiv",
        "pubmed", 
        "semantic_scholar",
        "crossref",
        "ieee",
        "google_scholar"
    ]
    
    def __init__(self, mcp_client=None):
        """
        Initialize the orchestrator
        
        Args:
            mcp_client: MCP client instance (if None, will use direct tool calls)
        """
        self.mcp_client = mcp_client
        self._tool_map = None  # Lazy initialization
        logger.info("Research Orchestrator initialized")
    
    def _get_tool_map(self):
        """Lazy initialization of tools to avoid recreating instances"""
        if self._tool_map is None:
            from mcp_server.tools.arxiv_tool import ArxivTool
            from mcp_server.tools.pubmed_tool import PubmedTool
            from mcp_server.tools.semantic_scholar_tool import SemanticScholarTool
            from mcp_server.tools.crossref_tool import CrossrefTool
            from mcp_server.tools.ieee_tool import IEEETool
            from mcp_server.tools.google_scholar_tool import GoogleScholarTool
            
            self._tool_map = {
                "arxiv": ArxivTool(),
                "pubmed": PubmedTool(),
                "semantic_scholar": SemanticScholarTool(),
                "crossref": CrossrefTool(),
                "ieee": IEEETool(),
                "google_scholar": GoogleScholarTool()
            }
        return self._tool_map
    
    async def search(self, query: ResearchQuery) -> Dict[str, Any]:
        """
        Execute a research query across specified sources
        
        Args:
            query: ResearchQuery object with search parameters
            
        Returns:
            Dict containing aggregated results from all sources
        """
        # Validate query input
        if not query.query or not query.query.strip():
            logger.error("Empty query provided")
            return {"error": "Query cannot be empty", "results": {}}
        
        if len(query.query) > 500:
            logger.warning("Query too long, truncating to 500 characters")
            query.query = query.query[:500]
        
        if query.max_results <= 0 or query.max_results > 100:
            logger.warning(f"Invalid max_results {query.max_results}, setting to 10")
            query.max_results = 10
        
        logger.info(f"Starting search for: '{query.query}'")
        logger.info(f"Sources: {query.sources}")
        logger.info(f"Max results per source: {query.max_results}")
        
        # Validate sources without mutating input
        invalid_sources = [s for s in query.sources if s not in self.AVAILABLE_SOURCES]
        valid_sources = [s for s in query.sources if s in self.AVAILABLE_SOURCES]
        
        if invalid_sources:
            logger.warning(f"Invalid sources will be skipped: {invalid_sources}")
        
        if not valid_sources:
            return {"error": "No valid sources specified", "results": {}}
        
        # Execute searches
        if self.mcp_client:
            results = await self._search_via_mcp(query, valid_sources)
        else:
            results = await self._search_direct(query, valid_sources)
        
        logger.info(f"Search completed. Found results from {len(results)} sources")
        
        return {
            "query": query.query,
            "sources_searched": valid_sources,
            "total_sources": len(results),
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _search_via_mcp(self, query: ResearchQuery, valid_sources: List[str]) -> Dict[str, Any]:
        """Search using MCP client"""
        logger.info("Executing search via MCP server...")
        
        # This will be implemented when MCP client is connected
        # For now, use direct search
        return await self._search_direct(query, valid_sources)
    
    async def _search_direct(self, query: ResearchQuery, valid_sources: List[str]) -> Dict[str, Any]:
        """Search using direct tool imports"""
        tool_map = self._get_tool_map()
        
        tasks = []
        source_names = []
        
        for source in valid_sources:
            if source in tool_map:
                logger.info(f"  → Querying {source}...")
                tool = tool_map[source]
                task = tool.search(query.query, max_results=query.max_results)
                tasks.append(task)
                source_names.append(source)
        
        # Execute all searches in parallel with timeout
        try:
            results_list = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=30.0  # 30 seconds timeout
            )
        except asyncio.TimeoutError:
            logger.error("Search timeout after 30 seconds")
            return {"error": "Search timeout after 30 seconds", "results": {}}
        
        # Aggregate results
        results = {}
        for source, result in zip(source_names, results_list):
            if isinstance(result, Exception):
                logger.error(f"  ✗ {source} failed: {str(result)}")
                results[source] = {"error": str(result), "results": []}
            else:
                count = result.get("total_results", 0)
                logger.info(f"  ✓ {source}: {count} results")
                results[source] = result
        
        return results
    
    async def summarize_paper(self, paper_identifier: str, source: str = "auto") -> Dict[str, Any]:
        """
        Get detailed information and summary for a specific paper
        
        Args:
            paper_identifier: Paper ID, DOI, or title
            source: Source to search (or "auto" to search all)
            
        Returns:
            Dict with paper details
        """
        if not paper_identifier or not paper_identifier.strip():
            logger.error("Empty paper identifier provided")
            return {"error": "Paper identifier cannot be empty", "paper": None}
        
        logger.info(f"Summarizing paper: {paper_identifier}")
        
        if source == "auto":
            # Search across all sources
            query = ResearchQuery(
                query=paper_identifier,
                sources=self.AVAILABLE_SOURCES,
                max_results=1
            )
            results = await self.search(query)
            
            # Return first match
            for src, data in results["results"].items():
                if data.get("results"):
                    return {
                        "source": src,
                        "paper": data["results"][0]
                    }
            
            return {"error": "Paper not found", "paper": None}
        else:
            query = ResearchQuery(
                query=paper_identifier,
                sources=[source],
                max_results=1
            )
            results = await self.search(query)
            
            if results["results"].get(source, {}).get("results"):
                return {
                    "source": source,
                    "paper": results["results"][source]["results"][0]
                }
            
            return {"error": "Paper not found", "paper": None}
    
    async def find_related_papers(self, paper_title: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Find papers related to a given paper
        
        Args:
            paper_title: Title of the reference paper
            max_results: Maximum number of related papers
            
        Returns:
            Dict with related papers
        """
        if not paper_title or not paper_title.strip():
            logger.error("Empty paper title provided")
            return {"error": "Paper title cannot be empty", "results": {}}
        
        logger.info(f"Finding papers related to: {paper_title}")
        
        # Use Semantic Scholar for related papers (has best citation data)
        query = ResearchQuery(
            query=paper_title,
            sources=["semantic_scholar", "crossref"],
            max_results=max_results
        )
        
        return await self.search(query)
    
    async def compare_papers(self, paper_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple papers
        
        Args:
            paper_ids: List of paper identifiers
            
        Returns:
            Dict with comparison data
        """
        if not paper_ids:
            logger.error("Empty paper_ids list provided")
            return {"error": "Paper IDs list cannot be empty", "papers": [], "comparison": {}}
        
        logger.info(f"Comparing {len(paper_ids)} papers")
        
        papers = []
        for paper_id in paper_ids:
            result = await self.summarize_paper(paper_id)
            if result.get("paper"):
                papers.append(result["paper"])
        
        return {
            "total_papers": len(papers),
            "papers": papers,
            "comparison": self._generate_comparison(papers)
        }
    
    def _generate_comparison(self, papers: List[Dict]) -> Dict[str, Any]:
        """Generate comparison metrics for papers"""
        if not papers:
            return {}
        
        comparison = {
            "citation_stats": {},
            "year_range": {},
            "author_overlap": {}
        }
        
        # Citation statistics
        citations = [p.get("citation_count", 0) or p.get("citations", 0) for p in papers]
        if citations and len(citations) > 0:
            comparison["citation_stats"] = {
                "min": min(citations),
                "max": max(citations),
                "avg": sum(citations) / len(citations)
            }
        
        # Year range
        years = [int(p.get("year", 0)) for p in papers if p.get("year")]
        if years:
            comparison["year_range"] = {
                "earliest": min(years),
                "latest": max(years),
                "span": max(years) - min(years)
            }
        
        return comparison


async def main():
    """Example usage"""
    orchestrator = ResearchOrchestrator()
    
    # Example 1: Multi-source search
    query = ResearchQuery(
        query="machine learning in genomics",
        sources=["arxiv", "pubmed", "semantic_scholar"],
        max_results=5
    )
    
    results = await orchestrator.search(query)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
