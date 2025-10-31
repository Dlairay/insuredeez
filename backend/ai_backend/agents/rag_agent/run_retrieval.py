"""
Taxonomy Condition Filling Pipeline
Fills taxonomy conditions using embedded policy documents from ChromaDB

PREREQUISITE: Run 'python embed_policies.py' first to embed the policy documents
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.rag_agent.retrieval import create_taxonomy_filler


def main():
    """Main execution function"""
    print("\n" + "="*70)
    print("TAXONOMY CONDITION FILLING PIPELINE")
    print("="*70)

    # Step 1: Check if policies are embedded
    print("\nStep 1: Checking policy embeddings...")

    chroma_db_path = Path(__file__).parent / "chroma_db"

    if not chroma_db_path.exists():
        print("\n" + "="*70)
        print("✗ ERROR: ChromaDB not found!")
        print("="*70)
        print("\nYou must run the embedding process first:")
        print("  python embed_policies.py")
        print("\nThis will create the ChromaDB vector store needed for retrieval.")
        return

    print("✓ ChromaDB found. Policies are embedded.")

    # Step 2: Ask about overwrite behavior (will be set per-layer later if needed)
    overwrite = False  # Default off

    # Step 2b: Ask about verbose mode
    print("\n" + "-"*70)
    print("Verbose/Debug Mode:")
    print("  • OFF (default): Show only results")
    print("  • ON: Show detailed debug info (queries, context, Gemini responses)")
    print("-"*70)
    verbose_input = input("Enable verbose mode? (y/N): ").strip().lower()
    verbose = verbose_input == 'y'

    # Step 3: Initialize the taxonomy filler
    print("\nStep 3: Initializing Taxonomy Condition Filler...")

    try:
        filler = create_taxonomy_filler()
        filler.overwrite = overwrite
        filler.verbose = verbose
        print(f"✓ Taxonomy loaded from: {filler.taxonomy_path}")
        print(f"✓ Output will be saved to: {filler.output_path}")
        print(f"✓ Overwrite mode: {'ON' if overwrite else 'OFF'}")
        print(f"✓ Verbose mode: {'ON' if verbose else 'OFF'}")

    except Exception as e:
        print(f"✗ Error initializing filler: {e}")
        return

    # Step 4: Ask user what to do
    print("\n" + "-"*70)
    print("Choose an option:")
    print("1. Fill all layers (full pipeline)")
    print("2. Fill specific layer")
    print("3. Fill specific conditions")
    print("4. Test with a few conditions")
    print("-"*70)

    choice = input("Enter choice (1-4): ").strip()

    if choice == "1":
        # Fill all layers
        print("\nStarting full pipeline - this may take a while...")

        # Ask about overwrite for all layers
        print("\n" + "-"*70)
        print("Overwrite Mode:")
        print("  • OFF (default): Skip layers that are already filled")
        print("  • ON: Re-process all layers, even if already filled")
        print("-"*70)
        overwrite_input = input("Enable overwrite mode for all layers? (y/N): ").strip().lower()
        overwrite = overwrite_input == 'y'
        filler.overwrite = overwrite

        confirm = input("\nContinue? (y/n): ").strip().lower()

        if confirm == 'y':
            filler.fill_all_layers()
        else:
            print("Cancelled.")

    elif choice == "2":
        # Fill specific layer
        layers = list(filler.taxonomy["layers"].keys())
        print("\nAvailable layers:")
        for i, layer in enumerate(layers, 1):
            print(f"  {i}. {layer}")

        layer_idx = int(input("\nEnter layer number: ").strip()) - 1

        if 0 <= layer_idx < len(layers):
            layer_name = layers[layer_idx]

            # Ask about overwrite for this specific layer
            print("\n" + "-"*70)
            print("Overwrite Mode for this layer:")
            print("  • OFF (default): Skip conditions that are already filled")
            print("  • ON: Re-process all conditions in this layer")
            print("-"*70)
            overwrite_input = input(f"Enable overwrite mode for {layer_name}? (y/N): ").strip().lower()
            filler.overwrite = overwrite_input == 'y'

            filler.fill_layer(layer_name)
            filler.save_taxonomy()
            print(f"\n✓ Layer '{layer_name}' completed!")
        else:
            print("Invalid layer number")

    elif choice == "3":
        # Fill specific conditions
        layers = list(filler.taxonomy["layers"].keys())
        print("\nAvailable layers:")
        for i, layer in enumerate(layers, 1):
            print(f"  {i}. {layer}")

        layer_idx = int(input("\nEnter layer number: ").strip()) - 1

        if 0 <= layer_idx < len(layers):
            layer_name = layers[layer_idx]
            layer_conditions = filler.taxonomy["layers"][layer_name]

            print(f"\nConditions in {layer_name}:")
            for i, cond in enumerate(layer_conditions, 1):
                print(f"  {i}. {cond['condition']}")

            condition_indices = input("\nEnter condition numbers (comma-separated): ").strip()
            indices = [int(x.strip()) - 1 for x in condition_indices.split(",")]

            condition_names = [
                layer_conditions[i]["condition"]
                for i in indices
                if 0 <= i < len(layer_conditions)
            ]

            if condition_names:
                filler.fill_specific_conditions(layer_name, condition_names)
                print(f"\n✓ Conditions filled!")
            else:
                print("No valid conditions selected")
        else:
            print("Invalid layer number")

    elif choice == "4":
        # Test mode - fill first 3 conditions of first layer
        print("\nTest Mode: Filling first 3 conditions from first layer...")

        first_layer = list(filler.taxonomy["layers"].keys())[0]
        test_conditions = filler.taxonomy["layers"][first_layer][:3]
        test_condition_names = [c["condition"] for c in test_conditions]

        print(f"Testing with: {test_condition_names}")

        filler.fill_specific_conditions(first_layer, test_condition_names)
        print(f"\n✓ Test completed!")

    else:
        print("Invalid choice")

    print("\n" + "="*70)
    print("Pipeline execution completed!")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
