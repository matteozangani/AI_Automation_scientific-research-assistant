# 🤖 Agent-to-Agent (A2A) Paper Ranking System

An intelligent paper ranking system using **Agent-to-Agent (A2A)** communication pattern where a specialized ranking agent evaluates papers using LLM intelligence before the main research agent downloads PDFs.

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────┐
│      MAIN RESEARCH AGENT                │
│   (RAGResearchAgent - Orchestrator)    │
└────────────┬────────────────────────────┘
             │
             │ Query + 20 Papers
             ▼
┌─────────────────────────────────────────┐
│      A2A CALL (Agent-to-Agent)          │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│    RANKING SPECIALIST AGENT             │
│   (PaperRankingAgent - Specialist)     │
│                                         │
│  ✓ Reads all abstracts                 │
│  ✓ Analyzes semantic relevance         │
│  ✓ Evaluates methodology quality       │
│  ✓ Considers recency & impact          │
│  ✓ Returns top-10 ranked papers        │
└────────────┬────────────────────────────┘
             │
             │ Ranked Papers + Explanation
             ▼
┌─────────────────────────────────────────┐
│      MAIN RESEARCH AGENT                │
│   Downloads ONLY top-ranked papers      │
└─────────────────────────────────────────┘
```

---

## ✨ Key Features

- **🎯 Intelligent Ranking**: Uses Claude to evaluate paper relevance before downloading
- **⚡ Efficient**: Analyzes abstracts only (not full PDFs) - saves time and cost
- **🔧 Configurable**: Customizable ranking criteria (relevance, methodology, recency, impact)
- **📊 Explainable**: Provides reasoning for ranking decisions
- **🧩 Modular**: Specialist agent can be used independently or via A2A
- **🔄 Reusable**: Ranking agent can be called from any other agent

---

## 📦 Components

### 1. **PaperRankingAgent** (`agent/paper_ranking_agent.py`)
Specialist agent that ranks papers using LLM intelligence.

**Methods:**
- `rank_papers()`: Main ranking method
- `explain_ranking()`: Generate explanation for rankings
- `_prepare_paper_summaries()`: Format papers for LLM
- `_llm_rank()`: Get rankings from Claude
- `_parse_ranking_response()`: Parse LLM output
- `_apply_ranking()`: Reorder papers by rank

### 2. **A2A Interface** (`call_ranking_agent()`)
Simple function to call ranking agent from main agent.

### 3. **Integration** (in `RAGResearchAgent`)
A2A call integrated into search execution flow.

---

## 🚀 Usage

### Standalone Usage

```python
from agent.paper_ranking_agent import PaperRankingAgent

# Create ranking agent
ranking_agent = PaperRankingAgent()

# Rank papers
papers = [...]  # List of papers with title, abstract, etc.
query = "transformer attention mechanisms"

ranked_papers = await ranking_agent.rank_papers(
    papers=papers,
    query=query,
    max_papers=10
)

# Get explanation
explanation = await ranking_agent.explain_ranking(query, ranked_papers)
print(explanation)
```

### A2A Usage (from Main Agent)

```python
from agent.paper_ranking_agent import call_ranking_agent

# A2A call
ranked_papers, explanation = await call_ranking_agent(
    papers=papers,
    query="quantum computing",
    max_papers=10
)
```

### Integrated in RAG Agent

```python
from agent.rag_research_agent import RAGResearchAgent

# Ranking happens automatically
agent = RAGResearchAgent(max_papers=10)
result = await agent.execute("your research question")

# Ranking explanation included in results
print(result['search_results']['ranking_explanation'])
```

---

## ⚙️ Configuration

### Default Ranking Criteria

```python
criteria = {
    'relevance': 0.5,      # 50% - Semantic relevance to query
    'methodology': 0.2,    # 20% - Research methodology quality
    'recency': 0.15,       # 15% - Publication date
    'impact': 0.15         # 15% - Citations, venue quality
}
```

### Custom Criteria

```python
custom_criteria = {
    'relevance': 0.6,      # Prioritize relevance
    'methodology': 0.3,    # Focus on methodology
    'recency': 0.05,       # De-prioritize recency
    'impact': 0.05         # De-prioritize impact
}

ranked_papers = await agent.rank_papers(
    papers=papers,
    query=query,
    criteria=custom_criteria
)
```

---

## 📊 How It Works

### Step 1: Prepare Papers
```python
# Format each paper
Paper #1
Title: Attention Is All You Need
Authors: Vaswani, Shazeer, Parmar
Year: 2017
Citations: 50000
Abstract: We propose a new simple network architecture...
```

### Step 2: LLM Ranking
```python
# Claude evaluates based on:
- Semantic relevance to query
- Quality of research methodology
- Publication recency
- Citation count and venue quality

# Returns ranking:
RANKING: 3,7,1,9,2,5,10,4,6,8

