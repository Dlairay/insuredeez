import json
import pprint
import os

def collect_conditions(node, condition_key, store):
    """Recursively collect values for condition_key into store set."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == condition_key:
                store.add(v)
            else:
                collect_conditions(v, condition_key, store)
    elif isinstance(node, list):
        for item in node:
            collect_conditions(item, condition_key, store)


with open("Taxonomy_Hackathon.json", "r") as f:
    taxonomy = json.load(f)

layers = taxonomy.get("layers", {})

result = {}

# Layer 1: only `condition` fields
layer1_conditions = set()
collect_conditions(layers.get("layer_1_general_conditions", []), "condition", layer1_conditions)
result["layer_1_general_conditions"] = sorted(layer1_conditions)

# Layer 2: benefits, key name is `benefit_name`
layer2_conditions = set()
collect_conditions(layers.get("layer_2_benefits", []), "benefit_name", layer2_conditions)
result["layer_2_benefits"] = sorted(layer2_conditions)

# Layer 3: benefit-specific conditions (key is again `condition`)
layer3_conditions = set()
collect_conditions(layers.get("layer_3_benefit_specific_conditions", []), "condition", layer3_conditions)
result["layer_3_benefit_specific_conditions"] = sorted(layer3_conditions)

# Print results
pprint.pprint(result)

# Save the dictionary as a python object in a .py file (writes a module with variable `result`)
out_path = os.path.join(os.path.dirname(__file__), "taxonomy_conditions_data.py")
with open(out_path, "w") as out:
    out.write("result = " + pprint.pformat(result) + "\n")
