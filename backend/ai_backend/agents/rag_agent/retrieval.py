"""
Retrieval Pipeline for Taxonomy Condition Filling
Uses RAG embeddings to iteratively fill conditions in Taxonomy_Hackathon.json
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv
import google.generativeai as genai
import ray
from .agent import RAGAgent

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Ray remote function for parallel processing
@ray.remote
def extract_condition_remote(chroma_db_path: str, policy_mapping: Dict,
                             condition: Dict, product_name: str,
                             policy_filename: str, model_name: str, verbose: bool) -> Dict:
    """
    Ray remote function to extract a single condition.
    Initializes its own RAG agent and Gemini model to avoid serialization issues.
    """
    # Add parent directory to sys.path for imports
    import sys
    from pathlib import Path
    parent_dir = str(Path(__file__).parent.parent.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Re-initialize RAG agent in this worker
    from agents.rag_agent.agent import RAGAgent
    import google.generativeai as genai

    rag_agent = RAGAgent(chroma_db_path=chroma_db_path, auto_load=True)

    # Initialize Gemini model
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config={
            "temperature": 0,
            "response_mime_type": "application/json"
        }
    )

    # Extract condition name
    condition_name = condition.get("condition") or condition.get("benefit_name")
    condition_type = condition.get("condition_type", "")

    # Generate query (simplified semantic variation)
    query_parts = [condition_name.replace("_", " ")]
    if condition_type:
        query_parts.append(condition_type)
    query = " ".join(query_parts)

    # Retrieve context from RAG
    context_results = rag_agent.search_in_policy(policy_filename, query, k=8)

    if not context_results:
        return {
            "condition_exist": False,
            "original_text": "",
            "parameters": {}
        }

    # Format context
    context = "\n\n---\n\n".join([
        f"[Page {r['page']}]\n{r['content']}"
        for r in context_results
    ])

    # Build extraction prompt (simplified version)
    prompt = f"""You are an insurance policy extraction expert.

TASK: Extract information about "{condition_name}" from the policy text below.

POLICY CONTEXT:
{context}

OUTPUT SCHEMA - Return valid JSON:
{{
    "condition_exist": boolean,
    "original_text": string,
    "parameters": object
}}

