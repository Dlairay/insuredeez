"""
Needs Extraction Agent
Analyzes user itinerary and extracts insurance coverage needs
"""

import json
import os
from typing import Dict, List
from dotenv import load_dotenv
import google.generativeai as genai

from .tools import TaxonomyLoader, ItineraryParser
from .prompt import NEEDS_EXTRACTION_PROMPT

load_dotenv()


class NeedsExtractionAgent:
    """
    Agent that extracts insurance coverage needs from travel itineraries.
    Uses taxonomy-grounded tagging to identify relevant coverage needs.
    """

    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize the Needs Extraction Agent

        Args:
            model_name: Gemini model to use for extraction
        """
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.3,  # Slightly creative for need identification
                "response_mime_type": "application/json"
            }
        )

        # Initialize taxonomy loader
        self.taxonomy_loader = TaxonomyLoader()

    def extract_needs(self, itinerary: str, verbose: bool = False) -> Dict:
        """
        Extract coverage needs from itinerary

        Args:
            itinerary: Human-written travel itinerary text
            verbose: If True, print detailed extraction info

        Returns:
            Dictionary with coverage needs profile
        """
        if verbose:
            print("="*70)
            print("NEEDS EXTRACTION AGENT")
            print("="*70)
            print(f"\nItinerary length: {len(itinerary)} characters")

        # Step 1: Get taxonomy tags
        taxonomy = self.taxonomy_loader.get_all_tags()

        # Format taxonomy for prompt
        layer_1_str = ", ".join(taxonomy['layer_1'])
        layer_2_str = ", ".join(taxonomy['layer_2'])
        layer_3_str = ", ".join(taxonomy['layer_3'])

        # Step 2: Build extraction prompt
        prompt = NEEDS_EXTRACTION_PROMPT.format(
            layer_1_conditions=layer_1_str,
            layer_2_benefits=layer_2_str,
            layer_3_conditions=layer_3_str,
            itinerary=itinerary
        )

        if verbose:
            print("\nCalling Gemini for needs extraction...")

        # Step 3: Call Gemini
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)

            if verbose:
                print(f"\n✓ Extraction completed")
                print(f"  Found {len(result.get('coverage_needs', []))} coverage needs")

            # Step 4: Validate taxonomy tags
            all_tags = []
            for need in result.get('coverage_needs', []):
                all_tags.extend(need.get('taxonomy_tags', []))

            valid_tags, invalid_tags = self.taxonomy_loader.validate_tags(all_tags)

            if invalid_tags and verbose:
                print(f"\n⚠ Warning: {len(invalid_tags)} invalid tags detected:")
                for tag in invalid_tags[:5]:
                    print(f"    - {tag}")

            # Add validation info to result
            result['_metadata'] = {
                'total_tags': len(all_tags),
                'valid_tags': len(valid_tags),
                'invalid_tags': len(invalid_tags),
                'model_used': self.model.model_name
            }

            return result

        except Exception as e:
            print(f"✗ Error during extraction: {str(e)}")
            return {
                'coverage_needs': [],
                'trip_summary': {},
                'error': str(e)
            }

    def extract_needs_with_keyword_boost(self, itinerary: str, verbose: bool = False) -> Dict:
        """
        Extract needs with additional keyword-based detection for higher recall

        Args:
            itinerary: Travel itinerary text
            verbose: Print debug info

        Returns:
            Coverage needs profile with both LLM and keyword-based detection
        """
        if verbose:
            print("\n" + "="*70)
            print("HYBRID EXTRACTION (LLM + Keywords)")
            print("="*70)

        # Step 1: LLM-based extraction
        llm_result = self.extract_needs(itinerary, verbose=verbose)

        # Step 2: Keyword-based detection
        detected_risks = ItineraryParser.detect_risk_factors(itinerary)

        if verbose and detected_risks:
            print(f"\n✓ Keyword detection found {len(detected_risks)} risk factors:")
            for risk in detected_risks[:10]:
                print(f"    - {risk}")

        # Step 3: Map detected keywords to taxonomy tags
        keyword_mapping = ItineraryParser.extract_activities_keywords()
        keyword_needs = []

        for risk_keyword in detected_risks:
            related_tags = keyword_mapping.get(risk_keyword, [])
            if related_tags:
                keyword_needs.append({
                    "need_category": "auto_detected",
                    "taxonomy_tags": related_tags,
                    "reasoning": f"Detected from keyword: '{risk_keyword}' in itinerary",
                    "priority": "MEDIUM",
                    "itinerary_evidence": f"Keyword match: {risk_keyword}",
                    "source": "keyword_detection"
                })

        # Step 4: Merge LLM and keyword results (deduplicate)
        existing_tags = set()
        for need in llm_result.get('coverage_needs', []):
            existing_tags.update(need.get('taxonomy_tags', []))

        # Only add keyword needs with new tags
        for kw_need in keyword_needs:
            new_tags = [t for t in kw_need['taxonomy_tags'] if t not in existing_tags]
            if new_tags:
                kw_need['taxonomy_tags'] = new_tags
                llm_result['coverage_needs'].append(kw_need)
                existing_tags.update(new_tags)

        # Update metadata
        if '_metadata' in llm_result:
            llm_result['_metadata']['keyword_boost_enabled'] = True
            llm_result['_metadata']['keyword_detected_risks'] = detected_risks
            llm_result['_metadata']['total_needs'] = len(llm_result['coverage_needs'])

        return llm_result

    def format_needs_report(self, needs_result: Dict) -> str:
        """
        Format extraction result into human-readable report

        Args:
            needs_result: Result from extract_needs()

        Returns:
            Formatted string report
        """
        report = []
        report.append("="*70)
        report.append("COVERAGE NEEDS EXTRACTION REPORT")
        report.append("="*70)

        # Trip summary
        trip_summary = needs_result.get('trip_summary', {})
        if trip_summary:
            report.append("\nTRIP SUMMARY:")
            report.append(f"  Destinations: {', '.join(trip_summary.get('destinations', ['N/A']))}")
            report.append(f"  Duration: {trip_summary.get('duration_days', 'N/A')} days")
            report.append(f"  Activities: {', '.join(trip_summary.get('activities', ['N/A']))}")
            report.append(f"  Risk Factors: {', '.join(trip_summary.get('risk_factors', ['None identified']))}")

        # Coverage needs
        coverage_needs = needs_result.get('coverage_needs', [])
        report.append(f"\nIDENTIFIED COVERAGE NEEDS: {len(coverage_needs)}")
        report.append("-"*70)

        # Group by priority
        high_priority = [n for n in coverage_needs if n.get('priority') == 'HIGH']
        medium_priority = [n for n in coverage_needs if n.get('priority') == 'MEDIUM']
        low_priority = [n for n in coverage_needs if n.get('priority') == 'LOW']

        for priority_name, needs in [("HIGH PRIORITY", high_priority),
                                       ("MEDIUM PRIORITY", medium_priority),
                                       ("LOW PRIORITY", low_priority)]:
            if needs:
                report.append(f"\n{priority_name}:")
                for i, need in enumerate(needs, 1):
                    report.append(f"\n  [{i}] Category: {need.get('need_category', 'N/A')}")
                    report.append(f"      Tags: {', '.join(need.get('taxonomy_tags', []))}")
                    report.append(f"      Reason: {need.get('reasoning', 'N/A')}")
                    if need.get('itinerary_evidence'):
                        evidence = need['itinerary_evidence']
                        if len(evidence) > 100:
                            evidence = evidence[:100] + "..."
                        report.append(f"      Evidence: {evidence}")

        # Metadata
        metadata = needs_result.get('_metadata', {})
        if metadata:
            report.append("\n" + "-"*70)
            report.append("EXTRACTION METADATA:")
            report.append(f"  Total taxonomy tags: {metadata.get('total_tags', 0)}")
            report.append(f"  Valid tags: {metadata.get('valid_tags', 0)}")
            report.append(f"  Invalid tags: {metadata.get('invalid_tags', 0)}")
            report.append(f"  Model used: {metadata.get('model_used', 'N/A')}")

        report.append("="*70)

        return "\n".join(report)
