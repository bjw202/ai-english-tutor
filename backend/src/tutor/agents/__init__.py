"""
AI English Tutor Agents Package.

This package contains all agent nodes for the LangGraph workflow:
- supervisor: Routes tasks based on task_type
- reading: Reading comprehension analysis (Claude Sonnet)
- grammar: Grammar analysis (GPT-4o)
- vocabulary: Vocabulary extraction (Claude Haiku)
- image_processor: Text extraction from images
- aggregator: Combines all tutor agent results
"""

from tutor.agents.aggregator import aggregator_node
from tutor.agents.grammar import grammar_node
from tutor.agents.image_processor import image_processor_node
from tutor.agents.reading import reading_node
from tutor.agents.supervisor import supervisor_node
from tutor.agents.vocabulary import vocabulary_node

__all__ = [
    "supervisor_node",
    "reading_node",
    "grammar_node",
    "vocabulary_node",
    "image_processor_node",
    "aggregator_node",
]
