"""
Examples: RAG-based Deep Research with Full PDF Analysis
"""

import asyncio
import os
from agent.rag_research_agent import RAGResearchAgent


async def example_1_deep_research():
    """Example 1: Deep analysis with 10 papers"""
    
    print("\n" + "="*80)
    print("EXAMPLE 1: Deep Research with 10 Papers")
    print("="*80 + "\n")
    
    agent = RAGResearchAgent(max_papers=10)
    
    result = await agent.execute(
        query="What are the latest breakthroughs in transformer attention mechanisms?"
    )
    
    print("\n📊 RESEARCH REPORT:")
    print("="*80)
    print(result['report'])
    print("\n" + "="*80)
    print(f"\n📈 Papers Analyzed: {result['papers_analyzed']}")
    print(f"📦 Chunks Processed: {result['chunks_processed']}")
    

async def example_2_medical_research():
    """Example 2: Medical research with PubMed"""
    
    print("\n" + "="*80)
    print("EXAMPLE 2: Medical Research (PubMed)")
    print("="*80 + "\n")
    
    agent = RAGResearchAgent(max_papers=10)
    
    result = await agent.execute(
        query="What are the mechanisms of CRISPR off-target effects and how can they be minimized?"
    )
    
    print("\n📊 RESEARCH REPORT:")
    print("="*80)
    print(result['report'])
    print("\n" + "="*80)
    

async def example_3_comparative_analysis():
    """Example 3: Comparative analysis"""
    
    print("\n" + "="*80)
    print("EXAMPLE 3: Comparative Analysis")
    print("="*80 + "\n")
    
    agent = RAGResearchAgent(max_papers=10)
    
    result = await agent.execute(
        query="Compare different approaches to quantum error correction. "
              "Which methods show the most promise?"
    )
    
    print("\n📊 RESEARCH REPORT:")
    print("="*80)
    print(result['report'])
    print("\n" + "="*80)
    

async def example_4_custom_papers():
    """Example 4: Custom number of papers"""
    
    print("\n" + "="*80)
    print("EXAMPLE 4: Custom Configuration (5 papers)")
    print("="*80 + "\n")
    
    # Use fewer papers for faster testing
    agent = RAGResearchAgent(max_papers=5)
    
    result = await agent.execute(
        query="Summarize recent advances in few-shot learning"
    )
    
    print("\n📊 RESEARCH REPORT:")
    print("="*80)
    print(result['report'])
    print("\n" + "="*80)
    print(f"\n📈 Papers Analyzed: {result['papers_analyzed']}")
    

async def main():
    """Run examples"""
    
    print("\n" + "🚀 RAG RESEARCH AGENT EXAMPLES 🚀".center(80))
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ ERROR: ANTHROPIC_API_KEY not found!")
        print("Please set it in your .env file or environment variables.")
        print("\nExample:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        return
    
    # Run example (uncomment others to try them)
    await example_1_deep_research()
    
    # Uncomment to run other examples:
    # await example_2_medical_research()
    # await example_3_comparative_analysis()
    # await example_4_custom_papers()


if __name__ == "__main__":
    asyncio.run(main())
