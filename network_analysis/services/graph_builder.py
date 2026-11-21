"""
Graph Builder Service
----------------------
Reads approved EntityRelationships and direct database relationships from the DB
and constructs a rich NetworkX graph representing the criminal intelligence network.
"""
import networkx as nx
from ai_analysis.models import EntityRelationship
from cases.models import Case
from entities.models import Person, Vehicle, Organization, Location, PhoneRecord


def build_graph(include_pending=False):
    """
    Build a NetworkX DiGraph from EntityRelationship records as well as
    confirmed direct database relationships between cases and entities.

    Parameters
    ----------
    include_pending : bool
        If True, include relationships with review_status='pending' as well.

    Returns
    -------
    G : networkx.DiGraph
    """
    G = nx.DiGraph()

    # 1. Add Explicit EntityRelationship records
    if include_pending:
        rels = EntityRelationship.objects.all()
    else:
        rels = EntityRelationship.objects.filter(review_status='verified')

    for rel in rels:
        src = f"{rel.source_entity_type.lower()}:{rel.source_entity_id}"
        tgt = f"{rel.target_entity_type.lower()}:{rel.target_entity_id}"

        G.add_node(src, entity_type=rel.source_entity_type.lower(), entity_id=rel.source_entity_id)
        G.add_node(tgt, entity_type=rel.target_entity_type.lower(), entity_id=rel.target_entity_id)
        G.add_edge(src, tgt, label=rel.relationship_type.replace('_', ' ').title())

    # 2. Add Direct Case <-> Entity database relationships to guarantee complete connectivity
    cases = Case.objects.prefetch_related('persons', 'vehicles', 'organizations', 'locations').all()
    for c in cases:
        case_node = f"case:{c.pk}"
        G.add_node(case_node, entity_type='case', entity_id=c.pk)

        # Case -> Person
        for p in c.persons.all():
            p_node = f"person:{p.pk}"
            G.add_node(p_node, entity_type='person', entity_id=p.pk)
            if not G.has_edge(case_node, p_node):
                G.add_edge(case_node, p_node, label='Involved In')

        # Case -> Vehicle
        for v in c.vehicles.all():
            v_node = f"vehicle:{v.pk}"
            G.add_node(v_node, entity_type='vehicle', entity_id=v.pk)
            if not G.has_edge(case_node, v_node):
                G.add_edge(case_node, v_node, label='Associated Vehicle')
            # If vehicle has owner
            if v.owner:
                owner_node = f"person:{v.owner.pk}"
                G.add_node(owner_node, entity_type='person', entity_id=v.owner.pk)
                if not G.has_edge(owner_node, v_node):
                    G.add_edge(owner_node, v_node, label='Owns')

        # Case -> Organization
        for o in c.organizations.all():
            o_node = f"organization:{o.pk}"
            G.add_node(o_node, entity_type='organization', entity_id=o.pk)
            if not G.has_edge(case_node, o_node):
                G.add_edge(case_node, o_node, label='Connected Org')

        # Case -> Location
        for loc in c.locations.all():
            loc_node = f"location:{loc.pk}"
            G.add_node(loc_node, entity_type='location', entity_id=loc.pk)
            if not G.has_edge(case_node, loc_node):
                G.add_edge(case_node, loc_node, label='Incident Location')

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
                'label':       node_id,
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
