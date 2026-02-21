#!/usr/bin/env python3
import os
import sys

TO_COMPARE_DIR = "QuickUtils/ToCompare"
TO_REPLICATE_DIR = "QuickUtils/ToReplicate"
CONSENSUS_DIR = "assets/Consensus"
OUTPUT_FILE = f"{CONSENSUS_DIR}/ConsensusList.txt"

def load_packages(filepath):
    """Reads a file and returns a set of package names, stripping versions."""
    packages = set()
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Split allows parsing formats like `core/pkgname 1.0`
                pkg = line.split()[0]
                # Arch quirks: Strip version constraints
                for sym in ['>=', '<=', '=', '>', '<']:
                    if sym in pkg:
                        pkg = pkg.split(sym)[0]
                packages.add(pkg)
    except FileNotFoundError:
        print(f"⚠️  Warning: {filepath} not found.")
    return packages

def generate_consensus():
    print("🤝 Starting Consensus Generation...")

    # 1. Ensure output directory exists
    os.makedirs(CONSENSUS_DIR, exist_ok=True)

    # 2. Gather ToReplicate packages (Our Reference/Base)
    print(f"📂 Scanning reference lists in {TO_REPLICATE_DIR}/...")
    replicate_files = [f for f in os.listdir(TO_REPLICATE_DIR) if os.path.isfile(os.path.join(TO_REPLICATE_DIR, f))]
    if not replicate_files:
        print(f"❌ Error: No reference lists found in {TO_REPLICATE_DIR}/ to replicate.")
        sys.exit(1)

    reference_packages = set()
    for file in replicate_files:
        reference_packages.update(load_packages(os.path.join(TO_REPLICATE_DIR, file)))
    print(f"   -> Loaded {len(reference_packages)} unique reference packages.")

    # 3. Gather ToCompare packages (Other Computers/Secondary)
    print(f"📂 Scanning comparison lists in {TO_COMPARE_DIR}/...")
    compare_files = [f for f in os.listdir(TO_COMPARE_DIR) if os.path.isfile(os.path.join(TO_COMPARE_DIR, f))]
    
    if not compare_files:
        print("💡 No secondary lists found to compare. The consensus will just be the reference.")
        consensus_packages = reference_packages
    else:
        compare_packages = set()
        for file in compare_files:
            compare_packages.update(load_packages(os.path.join(TO_COMPARE_DIR, file)))
        
        print(f"   -> Loaded {len(compare_packages)} unique comparison packages.")
        
        # The Consensus: We want the packages that exist in our absolute references 
        # (ToReplicate) and potentially find the intersection or union.
        # Based on the prompt "re install on the host machine", a strict Intersection
        # provides only the guaranteed overlapping consensus, while a Union provides
        # an amalgamation. We will generate the strict Intersection (Consensus)
        consensus_packages = reference_packages.intersection(compare_packages)
        print(f"   -> Consensus Intersection: {len(consensus_packages)} packages overlap.")

    # 4. Output the result
    with open(OUTPUT_FILE, "w") as f:
        for pkg in sorted(list(consensus_packages)):
            f.write(pkg + "\n")

    print(f"\n✅ Perfect! Output saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_consensus()
