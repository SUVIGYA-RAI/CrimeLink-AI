"""
Graph Metrics Service
---------------------
Calculates NetworkX centrality metrics and stores them in the GraphNode table.

Metric explanations (plain English):
- Degree Centrality   : fraction of nodes this node is directly connected to.
                        High value → many direct connections.
- Betweenness         : how often this node sits on the shortest path between other nodes.
                        High value → acts as a bridge in the network.
- PageRank            : importance / influence score (same idea as Google PageRank).
                        High value → connected to other important nodes.
- Connected Components: groups of nodes that are all reachable from each other.
"""
import networkx as nx
from network_analysis.models import GraphNode
from .graph_builder import build_graph


def compute_and_save_metrics(include_pending=False):
    """
    Build the graph, calculate all metrics, persist them in GraphNode.
    Returns a summary dict for the view to display.
    """
    G = build_graph(include_pending=include_pending)

    if G.number_of_nodes() == 0:
        return {
            'nodes': 0, 'edges': 0, 'components': 0,
            'top_nodes': [], 'message': 'No verified relationships found. Add and verify relationships first.'
        }

    # Undirected copy for certain algorithms
    UG = G.to_undirected()

    # ── Centrality metrics ─────────────────────────────────────────────────────
    degree_centrality = nx.degree_centrality(G)
    try:
        betweenness = nx.betweenness_centrality(G)
    except Exception:
        betweenness = {n: 0.0 for n in G.nodes()}
    try:
        pagerank = nx.pagerank(G, alpha=0.85)
    except Exception:
        pagerank = {n: 0.0 for n in G.nodes()}

    # ── Connected components ───────────────────────────────────────────────────
    components = list(nx.connected_components(UG))
    component_map = {}  # node_id → component index
    for idx, component in enumerate(components):
        for node in component:
            component_map[node] = idx

    # ── Persist to DB ──────────────────────────────────────────────────────────
    GraphNode.objects.all().delete()  # fresh rebuild

    for node_id, data in G.nodes(data=True):
        entity_type = data.get('entity_type', 'unknown')
        entity_id   = data.get('entity_id', 0)

        GraphNode.objects.update_or_create(
            entity_type=entity_type,
            entity_id=entity_id,
            defaults={
                'label':              node_id,
                'degree_centrality':  round(degree_centrality.get(node_id, 0.0), 4),
                'betweenness':        round(betweenness.get(node_id, 0.0), 4),
                'pagerank':           round(pagerank.get(node_id, 0.0), 4),
                'component_id':       component_map.get(node_id, 0),
            }
        )

    top_nodes = GraphNode.objects.order_by('-degree_centrality')[:5]

    return {
        'nodes':      G.number_of_nodes(),
        'edges':      G.number_of_edges(),
        'components': len(components),
        'top_nodes':  list(top_nodes),
        'message':    'Graph metrics calculated successfully.',
    }
