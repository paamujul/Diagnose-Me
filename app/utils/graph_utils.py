import networkx as nx
from typing import List, Set, Dict, Tuple


def calculate_graph_metrics(graph: nx.Graph) -> Dict:
    """Calculate graph metrics for analysis"""
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "density": nx.density(graph),
        "average_degree": sum(dict(graph.degree()).values()) / graph.number_of_nodes()
        if graph.number_of_nodes() > 0
        else 0,
    }


def find_shortest_path(graph: nx.Graph, source: str, target: str) -> List[str]:
    """Find shortest path between two nodes"""
    try:
        return nx.shortest_path(graph, source, target)
    except nx.NetworkXNoPath:
        return []


def get_node_neighbors(graph: nx.Graph, node: str, depth: int = 1) -> Set[str]:
    """Get neighbors of a node up to specified depth"""
    neighbors = set()
    if node not in graph:
        return neighbors

    current_level = {node}
    for _ in range(depth):
        next_level = set()
        for n in current_level:
            next_level.update(graph.neighbors(n))
        neighbors.update(next_level)
        current_level = next_level

    neighbors.discard(node)
    return neighbors
