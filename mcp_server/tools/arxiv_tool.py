import aiohttp
import asyncio
import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ArxivTool:
    """Tool for searching arXiv papers"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    DEFAULT_TIMEOUT = 30
    MAX_RESULTS_LIMIT = 100
    MAX_XML_SIZE = 10_000_000  # 10MB
    
    async def search(self, query: str, max_results: int = 10, sort_by: str = "relevance") -> Dict[str, Any]:
        """
        Search arXiv for papers
        
        Args:
            query: Search query
            max_results: Maximum number of results
            sort_by: Sort order (relevance, lastUpdatedDate, submittedDate)
        
        Returns:
            Dict containing search results
        """
        # Validate inputs
        if not query or not query.strip():
            return {"error": "Query cannot be empty", "results": []}
        
        query = query.strip()
        
        if max_results <= 0 or max_results > self.MAX_RESULTS_LIMIT:
            logger.warning(f"Invalid max_results {max_results}, setting to 10")
            max_results = 10
        
        if sort_by not in ["relevance", "lastUpdatedDate", "submittedDate"]:
            logger.warning(f"Invalid sort_by '{sort_by}', using 'relevance'")
            sort_by = "relevance"
        
        logger.info(f"Searching arXiv for: {query}, max_results: {max_results}, sort_by: {sort_by}")
        
        sort_map = {
            "relevance": "relevance",
            "lastUpdatedDate": "lastUpdatedDate",
            "submittedDate": "submittedDate"
        }
        
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": sort_map.get(sort_by, "relevance"),
            "sortOrder": "descending"
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.DEFAULT_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status == 200:
                        xml_data = await response.text()
                        return self._parse_arxiv_response(xml_data)
                    else:
                        logger.error(f"arXiv API returned HTTP {response.status}")
                        return {"error": f"HTTP {response.status}", "results": []}
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {str(e)}")
            return {"error": f"Network error: {str(e)}", "results": []}
        except asyncio.TimeoutError:
            logger.error(f"Request timeout after {self.DEFAULT_TIMEOUT} seconds")
            return {"error": "Request timeout", "results": []}
        except Exception as e:
            logger.error(f"Unexpected error in arXiv search: {str(e)}", exc_info=True)
            return {"error": str(e), "results": []}
    
    def _parse_arxiv_response(self, xml_data: str) -> Dict[str, Any]:
        """Parse arXiv XML response"""
        try:
            # Check XML size to prevent XML bombs
            if len(xml_data) > self.MAX_XML_SIZE:
                logger.error(f"XML response too large: {len(xml_data)} bytes")
                return {"error": "Response too large", "results": []}
            
            root = ET.fromstring(xml_data)
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
            return {"error": f"XML parsing error: {str(e)}", "results": []}
        
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        
        papers = []
        for entry in root.findall('atom:entry', namespace):
            try:
                paper = {
                    "title": entry.find('atom:title', namespace).text.strip() if entry.find('atom:title', namespace) is not None else "",
                    "authors": [author.find('atom:name', namespace).text for author in entry.findall('atom:author', namespace)],
                    "summary": entry.find('atom:summary', namespace).text.strip() if entry.find('atom:summary', namespace) is not None else "",
                    "published": entry.find('atom:published', namespace).text if entry.find('atom:published', namespace) is not None else "",
                    "updated": entry.find('atom:updated', namespace).text if entry.find('atom:updated', namespace) is not None else "",
                    "pdf_url": next((link.get('href') for link in entry.findall('atom:link', namespace) if link.get('title') == 'pdf'), None),
                    "arxiv_url": entry.find('atom:id', namespace).text if entry.find('atom:id', namespace) is not None else "",
                    "categories": [cat.get('term') for cat in entry.findall('atom:category', namespace)]
                }
                papers.append(paper)
            except Exception as e:
                logger.warning(f"Failed to parse arXiv entry: {str(e)}")
                continue
        
        logger.info(f"Successfully parsed {len(papers)} arXiv papers")
        
        return {
            "source": "arXiv",
            "total_results": len(papers),
            "results": papers
        }