import aiohttp
import xml.etree.ElementTree as ET
from typing import Dict, List, Any
from datetime import datetime


class ArxivTool:
    """Tool for searching arXiv papers"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
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
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status == 200:
                        xml_data = await response.text()
                        return self._parse_arxiv_response(xml_data)
                    else:
                        return {"error": f"HTTP {response.status}", "results": []}
        except Exception as e:
            return {"error": str(e), "results": []}
    
    def _parse_arxiv_response(self, xml_data: str) -> Dict[str, Any]:
        """Parse arXiv XML response"""
        root = ET.fromstring(xml_data)
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        
        papers = []
        for entry in root.findall('atom:entry', namespace):
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
        
        return {
            "source": "arXiv",
            "total_results": len(papers),
            "results": papers
        }
