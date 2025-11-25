"""
Unit tests for Paper Ranking Agent (A2A)
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from agent.paper_ranking_agent import PaperRankingAgent, call_ranking_agent


# ============= FIXTURES =============
@pytest.fixture
def sample_papers():
    """Sample papers for testing"""
    return [
        {
            'title': 'Attention Is All You Need',
            'summary': 'We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.',
            'authors': ['Vaswani', 'Shazeer', 'Parmar'],
            'year': '2017',
            'citation_count': 50000,
            'arxiv_id': '1706.03762'
        },
        {
            'title': 'BERT: Pre-training of Deep Bidirectional Transformers',
            'summary': 'We introduce BERT, which stands for Bidirectional Encoder Representations from Transformers.',
            'authors': ['Devlin', 'Chang', 'Lee'],
            'year': '2018',
            'citation_count': 40000,
            'arxiv_id': '1810.04805'
        },
        {
            'title': 'Improving Language Understanding by Generative Pre-Training',
            'summary': 'We demonstrate that large gains on these tasks can be realized by generative pre-training.',
            'authors': ['Radford', 'Narasimhan'],
            'year': '2018',
            'citation_count': 10000,
            'arxiv_id': '1801.06146'
        },
        {
            'title': 'Irrelevant Paper About Cooking',
            'summary': 'How to cook pasta perfectly every time using machine learning.',
            'authors': ['Chef', 'Gordon'],
            'year': '2023',
            'citation_count': 5,
            'arxiv_id': '2023.12345'
        }
    ]


@pytest.fixture
def mock_llm_response():
    """Mock LLM ranking response"""
    class MockResponse:
        content = """RANKING: 1,2,3,4

EXPLANATION:
Paper #1: Foundational work on transformer architecture, highly relevant
Paper #2: Important extension of transformers to language understanding
Paper #3: Pioneering work on generative pre-training"""
    
    return MockResponse()


# ============= TESTS =============
class TestPaperRankingAgent:
    """Test Paper Ranking Agent"""
    
    @pytest.mark.skipif(not os.getenv('ANTHROPIC_API_KEY'), reason="No API key")
    def test_initialization(self):
        """Test agent initialization"""
        agent = PaperRankingAgent()
        assert agent is not None
        assert agent.llm is not None
    
    def test_initialization_without_api_key(self):
        """Test initialization fails without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY required"):
                PaperRankingAgent()
    
    def test_prepare_paper_summaries(self, sample_papers):
        """Test paper summary preparation"""
        agent = PaperRankingAgent(api_key="test-key")
        
        summaries = agent._prepare_paper_summaries(sample_papers)
        
        assert "Paper #1" in summaries
        assert "Attention Is All You Need" in summaries
        assert "Vaswani" in summaries
        assert "2017" in summaries
        assert "50000" in summaries
    
    def test_parse_ranking_response(self):
        """Test parsing LLM ranking response"""
        agent = PaperRankingAgent(api_key="test-key")
        
        response = """RANKING: 3,1,4,2

EXPLANATION:
Paper #3 is most relevant because..."""
        
        ranking = agent._parse_ranking_response(response)
        
        assert ranking == [3, 1, 4, 2]
    
    def test_parse_ranking_response_fallback(self):
        """Test parsing fallback when format is unexpected"""
        agent = PaperRankingAgent(api_key="test-key")
        
        response = "3,1,4,2"  # No RANKING: prefix
        
        ranking = agent._parse_ranking_response(response)
        
        assert ranking == [3, 1, 4, 2]
    
    def test_apply_ranking(self, sample_papers):
        """Test applying ranking to papers"""
        agent = PaperRankingAgent(api_key="test-key")
        
        ranking = [2, 1, 3, 4]
        ranked_papers = agent._apply_ranking(sample_papers, ranking)
        
        assert len(ranked_papers) == 4
        assert ranked_papers[0]['title'] == 'BERT: Pre-training of Deep Bidirectional Transformers'
        assert ranked_papers[1]['title'] == 'Attention Is All You Need'
        assert 'ranking_score' in ranked_papers[0]
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv('ANTHROPIC_API_KEY'), reason="No API key")
    async def test_rank_papers_integration(self, sample_papers):
        """Integration test: rank papers with real LLM"""
        agent = PaperRankingAgent()
        
        query = "transformer architectures for natural language processing"
        
        ranked_papers = await agent.rank_papers(
            papers=sample_papers,
            query=query,
            max_papers=3
        )
        
        assert len(ranked_papers) <= 3
        assert all('ranking_score' in p for p in ranked_papers)
        
        # Irrelevant paper should be ranked lower
        titles = [p['title'] for p in ranked_papers]
        assert 'Irrelevant Paper About Cooking' not in titles[:2]
    
    @pytest.mark.asyncio
    async def test_rank_papers_with_mock(self, sample_papers, mock_llm_response):
        """Test rank_papers with mocked LLM"""
        with patch('agent.paper_ranking_agent.ChatAnthropic') as mock_claude:
            mock_instance = Mock()
            mock_instance.ainvoke = AsyncMock(return_value=mock_llm_response)
            mock_claude.return_value = mock_instance
            
            agent = PaperRankingAgent(api_key="test-key")
            agent.llm = mock_instance
            
            query = "transformer architectures"
            ranked_papers = await agent.rank_papers(
                papers=sample_papers,
                query=query,
                max_papers=3
            )
            
            assert len(ranked_papers) == 3
            assert ranked_papers[0]['title'] == 'Attention Is All You Need'
    
    @pytest.mark.asyncio
    async def test_explain_ranking(self, sample_papers):
        """Test ranking explanation generation"""
        with patch('agent.paper_ranking_agent.ChatAnthropic') as mock_claude:
            mock_response = Mock()
            mock_response.content = "These papers are relevant because they cover transformer architectures."
            
            mock_instance = Mock()
            mock_instance.ainvoke = AsyncMock(return_value=mock_response)
            mock_claude.return_value = mock_instance
            
            agent = PaperRankingAgent(api_key="test-key")
            agent.llm = mock_instance
            
            explanation = await agent.explain_ranking(
                query="transformers",
                top_papers=sample_papers[:3]
            )
            
            assert "transformer" in explanation.lower()
            assert len(explanation) > 10
    
    def test_empty_papers_list(self):
        """Test handling empty papers list"""
        agent = PaperRankingAgent(api_key="test-key")
        
        result = asyncio.run(agent.rank_papers(
            papers=[],
            query="test query",
            max_papers=10
        ))
        
        assert result == []


