import json

with open("assets/IntermediateReports/UncutForest.json") as f:
    forest = json.load(f)

all_packages = set(forest.keys())
all_dependencies = set(dep for deps in forest.values() for dep in deps)

deps_as_leaves = 0
deps_as_parents = 0

for pkg in all_packages:
    if pkg in all_dependencies:
        has_children = len(forest.get(pkg, [])) > 0
        if has_children:
            deps_as_parents += 1
        else:
            deps_as_leaves += 1

print(f"Dependencies that have children (parents): {deps_as_parents}")
print(f"Dependencies that are leaf nodes: {deps_as_leaves}")
