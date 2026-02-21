#!/usr/bin/env python3
import json

import os

INPUT_JSON = "assets/IntermediateReports/UncutForest.json"
EXPLICIT_LIST = "assets/IntermediateReports/ExplicitPackages.txt"
IMPLICIT_LIST = "assets/IntermediateReports/ImplicitPackages.txt"
PRUNED_OUTPUT = "assets/IntermediateReports/PrunedForest.json"
FULL_TREE_OUTPUT = "assets/IntermediateReports/FullTree.json"

def load_list(filepath):
    """Safely loads a simple text list of packages."""
    if not os.path.exists(filepath):
        return set()
    with open(filepath, 'r') as f:
        return set(line.strip() for line in f if line.strip())

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
        
    explicit_packages = load_list(EXPLICIT_LIST)
    implicit_packages = load_list(IMPLICIT_LIST)

    # Set A: Every package explicitly listed on the system
    all_packages = set(forest.keys())
    all_dependencies = set(dep for deps in forest.values() for dep in deps)

    # ---------------------------------------------------------
    # 1. Structure the Map (PrunedForest.json)
    # Every package listed exactly once, tagged with its status.
    # ---------------------------------------------------------
    pruned_forest = {}
    for pkg in sorted(list(all_packages)):
        # ENTERPRISE LOGIC OVERRIDE: 
        # Bypass mathematical contradictions (like evdi-dkms vs glibc both being intermediate nodes).
        # We query Pacman's absolute brain:
        if pkg in explicit_packages:
            # User explicitly ran `paru -S pkg`. It is absolutely a Principal Root.
            is_dependency = False
        elif pkg in implicit_packages:
            # It was pulled in automatically as a dependency (`paru -S --asdeps`).
            is_dependency = True
        else:
            # Fallback for custom lists not reflecting the current host DB (DAG graph analysis).
            # If it has children, assume it's a tree/root. Else, it's a dependency leaf.
            has_children = len(forest.get(pkg, [])) > 0
            if has_children:
                is_dependency = False
            else:
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
