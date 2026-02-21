#!/bin/bash
# generating-uncut-forest.sh

INPUT_FILE="assets/PackagesListParu.txt"
JSON_OUT="assets/IntermediateReports/UncutForest.json"

echo "--> 1. Stripping versions from master list..."
awk '{print $1}' "$INPUT_FILE" | sort -u > assets/IntermediateReports/TempPkgList.txt

echo "--> 2. Querying paru for full dependency graph (this takes a moment)..."
# COLUMNS=10000 prevents line-wrapping. LANG=C forces English output for safe parsing.
COLUMNS=10000 LANG=C paru -Si $(< assets/IntermediateReports/TempPkgList.txt) 2>/dev/null > assets/IntermediateReports/TempParuRaw.txt

echo "--> 3. Parsing data into JSON..."
python3 -c '
import json, re

forest = {}
current_pkg = None

with open("assets/IntermediateReports/TempParuRaw.txt", "r") as f:
    for line in f:
        # Catch the package name
        if line.startswith("Name") and ":" in line:
            current_pkg = line.split(":", 1)[1].strip()
            if current_pkg not in forest:
                forest[current_pkg] = []
                
        # Catch the dependencies for the current package
        elif line.startswith("Depends On") and current_pkg:
            deps_str = line.split(":", 1)[1].strip()
            if deps_str != "None":
                # Split by space and strip version constraints (e.g., qt6-base>=6.1.0 -> qt6-base)
                deps = [re.sub(r"[<>=].*", "", d) for d in deps_str.split()]
                forest[current_pkg] = [d for d in deps if d]
            
            # Lock until we hit the next package name
            current_pkg = None 

with open("'"$JSON_OUT"'", "w") as f:
    json.dump(forest, f, indent=4)
'

# Clean up the working files
rm assets/IntermediateReports/TempPkgList.txt assets/IntermediateReports/TempParuRaw.txt

echo "--> DONE! The uncut forest is successfully saved to: $JSON_OUT"
