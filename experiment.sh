#! /bin/bash

# 1. Clean your master list and get your current system state
awk '{print $1}' packages.list-paru.txt | sort -u > total.txt
pacman -Qq | sort -u > installed.txt

# 2. Build the dependency pool (Calculate the DAG)
echo "Calculating dependency tree..."
paru -Si $(< total.txt) 2>/dev/null | awk -F': ' '/^Depends On/ {print $2}' | tr -s ' ' '\n' | sed 's/[<>=].*//' | grep -v "None" | sort -u > all_deps.txt

# 3. Split your master list into True Roots and Sub-packages
comm -23 total.txt all_deps.txt > roots.txt
comm -12 total.txt all_deps.txt > deps.txt

# 4. Filter against what you already have installed
comm -23 roots.txt installed.txt > missing_roots.txt
comm -23 deps.txt installed.txt > missing_deps.txt

echo "Missing Roots: $(wc -l < missing_roots.txt) | Missing Deps: $(wc -l < missing_deps.txt)"
echo "Starting installation phase..."

# 5. Loop 1: Install the True Roots (Explicitly)
while read -r pkg; do
    paru -S --noconfirm "$pkg" || echo "$pkg" >> failed_roots.txt
done < missing_roots.txt

# 6. Loop 2: Install the leftover Sub-packages (As Dependencies)
while read -r pkg; do
    paru -S --asdeps --noconfirm "$pkg" || echo "$pkg" >> failed_deps.txt
done < missing_deps.txt

echo "Done! Time to sleep like Patrick."
