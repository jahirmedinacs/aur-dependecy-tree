#!/usr/bin/env python3
import os
import sys
import json
import fnmatch

TO_COMPARE_DIR = "QuickUtils/ToCompare"
TO_REPLICATE_DIR = "QuickUtils/ToReplicate"
CONSENSUS_DIR = "assets/Consensus"

TO_INSTALL_FOREST = f"{CONSENSUS_DIR}/ToInstall_OptimizedForest.json"
ALREADY_EXISTS_FOREST = f"{CONSENSUS_DIR}/AlreadyExists_OptimizedForest.json"
TO_INSTALL_MISSING = f"{CONSENSUS_DIR}/ToInstall_MissingPackages.json"
ALREADY_EXISTS_MISSING = f"{CONSENSUS_DIR}/AlreadyExists_MissingPackages.json"

def load_json(filepath):
    """Safely loads a JSON file."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Warning: {filepath} not found.")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error: {filepath} is not valid JSON.")
        return None

def find_file(directory, pattern):
    """Finds the first file matching a pattern in a directory."""
    for f in os.listdir(directory):
        if fnmatch.fnmatch(f, pattern):
            return os.path.join(directory, f)
    return None

def compare_forests(master, host):
    """Compares two OptimizedForest DAGs (SuperRoots, StandalonePackages, Dependencies)."""
    to_install = {"SuperRoots": {}, "StandalonePackages": [], "Dependencies": {}}
    already_exists = {"SuperRoots": {}, "StandalonePackages": [], "Dependencies": {}}

    # Normalize inputs: if they are flat lists, treat them as StandalonePackages (e.g., legacy MissingPackages)
    master_dict = master if isinstance(master, dict) else {"SuperRoots": {}, "StandalonePackages": master if isinstance(master, list) else [], "Dependencies": {}}
    host_dict = host if isinstance(host, dict) else {"SuperRoots": {}, "StandalonePackages": host if isinstance(host, list) else [], "Dependencies": {}}

    # 1. Compare Standalone Packages (1-to-1)
    master_standalone = set(master_dict.get("StandalonePackages", []))
    host_standalone = set(host_dict.get("StandalonePackages", []))

    to_install["StandalonePackages"] = sorted(list(master_standalone - host_standalone))
    already_exists["StandalonePackages"] = sorted(list(master_standalone.intersection(host_standalone)))

    # 2. Compare Super Roots (Group-by-Group, then Package-by-Package)
    master_roots = master_dict.get("SuperRoots", {})
    host_roots = host_dict.get("SuperRoots", {})

    for group, m_pkgs in master_roots.items():
        m_set = set(m_pkgs)
        if group in host_roots:
            # Group exists on both. Compare packages inside lazily.
            h_set = set(host_roots[group])
            
            missing_pkgs = m_set - h_set
            existing_pkgs = m_set.intersection(h_set)
            
            if missing_pkgs:
                to_install["SuperRoots"][group] = sorted(list(missing_pkgs))
            if existing_pkgs:
                already_exists["SuperRoots"][group] = sorted(list(existing_pkgs))
        else:
            # Group is completely missing from host. Add all to ToInstall.
            to_install["SuperRoots"][group] = sorted(list(m_set))

    # 3. Compare Strict Dependencies (Dictionary Key intersection)
    master_deps = master_dict.get("Dependencies", {})
    host_deps = host_dict.get("Dependencies", {})
    
    for dep, data in master_deps.items():
        if dep in host_deps:
            already_exists["Dependencies"][dep] = data
        else:
            to_install["Dependencies"][dep] = data

    return to_install, already_exists

# (compare_flat_lists function removed in favor of recursive DAG union logic)

def generate_consensus():
    print("🤝 Starting JSON DAG Consensus Generation...")

    os.makedirs(CONSENSUS_DIR, exist_ok=True)

    # ==========================================
    # 1. Compare OptimizedForest.json
    # ==========================================
    master_forest_path = find_file(TO_REPLICATE_DIR, "*OptimizedForest.json")
    host_forest_path = find_file(TO_COMPARE_DIR, "*OptimizedForest.json")

    if master_forest_path:
        print(f"📂 Analyzing DAG: {master_forest_path}")
        master_forest = load_json(master_forest_path)
        host_forest = load_json(host_forest_path) if host_forest_path else {"SuperRoots": {}, "StandalonePackages": []}
        
        if host_forest_path:
            print(f"📂 Comparing against host DAG: {host_forest_path}")
        else:
            print(f"💡 No host DAG found in {TO_COMPARE_DIR}/. Assuming host is empty.")

        if master_forest:
            install_forest, exists_forest = compare_forests(master_forest, host_forest)
            
            with open(TO_INSTALL_FOREST, "w") as f:
                json.dump(install_forest, f, indent=4)
            with open(ALREADY_EXISTS_FOREST, "w") as f:
                json.dump(exists_forest, f, indent=4)
            
            print(f"   ✅ Saved {TO_INSTALL_FOREST}")
            print(f"   ✅ Saved {ALREADY_EXISTS_FOREST}")
    else:
        print(f"❌ Error: Could not find any OptimizedForest.json in {TO_REPLICATE_DIR}/.")

    # ==========================================
    # 2. Compare MissingPackages.json
    # ==========================================
    master_missing_path = find_file(TO_REPLICATE_DIR, "*MissingPackages.json")
    host_missing_path = find_file(TO_COMPARE_DIR, "*MissingPackages.json")

    if master_missing_path:
        print(f"\n📂 Analyzing MissingList: {master_missing_path}")
        master_missing = load_json(master_missing_path)
        host_missing = load_json(host_missing_path) if host_missing_path else []

        install_missing, exists_missing = compare_forests(master_missing, host_missing)
        
        with open(TO_INSTALL_MISSING, "w") as f:
            json.dump(install_missing, f, indent=4)
        with open(ALREADY_EXISTS_MISSING, "w") as f:
            json.dump(exists_missing, f, indent=4)
            
        print(f"   ✅ Saved {TO_INSTALL_MISSING}")
        print(f"   ✅ Saved {ALREADY_EXISTS_MISSING}")
    else:
        print(f"\n💡 Note: No MissingPackages.json found in {TO_REPLICATE_DIR}/ to compare.")

if __name__ == "__main__":
    generate_consensus()
