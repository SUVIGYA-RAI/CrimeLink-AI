"""
Network Analysis - Models
-------------------------
Stores pre-computed graph metrics so the results page loads fast.
Metrics are recalculated whenever the investigator clicks "Rebuild Graph".
"""
from django.db import models


class GraphNode(models.Model):
    """
    Represents one node in the criminal network graph.
    Each node corresponds to an entity in the database.
    """
    entity_type         = models.CharField(max_length=50)   # person, vehicle, case, organization
    entity_id           = models.PositiveIntegerField()
    label               = models.CharField(max_length=200)  # display name on graph
    degree_centrality   = models.FloatField(default=0.0)    # how many direct connections
    betweenness         = models.FloatField(default=0.0)    # how often on shortest paths
    pagerank            = models.FloatField(default=0.0)    # importance / influence score
    component_id        = models.IntegerField(default=0)    # which connected group it belongs to
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('entity_type', 'entity_id')
        ordering = ['-degree_centrality']

    def __str__(self):
        return f"{self.entity_type.capitalize()}: {self.label}"