Extract the information and return ONLY the JSON."""

    # Call Gemini
    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        return result
    except Exception as e:
        return {
            "condition_exist": False,
            "original_text": "",
            "parameters": {}
        }


class TaxonomyConditionFiller:
    """
    Fills taxonomy conditions by retrieving relevant policy information
    from embedded documents using RAG pipeline.
    """

    def __init__(
        self,
        taxonomy_path: str,
        output_path: str = None,
        model_name: str = "gemini-2.5-flash",
        overwrite: bool = False,
        verbose: bool = False,
        max_workers: int = 5
    ):
        """
        Initialize the taxonomy condition filler.

        Args:
            taxonomy_path: Path to source Taxonomy_Hackathon.json
            output_path: Path to save filled taxonomy (defaults to rag_agent folder)
            model_name: Gemini model to use for extraction (default: gemini-2.5-flash)
            overwrite: If False, skip layers that are already filled (default: False)
            verbose: If True, show detailed debug information (default: False)
            max_workers: Max parallel workers for batch processing (default: 5)
        """
        self.taxonomy_path = Path(taxonomy_path)
        self.overwrite = overwrite
        self.verbose = verbose
        self.max_workers = max_workers

        # Default output path in rag_agent folder
        if output_path is None:
            output_path = Path(__file__).parent / "Taxonomy_Filled.json"
        self.output_path = Path(output_path)

        # Initialize RAG agent
        self.rag_agent = RAGAgent(auto_load=True)

        # Initialize Gemini model with JSON mode for structured output
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0,
                "response_mime_type": "application/json"
            }
        )

        # Load taxonomy
        self.taxonomy = self._load_taxonomy()

        # Map policy files to product names
        self.policy_mapping = self._create_policy_mapping()

    def _load_taxonomy(self) -> Dict:
        """Load the taxonomy JSON file."""
        with open(self.taxonomy_path, 'r') as f:
            return json.load(f)

    def _create_policy_mapping(self) -> Dict[str, str]:
        """
        Map product names to policy filenames.

        Returns:
            Dictionary mapping product names to policy filenames
        """
        # Get available policies
        policies = self.rag_agent.get_available_policies()

        # Create mapping based on product names in taxonomy
        products = self.taxonomy.get("products", [])

        # Map Product A, B, C to actual policy files
        # Adjust this mapping based on your actual policy files
        mapping = {}

        # You can customize this mapping logic
        if len(policies) >= len(products):
            for i, product in enumerate(products):
                if i < len(policies):
                    mapping[product] = policies[i]

        print(f"Policy mapping created: {mapping}")
        return mapping

    def _generate_query_for_condition(self, condition: str, condition_type: str) -> str:
        """
        Generate a search query based on condition name and type.
        Uses multiple query variations to improve retrieval quality.

        Args:
            condition: Name of the condition (e.g., "age_eligibility")
            condition_type: Type of condition (e.g., "eligibility", "exclusion")

        Returns:
            Search query string
        """
        # Convert snake_case to readable text
        readable_condition = condition.replace('_', ' ').title()

        # Create semantic variations of the condition name for better matching
        semantic_variations = {
            "age_eligibility": "age eligibility minimum maximum years old insured person",
            "good_health": "health medical condition pre-existing fitness eligibility",
            "pre_existing_conditions": "pre-existing medical condition exclusion lookback period",
            "trip_start_singapore": "trip must begin start Singapore departure",
            "child_accompaniment_requirement": "child accompanied parent guardian age",
            "travel_advisory_exclusion": "travel advisory warning exclusion",
            "awareness_of_circumstances": "aware circumstances known event",
            "pre_trip_purchased": "purchase before trip departure commencement",
            "declaration_of_previous_insurance": "previous insurance declaration",
            "medical_advice_and_treatment_restriction": "medical advice treatment restriction travel"
        }

        # Get semantic variation if available, otherwise use readable condition
        base_query = semantic_variations.get(condition, readable_condition)

        # Combine with condition type for targeted retrieval
        query_templates = {
            "eligibility": f"{base_query} eligibility requirements conditions policy",
            "exclusion": f"{base_query} exclusion limitation not covered policy",
            "coverage": f"{base_query} coverage benefits what is covered policy",
            "limit": f"{base_query} limit maximum amount benefits policy",
        }

        return query_templates.get(
            condition_type,
            f"{base_query} policy conditions"
        )

    def _extract_condition_info(
        self,
        condition_name: str,
        condition_type: str,
        policy_context: str,
        product_name: str
    ) -> Dict[str, Any]:
        """
        Use Gemini to extract structured condition information from policy context.

        Args:
            condition_name: Name of the condition
            condition_type: Type of condition
            policy_context: Retrieved context from policy documents
            product_name: Name of the product/policy

        Returns:
            Dictionary with condition_exist, original_text, and parameters
        """
        prompt = f"""You are an intelligent insurance policy analyzer with expertise in understanding insurance terminology and concepts.

TASK: Analyze the policy to find information about "{condition_name.replace('_', ' ').title()}" (condition type: {condition_type})

Product/Policy: {product_name}

POLICY CONTEXT (Retrieved from semantic search):
{policy_context}

IMPORTANT NOTE ON TABLES:
The policy context may contain tables in HTML format (e.g., <table><tr><td>...</td></tr></table>).
These tables contain structured information about coverage limits, benefits, and plan details.
When you see HTML tables, parse them carefully to extract plan-specific values and map them correctly.

---

YOUR ROLE:
You are analyzing an insurance policy to extract specific condition information. Use your knowledge of insurance terminology and concepts to:
1. Understand what the condition "{condition_name}" means in insurance context
2. Find SEMANTICALLY RELATED information in the policy, even if exact wording differs
3. Map policy language to the requested condition intelligently

UNDERSTANDING THE CONDITION:
- Condition name: "{condition_name.replace('_', ' ').title()}"
- Condition type: {condition_type}
- Use your insurance knowledge to understand what this condition typically means
- Look for related concepts, synonyms, and insurance-standard terms
- Consider how policies typically express this type of requirement

INTELLIGENCE GUIDELINES:
- BE SMART: If the condition is "good_health", recognize terms like "medical condition", "pre-existing condition", "health declaration", "fitness", etc.
- BE FLEXIBLE: Different policies use different wording - "must be" vs "required to be" vs "shall be" all mean the same thing
- BE CONTEXTUAL: A condition about "age" might be expressed as "eligibility age", "covered age range", "insurable age", etc.
- BE INFERENTIAL: If you see information that clearly relates to the condition, extract it even if not explicitly labeled

