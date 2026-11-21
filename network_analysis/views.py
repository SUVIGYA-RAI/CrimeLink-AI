"""
Network Analysis - Views
------------------------
Thin views that call service functions and render templates.
"""
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from ai_analysis.models import EntityRelationship
from .models import GraphNode
from .services.graph_builder import build_graph, graph_to_cytoscape
from .services.graph_metrics import compute_and_save_metrics


@login_required
def home(request):
    """Network analysis summary: metrics and top nodes."""
    nodes = GraphNode.objects.order_by('-degree_centrality')
    total_nodes = nodes.count()
    total_edges = EntityRelationship.objects.filter(review_status='verified').count()

    context = {
        'nodes':       nodes[:10],
        'total_nodes': total_nodes,
        'total_edges': total_edges,
    }
    return render(request, 'network_analysis/home.html', context)


@login_required
def rebuild_graph(request):
    """Recalculate all NetworkX metrics and store them in GraphNode."""
    include_pending = request.GET.get('include_pending', 'false') == 'true'
    summary = compute_and_save_metrics(include_pending=include_pending)
    messages.success(request, summary['message'])
    return redirect('network_analysis:home')


@login_required
def network_graph(request):
    """
    Interactive Cytoscape.js visualization.
    Builds graph data and passes it as JSON to the template.
    """
    include_pending = request.GET.get('include_pending', 'false') == 'true'
    G = build_graph(include_pending=include_pending)
    elements = graph_to_cytoscape(G)

    # Enrich node labels with actual entity names from the DB
    # For persons, vehicles, cases, organizations — look them up
    for el in elements:
        if 'source' not in el['data']:   # it is a node, not an edge
            entity_type = el['data']['entity_type']
            entity_id   = el['data']['entity_id']
            label = _get_entity_label(entity_type, entity_id)
            el['data']['label'] = label

    context = {
        'elements_json':   json.dumps(elements),
        'include_pending': include_pending,
        'node_count':      G.number_of_nodes(),
        'edge_count':      G.number_of_edges(),
    }
    return render(request, 'network_analysis/network_graph.html', context)


def _get_entity_label(entity_type, entity_id):
    """Return a human-readable label for a node."""
    try:
        if entity_type == 'person':
            from entities.models import Person
            obj = Person.objects.get(pk=entity_id)
            return obj.full_name
        elif entity_type == 'vehicle':
            from entities.models import Vehicle
            obj = Vehicle.objects.get(pk=entity_id)
            return obj.registration_number
        elif entity_type == 'organization':
            from entities.models import Organization
            obj = Organization.objects.get(pk=entity_id)
            return obj.name
        elif entity_type == 'location':
            from entities.models import Location
            obj = Location.objects.get(pk=entity_id)
            return obj.location_name
        elif entity_type == 'case':
            from cases.models import Case
            obj = Case.objects.get(pk=entity_id)
            return f"{obj.case_number} - {obj.title}"
        elif entity_type in ('phone', 'phonerecord'):
            from entities.models import PhoneRecord
            obj = PhoneRecord.objects.get(pk=entity_id)
            return f"{obj.caller_number} → {obj.receiver_number}"
    except Exception:
        pass
    return f"{entity_type}:{entity_id}"
