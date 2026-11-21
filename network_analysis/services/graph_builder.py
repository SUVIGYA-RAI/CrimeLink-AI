"""
Graph Builder Service
----------------------
Reads approved EntityRelationships from the DB and constructs a NetworkX graph.
"""
import networkx as nx
from ai_analysis.models import EntityRelationship


def build_graph(include_pending=False):
    """
    Build a NetworkX DiGraph from EntityRelationship records.

    Parameters
    ----------
    include_pending : bool
        If True, include relationships with review_status='pending' as well.

    Returns
    -------
    G : networkx.DiGraph
    """
    G = nx.DiGraph()

    if include_pending:
        rels = EntityRelationship.objects.all()
    else:
        rels = EntityRelationship.objects.filter(review_status='verified')

    for rel in rels:
        # Node IDs are strings like "person:1" or "vehicle:3"
        src = f"{rel.source_entity_type}:{rel.source_entity_id}"
        tgt = f"{rel.target_entity_type}:{rel.target_entity_id}"

        # Add nodes with metadata
        G.add_node(src, entity_type=rel.source_entity_type, entity_id=rel.source_entity_id)
        G.add_node(tgt, entity_type=rel.target_entity_type, entity_id=rel.target_entity_id)

        # Add directed edge with label
        G.add_edge(src, tgt, label=rel.relationship_type)

    return G


def graph_to_cytoscape(G):
    """
    Convert a NetworkX graph to Cytoscape.js element format.

    Returns
    -------
    list of dicts  (Cytoscape.js elements array)
    """
    elements = []

    # Nodes
    for node_id, data in G.nodes(data=True):
        elements.append({
            'data': {
                'id':          node_id,
                'label':       node_id,                     # replaced with real name in view
                'entity_type': data.get('entity_type', ''),
                'entity_id':   data.get('entity_id', 0),
            }
        })

    # Edges
    for src, tgt, data in G.edges(data=True):
        elements.append({
            'data': {
                'id':     f"{src}__{tgt}",
                'source': src,
                'target': tgt,
                'label':  data.get('label', ''),
            }
        })

    return elements