SEMANTIC MATCHING EXAMPLES:
- "good_health" → "no pre-existing conditions", "medically fit", "health requirements", "medical history"
- "age_eligibility" → "age limits", "eligible ages", "age range", "minimum/maximum age"
- "coverage_duration" → "policy period", "term", "coverage term", "duration of coverage"
- "geographical_coverage" → "territorial limits", "covered regions", "area of coverage"

OUTPUT SCHEMA - Return valid JSON:
{{
    "condition_exist": boolean,
    "original_text": string,
    "parameters": object
}}

FIELD REQUIREMENTS:

1. "condition_exist" (boolean):
   - true: If you find ANY information in the policy context that relates to this condition
   - Think broadly: related concepts, synonyms, insurance-standard terms
   - If the policy addresses this aspect of coverage, mark as true
   - false: Only if the policy context has NO relevant information at all

2. "original_text" (string):
   - Extract the EXACT verbatim text from the policy that relates to this condition
   - **KEEP IT CONCISE**: Extract only the most relevant 1-3 sentences
   - Do NOT include entire sections, tables, or supplementary information
   - Focus on the core requirement/condition statement
   - If there are multiple relevant statements, prioritize the primary definition
   - Preserve the original wording exactly as written
   - Empty string "" only if condition_exist is false

3. "parameters" (object):
   - Extract quantifiable values directly related to THE CONDITION
   - For eligibility/exclusion conditions: Extract criteria (age ranges, time periods, requirements)
   - For coverage/benefit conditions: Extract coverage limits and plan-specific amounts
   - When parsing HTML tables:
     * Extract plan names (e.g., "Standard Plan", "Elite Plan", "Premier Plan")
     * Extract corresponding values for each plan
     * Use descriptive keys like "standard_plan_limit", "elite_plan_limit"
   - Use clear, descriptive keys (e.g., "minimum_age", "lookback_period", "coverage_limit")
   - Preserve units and formats (e.g., "18 years", "90 days", "$75,000")
   - Empty object {{}} if no quantifiable values found

EXAMPLES:

Example 1 - Smart matching:
Condition: "good_health"
Policy text: "You must not have been diagnosed with any medical condition in the past 12 months"
Output:
{{
    "condition_exist": true,
    "original_text": "You must not have been diagnosed with any medical condition in the past 12 months",
    "parameters": {{
        "lookback_period": "12 months",
        "requirement": "no medical conditions diagnosed"
    }}
}}

Example 2 - Flexible interpretation:
Condition: "age_eligibility"
Policy text: "Coverage is available for individuals aged 21 to 70"
Output:
{{
    "condition_exist": true,
    "original_text": "Coverage is available for individuals aged 21 to 70",
    "parameters": {{
        "minimum_age": "21 years",
        "maximum_age": "70 years"
    }}
}}

Example 3 - Truly not found:
Condition: "scuba_diving_coverage"
Policy text: (context about age and health, nothing about activities)
Output:
{{
    "condition_exist": false,
    "original_text": "",
    "parameters": {{}}
}}

---

IMPORTANT REMINDERS:
- Use your intelligence and insurance expertise
- Think semantically, not just literally
- Different policies express the same concepts differently
- Extract exact text, but be smart about recognizing relevance
- Return ONLY valid JSON, no additional text

