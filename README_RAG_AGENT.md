## 🤖 A2A Paper Ranking (NEW!)

The RAG Research Agent now includes an intelligent paper ranking system using **Agent-to-Agent (A2A)** communication.

### How It Works

```
Search (20 papers) → A2A Call → Ranking Agent → Top 10 → Download PDFs
```

### Benefits
- ✅ **Better Selection**: LLM evaluates relevance before downloading
- ✅ **Faster**: Downloads only most relevant papers
- ✅ **Explainable**: Provides reasoning for paper selection
- ✅ **Cost-Effective**: +$0.02 for significantly better quality

### Example

```python
agent = RAGResearchAgent(max_papers=10)
result = await agent.execute("transformer attention mechanisms")

# Check ranking explanation
print(result['search_results']['ranking_explanation'])
```

For detailed documentation, see [README_A2A_RANKING.md](README_A2A_RANKING.md)
