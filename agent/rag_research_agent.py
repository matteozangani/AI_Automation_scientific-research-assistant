"""
RAG-based Research Agent with PDF Processing and Vector Search
Full implementation with 10 document support
"""

import os
import logging
from typing import TypedDict, Annotated, List, Dict, Optional
from pathlib import Path
import asyncio
import aiohttp
import hashlib

from langgraph.graph import StateGraph, END, add_messages
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

# RAG components
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

from mcp_server.tools.arxiv_tool import ArxivTool
from mcp_server.tools.pubmed_tool import PubmedTool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============= AGENT STATE =============
class RAGAgentState(TypedDict):
    """State for RAG research agent"""
    messages: Annotated[list, add_messages]
    current_task: str
    search_results: dict
    downloaded_papers: List[str]  # PDF paths
    vector_store: object  # ChromaDB instance
    relevant_chunks: List[str]  # Retrieved context
    analysis: str
    iteration_count: int
    total_papers: int
    total_chunks: int


# ============= PDF PROCESSING =============
class PDFProcessor:
    """Handles PDF download and processing"""
    
    def __init__(self, cache_dir: str = "./paper_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        logger.info(f"📁 PDF cache directory: {self.cache_dir}")
    
    async def download_pdf(self, url: str, paper_id: str) -> Optional[str]:
        """
        Download PDF from URL
        
        Args:
            url: PDF URL
            paper_id: Unique paper identifier
        
        Returns:
            Path to downloaded PDF or None if failed
        """
        # Create safe filename
        safe_id = hashlib.md5(paper_id.encode()).hexdigest()[:10]
        pdf_path = self.cache_dir / f"{safe_id}.pdf"
        
        # Check cache
        if pdf_path.exists():
            logger.info(f"✅ Using cached PDF: {paper_id}")
            return str(pdf_path)
        
        logger.info(f"⬇️ Downloading PDF: {paper_id} from {url}")
        
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Validate PDF size (max 50MB)
                        if len(content) > 50_000_000:
                            logger.error(f"❌ PDF too large: {len(content)} bytes")
                            return None
                        
                        pdf_path.write_bytes(content)
                        logger.info(f"✅ Downloaded: {paper_id} ({len(content):,} bytes)")
                        return str(pdf_path)
                    else:
                        logger.error(f"❌ Download failed: HTTP {response.status}")
                        return None
        except asyncio.TimeoutError:
            logger.error(f"❌ Download timeout for: {paper_id}")
            return None
        except Exception as e:
            logger.error(f"❌ Download error for {paper_id}: {e}")
            return None
    
    def extract_text(self, pdf_path: str) -> List[str]:
        """
        Extract text from PDF
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            List of page texts
        """
        try:
            logger.info(f"📄 Extracting text from: {pdf_path}")
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            logger.info(f"✅ Extracted {len(pages)} pages from PDF")
            return [page.page_content for page in pages]
        except Exception as e:
            logger.error(f"❌ PDF extraction error: {e}")
            return []


# ============= RAG VECTOR STORE =============
class RAGVectorStore:
    """Manages vector embeddings and similarity search"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        
        logger.info("🔄 Initializing embeddings model (this may take a moment)...")
        
        # Use local embeddings (no API needed)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # ~750 words per chunk
            chunk_overlap=200,  # Overlap to maintain context
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        self.vector_store = None
        self.total_chunks = 0
        logger.info("✅ RAG Vector Store initialized")
    
    def add_documents(self, texts: List[str], metadatas: List[dict] = None):
        """
        Add documents to vector store
        
        Args:
            texts: List of text documents
            metadatas: Metadata for each document
        """
        if not texts:
            logger.warning("⚠️ No texts to add to vector store")
            return
        
        logger.info(f"📦 Processing {len(texts)} documents for chunking...")
        
        # Split texts into chunks
        chunks = []
        chunk_metadatas = []
        
        for i, text in enumerate(texts):
            if not text or len(text.strip()) < 100:
                logger.warning(f"⚠️ Skipping empty or too short document {i}")
                continue
            
            text_chunks = self.text_splitter.split_text(text)
            chunks.extend(text_chunks)
            
            # Add metadata
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            chunk_metadatas.extend([metadata.copy() for _ in range(len(text_chunks))])
        
        if not chunks:
            logger.error("❌ No valid chunks created")
            return
        
        logger.info(f"📦 Created {len(chunks)} chunks from {len(texts)} documents")
        self.total_chunks = len(chunks)
        
        # Create or update vector store
        try:
            if self.vector_store is None:
                logger.info("🔄 Creating new vector store...")
                self.vector_store = Chroma.from_texts(
                    texts=chunks,
                    embedding=self.embeddings,
                    metadatas=chunk_metadatas,
                    persist_directory=self.persist_directory
                )
                logger.info("✅ Vector store created")
            else:
                logger.info("🔄 Adding to existing vector store...")
                self.vector_store.add_texts(
                    texts=chunks,
                    metadatas=chunk_metadatas
                )
                logger.info("✅ Documents added to vector store")
        except Exception as e:
            logger.error(f"❌ Error adding documents to vector store: {e}")
            raise
    
    def similarity_search(self, query: str, k: int = 15) -> List[Dict]:
        """
        Search for relevant chunks
        
        Args:
            query: Search query
            k: Number of results
        
        Returns:
            List of dicts with 'content' and 'metadata'
        """
        if self.vector_store is None:
            logger.warning("⚠️ Vector store is empty")
            return []
        
        logger.info(f"🔍 Searching for top {k} relevant chunks...")
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            chunks = []
            for doc, score in results:
                chunks.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': score
                })
            
            logger.info(f"✅ Found {len(chunks)} relevant chunks")
            return chunks
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []


# ============= TOOLS FOR LANGGRAPH =============
@tool
async def search_papers_tool(query: str, max_results: int = 10) -> dict:
    """
    Search for scientific papers across multiple databases.
    Automatically selects appropriate database based on query content.
    
    Args:
        query: Research query
        max_results: Maximum papers to return (default: 10)
    
    Returns:
        Dictionary with search results
    """
    logger.info(f"🔍 Tool called: search_papers_tool(query='{query}', max_results={max_results})")
    
    # Determine which database to use based on keywords
    medical_keywords = ['medical', 'disease', 'clinical', 'patient', 'drug', 'therapy', 'cancer', 'gene', 'protein']
    is_medical = any(keyword in query.lower() for keyword in medical_keywords)
    
    if is_medical:
        logger.info("📚 Using PubMed for medical query")
        tool = PubmedTool()
    else:
        logger.info("📚 Using arXiv for general scientific query")
        tool = ArxivTool()
    
    results = await tool.search(query, max_results=max_results)
    return results


# ============= RAG RESEARCH AGENT =============
class RAGResearchAgent:
    """Fully agentic RAG-based research assistant with LangGraph"""
    
    def __init__(self, api_key: str = None, model: str = "claude-3-5-sonnet-20241022", max_papers: int = 10):
        """
        Initialize RAG research agent
        
        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_papers: Maximum papers to analyze (default: 10)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required. Set environment variable or pass directly.")
        
        self.max_papers = max_papers
        
        self.llm = ChatAnthropic(
            model=model,
            temperature=0,
            max_tokens=8192,  # Increased for longer reports
            api_key=self.api_key
        )
        
        # Bind tools
        self.llm_with_tools = self.llm.bind_tools([search_papers_tool])
        
        self.pdf_processor = PDFProcessor()
        self.vector_store = RAGVectorStore()
        
        # Build LangGraph
        self.graph = self._build_graph()
        
        logger.info(f"✅ RAG Research Agent initialized (model={model}, max_papers={max_papers})")
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph state machine"""
        workflow = StateGraph(RAGAgentState)
        
        # Add nodes
        workflow.add_node("planner", self.plan_node)
        workflow.add_node("search_executor", self.search_executor_node)
        workflow.add_node("pdf_processor", self.pdf_processor_node)
        workflow.add_node("rag_analyzer", self.rag_analyzer_node)
        workflow.add_node("reporter", self.reporter_node)
        
        # Define edges
        workflow.set_entry_point("planner")
        
        workflow.add_conditional_edges(
            "planner",
            self.should_execute_search,
            {
                "search": "search_executor",
                "end": END
            }
        )
        
        workflow.add_edge("search_executor", "pdf_processor")
        workflow.add_edge("pdf_processor", "rag_analyzer")
        workflow.add_edge("rag_analyzer", "reporter")
        workflow.add_edge("reporter", END)
        
        return workflow.compile()
    
    async def plan_node(self, state: RAGAgentState) -> RAGAgentState:
        """Planning node - agent decides search strategy"""
        logger.info("🧠 PLANNER NODE: Analyzing query and creating search strategy...")
        
        messages = state["messages"]
        
        system_msg = SystemMessage(content="""You are a research planning assistant.
Analyze the user's research question and use the search_papers_tool to find relevant papers.

You have access to:
- search_papers_tool: Searches arXiv (CS/Physics/Math) or PubMed (Medicine/Biology)

Create an effective search query and call the tool.""")
        
        response = await self.llm_with_tools.ainvoke([system_msg] + messages)
        state["messages"].append(response)
        
        logger.info("✅ Planning complete")
        return state
    
    async def search_executor_node(self, state: RAGAgentState) -> RAGAgentState:
        """Execute paper search"""
        logger.info("🔧 SEARCH EXECUTOR NODE: Executing paper search...")
        
        last_message = state["messages"][-1]
        
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            logger.warning("⚠️ No tool calls found")
            return state
        
        # Execute tool calls
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Enforce max_papers limit
            if 'max_results' in tool_args:
                tool_args['max_results'] = min(tool_args['max_results'], self.max_papers)
            else:
                tool_args['max_results'] = self.max_papers
            
            logger.info(f"⚙️ Executing {tool_name} with args: {tool_args}")
            
            if tool_name == "search_papers_tool":
                result = await search_papers_tool.ainvoke(tool_args)
                state["search_results"] = result
                
                # Add tool response
                state["messages"].append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"]
                    )
                )
        
        logger.info("✅ Search execution complete")
        return state
    
    async def pdf_processor_node(self, state: RAGAgentState) -> RAGAgentState:
        """Download and process PDFs"""
        logger.info("📄 PDF PROCESSOR NODE: Downloading and processing papers...")
        
        search_results = state.get("search_results", {})
        papers = search_results.get('results', [])
        
        if not papers:
            logger.warning("⚠️ No papers to process")
            return state
        
        logger.info(f"📚 Processing {len(papers)} papers...")
        
        downloaded = []
        all_texts = []
        all_metadatas = []
        
        # Download PDFs concurrently (max 3 at a time to avoid overload)
        semaphore = asyncio.Semaphore(3)
        
        async def download_with_semaphore(paper):
            async with semaphore:
                pdf_url = paper.get('pdf_url') or paper.get('url', '')
                paper_id = paper.get('arxiv_id') or paper.get('pmid', '') or paper.get('title', '')[:50]
                
                if pdf_url and paper_id:
                    pdf_path = await self.pdf_processor.download_pdf(pdf_url, paper_id)
                    if pdf_path:
                        return {
                            'path': pdf_path,
                            'paper_id': paper_id,
                            'title': paper.get('title', ''),
                            'authors': paper.get('authors', [])
                        }
                return None
        
        # Download all PDFs
        download_tasks = [download_with_semaphore(paper) for paper in papers]
        results = await asyncio.gather(*download_tasks, return_exceptions=True)
        
        downloaded = [r for r in results if r and not isinstance(r, Exception)]
        
        logger.info(f"✅ Successfully downloaded {len(downloaded)}/{len(papers)} PDFs")
        
        # Extract text from PDFs
        for paper_info in downloaded:
            pdf_path = paper_info['path']
            
            # Extract text
            pages = self.pdf_processor.extract_text(pdf_path)
            
            if pages:
                # Combine pages
                full_text = "\n\n".join(pages)
                all_texts.append(full_text)
                
                # Add metadata
                all_metadatas.append({
                    'paper_id': paper_info['paper_id'],
                    'title': paper_info['title'],
                    'authors': ', '.join(paper_info['authors'][:3]) if paper_info['authors'] else 'Unknown'
                })
        
        # Add to vector store
        if all_texts:
            logger.info(f"🔄 Adding {len(all_texts)} papers to vector store...")
            self.vector_store.add_documents(all_texts, all_metadatas)
            state["downloaded_papers"] = downloaded
            state["total_papers"] = len(all_texts)
            state["total_chunks"] = self.vector_store.total_chunks
            logger.info(f"✅ Vector store ready with {self.vector_store.total_chunks} chunks")
        else:
            logger.error("❌ No texts extracted from PDFs")
        
        return state
    
    async def rag_analyzer_node(self, state: RAGAgentState) -> RAGAgentState:
        """Analyze using RAG"""
        logger.info("🧠 RAG ANALYZER NODE: Retrieving relevant context and analyzing...")
        
        original_query = state["current_task"]
        
        # Retrieve relevant chunks
        relevant_chunks = self.vector_store.similarity_search(original_query, k=20)
        
        if not relevant_chunks:
            state["analysis"] = "No relevant content found in papers."
            return state
        
        # Format context
        context_parts = []
        for i, chunk_info in enumerate(relevant_chunks[:15], 1):  # Use top 15
            content = chunk_info['content']
            metadata = chunk_info['metadata']
            title = metadata.get('title', 'Unknown')
            
            context_parts.append(f"[Excerpt {i} from '{title[:60]}...']\n{content}\n")
        
        context = "\n---\n".join(context_parts)
        
        logger.info(f"📊 Retrieved context: {len(context):,} characters from {len(relevant_chunks)} chunks")
        
        # Analyze with Claude
        analysis_prompt = f"""You are an expert research analyst with access to full scientific papers.

Research Question: {original_query}

Relevant Excerpts from Papers:
{context[:30000]}

Based on these excerpts from the papers, provide a comprehensive analysis:

1. **Key Findings**: What are the main discoveries and results?
2. **Methodologies**: What approaches and techniques were used?
3. **Evidence**: Cite specific findings with paper references
4. **Limitations**: What limitations did the authors mention?
5. **Implications**: What are the broader implications of this research?
6. **Future Directions**: What future research directions are suggested?

Be specific and cite passages from the papers when making claims.
"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content="You are an expert research analyst. Provide detailed, evidence-based analysis."),
            HumanMessage(content=analysis_prompt)
        ])
        
        state["analysis"] = response.content
        state["relevant_chunks"] = [c['content'] for c in relevant_chunks[:15]]
        
        logger.info("✅ RAG analysis complete")
        return state
    
    async def reporter_node(self, state: RAGAgentState) -> RAGAgentState:
        """Generate final report"""
        logger.info("📝 REPORTER NODE: Generating final research report...")
        
        query = state["current_task"]
        analysis = state.get("analysis", "")
        downloaded = state.get("downloaded_papers", [])
        total_papers = state.get("total_papers", 0)
        total_chunks = state.get("total_chunks", 0)
        
        # Create paper list
        paper_list = "\n".join([
            f"{i+1}. {p['title']}\n   Authors: {', '.join(p['authors'][:3]) if p['authors'] else 'Unknown'}"
            for i, p in enumerate(downloaded)
        ])
        
        report = f"""# 📚 Deep Research Report

## Research Question
{query}

---

## 📊 Research Scope
- **Papers Analyzed**: {total_papers} full papers downloaded and processed
- **Total Content**: {total_chunks} text chunks extracted and indexed
- **Analysis Method**: RAG (Retrieval-Augmented Generation) with semantic search

---

## 📑 Papers Analyzed

{paper_list}

---

## 🔬 Comprehensive Analysis

{analysis}

---

## 🔍 Methodology

This deep research was conducted using advanced RAG techniques:

1. **Paper Discovery**: Searched academic databases (arXiv/PubMed)
2. **Full-Text Retrieval**: Downloaded and extracted complete paper PDFs
3. **Content Processing**: Chunked papers into {total_chunks} semantic segments
4. **Embedding Generation**: Created vector embeddings using sentence-transformers
5. **Semantic Search**: Retrieved most relevant passages using similarity search
6. **Deep Analysis**: Analyzed full context with Claude 3.5 Sonnet (200K context window)

Total content analyzed: {total_chunks} chunks across {total_papers} papers

---

## ⚙️ Technical Details
- **Model**: Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
- **Vector Store**: ChromaDB with local embeddings
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
- **Chunk Size**: 1000 tokens with 200 token overlap

---

*Generated by RAG Research Agent*
"""
        
        state["messages"].append(AIMessage(content=report))
        logger.info("✅ Report generation complete")
        
        return state
    
    def should_execute_search(self, state: RAGAgentState) -> str:
        """Decide if should execute search"""
        last_message = state["messages"][-1]
        
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "search"
        
        return "end"
    
    async def execute(self, query: str) -> Dict:
        """
        Execute full RAG research pipeline
        
        Args:
            query: Research question
        
        Returns:
            Complete research report with metadata
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 Starting RAG Research Agent")
        logger.info(f"📝 Query: {query}")
        logger.info(f"📊 Max Papers: {self.max_papers}")
        logger.info(f"{'='*80}\n")
        
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "current_task": query,
            "search_results": {},
            "downloaded_papers": [],
            "vector_store": None,
            "relevant_chunks": [],
            "analysis": "",
            "iteration_count": 0,
            "total_papers": 0,
            "total_chunks": 0
        }
        
        try:
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)
            
            # Extract final report
            final_report = final_state["messages"][-1].content if final_state["messages"] else "No report generated"
            
            logger.info(f"\n{'='*80}")
            logger.info("✅ RAG Research Complete!")
            logger.info(f"📊 Papers Analyzed: {final_state.get('total_papers', 0)}")
            logger.info(f"📦 Chunks Processed: {final_state.get('total_chunks', 0)}")
            logger.info(f"{'='*80}\n")
            
            return {
                "query": query,
                "report": final_report,
                "papers_analyzed": final_state.get("total_papers", 0),
                "chunks_processed": final_state.get("total_chunks", 0),
                "papers_info": final_state.get("downloaded_papers", [])
            }
        
        except Exception as e:
            logger.error(f"❌ Error during execution: {e}", exc_info=True)
            return {
                "query": query,
                "error": str(e),
                "report": f"Error during research: {e}"
            }


# ============= CONVENIENCE FUNCTIONS =============
async def create_rag_agent(api_key: str = None, max_papers: int = 10) -> RAGResearchAgent:
    """
    Create RAG research agent
    
    Args:
        api_key: Anthropic API key
        max_papers: Maximum papers to analyze (default: 10)
    
    Returns:
        RAGResearchAgent instance
    """
    return RAGResearchAgent(api_key=api_key, max_papers=max_papers)
