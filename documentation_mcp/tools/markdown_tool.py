"""
Markdown Generation Tool
Creates well-formatted Markdown documents with TOC, citations, code blocks
"""

import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarkdownTool:
    """Tool for generating Markdown documents"""
    
    async def generate(self, args: Dict[str, Any]) -> str:
        """
        Generate formatted Markdown document
        
        Args:
            args: {
                content: dict with sections,
                style: "academic" | "blog" | "technical",
                include_toc: bool,
                include_citations: bool
            }
        
        Returns:
            Formatted Markdown string
        """
        logger.info("📝 Generating Markdown document...")
        
        content = args.get('content', {})
        style = args.get('style', 'academic')
        include_toc = args.get('include_toc', True)
        include_citations = args.get('include_citations', True)
        
        markdown_parts = []
        
        # Title and metadata
        if 'title' in content:
            markdown_parts.append(f"# {content['title']}\n")
        
        if 'metadata' in content:
            meta = content['metadata']
            markdown_parts.append("---")
            if 'authors' in meta:
                markdown_parts.append(f"**Authors:** {', '.join(meta['authors'])}")
            if 'date' in meta:
                markdown_parts.append(f"**Date:** {meta['date']}")
            if 'affiliation' in meta:
                markdown_parts.append(f"**Affiliation:** {meta['affiliation']}")
            markdown_parts.append("---\n")
        
        # Table of Contents
        if include_toc and 'sections' in content:
            markdown_parts.append("## Table of Contents\n")
            for i, section in enumerate(content['sections'], 1):
                title = section.get('title', f'Section {i}')
                anchor = title.lower().replace(' ', '-').replace(':', '')
                markdown_parts.append(f"{i}. [{title}](#{anchor})")
            markdown_parts.append("\n---\n")
        
        # Sections
        if 'sections' in content:
            for section in content['sections']:
                markdown_parts.append(self._format_section(section, style))
        
        # Citations
        if include_citations and 'citations' in content:
            markdown_parts.append("\n---\n")
            markdown_parts.append("## References\n")
            for i, citation in enumerate(content['citations'], 1):
                markdown_parts.append(f"{i}. {self._format_citation(citation)}")
        
        result = "\n".join(markdown_parts)
        logger.info(f"✅ Generated Markdown document ({len(result)} chars)")
        
        return result
    
    def _format_section(self, section: Dict, style: str) -> str:
        """Format a single section"""
        parts = []
        
        # Section title
        title = section.get('title', 'Untitled Section')
        level = section.get('level', 2)
        parts.append(f"{'#' * level} {title}\n")
        
        # Section content
        if 'content' in section:
            parts.append(section['content'])
        
        # Subsections
        if 'subsections' in section:
            for subsection in section['subsections']:
                parts.append(self._format_section(subsection, style))
        
        # Code blocks
        if 'code' in section:
            lang = section.get('code_language', '')
            parts.append(f"```{lang}")
            parts.append(section['code'])
            parts.append("```")
        
        # Tables
        if 'table' in section:
            parts.append(self._format_table(section['table']))
        
        # Images
        if 'images' in section:
            for img in section['images']:
                alt = img.get('alt', 'Image')
                url = img.get('url', '')
                caption = img.get('caption', '')
                parts.append(f"![{alt}]({url})")
                if caption:
                    parts.append(f"*{caption}*")
        
        parts.append("")  # Empty line between sections
        
        return "\n".join(parts)
    
    def _format_citation(self, citation: Dict) -> str:
        """Format a citation"""
        authors = ', '.join(citation.get('authors', ['Unknown']))
        title = citation.get('title', 'Untitled')
        year = citation.get('year', 'n.d.')
        venue = citation.get('venue', '')
        doi = citation.get('doi', '')
        
        parts = [f"{authors}. ({year}). *{title}*."]
        if venue:
            parts.append(f" {venue}.")
        if doi:
            parts.append(f" https://doi.org/{doi}")
        
        return "".join(parts)
    
    def _format_table(self, table_data: Dict) -> str:
        """Format a Markdown table"""
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])
        
        if not headers or not rows:
            return ""
        
        # Header row
        table_lines = ["| " + " | ".join(headers) + " |"]
        
        # Separator
        table_lines.append("| " + " | ".join(['---'] * len(headers)) + " |")
        
        # Data rows
        for row in rows:
            if isinstance(row, dict):
                row_values = [str(row.get(h, '')) for h in headers]
            else:
                row_values = [str(v) for v in row]
            table_lines.append("| " + " | ".join(row_values) + " |")
        
        return "\n".join(table_lines)
    
    async def create_table(self, args: Dict[str, Any]) -> str:
        """Create a standalone table"""
        data = args.get('data', [])
        headers = args.get('headers', [])
        format_type = args.get('format', 'markdown')
        
        if format_type == 'markdown':
            return self._format_table({'headers': headers, 'rows': data})
        elif format_type == 'latex':
            return self._format_latex_table({'headers': headers, 'rows': data})
        elif format_type == 'html':
            return self._format_html_table({'headers': headers, 'rows': data})
        else:
            return str(data)
    
    def _format_latex_table(self, table_data: Dict) -> str:
        """Format a LaTeX table"""
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])
        
        num_cols = len(headers)
        latex = [
            "\\begin{table}[h]",
            "\\centering",
            f"\\begin{{tabular}}{{{'|c' * num_cols}|}}",
            "\\hline"
        ]
        
        # Headers
        latex.append(" & ".join(headers) + " \\\")
        latex.append("\\hline")
        
        # Rows
        for row in rows:
            if isinstance(row, dict):
                row_values = [str(row.get(h, '')) for h in headers]
            else:
                row_values = [str(v) for v in row]
            latex.append(" & ".join(row_values) + " \\\")
        
        latex.extend([
            "\\hline",
            "\\end{tabular}",
            "\\caption{Table caption}",
            "\\end{table}"
        ])
        
        return "\n".join(latex)
    
    def _format_html_table(self, table_data: Dict) -> str:
        """Format an HTML table"""
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])
        
        html = ["<table border='1'>", "<thead><tr>"]
        
        # Headers
        for h in headers:
            html.append(f"<th>{h}</th>")
        html.append("</tr></thead>")
        
        # Rows
        html.append("<tbody>")
        for row in rows:
            html.append("<tr>")
            if isinstance(row, dict):
                row_values = [str(row.get(h, '')) for h in headers]
            else:
                row_values = [str(v) for v in row]
            for v in row_values:
                html.append(f"<td>{v}</td>")
            html.append("</tr>")
        html.append("</tbody></table>")
        
        return "\n".join(html)