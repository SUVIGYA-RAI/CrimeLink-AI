"""
Cases app models.
Defines the Case model for investigation case management.
"""

from django.db import models
from django.contrib.auth.models import User


class Case(models.Model):
    """
    Represents an investigation case in the system.
    """
    # Status choices for the case
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('under_investigation', 'Under Investigation'),
        ('closed', 'Closed'),
    ]

    # Priority levels for the case
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    # Case type options
    CASE_TYPE_CHOICES = [
        ('theft', 'Theft'),
        ('fraud', 'Fraud'),
        ('cyber_crime', 'Cyber Crime'),
        ('murder', 'Murder'),
        ('assault', 'Assault'),
        ('drug_trafficking', 'Drug Trafficking'),
        ('money_laundering', 'Money Laundering'),
        ('kidnapping', 'Kidnapping'),
        ('other', 'Other'),
    ]

    case_number = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    case_type = models.CharField(max_length=30, choices=CASE_TYPE_CHOICES, default='other')
    location = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')

    # Who created this case
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cases_created')

    date_created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_created']  # Newest cases first

    def __str__(self):
        return f"{self.case_number} - {self.title}"

    def get_status_badge(self):
        """Return Bootstrap badge class based on status."""
        badges = {
            'open': 'badge-open',
            'under_investigation': 'badge-investigating',
            'closed': 'badge-closed',
        }
        return badges.get(self.status, 'bg-secondary')

    def get_priority_badge(self):
        """Return Bootstrap badge class based on priority."""
        badges = {
            'low': 'bg-success',
            'medium': 'bg-warning',
            'high': 'bg-danger',
        }
        return badges.get(self.priority, 'bg-secondary')
