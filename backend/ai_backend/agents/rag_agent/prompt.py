"""
Prompts for RAG Agent
Contains system prompts and templates for policy retrieval and Q&A
"""

# System prompt for policy Q&A with RAG context
POLICY_QA_SYSTEM_PROMPT = """You are a helpful insurance policy assistant. Your role is to answer questions about insurance policies accurately and clearly based on the provided policy documents.

Guidelines:
1. Base your answers strictly on the provided policy context
2. If the context doesn't contain enough information, say so clearly
3. Cite the specific policy document and page when providing information
4. Use clear, plain language to explain complex policy terms
5. If there are conditions or exclusions, highlight them clearly
6. Never make assumptions about coverage that isn't explicitly stated

Context from policy documents:
{context}

Question: {question}

Please provide a clear, accurate answer based on the policy context above."""


# Prompt template for policy summarization
POLICY_SUMMARY_PROMPT = """Based on the following excerpts from the policy document "{policy_name}", provide a concise summary of the key information:

{context}

Summary:"""


# Prompt for coverage verification
COVERAGE_CHECK_PROMPT = """You are analyzing insurance policy documents to determine coverage.

Policy Context:
{context}

Scenario: {scenario}

Based on the policy information provided, determine:
1. Is this scenario covered? (Yes/No/Unclear)
2. What are the relevant policy sections?
3. Are there any conditions or exclusions that apply?
4. What is the coverage limit if applicable?

Provide a structured response with clear reasoning."""


# Prompt for policy comparison
POLICY_COMPARISON_PROMPT = """Compare the following aspects across the provided policy documents:

Policies being compared: {policy_names}

Context from policies:
{context}

Comparison criteria: {criteria}

Please provide a clear comparison highlighting similarities and differences."""


# Prompt for extracting specific policy details
DETAIL_EXTRACTION_PROMPT = """Extract the following specific details from the policy documents:

{context}

Details to extract:
{details_list}

Provide the information in a structured format with source citations."""


def format_policy_qa_prompt(context: str, question: str) -> str:
    """
    Format a policy Q&A prompt with context and question.

    Args:
        context: Retrieved context from policy documents
        question: User's question

    Returns:
        Formatted prompt string
    """
    return POLICY_QA_SYSTEM_PROMPT.format(context=context, question=question)


def format_policy_summary_prompt(policy_name: str, context: str) -> str:
    """
    Format a policy summarization prompt.

    Args:
        policy_name: Name of the policy document
        context: Retrieved context from the policy

    Returns:
        Formatted prompt string
    """
    return POLICY_SUMMARY_PROMPT.format(policy_name=policy_name, context=context)


def format_coverage_check_prompt(context: str, scenario: str) -> str:
    """
    Format a coverage verification prompt.

    Args:
        context: Retrieved policy context
        scenario: Coverage scenario to check

    Returns:
        Formatted prompt string
    """
    return COVERAGE_CHECK_PROMPT.format(context=context, scenario=scenario)


def format_policy_comparison_prompt(
    policy_names: str,
    context: str,
    criteria: str
) -> str:
    """
    Format a policy comparison prompt.

    Args:
        policy_names: Names of policies being compared
        context: Combined context from all policies
        criteria: What to compare

    Returns:
        Formatted prompt string
    """
    return POLICY_COMPARISON_PROMPT.format(
        policy_names=policy_names,
        context=context,
        criteria=criteria
    )


def format_detail_extraction_prompt(context: str, details_list: str) -> str:
    """
    Format a detail extraction prompt.

    Args:
        context: Retrieved policy context
        details_list: List of details to extract

    Returns:
        Formatted prompt string
    """
    return DETAIL_EXTRACTION_PROMPT.format(
        context=context,
        details_list=details_list
    )
