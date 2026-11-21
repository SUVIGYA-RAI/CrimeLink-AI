"""
AI Analysis - Models
--------------------
Provides models for case-centric AI entity extraction, relationship tracking,
and explainable anomaly detection alerts.
"""
from django.db import models
from django.contrib.auth.models import User
from data_management.models import UploadedFile


class ExtractedCase(models.Model):
    """
    Case-level extraction staged from an uploaded FIR / investigation document.
    Enforces case-centric AI analysis: all extracted persons, vehicles, phone records,
    organizations, locations, and relationships belong directly to this case.
    """
    REVIEW_CHOICES = [
        ('pending',  'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    uploaded_file     = models.ForeignKey(
        UploadedFile, on_delete=models.CASCADE,
        related_name='extracted_cases'
    )
    case_number       = models.CharField(max_length=50, blank=True)
    title             = models.CharField(max_length=200)
    description       = models.TextField(blank=True)
    case_type         = models.CharField(max_length=50, default='other')
    incident_location = models.CharField(max_length=200, blank=True)
    review_status     = models.CharField(max_length=20, choices=REVIEW_CHOICES, default='pending')
    committed_case    = models.ForeignKey(
        'cases.Case', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='source_extractions'
    )
    extracted_data    = models.JSONField(
        default=dict, blank=True,
        help_text="Structured case payload with nested entities and relationships"
    )
    reviewed_by       = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_cases'
    )
    reviewed_at       = models.DateTimeField(null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Extracted Case: {self.case_number or 'Unnumbered'} - {self.title} ({self.review_status})"


class ExtractedEntity(models.Model):
    """
    Entity extracted from a FIR document by spaCy or regex.
    Can be grouped under an ExtractedCase to maintain case-centric context.
    """
    REVIEW_CHOICES = [
        ('pending',  'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    uploaded_file     = models.ForeignKey(
        UploadedFile, on_delete=models.SET_NULL, null=True,
        related_name='extracted_entities'
    )
    extracted_case    = models.ForeignKey(
        ExtractedCase, on_delete=models.CASCADE, null=True, blank=True,
        related_name='entities'
    )
    related_case      = models.ForeignKey(
        'cases.Case', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='extracted_entities'
    )
    entity_text       = models.CharField(max_length=255)
    entity_type       = models.CharField(max_length=50)
    role              = models.CharField(max_length=100, blank=True, help_text="Contextual role (e.g. Suspect, Complainant, Owner)")
    extraction_method = models.CharField(
        max_length=20,
        choices=[('spacy', 'spaCy'), ('regex', 'Regex')]
    )
    confidence        = models.FloatField(blank=True, null=True)
    review_status     = models.CharField(
        max_length=20,
        choices=REVIEW_CHOICES,
        default='pending',
    )
    reviewed_by       = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_entities'
    )
    reviewed_at       = models.DateTimeField(null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.entity_text} ({self.entity_type}) – {self.review_status}"


class EntityRelationship(models.Model):
    """
    Flexible relationship between any two entities or between a Case and an entity.

    IMPORTANT: Every relationship must cite an evidence_reference.
               Relationships do NOT imply guilt or criminal involvement.
    """
    REVIEW_CHOICES = [
        ('pending',  'Pending Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    source_entity_type = models.CharField(max_length=50)
    source_entity_id   = models.PositiveIntegerField()
    target_entity_type = models.CharField(max_length=50)
    target_entity_id   = models.PositiveIntegerField()
    relationship_type  = models.CharField(max_length=100)
    related_case       = models.ForeignKey(
        'cases.Case', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='relationships'
    )
    evidence_reference = models.TextField(blank=True)
    confidence_score   = models.FloatField(default=1.0)
    review_status      = models.CharField(max_length=20, choices=REVIEW_CHOICES, default='pending')
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return (f"{self.source_entity_type}:{self.source_entity_id} "
                f"→ {self.target_entity_type}:{self.target_entity_id} "
                f"({self.relationship_type})")

    def get_source_label(self):
        return self._resolve_label(self.source_entity_type, self.source_entity_id)

    def get_target_label(self):
        return self._resolve_label(self.target_entity_type, self.target_entity_id)

    def _resolve_label(self, entity_type, entity_id):
        try:
            entity_type = (entity_type or '').lower()
            if entity_type == 'person':
                from entities.models import Person
                return Person.objects.get(pk=entity_id).full_name
            elif entity_type == 'vehicle':
                from entities.models import Vehicle
                return Vehicle.objects.get(pk=entity_id).registration_number
            elif entity_type == 'organization':
                from entities.models import Organization
                return Organization.objects.get(pk=entity_id).name
            elif entity_type == 'location':
                from entities.models import Location
                return Location.objects.get(pk=entity_id).location_name
            elif entity_type == 'case':
                from cases.models import Case
                c = Case.objects.get(pk=entity_id)
                return f"{c.case_number} - {c.title}"
            elif entity_type in ('phone', 'phonerecord'):
                from entities.models import PhoneRecord
                rec = PhoneRecord.objects.get(pk=entity_id)
                return f"{rec.caller_number} → {rec.receiver_number}"
        except Exception:
            pass
        return f"{entity_type.capitalize()} #{entity_id}"


class AnalysisAlert(models.Model):
    """
    Anomaly alert generated by the detection engine.

    DISCLAIMER: Alerts are investigative leads only.
                They do NOT imply guilt or criminal involvement.
    """
    SEVERITY_CHOICES = [
        ('low',    'Low'),
        ('medium', 'Medium'),
        ('high',   'High'),
    ]
    REVIEW_CHOICES = [
        ('pending',   'Pending Review'),
        ('reviewed',  'Reviewed'),
        ('dismissed', 'Dismissed'),
    ]

    alert_type     = models.CharField(max_length=100)
    description    = models.TextField()
    related_record = models.CharField(max_length=200, blank=True)
    related_case   = models.ForeignKey(
        'cases.Case', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='analysis_alerts'
    )
    severity       = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    review_status  = models.CharField(max_length=20, choices=REVIEW_CHOICES, default='pending')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.severity.upper()}] {self.alert_type}"
