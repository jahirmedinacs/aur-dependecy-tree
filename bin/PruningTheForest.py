#!/usr/bin/env python3
import json

INPUT_JSON = "assets/IntermediateReports/UncutForest.json"
OUTPUT_JSON = "assets/IntermediateReports/PrunedForest.json"

def prune_forest():
    print("🪓 Chopping down the dependencies...")
    
    with open(INPUT_JSON, 'r') as f:
        forest = json.load(f)

    # Set A: Every package you explicitly listed
    all_packages = set(forest.keys())

    # Set B: Flatten every dependency list into one giant set
    all_dependencies = set(dep for deps in forest.values() for dep in deps)

    # The Magic Cut: Subtract the dependencies from the master list
    # We sort it alphabetically so the JSON is organized
    true_roots = sorted(list(all_packages - all_dependencies))

    # Save the pruned roots as a cleanly formatted JSON array
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(true_roots, f, indent=4)

    print(f"🌲 Original Forest Size:   {len(all_packages)} packages")
    print(f"🪵  Pruned Dependencies:    {len(all_packages) - len(true_roots)} packages")
    print(f"👑 True Roots Remaining:   {len(true_roots)} packages")
    print(f"✅ Saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    prune_forest()