class TestA2AInterface:
    """Test Agent-to-Agent interface"""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv('ANTHROPIC_API_KEY'), reason="No API key")
    async def test_call_ranking_agent_integration(self, sample_papers):
        """Integration test for A2A call"""
        query = "transformer architectures"
        
        ranked_papers, explanation = await call_ranking_agent(
            papers=sample_papers,
            query=query,
            max_papers=3
        )
        
        assert len(ranked_papers) <= 3
        assert isinstance(explanation, str)
        assert len(explanation) > 0
    
    @pytest.mark.asyncio
    async def test_call_ranking_agent_with_mock(self, sample_papers, mock_llm_response):
        """Test A2A call with mocked agent"""
        with patch('agent.paper_ranking_agent.PaperRankingAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent.rank_papers = AsyncMock(return_value=sample_papers[:3])
            mock_agent.explain_ranking = AsyncMock(return_value="Test explanation")
            mock_agent_class.return_value = mock_agent
            
            ranked_papers, explanation = await call_ranking_agent(
                papers=sample_papers,
                query="test",
                max_papers=3,
                api_key="test-key"
            )
            
            assert len(ranked_papers) == 3
            assert explanation == "Test explanation"
            mock_agent.rank_papers.assert_called_once()
            mock_agent.explain_ranking.assert_called_once()


class TestRankingCriteria:
    """Test different ranking criteria"""
    
    @pytest.mark.asyncio
    async def test_custom_criteria(self, sample_papers):
        """Test ranking with custom criteria weights"""
        with patch('agent.paper_ranking_agent.ChatAnthropic') as mock_claude:
            mock_response = Mock()
            mock_response.content = "RANKING: 1,2,3,4\n\nEXPLANATION: Test"
            
            mock_instance = Mock()
            mock_instance.ainvoke = AsyncMock(return_value=mock_response)
            mock_claude.return_value = mock_instance
            
            agent = PaperRankingAgent(api_key="test-key")
            agent.llm = mock_instance
            
            custom_criteria = {
                'relevance': 0.3,
                'methodology': 0.3,
                'recency': 0.2,
                'impact': 0.2
            }
            
            ranked_papers = await agent.rank_papers(
                papers=sample_papers,
                query="test",
                max_papers=3,
                criteria=custom_criteria
            )
            
            assert len(ranked_papers) <= 3


# ============= PERFORMANCE TESTS =============
class TestPerformance:
    """Test performance characteristics"""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv('ANTHROPIC_API_KEY'), reason="No API key")
    async def test_ranking_speed(self, sample_papers):
        """Test ranking completes within reasonable time"""
        import time
        
        agent = PaperRankingAgent()
        
        start = time.time()
        
        await agent.rank_papers(
            papers=sample_papers,
            query="transformer architectures",
            max_papers=3
        )
        
        elapsed = time.time() - start
        
        # Should complete in under 10 seconds
        assert elapsed < 10.0
    
    @pytest.mark.asyncio
    async def test_large_paper_list(self):
        """Test handling large number of papers"""
        # Create 50 papers
        large_paper_list = [
            {
                'title': f'Paper {i}',
                'summary': f'This is paper number {i} about transformers.',
                'authors': [f'Author{i}'],
                'year': '2023',
                'citation_count': i * 10
            }
            for i in range(50)
        ]
        
        with patch('agent.paper_ranking_agent.ChatAnthropic') as mock_claude:
            mock_response = Mock()
            # Generate ranking for all 50
            ranking_str = ','.join([str(i) for i in range(1, 51)])
            mock_response.content = f"RANKING: {ranking_str}\n\nEXPLANATION: Test"
            
            mock_instance = Mock()
            mock_instance.ainvoke = AsyncMock(return_value=mock_response)
            mock_claude.return_value = mock_instance
            
            agent = PaperRankingAgent(api_key="test-key")
            agent.llm = mock_instance
            
            ranked_papers = await agent.rank_papers(
                papers=large_paper_list,
                query="transformers",
                max_papers=10
            )
            
            # Should return exactly 10
            assert len(ranked_papers) == 10


# ============= RUN TESTS =============
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
