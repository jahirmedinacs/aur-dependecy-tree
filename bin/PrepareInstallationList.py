#!/usr/bin/env python3
import json
import os

INSTALL_FOREST_JSON = "assets/Consensus/ToInstall_OptimizedForest.json"
INSTALL_MISSING_JSON = "assets/Consensus/ToInstall_MissingPackages.json"
OUTPUT_FILE = "report/FinalInstallationList.txt"

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

def prepare_installation_list():
    print("📦 Preparing Final Installation List...")

    forest = load_json(INSTALL_FOREST_JSON)
    missing = load_json(INSTALL_MISSING_JSON)

    if not forest:
        print(f"❌ Error: Could not load {INSTALL_FOREST_JSON}. Have you run 'go-task Compare' yet?")
        return

    # Extract all elements that are explicitly installable roots
    explicit_list = []

    # 1. Grab the Group Roots (e.g., plasma, base-devel)
    super_roots = forest.get("SuperRoots", {})
    for group, pkgs in super_roots.items():
        explicit_list.append(group)

    # 2. Grab all StandalonePackages
    standalone = forest.get("StandalonePackages", [])
    explicit_list.extend(standalone)

    # 3. Grab all Implicit Dependencies directly
    implicit_deps = []
    dependencies = forest.get("Dependencies", {})
    if isinstance(dependencies, dict):
        implicit_deps.extend(dependencies.keys())

    # Clean up and deduplicate just in case
    explicit_list = sorted(list(set(explicit_list)))
    implicit_deps = sorted(list(set(implicit_deps)))

    # Process MissingPackages (these go as comments)
    missing_comments = []
    if missing:
        missing_pkgs = missing.get("StandalonePackages", [])
        if missing_pkgs:
            missing_comments = sorted(list(set(missing_pkgs)))

    # Output to File
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write("# ==========================================\n")
        f.write("# FINIALIZED ARCH MIGRATION INSTALL LIST\n")
        f.write("# ==========================================\n\n")

        f.write("# [1] PRINCIPAL ROOTS\n")
        f.write("# Install Explicitly: `paru -S $(< explicit_list)`\n")
        f.write("# ------------------------------------------\n")
        for pkg in explicit_list:
            f.write(pkg + "\n")

        if implicit_deps:
            f.write("\n\n# [2] NATIVE DEPENDENCIES\n")
            f.write("# Install Implicitly: `paru -S --asdeps $(< implicit_list)`\n")
            f.write("# ------------------------------------------\n")
            for pkg in implicit_deps:
                f.write(pkg + "\n")

        # Write missing packages as comments
        if missing_comments:
            f.write("\n\n# ==========================================\n")
            f.write("# MISSING PACKAGES (Virtual / Overlays)\n")
            f.write("# Review these manually. Often perfectly fine to skip.\n")
            f.write("# ==========================================\n")
            for pkg in missing_comments:
                f.write(f"# {pkg}\n")

    print(f"✅ Perfectly compiled {len(explicit_list)} Principal Roots!")
    if implicit_deps:
        print(f"✅ Compiled {len(implicit_deps)} strict Dependencies (--asdeps).")
    if missing_comments:
        print(f"   (Appended {len(missing_comments)} missing packages as comments at the bottom).")
    print(f"\n💾 Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    prepare_installation_list()
