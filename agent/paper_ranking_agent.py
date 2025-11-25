"""
Specialist Agent for Paper Ranking
Uses LLM to intelligently rank papers based on relevance, quality, and impact
"""

import os
import logging
from typing import List, Dict, Tuple
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaperRankingAgent:
    """
    Specialist agent that ranks papers using LLM intelligence
    Called by the main research agent via A2A pattern
    """
    
    def __init__(self, api_key: str = None, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize ranking agent
        
        Args:
            api_key: Anthropic API key
            model: Claude model for ranking
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        
        # Use separate LLM instance for ranking
        self.llm = ChatAnthropic(
            model=model,
            temperature=0,  # Deterministic ranking
            max_tokens=2048,
            api_key=self.api_key
        )
        
        logger.info(f"✅ Paper Ranking Agent initialized (model={model})")
    
    async def rank_papers(
        self, 
        papers: List[Dict], 
        query: str,
        max_papers: int = 10,
        criteria: Dict = None
    ) -> List[Dict]:
        """
        Rank papers using LLM analysis
        
        Args:
            papers: List of paper dictionaries with title, abstract, metadata
            query: User's research query
            max_papers: Number of top papers to return
            criteria: Optional ranking criteria weights
                {
                    'relevance': 0.5,  # Semantic relevance
                    'methodology': 0.2,  # Research methodology quality
                    'recency': 0.15,  # Publication date
                    'impact': 0.15  # Citations/venue quality
                }
        
        Returns:
            List of papers sorted by relevance score
        """
        logger.info(f"🎯 Ranking {len(papers)} papers for query: '{query}'")
        
        if not papers:
            logger.warning("⚠️ No papers to rank")
            return []
        
        # Default criteria
        if criteria is None:
            criteria = {
                'relevance': 0.5,
                'methodology': 0.2,
                'recency': 0.15,
                'impact': 0.15
            }
        
        # Prepare paper abstracts for LLM
        paper_summaries = self._prepare_paper_summaries(papers)
        
        # Get LLM ranking
        ranking = await self._llm_rank(query, paper_summaries, criteria, max_papers)
        
        # Reorder papers based on ranking
        ranked_papers = self._apply_ranking(papers, ranking)
        
        logger.info(f"✅ Ranking complete: top {len(ranked_papers)} papers selected")
        
        return ranked_papers[:max_papers]
    
    def _prepare_paper_summaries(self, papers: List[Dict]) -> str:
        """
        Format papers for LLM analysis
        """
        summaries = []
        
        for i, paper in enumerate(papers, 1):
            title = paper.get('title', 'No title')
            abstract = paper.get('summary', paper.get('abstract', 'No abstract'))[:600]
            authors = paper.get('authors', [])
            year = paper.get('year', paper.get('published', 'Unknown'))
            citations = paper.get('citation_count', 'N/A')
            
            summary = f"""
Paper #{i}
Title: {title}
Authors: {', '.join(authors[:3]) if authors else 'Unknown'}
Year: {year}
Citations: {citations}
Abstract: {abstract}
"""
            summaries.append(summary)
        
        return "\n---\n".join(summaries)
    
    async def _llm_rank(
        self, 
        query: str, 
        paper_summaries: str, 
        criteria: Dict,
        max_papers: int
    ) -> List[int]:
        """
        Use LLM to rank papers
        """
        system_prompt = f"""You are an expert research paper evaluator and ranking specialist.

Your job is to analyze and rank research papers based on their relevance to a given query.

Ranking Criteria (weighted):
- Relevance ({criteria['relevance']*100}%): How well the paper addresses the research question
- Methodology ({criteria['methodology']*100}%): Quality and rigor of research methods
- Recency ({criteria['recency']*100}%): Publication date (prefer recent papers)
- Impact ({criteria['impact']*100}%): Citations, venue quality, author reputation

You must be critical and selective. Only highly relevant papers should rank at the top."""

        user_prompt = f"""Research Query: "{query}"

Please analyze these papers and rank them from MOST to LEAST relevant:

{paper_summaries}

Instructions:
1. Read each abstract carefully
2. Evaluate semantic relevance to the query
3. Consider methodology quality (experimental design, sample size, etc.)
4. Factor in recency and impact
5. Provide ranking as comma-separated numbers (most relevant first)

Return ONLY the paper numbers in ranked order (e.g., "3,7,1,5,2,9,4,8,6,10")
Then explain your top {min(3, max_papers)} choices briefly.

Format:
RANKING: [numbers]
EXPLANATION:
Paper #X: [brief reason]
Paper #Y: [brief reason]
Paper #Z: [brief reason]
"""
        
        logger.info("🔍 Sending papers to LLM for ranking...")
        
        response = await self.llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        # Parse response
        ranking = self._parse_ranking_response(response.content)
        
        logger.info(f"📊 LLM Ranking: {ranking[:max_papers]}")
        
        return ranking
    
    def _parse_ranking_response(self, response: str) -> List[int]:
        """
        Parse LLM response to extract ranking
        """
        try:
            # Find the RANKING: line
            lines = response.split('\n')
            ranking_line = None
            
            for line in lines:
                if line.strip().startswith('RANKING:'):
                    ranking_line = line.split('RANKING:')[1].strip()
                    break
            
            if not ranking_line:
                # Try to find comma-separated numbers in first line
                ranking_line = lines[0].strip()
            
            # Parse numbers
            ranking = [int(x.strip()) for x in ranking_line.split(',')]
            
            logger.info(f"✅ Parsed ranking: {ranking}")
            return ranking
            
        except Exception as e:
            logger.error(f"❌ Failed to parse ranking: {e}")
            logger.error(f"Response was: {response[:200]}")
            # Fallback: return original order
            return list(range(1, 100))
    
    def _apply_ranking(self, papers: List[Dict], ranking: List[int]) -> List[Dict]:
        """
        Reorder papers based on LLM ranking
        """
        ranked_papers = []
        
        for rank in ranking:
            if rank <= len(papers):
                paper = papers[rank - 1]  # Convert 1-indexed to 0-indexed
                paper['ranking_score'] = len(ranking) - ranking.index(rank)  # Higher is better
                ranked_papers.append(paper)
        
        return ranked_papers
    
    async def explain_ranking(
        self, 
        query: str, 
        top_papers: List[Dict]
    ) -> str:
        """
        Generate explanation for why papers were ranked this way
        """
        paper_titles = "\n".join([
            f"{i+1}. {p.get('title', 'Unknown')}"
            for i, p in enumerate(top_papers[:5])
        ])
        
        prompt = f"""Query: "{query}"

Top ranked papers:
{paper_titles}

Provide a brief explanation (2-3 sentences) of why these papers are most relevant."""

        response = await self.llm.ainvoke([
            HumanMessage(content=prompt)
        ])
        
        return response.content


# ============= A2A INTERFACE =============
async def call_ranking_agent(
    papers: List[Dict],
    query: str,
    max_papers: int = 10,
    api_key: str = None
) -> Tuple[List[Dict], str]:
    """
    A2A interface: Call ranking agent from main agent
    
    Args:
        papers: Papers to rank
        query: Research query
        max_papers: Number of papers to return
        api_key: Anthropic API key
    
    Returns:
        Tuple of (ranked_papers, explanation)
    """
    logger.info(f"🔗 A2A Call: Invoking Paper Ranking Agent")
    
    # Create specialist agent
    ranking_agent = PaperRankingAgent(api_key=api_key)
    
    # Rank papers
    ranked_papers = await ranking_agent.rank_papers(
        papers=papers,
        query=query,
        max_papers=max_papers
    )
    
    # Get explanation
    explanation = await ranking_agent.explain_ranking(query, ranked_papers)
    
    logger.info(f"✅ A2A Call Complete: Received {len(ranked_papers)} ranked papers")
    
    return ranked_papers, explanation
