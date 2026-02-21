# AUR Dependency Tree Pipeline

A custom Directed Acyclic Graph (DAG) package manager extension for cleanly migrating and managing an Arch Linux system without polluting the explicit pacman database.

## The Goal
Take a flat text file of installed packages (e.g., from `paru -Qq`), mathematically deduce which ones are top-level applications (Roots) and which are just dependencies, group them by Arch meta-groups, and generate a clean installation blueprint.

This prevents the classic Arch issue where restoring from a flat list flags every library (like `qt6-base` or `wayland`) as an `explicit` install, making future maintenance and system pruning nearly impossible.

## The DAG Pipeline: Step-by-Step

The project is orchestrated sequentially using [Task](https://taskfile.dev/):

### 1. The Uncut Forest (`bin/GeneratingUncutForest.sh`)
* **Action:** Strips version numbers from the raw text file and queries `paru -Si` to grab the dependencies for every single package.
* **Output:** `assets/IntermediateReports/UncutForest.json` — A massive hash map linking every package to an array of its dependencies (`{"package": ["dep1", "dep2"]}`).

### 2. Pruning the Forest (`bin/PruningTheForest.py`)
* **Action:** Uses basic Set Theory to mathematically subtract all known dependencies from the master list.
* **Output:** `assets/IntermediateReports/PrunedForest.json` — A clean array of only the **"True Roots"** (top-level apps with an in-degree of 0, like `firefox`, `hyprland`, `zapzap`).

### 3. Finding Super Roots (`bin/FindingSuperRoots.py`)
* **Action:** Queries the True Roots against the Arch databases to see which official groups they belong to (e.g., `plasma`, `base-devel`, `gnome`).
* **Output:** `assets/IntermediateReports/SuperRoots.json` — Splits the list into `SuperRoots` (Group Name -> Array of Packages) and `StandalonePackages`.

### 4. Optimizing the Forest (`bin/OptimizingTheForest.py`)
* **Action:** Runs a Greedy **"Set Cover"** algorithm. It ranks Arch groups by size, lets the largest groups claim their packages first, and eliminates redundant or smaller overlapping sub-groups to ensure a mathematically perfect, non-overlapping graph.
* **Output:** `report/OptimizedForest.json` — The final installation blueprint.

### 5. The Sanity Check (`bin/SanityCheck.py`)
* **Action:** Performs a highly optimized List/Pointer-based **Breadth-First Search (BFS)** starting from the `OptimizedForest.json` and moving downwards via the `UncutForest.json` map to verify the integrity of the DAG. It ensures every package from the original text list is accounted for within the reach of the roots.
* **Output:** `report/MissingPackages.json` — A list of any unreached packages. (A small handful is normal, heavily consisting of debug symbols or virtual packages mapped to specific overlays like `dbus-units` -> `dbus-broker-units`).

## Usage

Ensure you have `go-task` installed (`pacman -S go-task`).

To run the entire migration analysis:
```bash
task Default
```

If you don't supply a package list in `assets/PackagesListParu.txt`, the `Setup` task will automatically generate one for your current system by fetching `paru -Qq`.

## Utility: Cross-Host Consensus

If you are managing multiple machines and want to compare a master blueprint against a specific host's current state:

1. Drop your Master Blueprint (the machine you want to replicate) into `QuickUtils/ToReplicate/` as a text file.
2. Drop the packages from your secondary host into `QuickUtils/ToCompare/`.
3. Run the consensus task:
```bash
go-task Compare
```
This utility mathematically treats the `ToReplicate` list as the absolute source of truth and uses the `ToCompare` lists as a filter, outputting two clean JSON lists:
* `assets/Consensus/ToInstall_OptimizedForest.json` (Packages in the Master blueprint that the host is missing).
* `assets/Consensus/AlreadyExists_OptimizedForest.json` (Packages in the Master blueprint that the host already has satisfied).

*(The identical structural breakdown is mapped for the `MissingPackages.json` analysis).*

### Preparing the Final Installer

Once you have generated your consensus, you can easily compile it into a simple flat text file for `pacman` or `paru` to ingest:
```bash
go-task PrepareInstallationList
```
This utility flattens the `ToInstall` arrays from the Consensus JSON drops and outputs `report/FinalInstallationList.txt`.

Inside this text file, all the core root packages are strictly listed line-by-line, and any unreached Virtual/Missing packages are safely appended purely as comments (`#`) at the bottom of the file for manual human review without breaking the package manager.
