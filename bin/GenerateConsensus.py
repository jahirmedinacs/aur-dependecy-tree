#!/usr/bin/env python3
import os
import sys
import json

TO_COMPARE_DIR = "QuickUtils/ToCompare"
TO_REPLICATE_DIR = "QuickUtils/ToReplicate"
CONSENSUS_DIR = "assets/Consensus"
TO_INSTALL_FILE = f"{CONSENSUS_DIR}/ToInstall.json"
ALREADY_EXISTS_FILE = f"{CONSENSUS_DIR}/AlreadyExists.json"

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

    # 2. Gather ToReplicate packages (Our Master Blueprint)
    print(f"📂 Scanning master blueprints in {TO_REPLICATE_DIR}/...")
    replicate_files = [f for f in os.listdir(TO_REPLICATE_DIR) if os.path.isfile(os.path.join(TO_REPLICATE_DIR, f))]
    if not replicate_files:
        print(f"❌ Error: No master blueprint lists found in {TO_REPLICATE_DIR}/.")
        sys.exit(1)

    master_packages = set()
    for file in replicate_files:
        master_packages.update(load_packages(os.path.join(TO_REPLICATE_DIR, file)))
    print(f"   -> Loaded {len(master_packages)} unique packages from the Master Blueprint.")

    # 3. Gather ToCompare packages (The Host Machine's Current State)
    print(f"📂 Scanning host state lists in {TO_COMPARE_DIR}/...")
    compare_files = [f for f in os.listdir(TO_COMPARE_DIR) if os.path.isfile(os.path.join(TO_COMPARE_DIR, f))]
    
    host_packages = set()
    if compare_files:
        for file in compare_files:
            host_packages.update(load_packages(os.path.join(TO_COMPARE_DIR, file)))
        print(f"   -> Loaded {len(host_packages)} unique packages currently on the Host.")
    else:
        print("💡 No host lists found in ToCompare. Assuming the host is completely empty.")

    # 4. Calculate Consensus
    # To Install: Packages in the master blueprint that are NOT on the host
    to_install = master_packages - host_packages
    
    # Already Exists: Packages in the master blueprint that ARE already on the host
    already_exists = master_packages.intersection(host_packages)

    print(f"   -> Analysis: {len(to_install)} packages need to be installed.")
    print(f"   -> Analysis: {len(already_exists)} packages are already satisfied.")

    # 5. Output the results as JSON
    with open(TO_INSTALL_FILE, "w") as f:
        json.dump(sorted(list(to_install)), f, indent=4)
        
    with open(ALREADY_EXISTS_FILE, "w") as f:
        json.dump(sorted(list(already_exists)), f, indent=4)

    print(f"\n✅ Perfect! Output saved to:")
    print(f"   📄 {TO_INSTALL_FILE}")
    print(f"   📄 {ALREADY_EXISTS_FILE}")

if __name__ == "__main__":
    generate_consensus()
