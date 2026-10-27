"""Two explicit graph views: routing connections and directed downstream supply."""
from graph_algorithms import dfs_reachable

NODES = {"Grid": "grid", "T1": "transformer", "T2": "transformer",
         "H1": "house", "H2": "house", "H3": "house", "H4": "house",
         "Battery A": "battery", "Battery B": "battery", "Solar": "solar"}
SUPPLY = {"Grid": ["T1", "T2"], "T1": ["H1", "H2", "Battery A"],
          "T2": ["H3", "H4", "Battery B", "Solar"]}
DOWNSTREAM = {node: SUPPLY.get(node, []) for node in NODES}
ROUTING = {node: [] for node in NODES}
for parent, children in DOWNSTREAM.items():
    for child in children:
        ROUTING[parent].append(child)
        ROUTING[child].append(parent)
POSITIONS = {"Grid": (0, 3), "T1": (-2, 2), "T2": (2, 2),
             "H1": (-3, 0), "H2": (-2, 0), "Battery A": (-1, 0),
             "H3": (0.5, 0), "H4": (1.5, 0), "Battery B": (2.5, 0), "Solar": (3.5, 0)}


def analyze_failure(transformer):
    if NODES.get(transformer) != "transformer":
        raise ValueError("Select a transformer: T1 or T2.")
    traversal = dfs_reachable(DOWNSTREAM, transformer)
    return {"traversal": traversal,
            "consumers": [n for n in traversal if NODES[n] == "house"],
            "unavailable_edges": [("Grid", transformer)] +
                                 [(transformer, n) for n in DOWNSTREAM[transformer]]}
