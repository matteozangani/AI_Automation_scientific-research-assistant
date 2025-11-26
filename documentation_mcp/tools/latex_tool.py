"""
LaTeX Compilation Tool
Compiles LaTeX documents with equations, tables, bibliography, and figures
"""

import logging
import os
import subprocess
import tempfile
from typing import Dict, Any
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LaTeXTool:
    """Tool for compiling LaTeX documents"""
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent.parent.parent / "templates" / "latex"
    
    async def compile(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compile LaTeX document
        
        Args:
            args: {
                content: dict with sections,
                template: "article" | "report" | "thesis" | "beamer",
                bibliography: list of citations,
                include_cover: bool
            }
        
        Returns:
            Dict with pdf_path, latex_source, status
        """
        logger.info("📄 Compiling LaTeX document...")
        
        content = args.get('content', {})
        template = args.get('template', 'article')
        bibliography = args.get('bibliography', [])
        include_cover = args.get('include_cover', True)
        
        # Generate LaTeX source
        latex_source = self._generate_latex(content, template, bibliography, include_cover)
        
        # Compile to PDF (if pdflatex available)
        try:
            pdf_path = await self._compile_to_pdf(latex_source)
            status = "success"
        except Exception as e:
            logger.warning(f"⚠️ PDF compilation failed: {e}")
            pdf_path = None
            status = "latex_only"
        
        return {
            'latex_source': latex_source,
            'pdf_path': pdf_path,
            'status': status
        }
    
    def _generate_latex(
        self, 
        content: Dict, 
        template: str, 
        bibliography: list,
        include_cover: bool
    ) -> str:
        """Generate LaTeX source code"""
        
        latex_parts = []
        
        # Document class
        if template == 'beamer':
            latex_parts.append(r"\documentclass{beamer}")
        elif template == 'thesis':
            latex_parts.append(r"\documentclass[12pt]{report}")
        else:
            latex_parts.append(r"\documentclass[11pt]{article}")
        
        # Packages
        latex_parts.extend([
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage{amsmath}",
            r"\usepackage{amssymb}",
            r"\usepackage{graphicx}",
            r"\usepackage{hyperref}",
            r"\usepackage{booktabs}",
            r"\usepackage{natbib}",
            r"\usepackage{geometry}",
            r"\geometry{margin=1in}",
            ""
        ])
        
        # Title and metadata
        if 'title' in content:
            latex_parts.append(rf"\title{{{self._escape_latex(content['title'])}}}")
        
        if 'metadata' in content:
            meta = content['metadata']
            if 'authors' in meta:
                authors = r" \and ".join([self._escape_latex(a) for a in meta['authors']])
                latex_parts.append(rf"\author{{{authors}}}")
            if 'date' in meta:
                latex_parts.append(rf"\date{{{self._escape_latex(meta['date'])}}}")
        
        # Begin document
        latex_parts.extend([
            "",
            r"\begin{document}",
            ""
        ])
        
        # Title page
        if include_cover:
            latex_parts.append(r"\maketitle")
            if template == 'thesis':
                latex_parts.append(r"\newpage")
        
        # Table of contents
        if content.get('include_toc', True):
            latex_parts.append(r"\tableofcontents")
            latex_parts.append(r"\newpage")
        
        # Abstract
        if 'abstract' in content:
            latex_parts.extend([
                r"\begin{abstract}",
                self._escape_latex(content['abstract']),
                r"\end{abstract}",
                ""
            ])
        
        # Sections
        if 'sections' in content:
            for section in content['sections']:
                latex_parts.append(self._format_section(section))
        
        # Bibliography
        if bibliography:
            latex_parts.extend([
                "",
                r"\bibliographystyle{ieeetr}",
                r"\bibliography{references}"
            ])
        
        # End document
        latex_parts.append(r"\end{document}")
        
        return "\n".join(latex_parts)
    
    def _format_section(self, section: Dict) -> str:
        """Format a LaTeX section"""
        parts = []
        
        # Section title
        title = section.get('title', 'Untitled')
        level = section.get('level', 1)
        
        section_commands = {
            1: r"\section",
            2: r"\subsection",
            3: r"\subsubsection"
        }
        
        cmd = section_commands.get(level, r"\paragraph")
        parts.append(f"{cmd}{{{{self._escape_latex(title)}}}}")
        
        # Content
        if 'content' in section:
            parts.append(self._escape_latex(section['content']))
        
        # Equations
        if 'equation' in section:
            parts.extend([
                r"\begin{equation}",
                section['equation'],
                r"\end{equation}"
            ])
        
        # Tables
        if 'table' in section:
            parts.append(self._format_table(section['table']))
        
        # Figures
        if 'figure' in section:
            fig = section['figure']
            parts.extend([
                r"\begin{figure}[h]",
                r"\centering",
                rf"\includegraphics[width=0.8\textwidth]{{{{fig.get('path', '')}}}}",
                rf"\caption{{{{self._escape_latex(fig.get('caption', ''))}}}}",
                rf"\label{{fig:{{{{fig.get('label', 'figure')}}}}}}",
                r"\end{figure}"
            ])
        
        parts.append("")
        return "\n".join(parts)
    
    def _format_table(self, table_data: Dict) -> str:
        """Format a LaTeX table"""
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])
        
        if not headers or not rows:
            return ""
        
        num_cols = len(headers)
        
        parts = [
            r"\begin{table}[h]",
            r"\centering",
            rf"\begin{{tabular}}{{{'|c' * num_cols}|}}",
            r"\hline"
        ]
        
        # Headers
        header_str = " & ".join([self._escape_latex(h) for h in headers])
        parts.append(rf"{header_str} \\ ")
        parts.append(r"\hline")
        
        # Rows
        for row in rows:
            if isinstance(row, dict):
                row_values = [str(row.get(h, '')) for h in headers]
            else:
                row_values = [str(v) for v in row]
            
            row_str = " & ".join([self._escape_latex(v) for v in row_values])
            parts.append(rf"{row_str} \\ ")
        
        parts.extend([
            r"\hline",
            r"\end{tabular}",
            rf"\caption{{{{table_data.get('caption', 'Table')}}}}",
            r"\end{table}"
        ])
        
        return "\n".join(parts)
    
    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters"""
        if not isinstance(text, str):
            text = str(text)
        
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\^{}',
            '\\': r'\textbackslash{}'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    async def _compile_to_pdf(self, latex_source: str) -> str:
        """Compile LaTeX source to PDF using pdflatex"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Write LaTeX source
            tex_file = tmpdir_path / "document.tex"
            tex_file.write_text(latex_source, encoding='utf-8')
            
            # Run pdflatex
            try:
                result = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', 'document.tex'],
                    cwd=tmpdir_path,
                    capture_output=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    logger.error(f"pdflatex error: {result.stderr.decode()}")
                    raise RuntimeError("LaTeX compilation failed")
                
                # Run twice for references
                subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', 'document.tex'],
                    cwd=tmpdir_path,
                    capture_output=True,
                    timeout=30
                )
                
                # Copy PDF to output
                pdf_file = tmpdir_path / "document.pdf"
                if pdf_file.exists():
                    output_path = Path.cwd() / "output" / "document.pdf"
                    output_path.parent.mkdir(exist_ok=True)
                    
                    import shutil
                    shutil.copy(pdf_file, output_path)
                    
                    logger.info(f"✅ PDF compiled: {output_path}")
                    return str(output_path)
                else:
                    raise RuntimeError("PDF file not generated")
                    
            except FileNotFoundError:
                raise RuntimeError("pdflatex not found. Install TeX Live or MiKTeX.")
            except subprocess.TimeoutExpired:
                raise RuntimeError("LaTeX compilation timed out")
