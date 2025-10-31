"""
RAG Agent Package for Policy Document Retrieval and Taxonomy Filling
"""

from .agent import RAGAgent, create_rag_agent
from .tools import PolicyRAGPipeline, initialize_rag_pipeline
from .prompt import (
    format_policy_qa_prompt,
    format_policy_summary_prompt,
    format_coverage_check_prompt,
    format_policy_comparison_prompt,
    format_detail_extraction_prompt
)
from .retrieval import TaxonomyConditionFiller, create_taxonomy_filler

__all__ = [
    "RAGAgent",
    "create_rag_agent",
    "PolicyRAGPipeline",
    "initialize_rag_pipeline",
    "TaxonomyConditionFiller",
    "create_taxonomy_filler",
    "format_policy_qa_prompt",
    "format_policy_summary_prompt",
    "format_coverage_check_prompt",
    "format_policy_comparison_prompt",
    "format_detail_extraction_prompt",
]
