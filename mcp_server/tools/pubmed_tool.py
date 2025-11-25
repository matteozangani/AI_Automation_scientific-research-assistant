import aiohttp
import asyncio
import logging
from typing import Dict, List, Any
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class PubmedTool:
    """Tool for searching PubMed database"""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    DEFAULT_TIMEOUT = 30
    MAX_RESULTS_LIMIT = 100
    MAX_XML_SIZE = 10_000_000  # 10MB
    
    async def search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search PubMed for papers
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
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
        
        logger.info(f"Searching PubMed for: {query}, max_results: {max_results}")
        
        try:
            # Step 1: Search for PMIDs
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json"
            }
            
            timeout = aiohttp.ClientTimeout(total=self.DEFAULT_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Get PMIDs
                async with session.get(f"{self.BASE_URL}/esearch.fcgi", params=search_params) as response:
                    if response.status != 200:
                        logger.error(f"PubMed search API returned HTTP {response.status}")
                        return {"error": f"HTTP {response.status}", "results": []}
                    
                    data = await response.json()
                    pmids = data.get("esearchresult", {}).get("idlist", [])
                    
                    if not pmids:
                        logger.info("No results found in PubMed")
                        return {"source": "PubMed", "total_results": 0, "results": []}
                    
                    logger.info(f"Found {len(pmids)} PMIDs")
                    
                    # Step 2: Fetch details for PMIDs
                    fetch_params = {
                        "db": "pubmed",
                        "id": ",".join(pmids),
                        "retmode": "xml"
                    }
                    
                    async with session.get(f"{self.BASE_URL}/efetch.fcgi", params=fetch_params) as fetch_response:
                        if fetch_response.status != 200:
                            logger.error(f"PubMed fetch API returned HTTP {fetch_response.status}")
                            return {"error": f"HTTP {fetch_response.status}", "results": []}
                        
                        xml_data = await fetch_response.text()
                        return self._parse_pubmed_response(xml_data)
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {str(e)}")
            return {"error": f"Network error: {str(e)}", "results": []}
        except asyncio.TimeoutError:
            logger.error(f"Request timeout after {self.DEFAULT_TIMEOUT} seconds")
            return {"error": "Request timeout", "results": []}
        except Exception as e:
            logger.error(f"Unexpected error in PubMed search: {str(e)}", exc_info=True)
            return {"error": str(e), "results": []}
    
    def _parse_pubmed_response(self, xml_data: str) -> Dict[str, Any]:
        """Parse PubMed XML response"""
        try:
            # Check XML size to prevent XML bombs
            if len(xml_data) > self.MAX_XML_SIZE:
                logger.error(f"XML response too large: {len(xml_data)} bytes")
                return {"error": "Response too large", "results": []}
            
            root = ET.fromstring(xml_data)
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
            return {"error": f"XML parsing error: {str(e)}", "results": []}
        
        papers = []
        for article in root.findall('.//PubmedArticle'):
            try:
                medline = article.find('.//MedlineCitation')
                pmid = medline.find('.//PMID').text if medline.find('.//PMID') is not None else ""
                
                article_data = medline.find('.//Article')
                title = article_data.find('.//ArticleTitle').text if article_data.find('.//ArticleTitle') is not None else ""
                
                abstract_texts = article_data.findall('.//AbstractText')
                abstract = " ".join([a.text for a in abstract_texts if a.text]) if abstract_texts else ""
                
                authors = []
                for author in article_data.findall('.//Author'):
                    last_name = author.find('.//LastName')
                    first_name = author.find('.//ForeName')
                    if last_name is not None and first_name is not None:
                        authors.append(f"{first_name.text} {last_name.text}")
                
                journal = article_data.find('.//Journal/Title')
                journal_name = journal.text if journal is not None else ""
                
                pub_date = article_data.find('.//PubDate')
                year = pub_date.find('.//Year').text if pub_date is not None and pub_date.find('.//Year') is not None else ""
                
                paper = {
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "journal": journal_name,
                    "year": year,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                }
                papers.append(paper)
            except Exception as e:
                logger.warning(f"Failed to parse PubMed article: {str(e)}")
                continue
        
        logger.info(f"Successfully parsed {len(papers)} PubMed papers")
        
        return {
            "source": "PubMed",
            "total_results": len(papers),
            "results": papers
        }
