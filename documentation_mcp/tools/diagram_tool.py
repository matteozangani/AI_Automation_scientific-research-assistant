# Diagram Generation Tool

This Python module provides functionality to generate diagrams using Mermaid syntax, utilizing LLM-powered generation.

## Supported Diagram Types
1. **Flowchart**: Create flowcharts for process visualization.
2. **Sequence Diagram**: Illustrate interactions in systems.
3. **Architecture Diagram**: Visualize system architecture effectively.
4. **Gantt Diagram**: Timeline-based representation of tasks.
5. **Class Diagram**: Class-based representations to aid understanding of object-oriented design.
6. **ER Diagram**: Entity-Relationship diagrams for data modeling.
7. **State Diagram**: Representation of state machines and transitions.

## Usage
To use the diagram generation tool, import the module and call the desired diagram generation function with the necessary parameters.

Example:
```python
from diagram_tool import DiagramGenerator

dg = DiagramGenerator()  # Initialize the generator

# Generate a flowchart
flowchart_code = dg.generate_flowchart_code('Start -> Step1 -> Step2 -> End')
print(flowchart_code)
```

## Requirements
- Ensure you have Python installed.
- Mermaid.js for rendering the diagrams.

## Conclusion
This tool integrates seamlessly with other automation scripts and enhances documentation through visual aids. Future enhancements may include more diagram types and customization options.