EXPLANATION:
Paper #3: Most directly addresses the query with novel methodology
Paper #7: Strong experimental design and recent publication
Paper #1: Foundational work with high impact
```

### Step 3: Apply Ranking
```python
# Reorder papers and add scores
[
    {'title': 'Paper 3', 'ranking_score': 10},
    {'title': 'Paper 7', 'ranking_score': 9},
    {'title': 'Paper 1', 'ranking_score': 8},
    ...
]
```

---

## 🎯 Benefits

### Without A2A Ranking
```
Search → Download 10 papers → Process all → Some may be irrelevant
- Time: ~30 seconds
- Cost: $0.15
- Quality: Mixed (some irrelevant papers processed)
```

### With A2A Ranking
```
Search → Get 20 papers → Rank with LLM → Download top-10 → Process only best
- Time: ~25 seconds (faster PDF selection)
- Cost: $0.17 (+$0.02 for ranking)
- Quality: HIGH (only most relevant papers)
```

**Trade-off:** +$0.02 for significantly better quality ✅

---

## 📈 Performance

### Speed
- Ranking 20 papers: ~2-5 seconds
- Abstracts only (no PDF download needed)
- Parallel with main agent workflow

### Cost
- Input tokens: ~5K (20 abstracts)
- Output tokens: ~500 (ranking + explanation)
- **Total: ~$0.02 per ranking**

### Accuracy
- LLM understands semantic relevance
- Considers multiple factors holistically
- Explainable decisions

---

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest tests/test_paper_ranking_agent.py -v

# Skip integration tests (no API key needed)
pytest tests/test_paper_ranking_agent.py -v -m "not integration"

# Only integration tests (requires API key)
pytest tests/test_paper_ranking_agent.py -v -m integration
```

### Test Coverage
- ✅ Agent initialization
- ✅ Paper summary preparation
- ✅ LLM response parsing
- ✅ Ranking application
- ✅ A2A interface
- ✅ Custom criteria
- ✅ Error handling
- ✅ Performance characteristics

---

## 🔧 Extending

### Add New Ranking Factor

```python
# In PaperRankingAgent._llm_rank()
system_prompt = f"""Ranking Criteria:
- Relevance ({criteria['relevance']*100}%)
- Methodology ({criteria['methodology']*100}%)
- Recency ({criteria['recency']*100}%)
- Impact ({criteria['impact']*100}%)
- NEW_FACTOR ({criteria['new_factor']*100}%)  # ← Add here
"""
```

### Use Different Model

```python
# Use Claude Opus for even better ranking
ranking_agent = PaperRankingAgent(
    model="claude-3-opus-20240229"
)
```

### Chain Multiple Ranking Agents

```python
# First pass: semantic relevance
semantic_ranked = await semantic_ranking_agent.rank_papers(...)

# Second pass: methodology evaluation
final_ranked = await methodology_ranking_agent.rank_papers(semantic_ranked)
```

---

## 🆚 Comparison: Ranking Methods

| Method | Speed | Cost | Quality | Explainable |
|--------|-------|------|---------|-------------|
| **No Ranking** | Fast | $0 | Low | ❌ |
| **Keyword Matching** | Fast | $0 | Medium | ⚠️ |
| **TF-IDF** | Fast | $0 | Medium | ⚠️ |
| **Embeddings Only** | Fast | $0 | Good | ❌ |
| **LLM Ranking (A2A)** | Medium | $0.02 | **Excellent** | ✅ |
| **LLM + Citations** | Medium | $0.03 | **Excellent** | ✅ |

---

## 💡 Best Practices

### 1. Search More, Download Less
```python
# Get 20 papers, rank, download top-10
search_limit = max_papers * 2
ranked_papers = await ranking_agent.rank_papers(papers, query, max_papers=10)
```

### 2. Cache Rankings
```python
# Store rankings to avoid re-ranking same query
ranking_cache[query_hash] = ranked_papers
```

### 3. Provide Context
```python
# Better ranking with more context
query = f"{user_query}. Focus on: {additional_context}"
```

### 4. Review Explanations
```python
# Use explanations to improve future queries
explanation = await ranking_agent.explain_ranking(query, ranked_papers)
logger.info(f"Ranking reason: {explanation}")
```

---

## 🐛 Troubleshooting

### Issue: Ranking seems random
**Solution:** Check ranking explanation
```python
explanation = await agent.explain_ranking(query, ranked_papers)
print(explanation)  # Understand why papers were ranked this way
```

### Issue: Same papers always ranked top
**Solution:** Adjust criteria weights
```python
criteria = {
    'relevance': 0.3,  # Reduce relevance weight
    'recency': 0.4     # Increase recency weight
}
```

### Issue: Ranking takes too long
**Solution:** Reduce number of papers to rank
```python
# Rank fewer papers
search_limit = max_papers * 1.5  # Instead of 2x
```

### Issue: Unexpected ranking order
**Solution:** Check paper metadata quality
```python
# Ensure papers have good abstracts
for paper in papers:
    if len(paper.get('summary', '')) < 100:
        logger.warning(f"Short abstract: {paper['title']}")
```

---

## 📚 References

- [LangChain Agent Patterns](https://python.langchain.com/docs/modules/agents/)
- [Multi-Agent Systems](https://lilianweng.github.io/posts/2023-06-23-agent/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [RAG Best Practices](https://www.pinecone.io/learn/retrieval-augmented-generation/)

---

## 🤝 Contributing

Ideas for improvement:
- [ ] Add citation network analysis
- [ ] Implement author reputation scoring
- [ ] Add venue/journal quality database
- [ ] Create ranking visualization dashboard
- [ ] Add A/B testing framework for criteria
- [ ] Implement learning from user feedback

---

## 📄 License

MIT License - See LICENSE file

---

**Built with ❤️ using Agent-to-Agent (A2A) pattern**
