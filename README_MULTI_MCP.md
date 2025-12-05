# AI Automation Scientific Research Assistant: Multi-MCP Documentation Server

This project implements a fully orchestrated **Documentation MCP** (Multi-Agent Collaboration Protocol) for automated scientific research documentation, including:

- **Markdown**: with Table of Contents, citations, and tables
- **Diagram generation**: Mermaid syntax and LLM support
- **LaTeX/PDF**: PDF reports with equations, figures, bibliography
- **PowerPoint**: slides with professional themes, notes, tables
- **Word**: DOCX with templates and images
- **Bibliography**: APA, MLA, IEEE, BibTeX, RIS, etc.
- **Meta-Orchestrator**: coordinates research and documentation agents for end-to-end workflow

## Structure

```
documentation_mcp/
├── server.py
├── agents/
│   ├── documentation_agent.py
├── tools/
│   ├── markdown_tool.py
│   ├── diagram_tool.py
│   ├── latex_tool.py
│   ├── pptx_tool.py
│   ├── docx_tool.py
│   ├── bibliography_tool.py
meta_orchestrator/
├── mcp_client.py
├── coordinator.py
```

## Usage

1. **Configure environment variables** (e.g. `ANTHROPIC_API_KEY` for Claude).
2. **Install dependencies**:  
   `pip install -r requirements.txt`
3. **Start Documentation MCP server** (see `server.py`).
4. **Use agents/tools via Meta-Orchestrator** for research-to-paper pipelines.

## Example workflow

```python
from meta_orchestrator.coordinator import run_research_workflow

result = await run_research_workflow("AI in Healthcare", format="latex")
print(result['document'])
```

## Contributing

PRs welcome for new document formats, automation agents, workflow improvements, etc.

## License

MIT