from django.test import TestCase
from ai_analysis.models import EntityRelationship
from network_analysis.services.graph_builder import build_graph, graph_to_cytoscape
from network_analysis.services.graph_metrics import compute_and_save_metrics
from network_analysis.models import GraphNode


class NetworkAnalysisServicesTest(TestCase):
    def setUp(self):
        # Create verified relationships
        EntityRelationship.objects.create(
            source_entity_type='person',
            source_entity_id=1,
            target_entity_type='vehicle',
            target_entity_id=10,
            relationship_type='Owns',
            review_status='verified',
            evidence_reference='Registration records'
        )
        EntityRelationship.objects.create(
            source_entity_type='person',
            source_entity_id=1,
            target_entity_type='organization',
            target_entity_id=5,
            relationship_type='Member Of',
            review_status='verified',
            evidence_reference='Company registry'
        )

    def test_build_graph(self):
        G = build_graph(include_pending=False)
        self.assertEqual(G.number_of_nodes(), 3)
        self.assertEqual(G.number_of_edges(), 2)

    def test_graph_to_cytoscape(self):
        G = build_graph(include_pending=False)
        elements = graph_to_cytoscape(G)
        node_elements = [el for el in elements if 'source' not in el['data']]
        edge_elements = [el for el in elements if 'source' in el['data']]
        self.assertEqual(len(node_elements), 3)
        self.assertEqual(len(edge_elements), 2)

    def test_compute_metrics(self):
        summary = compute_and_save_metrics(include_pending=False)
        self.assertEqual(summary['nodes'], 3)
        self.assertEqual(summary['edges'], 2)
        self.assertTrue(GraphNode.objects.filter(entity_type='person', entity_id=1).exists())
