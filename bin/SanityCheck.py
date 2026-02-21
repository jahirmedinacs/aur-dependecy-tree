#!/usr/bin/env python3
import os
import json
import sys

ORIGINAL_LIST = "assets/PackagesListParu.txt"
UNCUT_FOREST = "assets/IntermediateReports/UncutForest.json"
OPTIMIZED_FOREST = "report/OptimizedForest.json"

def load_list(filepath):
    """Safely loads a simple text list of packages."""
    if not os.path.exists(filepath):
        return set()
    with open(filepath, 'r') as f:
        return set(line.strip() for line in f if line.strip())


def sanity_check():
    print("🕵️  Starting Sanity Check: Re-growing the tree...")
    
    # 1. Parse the original master list
    original_packages = set()
    try:
        with open(ORIGINAL_LIST, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Split allows parsing formats like `core/pkgname 1.0` if present
                pkg = line.split()[0]
                # Arch quirks: Strip version constraints (e.g. pkg>=1.0)
                for sym in ['>=', '<=', '=', '>', '<']:
                    if sym in pkg:
                        pkg = pkg.split(sym)[0]
                original_packages.add(pkg)
    except FileNotFoundError:
        print(f"❌ Error: {ORIGINAL_LIST} not found.")
        sys.exit(1)

    # 2. Extract our final Optimized Roots
    try:
        with open(OPTIMIZED_FOREST, "r") as f:
            opt_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {OPTIMIZED_FOREST} not found.")
        sys.exit(1)

    optimized_roots = set(opt_data.get("StandalonePackages", []))
    for pkgs in opt_data.get("SuperRoots", {}).values():
        optimized_roots.update(pkgs)

    # 3. Load the raw dependency graph
    try:
        with open(UNCUT_FOREST, "r") as f:
            graph = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {UNCUT_FOREST} not found.")
        sys.exit(1)

    # 4. Breadth-First Search (BFS) to regrow the tree
    # Using competitive programming style optimization:
    reconstructed_set = set()
    queue = []
    
    # Add all valid optimized roots to establish the top layer
    for root in optimized_roots:
        if root in original_packages:
            queue.append(root)
            reconstructed_set.add(root)

    # Fast BFS traversal using list with integer pointer (avoids list pop(0) scaling issue)
    head = 0
    while head < len(queue):
        current = queue[head]
        head += 1
        
        # If the package has mapped dependencies
        if current in graph:
            for dep in graph[current]:
                # We only traverse and save packages that belong to our original list
                if dep in original_packages and dep not in reconstructed_set:
                    reconstructed_set.add(dep)
                    queue.append(dep)

    # 5. The Verdict
    missing = original_packages - reconstructed_set

    print(f"\n📊 RESULTS:")
    print(f"Original List Size: {len(original_packages)}")
    print(f"Reconstructed Size: {len(reconstructed_set)}")

    if not missing:
        print("\n✅ PERFECT MATCH! No information was lost. The roots cover the entire forest.")
    else:
        print(f"\n⚠️  {len(missing)} packages were in the original list but not reached by the roots.")
        print("💡 NOTE: This is usually perfectly normal! It happens due to 'Virtual Packages'.")
        print("   (e.g., An app requests 'dbus-units', but you specifically installed 'dbus-broker-units').")
        print("\nMissing packages for your review:")
        for m in sorted(list(missing)):
            print(f" - {m}")
        explicit_packages = load_list("assets/IntermediateReports/ExplicitPackages.txt")
        implicit_packages = load_list("assets/IntermediateReports/ImplicitPackages.txt")
        
        missing_explicit = sorted([p for p in missing if p in explicit_packages or (p not in explicit_packages and p not in implicit_packages)])
        missing_implicit = sorted([p for p in missing if p in implicit_packages])

        missing_json_obj = {
            "StandalonePackages": missing_explicit,
            "Dependencies": {pkg: {"is_dependency": True, "dependencies": []} for pkg in missing_implicit}
        }
            
        with open("report/MissingPackages.json", "w") as f:
            json.dump(missing_json_obj, f, indent=4)
        print("\n💾 Saved structured missing packages to: report/MissingPackages.json")

if __name__ == "__main__":
    sanity_check()
