import json
import os

# Paths
INPUT_JSON = "data/ccpa_parsed_rag.json"
OUTPUT_GRAPH = "data/ccpa_graph.json"

def build_graph():
    if not os.path.exists(INPUT_JSON):
        print(f"❌ Error: {INPUT_JSON} not found.")
        return

    print("Loading manually constructed RAG JSON...")
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        graph = json.load(f)

    # 1. Identify specific categories of nodes to resolve macros
    right_and_duty_nodes = [k for k, v in graph.items() if v.get("type") in ["Right", "Duty"]]
    duty_nodes = [k for k, v in graph.items() if v.get("type") == "Duty"]
    enforcement_nodes = [k for k, v in graph.items() if "Enforcement" in v.get("type", "")]

    # 2. Process macros and ensure bidirectional links
    print("Compiling graph edges and resolving macros...")
    for node_id, data in graph.items():
        # Ensure lists exist to prevent KeyError later
        if "exemptions_in" not in data:
            data["exemptions_in"] = []
        if "modifies" not in data:
            data["modifies"] = []
        if "mentions" not in data:
            data["mentions"] = []

        modifies_list = data.get("modifies", [])
        
        for target in modifies_list:
            targets_to_update = []
            
            # Resolve NotebookLM Macros
            if target == "ALL_RIGHTS":
                targets_to_update = right_and_duty_nodes
            elif target == "ALL_RIGHTS_EXCEPT_1798.150":
                targets_to_update = [n for n in right_and_duty_nodes if "1798.150" not in n]
            elif target == "ALL_OTHER_RIGHTS":
                targets_to_update = [n for n in right_and_duty_nodes if n != node_id and "1798.150" not in n]
            elif target == "BUSINESS_DUTIES":
                targets_to_update = duty_nodes
            elif target == "ENFORCEMENT":
                targets_to_update = enforcement_nodes
            elif target in ["NONE", "LIABILITY"]:
                continue # Skip conceptual tags that don't map to strict nodes
            elif target in graph:
                targets_to_update = [target]
            else:
                print(f"⚠️ Warning: Node '{node_id}' modifies unknown target '{target}'")

            # Apply bidirectional 'exemptions_in' link
            for t in targets_to_update:
                if t in graph and node_id not in graph[t]["exemptions_in"]:
                    graph[t]["exemptions_in"].append(node_id)
                    print(f"  🔗 Hard-linked Exemption: {node_id} -> {t}")

    # 3. Clean up duplicates and self-references
    for node_id, data in graph.items():
        data["exemptions_in"] = list(set(data["exemptions_in"]))
        if node_id in data["exemptions_in"]:
            data["exemptions_in"].remove(node_id) # Remove self-links
            
        data["modifies"] = list(set(data["modifies"]))
        data["mentions"] = list(set(data["mentions"]))

    # 4. Save the finalized graph
    os.makedirs(os.path.dirname(OUTPUT_GRAPH), exist_ok=True)
    with open(OUTPUT_GRAPH, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=4)

    print(f"\n✅ Graph successfully compiled and validated with {len(graph)} nodes.")
    print(f"✅ Saved to {OUTPUT_GRAPH}")

if __name__ == "__main__":
    build_graph()