Now analyze the policy context and extract information for the condition:"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            if self.verbose:
                print(f"    [DEBUG] Gemini raw response:\n{response_text}\n")

            # Since we set response_mime_type to application/json,
            # the response should already be clean JSON
            result = json.loads(response_text)

            # Validate schema
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")

            if "condition_exist" not in result:
                raise ValueError("Missing 'condition_exist' field")

            if "original_text" not in result:
                raise ValueError("Missing 'original_text' field")

            if "parameters" not in result:
                raise ValueError("Missing 'parameters' field")

            # Ensure proper types
            result["condition_exist"] = bool(result["condition_exist"])
            result["original_text"] = str(result["original_text"])
            if not isinstance(result["parameters"], dict):
                result["parameters"] = {}

            if self.verbose:
                print(f"    [DEBUG] Parsed result: condition_exist={result['condition_exist']}, "
                      f"params={result['parameters']}")

            return result

        except json.JSONDecodeError as e:
            print(f"  ✗ JSON parsing error: {e}")
            print(f"  Response text: {response_text[:200]}...")
            return {
                "condition_exist": False,
                "original_text": "",
                "parameters": {}
            }
        except Exception as e:
            print(f"  ✗ Error extracting condition info: {e}")
            return {
                "condition_exist": False,
                "original_text": "",
                "parameters": {}
            }

    def _fill_condition_for_product(
        self,
        condition: Dict,
        product_name: str,
        policy_filename: str
    ) -> Dict[str, Any]:
        """
        Fill a single condition for a specific product using RAG retrieval.

        Args:
            condition: Condition dictionary from taxonomy
            product_name: Name of the product
            policy_filename: Filename of the policy to search

        Returns:
            Updated product condition info
        """
        # Handle both "condition" (layer 1) and "benefit_name" (layer 2) structures
        condition_name = condition.get("condition") or condition.get("benefit_name")
        condition_type = condition.get("condition_type", "")

        # Generate query
        query = self._generate_query_for_condition(condition_name, condition_type)

        if self.verbose:
            print(f"\n    [DEBUG] Query: {query}")

        # Retrieve relevant context from specific policy
        try:
            results = self.rag_agent.search_in_policy(
                policy_filename,
                query,
                k=8  # Get top 8 relevant chunks for better coverage
            )

            if self.verbose:
                print(f"    [DEBUG] Retrieved {len(results)} chunks from policy")

            # Combine contexts
            policy_context = "\n\n---\n\n".join([
                f"[Page {r['page']}]\n{r['content']}"
                for r in results
            ])

            if self.verbose:
                context_preview = policy_context[:300] + "..." if len(policy_context) > 300 else policy_context
                print(f"    [DEBUG] Context preview:\n{context_preview}\n")

        except Exception as e:
            print(f"  ✗ Error retrieving context: {e}")
            policy_context = ""

        # Extract condition information using Gemini
        if policy_context:
            condition_info = self._extract_condition_info(
                condition_name,
                condition_type,
                policy_context,
                product_name
            )
        else:
            if self.verbose:
                print(f"    [DEBUG] No context retrieved - marking as not found")
            condition_info = {
                "condition_exist": False,
                "original_text": "",
                "parameters": {}
            }

        return condition_info

    def _is_layer_filled(self, layer_name: str) -> bool:
        """
        Check if a layer has already been filled with data.

        A layer is considered filled if at least one product in at least one condition
        has non-empty data (condition_exist is not None/False or has original_text).

        Args:
            layer_name: Name of the layer to check

        Returns:
            True if layer appears to be filled, False otherwise
        """
        layer = self.taxonomy["layers"].get(layer_name, [])

        if not layer:
            return False

        # Check if any condition in the layer has filled data
        for condition in layer:
            products = condition.get("products", {})
            for _product_name, product_info in products.items():
                # Check if this product has meaningful data
                if isinstance(product_info, dict):
                    condition_exist = product_info.get("condition_exist")
                    original_text = product_info.get("original_text", "")

                    # If condition_exist is explicitly set or has original_text, consider it filled
                    if condition_exist is not None or original_text:
                        return True

        return False

    def fill_layer(self, layer_name: str, force_overwrite: bool = None) -> None:
        """
        Fill all conditions in a specific layer using Ray for parallel batch processing.

        Args:
            layer_name: Name of the layer (e.g., "layer_1_general_conditions")
            force_overwrite: If provided, overrides the instance overwrite setting
        """
        # Determine whether to overwrite
        should_overwrite = force_overwrite if force_overwrite is not None else self.overwrite

        # Check if layer is already filled
        if not should_overwrite and self._is_layer_filled(layer_name):
            print(f"\n{'='*70}")
            print(f"⏭ Skipping Layer (already filled): {layer_name}")
            print(f"{'='*70}")
            print(f"Use overwrite=True to force re-fill this layer")
            return

        print(f"\n{'='*70}")
        print(f"Processing Layer: {layer_name}")
        print(f"{'='*70}")

        layer = self.taxonomy["layers"].get(layer_name, [])

        # Initialize Ray if not already initialized
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)

        # Prepare ALL tasks for batch processing
        all_tasks = []
        for i, condition in enumerate(layer):
            products = condition.get("products", {})
            for product_name in products.keys():
                policy_filename = self.policy_mapping.get(product_name)
                if policy_filename:
                    all_tasks.append((i, condition, product_name, policy_filename))

        if not all_tasks:
            print("No tasks to process")
            return

        print(f"\nBatch processing {len(all_tasks)} extractions using Ray")
        print(f"Processing up to {self.max_workers} API calls simultaneously\n")

        # Submit all tasks to Ray
        futures = []
        chroma_db_path = str(self.rag_agent.pipeline.chroma_db_path)

        for i, condition, product_name, policy_filename in all_tasks:
            future = extract_condition_remote.remote(
                chroma_db_path,
                self.policy_mapping,
                condition,
                product_name,
                policy_filename,
                self.model.model_name,
                self.verbose
            )
            futures.append((i, condition, product_name, future))

        # Collect results as they complete
        results = {}
        completed = 0

        for i, condition, product_name, future in futures:
            try:
                filled_info = ray.get(future)

                # Store result
                if i not in results:
                    results[i] = {}
                results[i][product_name] = filled_info

                completed += 1
                condition_name = condition.get("condition") or condition.get("benefit_name")
                exists = filled_info.get("condition_exist", False)
                status = "✓" if exists else "✗"

                print(f"[{completed}/{len(all_tasks)}] {status} {condition_name} - {product_name}")

            except Exception as e:
                print(f"  ✗ Error: {product_name} - {str(e)}")

        # Update taxonomy with all results
        print(f"\nUpdating taxonomy with {len(results)} conditions...")
        for condition_idx, product_results in results.items():
            condition = layer[condition_idx]
            products = condition.get("products", {})
            for product_name, filled_info in product_results.items():
                products[product_name] = filled_info

        # Save progress after layer completion
        self.save_taxonomy()
        print(f"✓ Layer saved to {self.output_path}")

    def fill_all_layers(self) -> None:
        """Fill all layers in the taxonomy."""
        print("\n" + "="*70)
        print("Starting Taxonomy Condition Filling")
        print("="*70)

        layers = self.taxonomy.get("layers", {})
        total_layers = len(layers)

        for idx, layer_name in enumerate(layers.keys(), 1):
            print(f"\nLayer {idx}/{total_layers}: {layer_name}")
            self.fill_layer(layer_name)

            # Save progress after each layer
            self.save_taxonomy()
            print(f"\n✓ Progress saved to {self.output_path}")

        print("\n" + "="*70)
        print("✓ All Layers Completed!")
        print(f"✓ Filled taxonomy saved to: {self.output_path}")
        print("="*70)

    def fill_specific_conditions(
        self,
        layer_name: str,
        condition_names: List[str]
    ) -> None:
        """
        Fill specific conditions in a layer.

        Args:
            layer_name: Name of the layer
            condition_names: List of condition names to fill
        """
        print(f"\nProcessing specific conditions in {layer_name}")

        layer = self.taxonomy["layers"].get(layer_name, [])

        for condition in layer:
            # Handle both "condition" (layer 1) and "benefit_name" (layer 2) structures
            cond_name = condition.get("condition") or condition.get("benefit_name")
            if cond_name in condition_names:
                condition_name = cond_name
                print(f"\nProcessing: {condition_name}")

                products = condition.get("products", {})
                for product_name in products.keys():
                    policy_filename = self.policy_mapping.get(product_name)

                    if policy_filename:
                        print(f"  → {product_name}")
                        filled_info = self._fill_condition_for_product(
                            condition,
                            product_name,
                            policy_filename
                        )
                        products[product_name] = filled_info

        self.save_taxonomy()
        print(f"\n✓ Saved to {self.output_path}")

    def save_taxonomy(self) -> None:
        """Save the filled taxonomy to output file."""
        with open(self.output_path, 'w') as f:
            json.dump(self.taxonomy, f, indent=2)

    def get_taxonomy(self) -> Dict:
        """Get the current taxonomy dictionary."""
        return self.taxonomy


def create_taxonomy_filler(
    taxonomy_path: str = None
) -> TaxonomyConditionFiller:
    """
    Factory function to create a TaxonomyConditionFiller.

    Args:
        taxonomy_path: Path to Taxonomy_Hackathon.json

    Returns:
        Initialized TaxonomyConditionFiller
    """
    if taxonomy_path is None:
        taxonomy_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "block_one",
            "Taxonomy_Hackathon.json"
        )

    return TaxonomyConditionFiller(taxonomy_path)
