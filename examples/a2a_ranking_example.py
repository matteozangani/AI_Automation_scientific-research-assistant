"""
Example: Agent-to-Agent Paper Ranking
"""

import asyncio
import os
from agent.rag_research_agent import RAGResearchAgent


async def example_a2a_ranking():
    """Test A2A ranking with specialist agent"""
    
    print("\n" + "="*80)
    print("EXAMPLE: Agent-to-Agent Paper Ranking")
    print("="*80 + "\n")
    
    # Create main research agent
    agent = RAGResearchAgent(max_papers=5)
    
    # Execute research (will use A2A ranking internally)
    result = await agent.execute(
        "What are the most effective approaches to reduce transformer model size "
        "while maintaining accuracy?"
    )
    
    print("\n📊 RESEARCH REPORT:")
    print("="*80)
    print(result['report'])
    print("\n" + "="*80)
    
    # Show ranking details
    if 'ranking_explanation' in result.get('search_results', {}):
        print("\n🎯 RANKING EXPLANATION:")
        print(result['search_results']['ranking_explanation'])


async def example_compare_rankings():
    """Compare with and without A2A ranking"""
    
    print("\n" + "="*80)
    print("COMPARISON: With vs Without A2A Ranking")
    print("="*80 + "\n")
    
    query = "Latest advances in quantum error correction"
    
    # With A2A ranking
    print("🤖 WITH A2A Ranking Specialist:")
    agent_a2a = RAGResearchAgent(max_papers=3)
    result_a2a = await agent_a2a.execute(query)
    
    print(f"Papers analyzed: {result_a2a['papers_analyzed']}")
    print("Top papers:")
    for i, paper in enumerate(result_a2a.get('papers_info', [])[:3], 1):
        print(f"{i}. {paper['title'][:70]}...")
    
    print("\n" + "-"*80 + "\n")


async def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set!")
        return
    
    await example_a2a_ranking()
    # await example_compare_rankings()


if __name__ == "__main__":
    asyncio.run(main())
