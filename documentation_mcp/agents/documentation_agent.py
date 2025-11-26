"""
Documentation Agent with Reasoning and Quality Evaluation
Main orchestrator agent for document generation tasks
"""

import logging
import os
from typing import Dict, Any, List
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentationAgent:
    """
    Main agent for documentation tasks with reasoning capabilities
    Uses Claude for intelligent document planning and quality evaluation
    """
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0.3,
            api_key=api_key
        )
        
        self.tools = self._initialize_tools()