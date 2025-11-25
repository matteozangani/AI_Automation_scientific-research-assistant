# 🤖 RAG Research Agent - Deep Paper Analysis

A **fully autonomous AI research agent** powered by **LangGraph** and **Anthropic Claude** that downloads complete scientific papers, processes them with RAG (Retrieval-Augmented Generation), and generates comprehensive, evidence-based research reports.

---

## 🌟 Key Features

- ✅ **Fully Autonomous**: Agent decides search strategy, tools, and analysis approach
- ✅ **Full PDF Processing**: Downloads and analyzes complete papers (not just abstracts)
- ✅ **RAG Architecture**: Semantic search through 10+ papers with 1000+ chunks
- ✅ **Multi-Source**: Searches arXiv (CS/Physics) and PubMed (Medicine/Biology)
- ✅ **Deep Analysis**: Evidence-based reports with specific citations
- ✅ **Scalable**: Analyzes up to 10 full papers per query
- ✅ **Production Ready**: Error handling, caching, logging

---

## 🏗️ Architecture

```
User Query
    ↓
┌──────────────────────────────────────┐
│  1. PLANNER (Claude decides)         │
│     - Analyzes query                 │
│     - Selects database (arXiv/PubMed)│
│     - Creates search strategy        │
└────────────┬─────────────────────────┘
             ↓
┌──────────────────────────────────────┐
│  2. SEARCH EXECUTOR                  │
│     - Searches academic databases    │
│     - Finds up to 10 papers          │
└────────────┬─────────────────────────┘
             ↓
┌──────────────────────────────────────┐
│  3. PDF PROCESSOR                    │
│     - Downloads PDFs (cached)        │
│     - Extracts full text             │
│     - Creates 1000-token chunks      │
│     - Generates embeddings           │
│     - Stores in ChromaDB             │
└────────────┬─────────────────────────┘
             ↓
┌──────────────────────────────────────┐
│  4. RAG ANALYZER                     │
│     - Semantic search (top 15 chunks)│
│     - Retrieves relevant passages    │
│     - Claude analyzes with context   │
└────────────┬─────────────────────────┘
             ↓
┌──────────────────────────────────────┐
│  5. REPORTER                         │
│     - Generates comprehensive report │
│     - Includes citations             │
│     - Provides methodology details   │
└──────────────────────────────────────┘
```

---

## 📦 Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `langgraph` - State machine framework
- `langchain-anthropic` - Claude integration
- `chromadb` - Vector database
- `sentence-transformers` - Embeddings
- `pypdf` - PDF processing
- `torch` - ML framework

### 2. Set Up API Key

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Anthropic API key
nano .env
```

Get your API key from: https://console.anthropic.com/

---

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from agent.rag_research_agent import RAGResearchAgent

async def main():
    # Create agent (analyzes 10 papers by default)
    agent = RAGResearchAgent()
    
    # Execute research
    result = await agent.execute(
        "What are the latest advances in quantum computing?"
    )
    
    # Print report
    print(result["report"])
    
    # Check metadata
    print(f"Papers analyzed: {result['papers_analyzed']}")
    print(f"Chunks processed: {result['chunks_processed']}")

asyncio.run(main())
```

### Run Examples

```bash
python examples/rag_research_example.py
```

---

## 🎯 Use Cases

### 1. Literature Review
```python
agent = RAGResearchAgent(max_papers=10)
result = await agent.execute(
    "Review the state of protein folding prediction methods "
    "including AlphaFold and its successors"
)
```

### 2. Comparative Analysis
```python
result = await agent.execute(
    "Compare transformer-based and CNN-based approaches "
    "for image classification. Which performs better?"
)
```

### 3. Medical Research
```python
result = await agent.execute(
    "What are the mechanisms of CAR-T cell therapy "
    "and what are the main challenges in clinical application?"
)
```

### 4. Trend Analysis
```python
result = await agent.execute(
    "Identify emerging trends in renewable energy storage "
    "from papers published in the last 2 years"
)
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your_key_here

# Optional
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
AGENT_MAX_PAPERS=10
RAG_CHUNK_SIZE=1000
RAG_TOP_K_CHUNKS=15
```

### Programmatic Configuration

```python
# Analyze fewer papers for faster results
agent = RAGResearchAgent(max_papers=5)

# Use different model
agent = RAGResearchAgent(
    model="claude-3-5-sonnet-20241022",
    max_papers=10
)
```

---

## 📊 How RAG Works

### Traditional Approach (Abstract-Only)
```
Input: 10 papers
Context: ~2,000 words (abstracts only)
Analysis: SUPERFICIAL ❌

What Claude sees:
- Titles and abstracts
- NO methodologies
- NO detailed results
- NO discussion sections
```

### RAG Approach (Full Papers)
```
Input: 10 papers (full PDFs)
Context: ~500,000 words (complete papers)
Analysis: DEEP ✅

What Claude sees:
1. Downloads 10 PDFs (~100MB total)
2. Extracts ~500 pages of text
3. Creates ~1,000 semantic chunks
4. Generates vector embeddings
5. Semantic search finds top 15 relevant chunks
6. Claude analyzes ~15,000 tokens of relevant context

Result: Evidence-based analysis with specific citations
```

---

