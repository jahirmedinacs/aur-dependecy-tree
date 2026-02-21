#!/usr/bin/env python3
import json
import subprocess

INPUT_JSON = "assets/IntermediateReports/PrunedForest.json"
OUTPUT_JSON = "assets/IntermediateReports/SuperRoots.json"

def find_super_roots():
    print("🔍 Scanning packages for group memberships...")
    
    with open(INPUT_JSON, 'r') as f:
        pruned_map = json.load(f)

    # Filter out everything that is strictly a dependency; keep only True Roots
    roots = [pkg for pkg, data in pruned_map.items() if not data.get("is_dependency", True)]

    grouped_forest = {}
    standalone = []

    # Query paru for all root packages at once to save time
    # LANG=C forces English output for safe parsing
    if not roots:
        print("⚠️  No roots found to find super groups for!")
        return

    try:
        # Use -Si to query Arch repos for group memberships of these known roots
        result = subprocess.run(
            ['paru', '-Si'] + roots,
            capture_output=True, text=True, env={"LANG": "C", "COLUMNS": "10000"}
        )
    except FileNotFoundError:
        print("❌ Error: paru not found!")
        return

    current_pkg = None
    
    for line in result.stdout.split('\n'):
        # Catch the package name
        if line.startswith("Name") and ":" in line:
            current_pkg = line.split(":", 1)[1].strip()
            
        # Catch the group(s)
        elif line.startswith("Groups") and current_pkg:
            groups_str = line.split(":", 1)[1].strip()
            
            if groups_str and groups_str != "None":
                # Splitting groups if a package belongs to multiple
                for group in groups_str.split():
                    if group not in grouped_forest:
                        grouped_forest[group] = []
                    grouped_forest[group].append(current_pkg)
            else:
                standalone.append(current_pkg)
                
            # Lock until next block
            current_pkg = None
    dependencies_map = {pkg: data for pkg, data in pruned_map.items() if data.get("is_dependency", True)}

    final_output = {
        "SuperRoots": grouped_forest,
        "StandalonePackages": sorted(standalone),
        "Dependencies": dependencies_map
    }

    with open(OUTPUT_JSON, 'w') as f:
        json.dump(final_output, f, indent=4)

    print(f"🎯 Found {len(grouped_forest)} Super Roots (Groups).")
    print(f"🐺 Left with {len(standalone)} Standalone packages.")
    print(f"✅ Saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    find_super_roots()
