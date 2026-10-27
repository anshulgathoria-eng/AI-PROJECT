"""Manual queue-based BFS and stack-based DFS, including cyclic networks."""
from collections import deque


def bfs_nearest_source(graph, start, available_sources, blocked_nodes=()):
    blocked = set(blocked_nodes)
    if start not in graph or start in blocked:
        return {"source": None, "path": [], "connections": None, "traversal": []}
    queue, parents, traversal = deque([start]), {start: None}, []
    while queue:
        node = queue.popleft()
        traversal.append(node)
        if node in available_sources:
            path, current = [], node
            while current is not None:
                path.append(current)
                current = parents[current]
            return {"source": node, "path": path[::-1], "connections": len(path) - 1,
                    "traversal": traversal}
        for neighbor in graph.get(node, []):
            if neighbor not in parents and neighbor not in blocked:
                parents[neighbor] = node
                queue.append(neighbor)
    return {"source": None, "path": [], "connections": None, "traversal": traversal}


def dfs_reachable(graph, start, blocked_nodes=()):
    if start not in graph or start in blocked_nodes:
        return []
    stack, visited, traversal = [start], set(blocked_nodes), []
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        traversal.append(node)
        stack.extend(reversed(graph.get(node, [])))
    return traversal
