#!/usr/bin/env python3
import json

INPUT_JSON = "assets/IntermediateReports/SuperRoots.json"
OUTPUT_JSON = "report/OptimizedForest.json"

def optimize_forest():
    print("🧠 Running Greedy Set Cover optimization...")
    
    with open(INPUT_JSON, 'r') as f:
        data = json.load(f)

    super_roots = data.get("SuperRoots", {})
    standalone = data.get("StandalonePackages", [])

    # Step 1: Rank the groups by how many packages they contain (Descending)
    # The biggest groups are the most "valuable" super roots.
    ranked_groups = sorted(super_roots.items(), key=lambda x: len(x[1]), reverse=True)

    optimized_roots = {}
    claimed_packages = set()
    pruned_groups_count = 0

    # Step 2: Let the biggest groups claim their packages first
    for group_name, packages in ranked_groups:
        # Check which packages in this group haven't been claimed by a bigger group yet
        unclaimed_packages = [pkg for pkg in packages if pkg not in claimed_packages]
        
        # If this group actually provides new, unclaimed packages, keep it
        if unclaimed_packages:
            optimized_roots[group_name] = sorted(unclaimed_packages)
            claimed_packages.update(unclaimed_packages)
        else:
            # This group was entirely swallowed by larger groups!
            pruned_groups_count += 1

    # Step 3: Save the mathematically perfect, non-overlapping graph
    dependencies = data.get("Dependencies", {})

    final_output = {
        "SuperRoots": optimized_roots,
        "StandalonePackages": standalone,
        "Dependencies": dependencies
    }

    with open(OUTPUT_JSON, 'w') as f:
        json.dump(final_output, f, indent=4)

    print(f"🔪 Pruned {pruned_groups_count} redundant/overlapping sub-groups.")
    print(f"👑 Kept {len(optimized_roots)} mathematically distinct Super Roots.")
    print(f"✅ Saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    optimize_forest()