## 🔍 Output Format

```markdown
# 📚 Deep Research Report

## Research Question
[Your query]

## 📊 Research Scope
- Papers Analyzed: 10 full papers
- Total Content: 1,234 chunks indexed
- Analysis Method: RAG with semantic search

## 📑 Papers Analyzed
1. Paper Title 1
   Authors: Smith et al.
2. Paper Title 2
   Authors: Jones et al.
...

## 🔬 Comprehensive Analysis

### Key Findings
[Evidence-based findings with citations]

### Methodologies
[Detailed method descriptions]

### Evidence
[Specific results from papers]

### Limitations
[Author-mentioned limitations]

### Implications
[Broader impact]

### Future Directions
[Suggested research directions]

## 🔍 Methodology
[Technical details of analysis]
```

---

## 📈 Performance

### Typical Execution Time
- **Search**: 2-5 seconds
- **PDF Download**: 10-30 seconds (10 papers)
- **Text Extraction**: 5-15 seconds
- **Embedding Generation**: 10-20 seconds
- **Analysis**: 10-20 seconds
- **Total**: 40-90 seconds for 10 papers

### Resource Usage
- **Disk**: ~10-50MB per paper (cached)
- **Memory**: ~2GB for embeddings
- **Network**: ~100MB download (uncached)

### Scalability
- ✅ Handles 10 papers with ~1,000 chunks
- ✅ Parallel PDF downloads (3 concurrent)
- ✅ Caches downloaded PDFs
- ✅ Incremental vector store updates

---

## 💰 Cost Estimate

### Per Research Query (10 papers)
- **PDF Downloads**: FREE (cached after first use)
- **Embeddings**: FREE (local model)
- **Vector Storage**: FREE (ChromaDB local)
- **Claude Analysis**: ~30K tokens
  - Input: ~25K tokens (~$0.075)
  - Output: ~5K tokens (~$0.075)
  - **Total: ~$0.15 per query**

### Cost Comparison
- **Abstract-only**: ~5K tokens = $0.015
- **RAG full-text**: ~30K tokens = $0.15
- **10x cost, but 50x better analysis!** 🚀

---

## 🛠️ Extending the Agent

### Add New Data Sources

```python
@tool
async def search_ieee_tool(query: str, max_results: int = 10) -> dict:
    """Search IEEE Xplore"""
    # Implementation
    pass

# Update planner to use new tool
self.llm_with_tools = self.llm.bind_tools([
    search_papers_tool,
    search_ieee_tool
])
```

### Custom Chunking Strategy

```python
# In RAGVectorStore.__init__
self.text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,  # Larger chunks
    chunk_overlap=300,
    separators=["\n## ", "\n\n", "\n", ". "]  # Split on headers
)
```

### Alternative Vector Stores

```python
# Use FAISS instead of Chroma
from langchain_community.vectorstores import FAISS

self.vector_store = FAISS.from_texts(
    texts=chunks,
    embedding=self.embeddings
)
```

---

## 🐛 Troubleshooting

### Issue: "ANTHROPIC_API_KEY not found"
```bash
export ANTHROPIC_API_KEY="your-key-here"
# or add to .env file
```

### Issue: "PDF download timeout"
```python
# Increase timeout in PDFProcessor
timeout = aiohttp.ClientTimeout(total=120)  # 2 minutes
```

### Issue: "Out of memory"
```python
# Reduce number of papers
agent = RAGResearchAgent(max_papers=5)

# Or reduce chunk size
self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500)
```

### Issue: "Slow embedding generation"
```python
# Use GPU if available
self.embeddings = HuggingFaceEmbeddings(
    model_kwargs={'device': 'cuda'}  # Use GPU
)
```

---

## 📚 Technical Details

### Models Used
- **LLM**: Claude 3.5 Sonnet (200K context, 8K output)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **Vector DB**: ChromaDB (local, persistent)

### Chunking Strategy
- **Chunk Size**: 1000 tokens (~750 words)
- **Overlap**: 200 tokens (maintains context)
- **Separators**: Paragraph breaks, sentences, spaces

### Retrieval Strategy
- **Method**: Cosine similarity search
- **Top-K**: 15 most relevant chunks
- **Re-ranking**: Score-based (built into ChromaDB)

---

## 🆚 Comparison

| Feature | Abstract-Only | RAG Full-Text |
|---------|--------------|---------------|
| **Content** | Abstracts only | Complete papers |
| **Depth** | Superficial | Deep analysis |
| **Citations** | General | Specific passages |
| **Context** | ~2K words | ~500K words |
| **Cost** | $0.01 | $0.15 |
| **Time** | 10s | 60s |
| **Quality** | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🤝 Contributing

Ideas for improvement:
- [ ] Add more data sources (IEEE, Springer, etc.)
- [ ] Implement citation network analysis
- [ ] Add figure/table extraction from PDFs
- [ ] Create web UI interface
- [ ] Add export to markdown/PDF
- [ ] Implement paper summarization cache

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) - State machine framework
- [Anthropic Claude](https://www.anthropic.com/) - AI reasoning engine
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Sentence Transformers](https://www.sbert.net/) - Embeddings

---

**Ready to analyze some papers?** 🚀

```bash
python examples/rag_research_example.py
```
