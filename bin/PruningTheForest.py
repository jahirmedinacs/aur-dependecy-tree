#!/usr/bin/env python3
import json

INPUT_JSON = "assets/IntermediateReports/UncutForest.json"
PRUNED_OUTPUT = "assets/IntermediateReports/PrunedForest.json"
FULL_TREE_OUTPUT = "assets/IntermediateReports/FullTree.json"

def build_nested_tree(forest, package, global_seen=None):
    """
    Recursively builds a nested dictionary representing a package's full dependency tree.
    Uses a single global 'seen' set per Root to prevent combinatorial explosion 
    and memory exhaustion when generating massive Arch Linux generic graphs.
    """
    if global_seen is None:
        global_seen = set()

    # If we've already mapped this dependency *anywhere* under this root tree, just list it as a string
    # instead of spawning a duplicate 500-node subgraph.
    if package in global_seen:
        return "[Already Mapped Above]"

    global_seen.add(package)

    deps = forest.get(package, [])
    if not deps:
        return {} # Leaf node

    tree = {}
    for dep in sorted(deps):
        tree[dep] = build_nested_tree(forest, dep, global_seen)
    return tree

def prune_forest():
    print("🪓 Chopping down the dependencies and mapping the Forest...")
    
    with open(INPUT_JSON, 'r') as f:
        forest = json.load(f)

    # Set A: Every package explicitly listed on the system
    all_packages = set(forest.keys())

    # Set B: Every package identified as a dependency by something else
    all_dependencies = set(dep for deps in forest.values() for dep in deps)

    # ---------------------------------------------------------
    # 1. Structure the Map (PrunedForest.json)
    # Every package listed exactly once, tagged with its status.
    # ---------------------------------------------------------
    pruned_forest = {}
    for pkg in sorted(list(all_packages)):
        # Important Logic Override: "if some child node is a root (parent) 
        # it preserves their root condition and should not be marked as dependecy"
        # Therefore, if the node has its own children, it is a tree itself -> it is a Root!
        has_children = len(forest.get(pkg, [])) > 0
        
        if has_children:
            # It's a parent/tree! Give it sovereign Root priority.
            is_dependency = False
        else:
            # It is a leaf node. It is only a dependency if something explicitly requires it.
            is_dependency = pkg in all_dependencies
        
        pruned_forest[pkg] = {
            "is_dependency": is_dependency,
            "dependencies": sorted(forest.get(pkg, []))
        }

    with open(PRUNED_OUTPUT, 'w') as f:
        json.dump(pruned_forest, f, indent=4)

    # ---------------------------------------------------------
    # 2. Build the Visual Hierarchy (FullTree.json)
    # ---------------------------------------------------------
    true_roots = [pkg for pkg, data in pruned_forest.items() if not data["is_dependency"]]

    full_tree = {}
    for root in sorted(true_roots):
        full_tree[root] = build_nested_tree(forest, root)

    with open(FULL_TREE_OUTPUT, 'w') as f:
        json.dump(full_tree, f, indent=4)

    print(f"🌲 Original Forest Size:   {len(all_packages)} packages")
    print(f"🪵  Strict Dependencies:    {sum(1 for v in pruned_forest.values() if v['is_dependency'])} packages")
    print(f"👑 True Sovereign Roots:   {len(true_roots)} packages")
    print(f"✅ Map Saved to: {PRUNED_OUTPUT}")
    print(f"✅ Deep Tree Saved to: {FULL_TREE_OUTPUT}")

if __name__ == "__main__":
    prune_forest()
